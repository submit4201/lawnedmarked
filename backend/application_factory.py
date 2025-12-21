"""Application Factory and Bootstrap.

Creates and wires the full Event Sourcing + LLM stack.

Important:
- The repository is shared for the lifetime of the process.
- The GameEngine remains decoupled from handlers via registries.
"""

from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
from typing import Any, Dict, Tuple

from adjudication.game_master import GameMaster
from adjudication.judge import Judge
from command_handlers import ALL_HANDLERS
from core.events import GameEvent
from core.models import AgentState, LocationState
from engine.game_engine import GameEngine
from infrastructure.action_registry import ActionRegistry
from infrastructure.event_registry import EventRegistry
from infrastructure.event_repository import EventRepository, InMemoryEventRepository
from infrastructure.serialization import to_serializable as _to_serializable
from llm import AuditLog, LLMDispatcher, MockLLM, SessionStore, create_provider_from_env
from llm.tools import ToolExecutor, ToolSpec
from llm.tools.executors import ToolRouter
from llm.tools.registry import ToolRegistry
from projection.handlers.core_handlers import CORE_EVENT_HANDLERS
from projection.state_builder import StateBuilder


# ! _to_serializable is imported from infrastructure.serialization
# * Consolidated to eliminate code duplication


class ApplicationFactory:
    """Factory for creating and configuring the complete game application."""

    @staticmethod
    def create_game_engine(
        event_repository: EventRepository | None = None,
    ) -> Tuple[GameEngine, GameMaster, Judge, LLMDispatcher]:
        """Create and initialize the complete system.

        Returns:
            (game_engine, game_master, judge, llm_dispatcher)
        """

        # Best-effort env loading (no hardcoded paths).
        # ! Load from parent directory if .env isn't in current dir
        try:
            from dotenv import load_dotenv  # type: ignore
            from pathlib import Path
            
            # Try current dir first, then parent
            if Path(".env").exists():
                load_dotenv()
            elif Path("../.env").exists():
                load_dotenv(Path("../.env"))
            else:
                # Let dotenv search up the directory tree
                load_dotenv(find_dotenv=True)
        except Exception:
            pass

        if event_repository is None:
            event_repository = InMemoryEventRepository()

        action_registry = ActionRegistry()
        event_registry = EventRegistry()

        for command_type, handler in ALL_HANDLERS.items():
            action_registry.register(command_type, handler)

        for event_type, handler in CORE_EVENT_HANDLERS.items():
            event_registry.register(event_type, handler)

        # Initial state template with a predictable starter location.
        initial_state = AgentState(agent_id="TEMPLATE")
        initial_state.locations["LOC_001"] = LocationState(
            location_id="LOC_001",
            zone="DOWNTOWN",
            monthly_rent=2000.0,
            current_cleanliness=85.0,
            inventory_detergent=2000,
            inventory_softener=1000,
        )
        state_builder = StateBuilder(event_registry, initial_state)

        game_engine = GameEngine(
            event_repository=event_repository,
            action_registry=action_registry,
            event_registry=event_registry,
            state_builder=state_builder,
        )

        game_master = GameMaster(event_repository)
        judge = Judge(event_repository)

        # LLM stack
        session_store = SessionStore()
        audit_log = AuditLog(Path(__file__).resolve().parent / "logs" / "llm_responses.log")

        # Providers available to the dispatcher.
        #
        # If LLM_PROVIDERS is set (comma-separated), create all of them and set
        # "default" to a fallback chain that tries them in order.
        # Otherwise, keep the legacy behavior (local + optional azure_openai).
        from llm.providers import FallbackProvider

        provider_map: Dict[str, Any] = {"mock": MockLLM()}
        providers_csv = (os.getenv("LLM_PROVIDERS") or "").strip()

        # ! Common typo corrections for provider names
        PROVIDER_ALIASES = {
            "geminiest": "gemini",
            "gpt": "openai",
            "azure": "azure_openai",
            "azureopenai": "azure_openai",
        }

        if providers_csv:
            names = [n.strip().lower() for n in providers_csv.split(",") if n.strip()]
            # Apply typo corrections
            names = [PROVIDER_ALIASES.get(n, n) for n in names]
            built: list[Any] = []
            info_parts: list[str] = []
            for name in names:
                try:
                    p, info = create_provider_from_env(name)
                    provider_map[name] = p
                    built.append(p)
                    info_parts.append(info or name)
                except Exception as exc:
                    print(f"[LLM][{name}] Failed to create provider: {exc}")
            if built:
                provider_map["default"] = FallbackProvider(built)
                print(f"[LLM] Providers: {', '.join(info_parts)}")
                print(f"[LLM] Default: fallback({', '.join(names)})")
            else:
                print("[LLM] No providers created from LLM_PROVIDERS, falling back to local")
        else:
            provider_1, provider_info_1 = create_provider_from_env("local")
            if provider_info_1:
                # Keep initialization visible during startup
                print(f"[LLM] Provider: {provider_info_1}")
            provider_map["default"] = provider_1

            provider_2 = None
            provider_info_2 = ""
            azure_enabled = bool(
                (os.getenv("AZURE_api_key") or os.getenv("LLM_API_KEY"))
                and (os.getenv("AZURE_base_url") or os.getenv("LLM_ENDPOINT"))
                and (
                    os.getenv("AZURE_deployment")
                    or os.getenv("AZURE_deployment_name")
                    or os.getenv("LLM_MODEL")
                )
            )
            if azure_enabled:
                provider_2, provider_info_2 = create_provider_from_env("azure_openai")
                if provider_info_2:
                    print(f"[LLM] Provider: {provider_info_2}")
                if provider_2 is not None:
                    provider_map["azure_openai"] = provider_2

        # Ensure Gemini provider is available when configured.
        # This is primarily used for SYSTEM_GM / SYSTEM_JUDGE roles.
        if "gemini" not in provider_map and (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
            try:
                gem, info = create_provider_from_env("gemini")
                provider_map["gemini"] = gem
                print(f"[LLM] Provider: {info}")
            except Exception as exc:
                print(f"[LLM][gemini][warn] failed to initialize gemini provider: {exc}")
        def api_client(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            if action == "GET_STATE":
                agent_id = payload.get("agent_id", "")
                state = game_engine.get_current_state(agent_id)
                serial = _to_serializable(state)
                return {"agent_state": serial, "locations": serial.get("locations", {})}

            if action == "GET_HISTORY":
                agent_id = payload.get("agent_id", "")
                last_event_id = payload.get("last_event_id")
                limit = payload.get("limit")
                events = game_engine.get_event_log(agent_id)
                if last_event_id:
                    try:
                        idx = next(
                            i for i, e in enumerate(events) if getattr(e, "event_id", None) == last_event_id
                        )
                        events = events[idx + 1 :]
                    except StopIteration:
                        events = []
                # If no last_event_id was provided, allow returning only the last N events.
                if limit is not None:
                    try:
                        n = int(limit)
                        if n > 0:
                            events = events[-n:]
                    except Exception:
                        pass
                return {"new_events": [_to_serializable(e) for e in events]}

            if action == "SUBMIT_COMMAND":
                from llm_factory import LLMCommandFactory

                agent_id = payload.get("agent_id", "")
                command_name = payload.get("command_name", "")
                cmd_payload = dict(payload.get("payload", {}) or {})
                # Remove agent_id and command_name from payload if present to avoid multiple values error
                cmd_payload.pop("agent_id", None)
                cmd_payload.pop("command_name", None)
                
                command = LLMCommandFactory.from_llm(
                    agent_id=agent_id,
                    command_name=command_name,
                    **cmd_payload,
                )
                success, events, message = game_engine.execute_command(agent_id, command)
                return {"success": success, "events_emitted": len(events), "message": message}

            if action == "END_OF_TURN":
                from core.events_social_regulatory import EndOfTurnNotesSaved

                agent_id = payload.get("agent_id", "")
                notes = str(payload.get("notes", ""))
                note_evt = EndOfTurnNotesSaved(
                    event_id=f"NOTES_{agent_id}_{int(datetime.now().timestamp())}",
                    agent_id=agent_id,
                    timestamp=datetime.now(),
                    week=game_engine.get_current_state(agent_id).current_week,
                    notes=notes,
                )
                game_engine.event_repository.save(note_evt)
                return {"ok": True}

            return {"error": f"Unknown api_client action {action}"}

        tool_router = ToolRouter(session_store=session_store, api_client=api_client)
        tool_executor = ToolExecutor(
            [
                ToolSpec(
                    name=t.name,
                    description=t.description,
                    schema=t.schema,
                    handler=lambda p, n=t.name: tool_router.execute(n, p),
                )
                for t in ToolRegistry.get_all_tools()
            ],
            audit_log=audit_log,
        )

        from llm.dispatcher import GM_AGENT_ID, JUDGE_AGENT_ID

        # ! Default to first LLM_PROVIDERS entry for player, 'default' as fallback
        # Previously defaulted to 'default' which is the FallbackProvider - now use first real provider
        first_provider = names[0] if providers_csv and names else None
        gemini_available = "gemini" in provider_map
        default_player_provider = os.getenv("PLAYER_PROVIDER_KEY", first_provider or "default")
        if default_player_provider not in provider_map:
            default_player_provider = "default"

        gm_provider = os.getenv("GM_PROVIDER_KEY", "gemini" if gemini_available else "default")
        if gm_provider not in provider_map:
            gm_provider = "default"

        judge_provider = os.getenv("JUDGE_PROVIDER_KEY", "gemini" if gemini_available else "default")
        if judge_provider not in provider_map:
            judge_provider = "default"

        provider_config_map = {
            "PLAYER_000": {"provider_key": "default"},
            "PLAYER_001": {"provider_key": default_player_provider},
            GM_AGENT_ID: {"provider_key": gm_provider},
            JUDGE_AGENT_ID: {"provider_key": judge_provider},
        }

        llm_dispatcher = LLMDispatcher(
            provider_map=provider_map,
            provider_config_map=provider_config_map,
            tool_executor=tool_executor,
            audit_log=audit_log,
            session_store=session_store,
            command_executor=lambda agent_id, command: game_engine.execute_command(agent_id, command),
            game_engine=game_engine,
        )

        return game_engine, game_master, judge, llm_dispatcher


__all__ = ["ApplicationFactory"]
