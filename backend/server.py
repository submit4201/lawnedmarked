"""FastAPI gateway for Laundromat Tycoon.

Endpoints
- POST /game/turn/{agent_id}: submit a command
- GET  /state/get/{agent_id}: fetch current state
- GET  /state/get_history/{agent_id}: fetch event history (optional last_event_id filter)
"""

from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from application_factory import ApplicationFactory
from core.commands import Command
from engine.autonomous_simulation import AutonomousSimulation
from llm_factory import LLMCommandFactory, COMMAND_REGISTRY
from pathlib import Path

_LLM_AVAILABLE = False
_LLM_ERROR = None
try:
    from llm import (
        LLMDispatcher,
        SessionStore,
        AuditLog)
    from llm.providers import localprovider,mock
    from llm.tools import ToolSpec, ToolExecutor
    from llm.tools.executors import ToolRouter
    from llm.tools.registry import ToolRegistry
    _LLM_AVAILABLE = True
except Exception as exc:  # noqa: BLE001
    _LLM_AVAILABLE = False
    _LLM_ERROR = str(exc)

# Initialize engine and subsystems once
engine, game_master, judge = ApplicationFactory.create_game_engine()

# Optional LLM wiring with MockLLM (keeps server running if modules missing)
_session_store = SessionStore() if _LLM_AVAILABLE else None
_audit_log = AuditLog(Path(__file__).resolve().parent / "logs" / "llm_responses.log") if _LLM_AVAILABLE else None
_provider_info = "uninitialized"
_provider_error = None
_tool_executor = None
_dispatcher = None

if _LLM_AVAILABLE:
    def _api_client(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if action == "GET_STATE":
            agent_id = payload.get("agent_id", "")
            state = engine.get_current_state(agent_id)
            serial = _to_serializable(state)
            return {"agent_state": serial, "locations": serial.get("locations", {})}

        if action == "GET_HISTORY":
            agent_id = payload.get("agent_id", "")
            last_event_id = payload.get("last_event_id")
            events = engine.get_event_log(agent_id)
            if last_event_id:
                try:
                    idx = next(i for i, e in enumerate(events) if getattr(e, "event_id", None) == last_event_id)
                    events = events[idx + 1 :]
                except StopIteration:
                    events = []
            return {"new_events": [_to_serializable(e) for e in events]}

        if action == "SUBMIT_COMMAND":
            agent_id = payload.get("agent_id", "")
            command_name = payload.get("command_name", "")
            cmd_payload = payload.get("payload", {}) or {}
            command: Command = LLMCommandFactory.from_llm(agent_id=agent_id, command_name=command_name, **cmd_payload)
            success, events, message = engine.execute_command(agent_id, command)
            return {"success": success, "events_emitted": len(events), "message": message}

        if action == "END_OF_TURN":
            from core.events_social_regulatory import EndOfTurnNotesSaved
            from datetime import datetime as _dt

            agent_id = payload.get("agent_id", "")
            notes = str(payload.get("notes", ""))
            note_evt = EndOfTurnNotesSaved(
                event_id=f"NOTES_{agent_id}_{int(_dt.now().timestamp())}",
                agent_id=agent_id,
                timestamp=_dt.now(),
                week=engine.get_current_state(agent_id).current_week,
                notes=notes,
            )
            engine.event_repository.save(note_evt)
            return {"ok": True}

        return {"error": f"Unknown api_client action {action}"}

    _tool_router = ToolRouter(session_store=_session_store, api_client=_api_client)
    _tool_executor = ToolExecutor(
        [
            ToolSpec(name=t.name, description=t.description, schema=t.schema, handler=lambda p, n=t.name: _tool_router.execute(n, p))
            for t in ToolRegistry.get_all_tools()
        ],
        audit_log=_audit_log,
    )
    try:
        _provider = localprovider.LocalProvider(config=localprovider.localConfig())
        _provider_info = f"LocalProvider:{getattr(_provider.config, 'model', 'unknown')}"
    except Exception as exc:
        _provider_error = str(exc)
        _provider = mock.MockLLM()
        _provider_info = "MockLLM (fallback)"
        print(f"[LLM] Falling back to MockLLM: {exc}")
    _dispatcher = LLMDispatcher(
        provider=_provider,
        tool_executor=_tool_executor,
        audit_log=_audit_log,
        session_store=_session_store,
        command_executor=lambda agent_id, command: engine.execute_command(agent_id, command),
    )

app = FastAPI(title="Laundromat Tycoon API", version="0.1.0")


class CommandRequest(BaseModel):
    command_name: str
    payload: Dict[str, Any] = {}


class CommandResponse(BaseModel):
    success: bool
    events_emitted: int
    message: str


class StateResponse(BaseModel):
    agent_state: Dict[str, Any]
    locations: Dict[str, Any]


class EventLogResponse(BaseModel):
    new_events: List[Dict[str, Any]]


class ToolRequest(BaseModel):
    name: str
    payload: Dict[str, Any]

class ToolResponse(BaseModel):
    result: Dict[str, Any]


class LLMCommandResponse(BaseModel):
    success: bool
    events_emitted: int
    message: str
    notes_saved: bool = False


class LLMStatusResponse(BaseModel):
    llm_available: bool
    provider: str
    error: Optional[str] = None


def _to_serializable(obj: Any) -> Any:
    """Convert dataclass/enum/datetime-heavy structures to JSON-safe payloads."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _to_serializable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [_to_serializable(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    return obj


def _next_time(day: int, week: int) -> tuple[int, int]:
    """Compute the next (day, week) step. Day rolls over every 7 days."""
    new_day = day + 1
    new_week = week
    if new_day >= 7:
        new_day = 0
        new_week = week + 1
    return new_day, new_week


def _run_simulation_tick(agent_id: str) -> List[Any]:
    """Run one simulation step.

    Protocol:
    1) Engine emits and persists TimeAdvanced (first event of tick)
    2) AutonomousSimulation emits derived events (persisted)
    3) GameMaster and Judge emit their events (persisted)
    """
    before = engine.get_current_state(agent_id)
    current_day = int(getattr(before, "current_day", 0))
    current_week = int(getattr(before, "current_week", 0))
    new_day, new_week = _next_time(current_day, current_week)

    _ok, time_events = engine.advance_time(agent_id=agent_id, day=new_day, week=new_week)
    time_event = time_events[0]

    # Build state after TimeAdvanced to ensure all downstream work uses the same timestamp.
    state = engine.get_current_state(agent_id)

    generated: List[Any] = []

    # Autonomous simulation (daily).
    for location_id in list(state.locations.keys()):
        generated.extend(AutonomousSimulation.process_daily_tick(state, location_id))

        # Weekly processing at the start of the new week.
        if new_day == 0:
            generated.extend(AutonomousSimulation.process_weekly_costs(state, location_id))
            generated.extend(AutonomousSimulation.process_machine_wear(state, location_id))

    if new_day == 0:
        generated.extend(AutonomousSimulation.process_scandal_decay(state))
        # Simple monthly interest cadence: every 4 weeks.
        if new_week > 0 and (new_week % 4) == 0:
            generated.extend(AutonomousSimulation.process_monthly_interest(state))

    # Adjudication reactions.
    generated.extend(game_master.check_and_trigger_events(state))
    generated.extend(judge.evaluate_action_consequences(state, time_event))

    for event in generated:
        engine.event_repository.save(event)

    return [*time_events, *generated]


@app.post("/game/turn/{agent_id}")
async def submit_command(agent_id: str, cmd: CommandRequest | None = None):
    """Primary endpoint.

    - If cmd is provided (command_name+payload), executes that command.
    - If cmd is omitted, runs an LLM-driven player turn and returns emitted events + thoughts.
    """
    if cmd is None or not cmd.command_name:
        if not _LLM_AVAILABLE or _dispatcher is None:
            raise HTTPException(status_code=400, detail="LLM dispatcher unavailable")

        # Run deterministic time progression and autonomous simulation before the player's action.
        _run_simulation_tick(agent_id)

        # Build a simple context user message (the dispatcher also injects full state/history tool context).
        state = engine.get_current_state(agent_id)
        location_ids = list(state.locations.keys()) if state.locations else []
        context_msg = f"CURRENT GAME STATE (Week {state.current_week}, Day {getattr(state, 'current_day', 0)}): Cash=${state.cash_balance:.2f}; Locations={location_ids}"
        history_messages: List[Dict[str, Any]] = [{"role": "user", "content": context_msg}]

        try:
            result = await _dispatcher.run_player_turn(agent_id, history_messages)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"LLM Provider Error: {str(e)}")

        if "error" in result:
            raise HTTPException(status_code=400, detail=result.get("error"))

        return _to_serializable(result)

    # Direct command submission path
    try:
        command: Command = LLMCommandFactory.from_llm(agent_id=agent_id, command_name=cmd.command_name, **(cmd.payload or {}))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))

    success, events, message = engine.execute_command(agent_id, command)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return CommandResponse(success=True, events_emitted=len(events), message=message)


@app.get("/llm/status", response_model=LLMStatusResponse)
async def llm_status() -> LLMStatusResponse:
    return LLMStatusResponse(
        llm_available=_LLM_AVAILABLE,
        provider=_provider_info,
        error=_provider_error,
    )


@app.get("/state/get/{agent_id}", response_model=StateResponse)
async def get_state(agent_id: str):
    state = engine.get_current_state(agent_id)
    serial = _to_serializable(state)
    return StateResponse(agent_state=serial, locations=serial.get("locations", {}))


@app.get("/state/get_history/{agent_id}", response_model=EventLogResponse)
async def get_history(agent_id: str, last_event_id: Optional[str] = None):
    events = engine.get_event_log(agent_id)
    if last_event_id:
        try:
            idx = next(i for i, e in enumerate(events) if getattr(e, "event_id", None) == last_event_id)
            events = events[idx + 1 :]
        except StopIteration:
            events = []
    return EventLogResponse(new_events=[_to_serializable(e) for e in events])


@app.post("/tools/execute", response_model=ToolResponse)
async def execute_tool(req: ToolRequest) -> ToolResponse:
    if not _LLM_AVAILABLE or _tool_executor is None:
        raise HTTPException(status_code=400, detail="LLM tools unavailable")
    result = _tool_executor.execute(req.name, req.payload)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=str(result.get("error")))
    return ToolResponse(result=_to_serializable(result))


@app.post("/llm/player/turn/{agent_id}", response_model=LLMCommandResponse)
async def llm_player_turn(agent_id: str):
    if not _LLM_AVAILABLE or _dispatcher is None:
        raise HTTPException(status_code=400, detail="LLM dispatcher unavailable")

    # Run deterministic time progression and autonomous simulation before the player's action.
    _run_simulation_tick(agent_id)

    # Inject current game state as context
    state = engine.get_current_state(agent_id)
    state_summary = {
        "cash_balance": state.cash_balance,
        "current_week": state.current_week,
        "social_score": state.social_score,
        "total_debt": state.total_debt_owed,
        "locations": len(state.locations),
        "credit_rating": getattr(state, "credit_rating", 50),
    }
    
    # List actual location IDs if any
    location_ids = list(state.locations.keys()) if state.locations else []
    location_info = f"Location IDs: {location_ids}" if location_ids else "No locations yet - use OPEN_NEW_LOCATION first!"
    
    # Build context message with state and available commands
    context_msg = f"""
CURRENT GAME STATE (Week {state.current_week}):
- Cash Balance: ${state_summary['cash_balance']:.2f}
- Total Debt: ${state_summary['total_debt']:.2f}
- Social Score: {state_summary['social_score']:.1f}/100
- Credit Rating: {state_summary['credit_rating']}/100
- {location_info}

AVAILABLE COMMANDS:
{', '.join(list(COMMAND_REGISTRY.keys()))}

What action do you want to take this turn? Respond with Command(NAME): {{payload}}
"""
    
    history_messages: List[Dict[str, Any]] = [
        {"role": "user", "content": context_msg}
    ]
    
    try:
        result = await _dispatcher.run_player_turn(agent_id, history_messages)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM Provider Error: {str(e)}. Please check your local provider.")

    if "error" in result:
        raise HTTPException(status_code=400, detail=result.get("error"))

    events = result.get("events") or []
    notes = result.get("notes")

    notes_saved = False
    if notes:
        from core.events_social_regulatory import EndOfTurnNotesSaved
        from datetime import datetime as _dt

        note_evt = EndOfTurnNotesSaved(
            event_id=f"NOTES_{agent_id}_{len(str(notes))}_{int(_dt.now().timestamp())}",
            agent_id=agent_id,
            timestamp=_dt.now(),
            week=engine.get_current_state(agent_id).current_week,
            notes=str(notes),
        )
        engine.event_repository.save(note_evt)
        notes_saved = True

    if _LLM_AVAILABLE and _audit_log:
        from core.events_social_regulatory import AuditSnapshotRecorded
        from datetime import datetime as _dt

        entries = _audit_log.list()
        events_count = len(entries)
        last_type = entries[-1].get("type") if entries else ""
        snapshot = AuditSnapshotRecorded(
            event_id=f"AUDIT_{agent_id}_{events_count}",
            agent_id=agent_id,
            timestamp=_dt.now(),
            week=engine.get_current_state(agent_id).current_week,
            entries_count=events_count,
            last_event_type=last_type,
        )
        engine.event_repository.save(snapshot)

    return LLMCommandResponse(
        success=True,
        events_emitted=len(events),
        message="LLM turn completed",
        notes_saved=notes_saved,
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "registered_commands": list(COMMAND_REGISTRY.keys()),
        "llm": "ready" if _LLM_AVAILABLE else "disabled",
        "llm_error": _LLM_ERROR,
        "players": engine.list_agents(),
    }
