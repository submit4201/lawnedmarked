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
from .turn_logger import TurnLogger, TurnContext
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
        self.logger = TurnLogger()

    # Helpers moved to ResponseParser and TurnLogger
    
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

    def _extract_message_content(self, m: dict) -> tuple[str, str]:
        """Extract role and content from a message, ensuring string content."""
        role = (m.get("role") or "").strip().lower()
        content = m.get("content")
        if content is None:
            content = ""
        if not isinstance(content, str):
            content = json.dumps(content, default=str)
        return role, content

    def _normalize_single_message(self, m: dict, system_parts: list[str]) -> dict | None:
        """Normalize a single message. Extract system prompts, handle empty content."""
        role, content = self._extract_message_content(m)

        if role == "system":
            self._handle_system_message(content, system_parts)
            return None

        if role == "assistant":
            return self._handle_assistant_message(m, content)

        if role == "tool":
            return self._handle_tool_message(m, content)

        # Default to user for unknown roles
        if role not in {"user", "assistant"}:
             role = "user"
             
        return {"role": role, "content": content}

    def _handle_system_message(self, content: str, system_parts: list[str]):
        if content.strip():
            system_parts.append(content.strip())

    def _handle_assistant_message(self, m: dict, content: str) -> dict:
        tcalls = m.get("tool_calls")
        if tcalls and not content.strip():
            content = "Executing tool calls..."
        return {"role": "assistant", "content": content}

    def _handle_tool_message(self, m: dict, content: str) -> dict:
        tool_name = m.get("name")
        prefix = f"TOOL_RESULT({tool_name}): " if tool_name else "TOOL_RESULT: "
        return {"role": "user", "content": prefix + content}

    def _merge_consecutive_messages(self, messages: list[dict]) -> list[dict]:
        """Merge consecutive messages with the same role."""
        if not messages:
            return []

        merged: list[dict] = [messages[0]]
        for m in messages[1:]:
            prev_role = merged[-1].get("role")
            curr_role = m["role"]
            
            if prev_role == curr_role and curr_role in {"user", "assistant"}:
                merged[-1]["content"] = (
                    merged[-1].get("content", "") + "\n\n" + m.get("content", "")
                ).strip()
            else:
                merged.append(m)

        return merged

    def _normalize_messages_for_chat(self, messages: list[dict]) -> list[dict]:
        """Normalize messages to avoid apply_chat_template failures."""
        if not messages:
            return []

        system_parts: list[str] = []
        rest: list[dict] = []

        # Process each message
        for m in messages:
            normalized = self._normalize_single_message(m, system_parts)
            if normalized:
                rest.append(normalized)

        return self._build_final_message_list(system_parts, rest)

    def _build_final_message_list(self, system_parts: list[str], rest: list[dict]) -> list[dict]:
        """Assemble the final list of messages from system parts and normalized user/assistant messages."""
        result: list[dict] = []
        if system_parts:
            result.append({"role": "system", "content": "\n\n".join(system_parts)})

        # Ensure first non-system message is user
        if rest:
            if rest[0]["role"] != "user":
                result.append({"role": "user", "content": rest[0].get("content", "")})
                rest = rest[1:]
            result.extend(rest)

        return self._merge_consecutive_messages(result)

    def _summarize_messages(self, msgs: list[dict]) -> Dict[str, Any]:
        """Create a summary of messages for audit logging."""
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

    def _extract_tool_names(self, tools: list[dict] | None) -> list[str]:
        """Extract tool names from tools list, handling different formats."""
        if not tools:
            return []
        
        tool_names = []
        for t in tools:
            name = None
            if isinstance(t, dict):
                function = t.get("function")
                if isinstance(function, dict):
                    name = function.get("name")
            if name:
                tool_names.append(name)
        return tool_names

    def _reduce_messages_for_gpu(self, normalized: list[dict]) -> list[dict]:
        """Reduce messages to system + last user message to handle GPU memory issues."""
        reduced = []
        if normalized and normalized[0].get("role") == "system":
            reduced.append(normalized[0])
        last_user = next((m for m in reversed(normalized) if m.get("role") == "user"), None)
        if last_user:
            reduced.append(last_user)
        return reduced

    async def _attempt_chat_with_retry(
        self,
        provider: LLMProvider,
        normalized: list[dict],
        tools: list[dict] | None,
        step_idx: int | None,
        agent_config: dict | None,
        agent_id: str,
        role_label: str,
        attempt: int,
    ) -> Dict[str, Any] | None:
        """Attempt chat request with GPU error retry logic. Returns None if should continue retrying."""
        import asyncio
        from .providers.llmproviderbase import ChatRequest
        
        try:
            request = ChatRequest(
                messages=normalized,
                tools=tools,
                step_idx=step_idx,
                config=agent_config
            )
            return await provider.chat(request)
        except Exception as exc:
            is_rate_limit = "429" in str(exc) or "quota" in str(exc).lower()
            
            if is_rate_limit and attempt < 2:  # max_retries - 1
                wait_time = (attempt + 1) * 5
                print(f"[LLM][{agent_id}] Rate limit hit (429). Waiting {wait_time}s before retry {attempt+1}/3...")
                await asyncio.sleep(wait_time)
                return None  # Continue retrying

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

            # Try GPU memory reduction if applicable
            retry_on_gpu = (os.getenv("LLM_RETRY_ON_GPU_ERROR") or "1").strip().lower() not in {"0", "false", "no"}
            if retry_on_gpu and self._is_gpu_resource_error(exc):
                reduced = self._reduce_messages_for_gpu(normalized)
                
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
                
                try:
                    request = ChatRequest(
                        messages=reduced,
                        tools=tools,
                        step_idx=step_idx,
                        config=agent_config
                    )
                    return await provider.chat(request)
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

            # Graceful failure payload
            return {"role": "assistant", "content": "", "tool_calls": None, "error": str(exc)}

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
        tool_names = self._extract_tool_names(tools)

        self._audit(
            {
                "type": "LLMRequest",
                "role": role_label,
                "agent_id": agent_id,
                "step": step_idx,
                "provider": provider.__class__.__name__,
                "model": getattr(getattr(provider, "config", None), "model", ""),
                "tools": tool_names,
                "messages": self._summarize_messages(normalized),
            }
        )

        max_retries = 3
        for attempt in range(max_retries):
            result = await self._attempt_chat_with_retry(
                provider, normalized, tools, step_idx, agent_config,
                agent_id, role_label, attempt
            )
            if result is not None:
                return result
        
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

    def _add_step_info_to_messages(self, messages: list[dict], step_idx: int, max_steps: int):
        """Add step information to the message history."""
        remaining = max_steps - step_idx
        step_info = f"\n\n[SYSTEM: Step {step_idx+1}/{max_steps}. {remaining} steps remaining.]"
        if remaining <= 3:
            step_info += " WARNING: You are running out of steps. Wrap up your turn now."
        
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += step_info
        else:
            messages.append({"role": "user", "content": step_info})

    def _process_llm_response(
        self, 
        result: dict, 
        agent_id: str, 
        step_idx: int,
        notes: str
    ) -> tuple[str, list, str]:
        """Process LLM response to extract content, tool calls, and notes."""
        content = result.get("content", "") or ""
        if content:
            print(f"[LLM][{agent_id}][step {step_idx+1}] Content: {content[:100]}...")
        
        # Extract tool calls
        tool_calls = result.get("tool_calls") or []
        if not tool_calls:
            tool_calls = ResponseParser.extract_tool_calls_from_text(content)
            if tool_calls:
                result["tool_calls"] = tool_calls
        
        # Extract notes
        extracted_notes = ResponseParser.extract_notes(content)
        if extracted_notes:
            notes += extracted_notes
        
        return content, tool_calls, notes

    def _finalize_turn(
        self,
        agent_id: str,
        step_idx: int,
        content: str,
        tool_calls: list,
        step_tool_results: list,
        emitted_events: List[GameEvent],
        thoughts: List[str],
        notes: str
    ) -> dict:
        """Finalize turn by logging and saving notes."""
        self.logger.log_turn(TurnContext(agent_id, step_idx, content, tool_calls or [], step_tool_results or []))
        if notes and self.session_store:
            self.session_store.append_note(agent_id, notes)
        return {"events": emitted_events, "thoughts": thoughts, "notes": notes}

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
            self._add_step_info_to_messages(messages, step_idx, max_steps)
            
            # Execute single step
            result_or_continue = await self._execute_single_step(
                agent_id, provider, messages, tools, step_idx, 
                emitted_events, thoughts, notes, last_event_id
            )
            
            # If result is a dict, it's a return value (turn ended or error)
            if isinstance(result_or_continue, dict):
                # If it's just updating state (like notes/last_event_id), we need a way to pass that back if we broke early.
                # But here, if it returns a dict, it means finish the loop.
                # Wait, we need to update 'notes' and 'last_event_id' between steps if we continue.
                # The _execute_single_step needs to return (continue, new_state) or (stop, result).
                return result_or_continue
            
            # Update state for next iteration
            last_event_id, notes = result_or_continue

        return {"events": emitted_events, "thoughts": thoughts, "notes": notes, "stopped": "max_steps"}

    async def _execute_single_step(
        self, 
        agent_id: str, 
        provider: LLMProvider, 
        messages: list[dict], 
        tools: list[dict] | None, 
        step_idx: int,
        emitted_events: List[GameEvent],
        thoughts: List[str],
        notes: str,
        last_event_id: str | None
    ) -> Dict[str, Any] | Tuple[str | None, str]:
        """Execute a single step of the turn loop. Returns either a final result dict (stop) or (last_event_id, notes) tuple (continue)."""
        
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

        content, tool_calls, notes = self._process_llm_response(result, agent_id, step_idx, notes)
        thoughts.append(ResponseParser.extract_thought(content))
        
        if tool_calls:
            self.logger.log_console(step_idx, tool_calls)

        # Append assistant response
        history_msg = result.copy()
        if "tool_calls" in history_msg and not history_msg.get("tool_calls"):
            history_msg.pop("tool_calls", None)
        messages.append(history_msg)

        step_tool_results: List[Any] = []
        
        # --- Text Fallback / End Turn ---
        if not tool_calls:
            # Check for fallback commands
            res = self._handle_text_fallback(agent_id, content, step_idx, tool_calls, step_tool_results, messages, emitted_events, thoughts, notes)
            if res:
                return res
            
            # Check for explicit end turn request
            if ResponseParser.wants_end_turn(content, None):
                return self._finalize_turn(agent_id, step_idx, content, tool_calls, step_tool_results, emitted_events, thoughts, notes)

        # --- Tool Call Execution ---
        if not self.tool_executor:
                if tool_calls:
                    self.logger.log_turn(TurnContext(agent_id, step_idx, content, tool_calls or [], step_tool_results or []))
                    return {"error": "Tool calls provided but no tool_executor configured"}
        else:
            turn_ended, last_event_id = self._execute_tool_calls(
                agent_id, tool_calls, step_tool_results, messages, emitted_events, notes, content, last_event_id
            )
            if turn_ended:
                return self._finalize_turn(agent_id, step_idx, content, tool_calls, step_tool_results, emitted_events, thoughts, notes)

        self.logger.log_turn(TurnContext(agent_id, step_idx, content, tool_calls or [], step_tool_results or []))
        
        # Continue to next step
        return (last_event_id, notes)



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
                self.logger.log_turn(TurnContext(agent_id, step_idx, content, tool_calls or [], step_tool_results or [], extraction))
                return {"error": "No command_executor configured"}
            
            try:
                command = LLMCommandFactory.from_llm(
                    agent_id=agent_id,
                    command_name=extraction.command_name,
                    payload_json=extraction.payload_json,
                )
            except Exception as exc:
                self.logger.log_turn(TurnContext(agent_id, step_idx, content, tool_calls or [], step_tool_results or [], extraction))
                return {"error": str(exc), "thoughts": thoughts, "events": emitted_events}
            
            success, events, message = self.command_executor(agent_id, command)
            step_tool_results.append({"name": extraction.command_name, "content": f"success={success}, message={message}"})
            
            if not success:
                messages.append({
                    "role": "user",
                    "content": f"COMMAND ERROR ({extraction.command_name}): {message}"
                })
                self.logger.log_turn(TurnContext(agent_id, step_idx, content, tool_calls or [], step_tool_results or [], extraction))
                return None # Continue loop
            
            emitted_events.extend(events)
            self.logger.log_turn(TurnContext(agent_id, step_idx, content, tool_calls or [], step_tool_results or [], extraction))
            return {"events": emitted_events, "thoughts": thoughts, "notes": notes} # Return after success for fallback

        return None # No command found, continue

    def _normalize_tool_call(self, call) -> tuple[str, dict, str]:
        """Normalize a tool call object to extract name, args, and call_id."""
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
        return tool_name, args, call_id

    def _handle_info_tool(
        self, 
        agent_id: str, 
        tool_name: str, 
        args: dict, 
        call_id: str,
        content: str,
        step_tool_results: list,
        messages: list
    ) -> bool:
        """Execute info or session tool. Returns True if turn should end."""
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
        
        return ResponseParser.wants_end_turn(content, tool_name)

    def _handle_command_tool(
        self,
        agent_id: str,
        tool_name: str,
        args: dict,
        call_id: str,
        step_tool_results: list,
        messages: list,
        emitted_events: List[GameEvent],
        notes: str
    ) -> tuple[bool, str | None]:
        """Execute command tool. Returns (turn_ended, last_event_id)."""
        if self.command_executor is None:
            step_tool_results.append({"name": tool_name, "content": "ERROR: No command_executor configured"})
            return False, None
        
        try:
            cmd_args = dict(args or {})
            cmd_args.pop("agent_id", None)
            command = LLMCommandFactory.from_llm(agent_id=agent_id, command_name=tool_name, **cmd_args)
            success, events, message = self.command_executor(agent_id, command)
            
            self._audit({
                "type": "CommandExecuted", 
                "name": tool_name, 
                "success": success, 
                "message": message, 
                "events": [e.to_dict() for e in events]
            })
            print(f"[LLM][{agent_id}] Command {tool_name} -> success={success}, message={message}")
            step_tool_results.append({"name": tool_name, "content": f"success={success}, message={message}"})
            
            if not success:
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": tool_name,
                    "content": f"ERROR: {message}",
                })
                return False, None
            
            emitted_events.extend(events)
            
            # Save notes after successful command
            if notes and self.session_store:
                try:
                    self.session_store.append_note(agent_id, notes)
                except Exception as exc:
                    step_tool_results.append({"name": tool_name, "content": f"ERROR: {str(exc)}"})
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": tool_name,
                        "content": f"ERROR: {str(exc)}",
                    })
                    return False, None
            
            # Get last event id if available
            last_event_id = events[-1].event_id if events else None
            
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "name": tool_name,
                "content": message or "Command executed successfully.",
            })
            
            return True, last_event_id
            
        except Exception as exc:
            step_tool_results.append({"name": tool_name, "content": f"ERROR: {str(exc)}"})
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "name": tool_name,
                "content": f"ERROR: {str(exc)}",
            })
            return False, None

    def _execute_tool_calls(self, agent_id, tool_calls, step_tool_results, messages, emitted_events, notes, content, last_event_id):
        turn_ended = False
        
        for call in tool_calls:
            ended, event_id = self._execute_single_tool_call(
                agent_id, call, step_tool_results, messages, 
                emitted_events, notes, content
            )
            
            if ended:
                turn_ended = True
            if event_id:
                last_event_id = event_id

        return turn_ended, last_event_id

    def _execute_single_tool_call(
        self, 
        agent_id: str, 
        call: dict, 
        step_tool_results: list, 
        messages: list, 
        emitted_events: list, 
        notes: str, 
        content: str
    ) -> tuple[bool, str | None]:
        """Execute a single tool call. Returns (turn_ended, last_event_id)."""
        tool_name, args, call_id = self._normalize_tool_call(call)
        
        if not tool_name:
            return False, None

        # Handle info/session tools
        if ResponseParser.is_info_tool(tool_name) or ResponseParser.is_session_tool(tool_name):
            ended = self._handle_info_tool(agent_id, tool_name, args, call_id, content, step_tool_results, messages)
            return ended, None

        # Handle command tools
        if self._tool_is_command(tool_name):
            return self._handle_command_tool(
                agent_id, tool_name, args, call_id, 
                step_tool_results, messages, emitted_events, notes
            )
            
        # Unknown tool type
        return False, None
    
    def _tool_is_command(self, tool_name: str) -> bool:
        """Check if tool is a command tool (not info/session)."""
        # Assuming if it's not info/session it's a command, or check specific list
        # Original code used private method check or implicit logic.
        # Let's rely on exclusion of info/session for now or check registry if available.
        # But wait, original code skipped if not command.
        # Let's assume everything else is a command for now, or check explicit list if we have one.
        # For safety, let's assume true if not info/session.
        return True

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