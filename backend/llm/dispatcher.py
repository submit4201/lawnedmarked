from __future__ import annotations

from typing import Optional, Dict, Any, Callable, Tuple, List
from .providers import LLMProvider
from .prompts import SystemPrompts, extract_command_from_text
from .prompts_registry import player_messages, gm_messages, judge_messages
from .tools import ToolExecutor
from .audit import AuditLog
from llm_factory import LLMCommandFactory
from .tools.registry import ToolRegistry
from core.commands import Command
from core.events import GameEvent


class LLMDispatcher:
    def __init__(
        self,
        provider: LLMProvider,
        tool_executor: Optional[ToolExecutor] = None,
        audit_log: Optional[AuditLog] = None,
        session_store: Any | None = None,
        command_executor: Callable[[str, Command], Tuple[bool, List[GameEvent], str]] | None = None,
    ):
        self.provider = provider
        self.tool_executor = tool_executor
        self.audit_log = audit_log
        self.session_store = session_store
        self.command_executor = command_executor

    def _extract_thought(self, content: str) -> str:
        import re

        if not content:
            return ""
        m = re.search(r"<\|\-THOUGHT\-\|>\s*(.*?)\s*(?:<\|\-ACTION\-\|>|<\|\-OBSERVATION\-\|>|<\|\-REMEMBER\-\|>|<\|\-ENDTURN\-\|>)", content, re.S)
        if m:
            return m.group(1).strip()
        return content.strip()[:500]

    def _wants_end_turn(self, content: str, tool_name: str | None) -> bool:
        if tool_name == "end_of_turn":
            return True
        return "<|-ENDTURN-|>" in (content or "")

    def _tool_is_info(self, name: str) -> bool:
        return name in {"tool_help", "get_state", "get_history"}

    def _tool_is_session(self, name: str) -> bool:
        return name in {"end_of_turn"}

    def _tool_is_command(self, name: str) -> bool:
        return name not in {"tool_help", "get_state", "get_history", "end_of_turn"}

    async def run_player_turn(self, agent_id: str, history_messages: list[dict]) -> Dict[str, Any]:
        """Run a bounded multi-step player turn.

        The model may call informational tools multiple times. If it calls a command tool,
        the dispatcher instantiates the corresponding Command via LLMCommandFactory and
        executes it via the provided command_executor.
        """
        messages = player_messages(agent_id, history_messages, self.session_store)

        tools = ToolRegistry.as_openai_tools() if self.tool_executor else None
        emitted_events: List[GameEvent] = []
        thoughts: List[str] = []
        notes: str | None = None
        last_event_id: str | None = None

        # Initial tool context injection (state + history) so the model doesn't have to fetch it.
        if self.tool_executor:
            try:
                snap = self.tool_executor.execute("get_state", {"agent_id": agent_id})
                hist = self.tool_executor.execute("get_history", {"agent_id": agent_id, "last_event_id": None})
                messages.append({"role": "user", "content": f"STATE_SNAPSHOT: {snap}\nEVENT_HISTORY: {hist}"})
            except Exception:
                # Tool context is best-effort; the model can still call tools explicitly.
                pass

        result: Dict[str, Any] = {}
        for step_idx in range(6):
            result = await self.provider.chat(messages, tools=tools)
            self._audit({"type": "LLMResponse", "step": step_idx + 1, "data": result})

            content = result.get("content", "") or ""
            thoughts.append(self._extract_thought(content))

            tool_calls = result.get("tool_calls") or []
            if not tool_calls:
                # Allow text fallback for older/non-tool-call models.
                extraction = extract_command_from_text(content)
                if extraction.notes:
                    notes = extraction.notes
                if extraction.command_name:
                    if self.command_executor is None:
                        return {"error": "No command_executor configured"}
                    try:
                        command = LLMCommandFactory.from_llm(
                            agent_id=agent_id,
                            command_name=extraction.command_name,
                            payload_json=extraction.payload_json,
                        )
                    except Exception as exc:
                        return {"error": str(exc), "thoughts": thoughts, "events": emitted_events}
                    success, events, message = self.command_executor(agent_id, command)
                    if not success:
                        return {"error": message, "thoughts": thoughts, "events": emitted_events}
                    emitted_events.extend(events)
                break

            if not self.tool_executor:
                return {"error": "Tool calls provided but no tool_executor configured"}

            for call in tool_calls:
                fn = getattr(call, "function", None)
                tool_name = getattr(fn, "name", None) if fn else None
                args_json = getattr(fn, "arguments", "{}") if fn else "{}"
                try:
                    import json

                    args = json.loads(args_json) if isinstance(args_json, str) else (args_json or {})
                except Exception:
                    args = {}

                tool_name = str(tool_name or "")
                if not tool_name:
                    continue

                if self._tool_is_info(tool_name) or self._tool_is_session(tool_name):
                    out = self.tool_executor.execute(tool_name, args)
                    self._audit({"type": "ToolExecuted", "name": tool_name, "result": out})
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": getattr(call, "id", ""),
                            "name": tool_name,
                            "content": str(out),
                        }
                    )
                    if tool_name == "end_of_turn":
                        notes = str((args or {}).get("notes", ""))
                    if self._wants_end_turn(content, tool_name):
                        return {"events": emitted_events, "thoughts": thoughts, "notes": notes}
                    continue

                if self._tool_is_command(tool_name):
                    if self.command_executor is None:
                        return {"error": "No command_executor configured", "thoughts": thoughts, "events": emitted_events}
                    try:
                        command = LLMCommandFactory.from_llm(agent_id=agent_id, command_name=tool_name, **(args or {}))
                    except Exception as exc:
                        return {"error": str(exc), "thoughts": thoughts, "events": emitted_events}

                    success, events, message = self.command_executor(agent_id, command)
                    self._audit({"type": "CommandExecuted", "name": tool_name, "success": success, "message": message})
                    if not success:
                        return {"error": message, "thoughts": thoughts, "events": emitted_events}

                    emitted_events.extend(events)
                    if events:
                        last_event_id = getattr(events[-1], "event_id", last_event_id)

                    # Refresh tool context after state changes.
                    try:
                        snap = self.tool_executor.execute("get_state", {"agent_id": agent_id})
                        hist = self.tool_executor.execute("get_history", {"agent_id": agent_id, "last_event_id": last_event_id})
                        messages.append({"role": "user", "content": f"UPDATED_STATE: {snap}\nNEW_EVENTS: {hist}"})
                    except Exception:
                        pass

            # Continue loop; model can decide next step.

        # Max steps reached.
        return {"events": emitted_events, "thoughts": thoughts, "notes": notes, "stopped": "max_steps"}

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
