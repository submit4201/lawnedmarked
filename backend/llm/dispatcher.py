from __future__ import annotations

from typing import Optional, Dict, Any, Callable, Tuple, List
from .providers import LLMProvider
from .prompts import SystemPrompts, extract_command_from_text
from .prompts_registry import player_messages, gm_messages, judge_messages
from .tools import ToolExecutor
from .audit import AuditLog
from .sessions import SessionStore
from llm_factory import LLMCommandFactory
from .tools.registry import ToolRegistry
from core.commands import Command
from core.events import GameEvent
import json # Import json for parsing tool arguments
import os
import traceback
from pathlib import Path

# New helper classes
from .turn_logger import TurnLogger
from .response_parser import ResponseParser

# --- Constants for System Agents ---
GM_AGENT_ID = "SYSTEM_GM"
JUDGE_AGENT_ID = "SYSTEM_JUDGE"

# provider_map: Dict[str, LLMProvider] = {}
# provider_config_map: Dict[str, Any] = {role:str,config:provider_config,model:str,map_key:str}#map_key maps to provider_map key
class LLMDispatcher:
    def __init__(
        self,
        provider_map: Dict[str, LLMProvider],
        provider_config_map: Dict[str, Any],
        tool_executor: Optional[ToolExecutor] = None,
        audit_log: Optional[AuditLog] = None,
        session_store: SessionStore | None = None,
        command_executor: Callable[[str, Command], Tuple[bool, List[GameEvent], str]] | None = None,
        game_engine: Any = None,
    ):
        self.provider_map = provider_map
        self.provider_config_map = provider_config_map
        self.tool_executor = tool_executor
        self.audit_log = audit_log
        self.session_store = session_store
        self.command_executor = command_executor
        self.game_engine = game_engine
        self.provider: LLMProvider = None  # type: ignore # set in _get_provider_for_agent

    def _extract_thought(self, content: str) -> str:
        import re

        if not content:
            return ""
        # Try to find everything after <|-THOUGHT-|> until the next tag or end of string
        m = re.search(r"<\|\-THOUGHT\-\|>\s*(.*?)\s*(?:<\|-|$)", content, re.S)
        if m:
            return m.group(1).strip()
        
        # Fallback: if no tag, just return the first 500 chars
        return content.strip()[:500]
    
    def _extract_actions(self, content: str) -> str:
        '''extract the actions section from the content
        <|-ACTIONS-|> ... <|-ENDACTIONS-|>
        and extract commands from inside it.
        Commands are in the format:
        Command(NAME): {json payload} 
        '''
        import re
        if not content:
            return ""
        m = re.search(r"<\|\-ACTIONS\-\|>\s*(.*?)\s*<\|\-ENDACTIONS\-\|>", content, re.S)
        if m:
            # extract commands from m group 1 Command(NAME): {json payload}
            # we want to return a list of (cammand_name, payload_json) tuples
            actions_content = m.group(1).strip()
            command_pattern = re.compile(r"Command\((.*?)\):\s*(\{.*?\})", re.S)
            commands = command_pattern.findall(actions_content)
            for i in range(len(commands)):
                command_name = commands[i][0].strip()
                payload_json = commands[i][1].strip()
                commands[i] = (command_name, payload_json)
                print(f"Extracted command: {command_name} with payload: {payload_json}")
            return commands
        
        return []
    
    def _extract_notes(self, content: str) -> str:
        import re

        if not content:
            return ""
        # Match <|-NOTES-|> and everything after it, but stop if we see <|-ENDNOTES-|> or <|-ENDTURN-|>
        m = re.search(
            r"<\|\-NOTES\-\|>\s*(.*?)(?:\s*<\|\-ENDNOTES\-\|>|\s*<\|\-ENDTURN-|>|$)",
            content,
            re.S,
        )
        if m:
            return m.group(1).strip()
        return ""
            
    def _extract_tool_calls_from_text(self, text: str) -> list[dict]:
        """Extract <tool_call> tags from text and convert to OpenAI-style tool_calls."""
        import re
        import uuid
        
        calls = []
        # Match <tool_call> ... </tool_call> or <tool_call> ... (if tag is not closed)
        # We use a more robust pattern that captures everything between tags.
        pattern = r"<tool_call>\s*(.*?)\s*(?:</tool_call>|(?=<tool_call>)|$)"
        matches = re.finditer(pattern, text, re.S)
        
        for m in matches:
            try:
                raw_content = m.group(1).strip()
                # Remove markdown code blocks if present
                if raw_content.startswith("```"):
                    raw_content = re.sub(r"^```(?:json)?\n", "", raw_content)
                    raw_content = re.sub(r"\n```$", "", raw_content)
                
                # Try to find the first { and last } to extract JSON
                start = raw_content.find("{")
                end = raw_content.rfind("}")
                if start != -1 and end != -1:
                    json_str = raw_content[start:end+1]
                    
                    # Handle escaped JSON if the LLM wrapped it in a string
                    if "\\\"" in json_str:
                        try:
                            # Try to unescape by loading as a string first if it's wrapped in quotes
                            if raw_content.startswith("\"") and raw_content.endswith("\""):
                                json_str = json.loads(raw_content)
                            else:
                                # Manual unescape for common cases
                                json_str = json_str.replace("\\\"", "\"").replace("\\\\", "\\")
                        except Exception:
                            # If unescaping fails, fall back to the original JSON substring
                            pass

                    data = json.loads(json_str)
                    name = data.get("name")
                    args = data.get("arguments") or {}
                    if name:
                        calls.append({
                            "id": f"call_{uuid.uuid4().hex[:8]}",
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": json.dumps(args) if isinstance(args, dict) else str(args)
                            }
                        })
            except Exception as e:
                print(f"[LLM] Error parsing tool call: {e}")
                continue
        return calls

    def _log_to_markdown(self, agent_id: str, step_idx: int, content: str, tool_calls: list = None, tool_results: list = None, command_extraction: Any = None):
        """Log the turn step to a markdown file for debugging."""
        import re
        from datetime import datetime
        
        # Use absolute path relative to this file to avoid CWD issues
        log_dir = Path(__file__).resolve().parent.parent / "logs" / "turns"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_{agent_id}.md"
        filepath = log_dir / filename
        
        with open(filepath, "a", encoding="utf-8") as f:
            if step_idx == 0:
                f.write(f"\n---\n# Turn Log: {agent_id} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            fwrite = f.write
            fwrite(f"---\n## Step {step_idx + 1}\n\n")
            
            # Raw Response
            fwrite("### Raw Response\n\n")
            fwrite(f"```\n{content}\n```\n\n")

            # Sections
            patterns = [
                ("Thought", r"<\|-THOUGHT-\|>(.*?)(?=<\|-|$)"),
                ("Action Plan", r"<\|-ACTION PLAN-\|>(.*?)(?=<\|-|$)"),
                ("Checks", r"<\|-CHECKS-\|>(.*?)(?=<\|-|$)"),
                ("Command", r"<\|-COMMAND-\|>(.*?)(?=<\|-|$)"),
                ("Notes", r"<\|-NOTES-\|>(.*?)(?=<\|-|$)"),
            ]
            
            found_sections = False
            for title, pattern in patterns:
                match = re.search(pattern, content, re.S)
                if match:
                    text = match.group(1).strip()
                    if text:
                        f.write(f"### {title}\n{text}\n\n")
                        found_sections = True
            
            if tool_calls:
                f.write("### Tool Calls\n")
                for call in tool_calls:
                    if isinstance(call, dict):
                        name = call.get("function", {}).get("name")
                        args = call.get("function", {}).get("arguments")
                    else:
                        name = getattr(getattr(call, "function", {}), "name", "unknown")
                        args = getattr(getattr(call, "function", {}), "arguments", "{}")
                    f.write(f"- **{name}**\n")
                    f.write(f"  ```json\n{args}\n  ```\n")
                f.write("\n")
                found_sections = True

            if command_extraction and command_extraction.command_name:
                f.write(f"### Extracted Command (Text Fallback)\n")
                f.write(f"- **{command_extraction.command_name}**\n")
                f.write(f"  ```json\n{command_extraction.payload_json}\n  ```\n\n")
                found_sections = True

            if not found_sections and content.strip():
                if content.strip() != "Executing tool calls...":
                    f.write(f"### Raw Response\n{content.strip()}\n\n")
            
            if tool_results:
                f.write("### Tool Results\n")
                for res in tool_results:
                    name = res.get("name")
                    out = res.get("content")
                    if len(out) > 2000:
                        out = out[:2000] + "... (truncated)"
                    f.write(f"#### {name}\n{out}\n\n")

            f.write("---\n")

    def _wants_end_turn(self, content: str, tool_name: str | None) -> bool:
        if tool_name == "end_of_turn":
            return True
        import re
        # Robust check for end turn tag, allowing for common typos like } instead of >
        return bool(re.search(r"<\|\-ENDTURN\-[\|>\}]", content or ""))

    def _tool_is_info(self, name: str) -> bool:
        return name in {"tool_help", "get_history", "get_state", "get_inventory"}

    def _tool_is_session(self, name: str) -> bool:
        return name in {"end_of_turn"}

    def _tool_is_command(self, name: str) -> bool:
        # Check if it's a known command in the registry
        from .tools.registry import ToolRegistry
        all_tools = {t.name for t in ToolRegistry.get_all_tools()}
        return name in all_tools and not self._tool_is_info(name) and not self._tool_is_session(name)

    # --- Provider & Chat Helpers ---
    def _get_provider_for_agent(self, agent_id: str) -> LLMProvider:
        config_entry = self.provider_config_map.get(agent_id)
        if not config_entry:
            raise ValueError(f"No provider config found for agent {agent_id}")
        map_key = config_entry.get("provider_key") # Corrected from map_key to provider_key based on ApplicationFactory
        if not map_key or map_key not in self.provider_map:
            raise ValueError(f"No provider found for provider_key {map_key} for agent {agent_id}")
        self.provider = self.provider_map[map_key]
        return self.provider_map[map_key]

    def _is_gpu_resource_error(self, exc: BaseException) -> bool:
        msg = (str(exc) or "").lower()
        needles = [
            "opencl",
            "cl_out_of_resources",
            "out of resources",
            "out of memory",
            "failed to allocate",
            "allocation",
            "resource exhausted",
            "cuda out of memory",
            "hiperroroutofmemory",
        ]
        return any(n in msg for n in needles)

    def _normalize_messages_for_chat(self, messages: list[dict]) -> list[dict]:
        """Normalize messages to avoid apply_chat_template failures."""
        if not messages:
            return []

        system_parts: list[str] = []
        rest: list[dict] = []

        for m in messages:
            role = (m.get("role") or "").strip().lower()
            content = m.get("content")
            if content is None:
                content = ""
            if not isinstance(content, str):
                content = json.dumps(content, default=str)

            if role == "system":
                if content.strip():
                    system_parts.append(content.strip())
                continue

            if role == "assistant":
                # If assistant has tool_calls but no content, some templates fail.
                tcalls = m.get("tool_calls")
                if tcalls and not content.strip():
                    content = "Executing tool calls..."
                rest.append({"role": "assistant", "content": content})
                continue

            if role == "tool":
                tool_name = m.get("name")
                prefix = f"TOOL_RESULT({tool_name}): " if tool_name else "TOOL_RESULT: "
                rest.append({"role": "user", "content": prefix + content})
                continue

            if role not in {"user", "assistant"}:
                rest.append({"role": "user", "content": content})
                continue

            rest.append({"role": role, "content": content})

        merged: list[dict] = []
        if system_parts:
            merged.append({"role": "system", "content": "\n\n".join(system_parts)})

        for m in rest:
            if not merged:
                if m["role"] != "user":
                    merged.append({"role": "user", "content": m.get("content", "")})
                else:
                    merged.append(m)
                continue

            prev_role = merged[-1].get("role")
            if prev_role == m["role"] and m["role"] in {"user", "assistant"}:
                merged[-1]["content"] = (merged[-1].get("content", "") + "\n\n" + m.get("content", "")).strip()
            else:
                merged.append(m)

        return merged

    async def _chat_with_guards(
        self,
        *,
        provider: LLMProvider,
        agent_id: str,
        role_label: str,
        messages: list[dict],
        tools: list[dict] | None,
        step_idx: int | None,
        agent_config: dict | None,
    ) -> Dict[str, Any]:
        normalized = self._normalize_messages_for_chat(messages)

        def _summarize_msgs(msgs: list[dict]) -> Dict[str, Any]:
            roles = [m.get("role") for m in msgs]
            tail = msgs[-4:] if len(msgs) > 4 else msgs
            return {
                "count": len(msgs),
                "roles": roles,
                "tail_preview": [
                    {
                        "role": m.get("role"),
                        "content_preview": (m.get("content") or "").replace("\n", " ")[:200],
                    }
                    for m in tail
                ],
            }

        tool_names = []
        for t in tools or []:
            name = None
            if isinstance(t, dict):
                function = t.get("function")
                if isinstance(function, dict):
                    name = function.get("name")
            tool_names.append(name)

        self._audit(
            {
                "type": "LLMRequest",
                "role": role_label,
                "agent_id": agent_id,
                "step": step_idx,
                "provider": provider.__class__.__name__,
                "model": getattr(getattr(provider, "config", None), "model", ""),
                "tools": [n for n in tool_names if n],
                "messages": _summarize_msgs(normalized),
            }
        )

        retry_on_gpu = (os.getenv("LLM_RETRY_ON_GPU_ERROR") or "1").strip().lower() not in {"0", "false", "no"}
        
        import asyncio
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return await provider.chat(normalized, tools=tools, step_idx=step_idx, config=agent_config)
            except Exception as exc:
                is_rate_limit = "429" in str(exc) or "quota" in str(exc).lower()
                
                if is_rate_limit and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"[LLM][{agent_id}] Rate limit hit (429). Waiting {wait_time}s before retry {attempt+1}/{max_retries}...")
                    await asyncio.sleep(wait_time)
                    continue

                self._audit(
                    {
                        "type": "LLMError",
                        "role": role_label,
                        "agent_id": agent_id,
                        "step": step_idx,
                        "error": str(exc),
                        "traceback": "".join(traceback.format_exception_only(type(exc), exc))[-2000:],
                    }
                )

                if retry_on_gpu and self._is_gpu_resource_error(exc):
                    try:
                        # Keep only system + last user message to reduce memory pressure.
                        reduced = []
                        if normalized and normalized[0].get("role") == "system":
                            reduced.append(normalized[0])
                        last_user = next((m for m in reversed(normalized) if m.get("role") == "user"), None)
                        if last_user:
                            reduced.append(last_user)

                        self._audit(
                            {
                                "type": "LLMRetry",
                                "role": role_label,
                                "agent_id": agent_id,
                                "step": step_idx,
                                "reason": "gpu_resource_error",
                                "messages": {"count": len(reduced), "roles": [m.get("role") for m in reduced]},
                            }
                        )
                        return await provider.chat(reduced, tools=tools, step_idx=step_idx, config=agent_config)
                    except Exception as exc2:
                        self._audit(
                            {
                                "type": "LLMError",
                                "role": role_label,
                                "agent_id": agent_id,
                                "step": step_idx,
                                "error": str(exc2),
                                "retry": True,
                            }
                        )

                # Graceful failure payload so request doesn't crash.
                return {"role": "assistant", "content": "", "tool_calls": None, "error": str(exc)}
        
        return {"role": "assistant", "content": "", "tool_calls": None, "error": "Max retries exceeded"}

    # --- Turn Execution Logic ---

    def _prepare_turn_context(self, agent_id: str) -> dict:
        """Fetch state and competitor events for injection into system prompt."""
        state_obj = {}
        competitor_events = []
        if self.game_engine:
            try:
                from dataclasses import asdict
                state = self.game_engine.get_current_state(agent_id)
                state_obj = asdict(state)
                
                # Fetch last 10 events from all agents to find competitor actions
                all_events = self.game_engine.event_repository.load_all()
                competitor_events = [
                    e for e in reversed(all_events) 
                    if e.agent_id != agent_id and e.agent_id not in (GM_AGENT_ID, JUDGE_AGENT_ID)
                ][:10]
                
                # Convert to serializable (simple dict conversion)
                def _to_simple_dict(obj):
                    if hasattr(obj, "to_dict"):
                        return obj.to_dict()
                    if hasattr(obj, "__dict__"):
                        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
                    return str(obj)
                
                competitor_events = [_to_simple_dict(e) for e in competitor_events]
            except Exception as e:
                print(f"[LLM][{agent_id}] Error fetching state/events for prompt: {e}")
        return {"state_obj": state_obj, "competitor_events": competitor_events}

    async def run_player_turn(self, agent_id: str, history_messages: list[dict]) -> Dict[str, Any]:
        """Run a bounded multi-step player turn.
        
        Refactored to cleaner sub-methods.
        """
        provider = self._get_provider_for_agent(agent_id)
        
        # Log provider info
        try:
            cfg = getattr(provider, "config", None)
            model = getattr(cfg, "model", "") if cfg else ""
            endpoint = getattr(cfg, "endpoint", "") if cfg else ""
            print(f"[LLM] turn agent={agent_id} provider={provider.__class__.__name__} model={model!r} endpoint={endpoint!r}")
        except Exception:
            print(f"[LLM] turn agent={agent_id} provider={provider.__class__.__name__}")
        
        context = self._prepare_turn_context(agent_id)
        messages = player_messages(agent_id, history_messages, self.session_store, context["state_obj"], context["competitor_events"])

        # Provide the full tool set to the model.
        tools = ToolRegistry.as_openai_tools() if self.tool_executor else None
        
        return await self._execute_turn_loop(agent_id, provider, messages, tools)

    async def _execute_turn_loop(self, agent_id: str, provider: LLMProvider, messages: list[dict], tools: list[dict] | None) -> Dict[str, Any]:
        emitted_events: List[GameEvent] = []
        thoughts: List[str] = []
        notes: str = ""
        last_event_id: str | None = None

        if self.session_store:
            pnotes = self.session_store.get_notes(agent_id)
            if pnotes:
                notes += f"\nPrevious Notes:\n{pnotes}"

        max_steps = 10
        for step_idx in range(max_steps):
            # Info for the model
            remaining = max_steps - step_idx
            step_info = f"\n\n[SYSTEM: Step {step_idx+1}/{max_steps}. {remaining} steps remaining.]"
            if remaining <= 3:
                step_info += " WARNING: You are running out of steps. Wrap up your turn now."
            
            if messages and messages[-1]["role"] == "user":
                messages[-1]["content"] += step_info
            else:
                messages.append({"role": "user", "content": step_info})

            agent_config = self.provider_config_map.get(agent_id, {})
            result = await self._chat_with_guards(
                provider=provider,
                agent_id=agent_id,
                role_label="PLAYER",
                messages=messages,
                tools=tools,
                step_idx=step_idx,
                agent_config=agent_config,
            )
            
            self._audit({"type": "LLMResponse", "step": step_idx + 1, "data": result})

            content = result.get("content", "") or ""
            if content:
                print(f"[LLM][{agent_id}][step {step_idx+1}] Content: {content[:100]}...")
            
            thoughts.append(ResponseParser.extract_thought(content))
            extracted_notes = ResponseParser.extract_notes(content)
            if extracted_notes:
                notes += extracted_notes
            
            tool_calls = result.get("tool_calls") or []
            if not tool_calls:
                tool_calls = ResponseParser.extract_tool_calls_from_text(content)
                if tool_calls:
                    result["tool_calls"] = tool_calls

            # Log helpful info
            if tool_calls:
                self._log_tool_calls_console(step_idx, tool_calls)

            # Append assistant response
            history_msg = result.copy()
            if "tool_calls" in history_msg and not history_msg.get("tool_calls"):
                history_msg.pop("tool_calls", None)
            messages.append(history_msg)

            step_tool_results = []
            
            # --- Text Fallback Execution ---
            if not tool_calls:
                res = self._handle_text_fallback(agent_id, content, step_idx, tool_calls, step_tool_results, messages, emitted_events, thoughts, notes)
                if res:
                    return res  # Turn ended or commanded
                
                # Check for wants end turn
                if ResponseParser.wants_end_turn(content, None):
                     # Log final state
                     self.logger.log_turn(agent_id, step_idx, content, tool_calls, step_tool_results, None)
                     if notes and self.session_store:
                        self.session_store.append_note(agent_id, notes)
                     return {"events": emitted_events, "thoughts": thoughts, "notes": notes}

            # --- Tool Call Execution ---
            if not self.tool_executor:
                 # Logic for missing executor handled in loop or specific method if needed
                 if tool_calls:
                     self.logger.log_turn(agent_id, step_idx, content, tool_calls, step_tool_results, None)
                     return {"error": "Tool calls provided but no tool_executor configured"}
            else:
                turn_ended, last_event_id = self._execute_tool_calls(
                    agent_id, tool_calls, step_tool_results, messages, emitted_events, notes, content, last_event_id
                )
                if turn_ended:
                     self.logger.log_turn(agent_id, step_idx, content, tool_calls, step_tool_results, None)
                     return {"events": emitted_events, "thoughts": thoughts, "notes": notes}

            self.logger.log_turn(agent_id, step_idx, content, tool_calls, step_tool_results, None)

        return {"events": emitted_events, "thoughts": thoughts, "notes": notes, "stopped": "max_steps"}

    def _log_tool_calls_console(self, step_idx, tool_calls):
        print(f"\n--- TOOL CALLS (Step {step_idx+1}) ---")
        for call in tool_calls:
            if isinstance(call, dict):
                fn = call.get("function") or {}
                t_name = fn.get("name")
                t_args = fn.get("arguments")
            else:
                t_name = getattr(getattr(call, "function", {}), "name", "unknown")
                t_args = getattr(getattr(call, "function", {}), "arguments", "{}")
            print(f"Tool: `{t_name}`")
            print(f"Args: ```json\n{t_args}\n```")
        print("-----------------------------------\n")

    def _handle_text_fallback(self, agent_id, content, step_idx, tool_calls, step_tool_results, messages, emitted_events, thoughts, notes):
        """Handle cases where no native tool calls are present."""
        extraction = extract_command_from_text(content)
        if extraction.notes is not None:
            # Note: updating notes variable passed by reference isn't possible in python safely without a container, 
            # but we are in a method. We will just return if we handled something. 
            pass # extraction.notes is handled by caller via parsing content again or we should use extraction object
        
        # We need to respect the extracted notes if present
        # but the main loop already extracts notes from content via regex.
        
        if extraction.command_name:
            if self.command_executor is None:
                self.logger.log_turn(agent_id, step_idx, content, tool_calls, step_tool_results, extraction)
                return {"error": "No command_executor configured"}
            
            try:
                command = LLMCommandFactory.from_llm(
                    agent_id=agent_id,
                    command_name=extraction.command_name,
                    payload_json=extraction.payload_json,
                )
            except Exception as exc:
                self.logger.log_turn(agent_id, step_idx, content, tool_calls, step_tool_results, extraction)
                return {"error": str(exc), "thoughts": thoughts, "events": emitted_events}
            
            success, events, message = self.command_executor(agent_id, command)
            step_tool_results.append({"name": extraction.command_name, "content": f"success={success}, message={message}"})
            
            if not success:
                messages.append({
                    "role": "user",
                    "content": f"COMMAND ERROR ({extraction.command_name}): {message}"
                })
                self.logger.log_turn(agent_id, step_idx, content, tool_calls, step_tool_results, extraction)
                return None # Continue loop
            
            emitted_events.extend(events)
            self.logger.log_turn(agent_id, step_idx, content, tool_calls, step_tool_results, extraction)
            return {"events": emitted_events, "thoughts": thoughts, "notes": notes} # Return after success for fallback

        return None # No command found, continue

    def _execute_tool_calls(self, agent_id, tool_calls, step_tool_results, messages, emitted_events, notes, content, last_event_id):
        turn_ended = False
        for call in tool_calls:
            # Normalize call object
            if isinstance(call, dict):
                fn = call.get("function") or {}
                tool_name = fn.get("name")
                args_json = fn.get("arguments") or "{}"
                call_id = call.get("id") or ""
            else:
                fn = getattr(call, "function", None)
                tool_name = getattr(fn, "name", None) if fn else None
                args_json = getattr(fn, "arguments", "{}") if fn else "{}"
                call_id = getattr(call, "id", "")
            
            try:
                args = json.loads(args_json) if isinstance(args_json, str) else (args_json or {})
            except Exception:
                args = {}

            tool_name = str(tool_name or "")
            if not tool_name:
                continue

            if self._tool_is_info(tool_name) or self._tool_is_session(tool_name):
                out = self.tool_executor.execute(tool_name, args)
                self._audit({"type": "ToolExecuted", "name": tool_name, "result": out})
                print(f"[LLM][{agent_id}] Tool {tool_name} executed. Result length: {len(str(out))}")
                step_tool_results.append({"name": tool_name, "content": str(out)})
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": tool_name,
                    "content": str(out),
                })
                # Check for end of turn signal in args or content
                if ResponseParser.wants_end_turn(content, tool_name):
                    turn_ended = True
                continue

            if self._tool_is_command(tool_name):
                if self.command_executor is None:
                    step_tool_results.append({"name": tool_name, "content": "ERROR: No command_executor configured"})
                    continue
                try:
                    cmd_args = dict(args or {})
                    cmd_args.pop("agent_id", None)
                    command = LLMCommandFactory.from_llm(agent_id=agent_id, command_name=tool_name, **cmd_args)
                    success, events, message = self.command_executor(agent_id, command)
                    self._audit({"type": "CommandExecuted", "name": tool_name, "success": success, "message": message, "events": [e.to_dict() for e in events]})
                    print(f"[LLM][{agent_id}] Command {tool_name} -> success={success}, message={message}")
                    step_tool_results.append({"name": tool_name, "content": f"success={success}, message={message}"})
                    
                    if not success:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": tool_name,
                            "content": f"ERROR: {message}"
                        })
                        continue

                    emitted_events.extend(events)
                    if events:
                        last_event_id = getattr(events[-1], "event_id", last_event_id)

                    events_summary = [getattr(e, "event_type", "") for e in (events or [])]
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": tool_name,
                        "content": f"SUCCESS: emitted={events_summary}; last_event_id={last_event_id}"
                    })
                    
                    if notes and self.session_store:
                        self.session_store.append_note(agent_id, notes)
                except Exception as exc:
                    step_tool_results.append({"name": tool_name, "content": f"ERROR: {str(exc)}"})
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": tool_name,
                        "content": f"ERROR: {str(exc)}"
                    })
                continue
            
            # Unknown tool
            print(f"[LLM][{agent_id}] Unknown tool call: {tool_name}")
            step_tool_results.append({"name": tool_name, "content": f"ERROR: Tool '{tool_name}' not found."})
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "name": tool_name,
                "content": f"ERROR: Tool '{tool_name}' not found. Use tool_help to see available tools."
            })

        return turn_ended, last_event_id

    def _audit(self, event: Dict[str, Any]):
        if self.audit_log:
            self.audit_log.append(event)

    async def run_gm_turn(self, target_agent_id: str, history_messages: list[dict]) -> Dict[str, Any]:
        """Runs the LLM-driven Game Master turn."""
        agent_id = GM_AGENT_ID
        
        provider = self._get_provider_for_agent(agent_id)
        agent_config = self.provider_config_map.get(agent_id, {})
        messages = gm_messages(agent_id, history_messages, self.session_store)
        tools = ToolRegistry.as_openai_tools_only(["INJECT_WORLD_EVENT"])
        
        result = await self._chat_with_guards(
            provider=provider,
            agent_id=agent_id,
            role_label="GM",
            messages=messages,
            tools=tools,
            step_idx=0,
            agent_config=agent_config,
        )
        self._audit({"type": "LLMResponse", "role": "GM", "data": result})
        
        tool_calls = result.get("tool_calls") or []
        if not tool_calls:
            return {"success": True, "events": [], "message": "GM decided no event was injected."}

        # Handle GM commands (simplified for now to just return what it wanted to do)
        # The Orchestrator usually handles the execution for GM if it returns tool calls
        # But this method seems to have been returning a dict.
        # Checking original code... 
        # Original code returned {"success": True, "tool_calls": tool_calls} effectively if strictly following the flow in orchestrator
        # or executed it? 
        # The original code just stopped after getting result.
        
        return {"success": True, "tool_calls": tool_calls, "message": "GM generated tool calls."}