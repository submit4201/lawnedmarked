"""Application Factory and Bootstrap.

Creates and wires the full Event Sourcing + LLM stack.

Important:
- The repository is shared for the lifetime of the process.
- The GameEngine remains decoupled from handlers via registries.
"""

from __future__ import annotations

from datetime import datetime
import os
from typing import Any, Dict, Tuple, List

from adjudication.game_master import GameMaster
from adjudication.judge import Judge
from command_handlers import ALL_HANDLERS
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
from llm.providers import FallbackProvider


class ApplicationFactory:
    """Factory for creating and configuring the complete game application."""

    @staticmethod
    def create_game_engine(
        event_repository: EventRepository | None = None,
    ) -> Tuple[GameEngine, GameMaster, Judge, LLMDispatcher]:
        """Create and initialize the complete system."""
        
        ApplicationFactory._load_environment()

        if event_repository is None:
            event_repository = InMemoryEventRepository()

        game_engine = ApplicationFactory._setup_game_engine(event_repository)
        game_master = GameMaster(event_repository)
        judge = Judge(event_repository)

        llm_dispatcher = ApplicationFactory._setup_llm_stack(game_engine)

        return game_engine, game_master, judge, llm_dispatcher

    @staticmethod
    def _load_environment():
        """Best-effort env loading."""
        try:
            from dotenv import load_dotenv  # type: ignore
            
            # Try current dir first, then parent
            if Path(".env").exists():
                load_dotenv()
            elif Path("../.env").exists():
                load_dotenv(Path("../.env"))
            else:
                load_dotenv(find_dotenv=True)
        except Exception:
            # Environment loading is intentionally best-effort; failures here
            # must not prevent application startup.
            pass

    @staticmethod
    def _setup_game_engine(event_repository: EventRepository) -> GameEngine:
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

        return GameEngine(
            event_repository=event_repository,
            action_registry=action_registry,
            event_registry=event_registry,
            state_builder=state_builder,
        )

    @staticmethod
    def _setup_llm_stack(game_engine: GameEngine) -> LLMDispatcher:
        session_store = SessionStore()
        audit_log = AuditLog(Path(__file__).resolve().parent / "logs" / "llm_responses.log")
        
        provider_map = ApplicationFactory._create_provider_map()
        
        tool_router = ToolRouter(session_store=session_store, api_client=ApplicationFactory._create_api_client(game_engine))
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
        
        # Determine default keys
        gemini_available = "gemini" in provider_map
        default_player_provider = "default"
        # Since we don't have the explicit list of names easily without reparsing, we check keys
        # But we can re-implement logic if needed. For now "default" is safe if no other specific logic.
        
        # Re-parse quickly to find first custom provider if any
        providers_csv = (os.getenv("LLM_PROVIDERS") or "").strip()
        first_provider = None
        if providers_csv:
             # Basic parse to get first name
             first_provider = providers_csv.split(",")[0].strip().lower()
             
        p_key = os.getenv("PLAYER_PROVIDER_KEY", first_provider or "default")
        if p_key not in provider_map:
             p_key = "default"

        gm_provider = os.getenv("GM_PROVIDER_KEY", "gemini" if gemini_available else "default")
        if gm_provider not in provider_map:
            gm_provider = "default"

        judge_provider = os.getenv("JUDGE_PROVIDER_KEY", "gemini" if gemini_available else "default")
        if judge_provider not in provider_map:
            judge_provider = "default"
            
        provider_config_map = {
            "PLAYER_000": {"provider_key": "default"},
            "PLAYER_001": {"provider_key": p_key},
            GM_AGENT_ID: {"provider_key": gm_provider},
            JUDGE_AGENT_ID: {"provider_key": judge_provider},
        }

        return LLMDispatcher(
            provider_map=provider_map,
            provider_config_map=provider_config_map,
            tool_executor=tool_executor,
            audit_log=audit_log,
            session_store=session_store,
            command_executor=lambda agent_id, command: game_engine.execute_command(agent_id, command),
            game_engine=game_engine,
        )

    @staticmethod
    @staticmethod
    def _normalize_provider_name(name: str) -> str:
        """Normalize provider name using aliases."""
        PROVIDER_ALIASES = {
            "geminiest": "gemini",
            "gpt": "openai",
            "azure": "azure_openai",
            "azureopenai": "azure_openai",
        }
        return PROVIDER_ALIASES.get(name.lower(), name.lower())

    @staticmethod
    def _parse_provider_names(providers_csv: str) -> list[str]:
        """Parse and normalize provider names from CSV string."""
        if not providers_csv:
            return []
        names = [n.strip() for n in providers_csv.split(",") if n.strip()]
        return [ApplicationFactory._normalize_provider_name(n) for n in names]

    @staticmethod
    def _create_providers_from_list(names: list[str]) -> tuple[Dict[str, Any], list[Any], list[str]]:
        """Create providers from list of names. Returns (provider_map, built_list, info_list)."""
        provider_map: Dict[str, Any] = {}
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
        
        return provider_map, built, info_parts

    @staticmethod
    def _ensure_gemini_provider(provider_map: Dict[str, Any]):
        """Add Gemini provider if configured via env vars but not already in map."""
        has_gemini = "gemini" in provider_map
        has_gemini_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        
        if not has_gemini and has_gemini_key:
            try:
                gem, info = create_provider_from_env("gemini")
                provider_map["gemini"] = gem
                print(f"[LLM] Provider: {info}")
            except Exception as exc:
                print(f"[LLM][gemini][warn] failed to initialize gemini provider: {exc}")

    @staticmethod
    def _create_provider_map() -> Dict[str, Any]:
        provider_map: Dict[str, Any] = {"mock": MockLLM()}
        providers_csv = (os.getenv("LLM_PROVIDERS") or "").strip()

        if providers_csv:
            names = ApplicationFactory._parse_provider_names(providers_csv)
            created_map, built, info_parts = ApplicationFactory._create_providers_from_list(names)
            provider_map.update(created_map)
            
            if built:
                provider_map["default"] = FallbackProvider(built)
                print(f"[LLM] Providers: {', '.join(info_parts)}")
            else:
                print("[LLM] No providers created from LLM_PROVIDERS, falling back to local")
                ApplicationFactory._add_local_provider(provider_map)
        else:
            ApplicationFactory._add_local_provider(provider_map)
            
        ApplicationFactory._ensure_gemini_provider(provider_map)
        return provider_map

    @staticmethod
    def _add_local_provider(provider_map: Dict[str, Any]):
        provider_1, provider_info_1 = create_provider_from_env("local")
        if provider_info_1:
            print(f"[LLM] Provider: {provider_info_1}")
        provider_map["default"] = provider_1
        
        # Check Azure env vars to optionally add azure_openai
        # Logic copied from original
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
             p2, info2 = create_provider_from_env("azure_openai")
             if info2:
                 print(f"[LLM] Provider: {info2}")
             if p2:
                 provider_map["azure_openai"] = p2

    @staticmethod
    def _handle_get_state(game_engine: GameEngine, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET_STATE API action."""
        agent_id = payload.get("agent_id", "")
        state = game_engine.get_current_state(agent_id)
        serial = _to_serializable(state)
        return {"agent_state": serial, "locations": serial.get("locations", {})}

    @staticmethod
    def _filter_events_by_last_id(events: List[Any], last_event_id: Any) -> List[Any]:
        """Filter events to return only those after the specified event ID."""
        if not last_event_id:
            return events
        try:
            idx = next(
                i for i, e in enumerate(events) 
                if getattr(e, "event_id", None) == last_event_id
            )
            return events[idx + 1:]
        except StopIteration:
            return []
    
    @staticmethod
    def _apply_event_limit(events: List[Any], limit: Any) -> List[Any]:
        """Apply limit to event list if valid limit is provided."""
        if limit is None:
            return events
        try:
            n = int(limit)
            if n > 0:
                return events[-n:]
        except (TypeError, ValueError):
            # If limit cannot be parsed as a positive integer, ignore it and return all events.
            pass
        return events
    
    @staticmethod
    def _handle_get_history(game_engine: GameEngine, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET_HISTORY API action."""
        agent_id = payload.get("agent_id", "")
        last_event_id = payload.get("last_event_id")
        limit = payload.get("limit")
        
        events = game_engine.get_event_log(agent_id)
        
        events = ApplicationFactory._filter_events_by_id(events, last_event_id)
        events = ApplicationFactory._apply_event_limit(events, limit)
        
        return {"new_events": [_to_serializable(e) for e in events]}

    @staticmethod
    def _filter_events_by_id(events: list, last_event_id: str | None) -> list:
        """Filter events occurring after the given event ID."""
        if not last_event_id:
            return events
            
        try:
            # Find index of last_event_id
            idx = next(
                i for i, e in enumerate(events) 
                if getattr(e, "event_id", None) == last_event_id
            )
            return events[idx + 1:]
        except StopIteration:
            # If ID not found (or list empty), return empty list as standard behavior 
            # for "give me everything after X" if X isn't in the known history? 
            # Or should it return everything? Original logic returned [] on StopIteration.
            return []

    @staticmethod
    def _apply_event_limit(events: list, limit: Any) -> list:
        """Apply numerical limit to events list involved."""
        if limit is None:
            return events
            
        try:
            n = int(limit)
            if n > 0:
                return events[-n:]
        except (TypeError, ValueError):
            pass
            
        return events

    @staticmethod
    def _handle_submit_command(game_engine: GameEngine, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SUBMIT_COMMAND API action."""
        from llm_factory import LLMCommandFactory

        agent_id = payload.get("agent_id", "")
        command_name = payload.get("command_name", "")
        cmd_payload = dict(payload.get("payload", {}) or {})
        cmd_payload.pop("agent_id", None)
        cmd_payload.pop("command_name", None)
        
        command = LLMCommandFactory.from_llm(
            agent_id=agent_id,
            command_name=command_name,
            **cmd_payload,
        )
        success, events, message = game_engine.execute_command(agent_id, command)
        return {"success": success, "events_emitted": len(events), "message": message}

    @staticmethod
    def _handle_end_of_turn(game_engine: GameEngine, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle END_OF_TURN API action."""
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

    @staticmethod
    def _handle_api_request(game_engine: GameEngine, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route API requests to appropriate handler."""
        handlers = {
            "GET_STATE": ApplicationFactory._handle_get_state,
            "GET_HISTORY": ApplicationFactory._handle_get_history,
            "SUBMIT_COMMAND": ApplicationFactory._handle_submit_command,
            "END_OF_TURN": ApplicationFactory._handle_end_of_turn,
        }
        
        handler = handlers.get(action)
        if handler:
            return handler(game_engine, payload)
        
        return {"error": f"Unknown api_client action {action}"}

    @staticmethod
    def _create_api_client(game_engine: GameEngine) -> Any:
        def api_client(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            return ApplicationFactory._handle_api_request(game_engine, action, payload)
        return api_client

__all__ = ["ApplicationFactory"]
