from typing import Optional, Dict, Any
from .providers import LLMProvider
from .prompts import SystemPrompts, extract_command_from_text
from .prompts_registry import player_messages, gm_messages, judge_messages
from .tools import ToolExecutor
from .audit import AuditLog
from llm_factory import LLMCommandFactory
from .tools.registry import ToolRegistry


class LLMDispatcher:
    def __init__(
        self,
        provider: LLMProvider,
        tool_executor: Optional[ToolExecutor] = None,
        audit_log: Optional[AuditLog] = None,
        session_store: Any | None = None,
    ):
        self.provider = provider
        self.tool_executor = tool_executor
        self.audit_log = audit_log
        self.session_store = session_store

    async def run_player_turn(self, agent_id: str, history_messages: list[dict]) -> Dict[str, Any]:
        messages = player_messages(agent_id, history_messages, self.session_store)

        # Provide tool definitions (reduces prompt token usage; LLM can call tool_help)
        tools = ToolRegistry.as_openai_tools() if self.tool_executor else None

        # Tool-call loop (bounded; max 6 steps)
        result: Dict[str, Any] = {}
        for _ in range(6):
            result = await self.provider.chat(messages, tools=tools)
            self._audit({"type": "LLMResponse", "data": result})

            tool_calls = result.get("tool_calls")
            if not tool_calls or not self.tool_executor:
                break

            for call in tool_calls:
                fn = getattr(call, "function", None)
                tool_name = getattr(fn, "name", None) if fn else None
                args_json = getattr(fn, "arguments", "{}") if fn else "{}"
                try:
                    import json
                    args = json.loads(args_json) if isinstance(args_json, str) else (args_json or {})
                except Exception:
                    args = {}

                out = self.tool_executor.execute(tool_name or "", args)
                # If a transactional command tool executed, stop the turn here.
                if isinstance(out, dict) and ("events_emitted" in out or out.get("success") in (True, False)) and tool_name and tool_name not in ("tool_help", "get_state", "get_history", "end_of_turn"):
                    self._audit({"type": "LLMCommandExecuted", "name": tool_name, "result": out})
                    return {"execution": out}
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": getattr(call, "id", ""),
                        "name": tool_name,
                        "content": str(out),
                    }
                )
        extraction = extract_command_from_text(result.get("content", ""))
        self._audit({"type": "LLMCommandProposed", "name": extraction.command_name, "payload_json": extraction.payload_json})

        # Strict payload instantiation via LLMCommandFactory
        try:
            command = LLMCommandFactory.from_llm(agent_id=agent_id, command_name=extraction.command_name, payload_json=extraction.payload_json)
        except Exception as e:
            self._audit({"type": "LLMCommandInvalid", "error": str(e)})
            return {"error": str(e)}

        # Tool call audit hook (if any tools were called earlier in steps)
        self._audit({"type": "LLMCommandSubmitted", "name": extraction.command_name})
        return {"command": command, "notes": extraction.notes}

    def _audit(self, event: Dict[str, Any]):
        if self.audit_log:
            self.audit_log.append(event)

    async def run_gm_turn(self, agent_id: str, history_messages: list[dict]) -> Dict[str, Any]:
        messages = gm_messages(agent_id, history_messages, self.session_store)
        result = await self.provider.chat(messages)
        self._audit({"type": "LLMResponse", "role": "GM", "data": result})
        return {"content": result.get("content", "")}

    async def run_judge_turn(self, agent_id: str, history_messages: list[dict]) -> Dict[str, Any]:
        messages = judge_messages(agent_id, history_messages, self.session_store)
        result = await self.provider.chat(messages)
        self._audit({"type": "LLMResponse", "role": "JUDGE", "data": result})
        return {"content": result.get("content", "")}
