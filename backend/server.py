"""FastAPI gateway for Laundromat Tycoon.

This module is intentionally minimal and production-oriented.

Endpoints
- GET  /state/{agent_id}: fetch current agent state
- POST /api/advance_day: run one or more full simulation ticks
- GET  /health: liveness + basic metadata
"""

from datetime import datetime
import time
from typing import List, Optional
import uuid
from pathlib import Path

from fastapi import FastAPI, Query, Body
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles # Added for robust static file serving if needed
from pydantic import BaseModel

from core.events import GameStarted
from infrastructure.serialization import to_serializable as _to_serializable

try:
    # When imported as package module: backend.server
    from .application_factory import ApplicationFactory
    from .turn_orchestrator import TurnOrchestrator, default_days_from_env
except Exception:  # noqa: BLE001
    # When run from backend/ directory: uvicorn server:app
    from application_factory import ApplicationFactory
    from turn_orchestrator import TurnOrchestrator, default_days_from_env

# Initialize engine and subsystems once (singleton)
game_engine, gm, judge, llm_dispatcher = ApplicationFactory.create_game_engine()
orchestrator = TurnOrchestrator(game_engine, llm_dispatcher, gm, judge)

# Back-compat alias for older internal usage.
engine = game_engine

app = FastAPI(title="Laundromat Tycoon API", version="0.1.0")

# Mount static files if needed, or just serve specific files
# app.mount("/static", StaticFiles(directory="static"), name="static")

class AdvanceDayRequest(BaseModel):
    agent_ids: Optional[List[str]] = None
    days: Optional[int] = None


class StartGamePlayer(BaseModel):
    agent_id: str
    provider_key: Optional[str] = None


class StartGameRequest(BaseModel):
    # Either provide explicit players or a count.
    players: Optional[List[StartGamePlayer]] = None
    num_players: Optional[int] = None
    scenario: Optional[str] = None
    # If true, emits a new GameStarted even if one already exists.
    force: bool = False


class StartGameResponse(BaseModel):
    ok: bool
    created: List[str]
    existing: List[str]
    players: List[str]


@app.get("/state/{agent_id}")
async def get_state_v2(agent_id: str):
    """Return a JSON-serializable AgentState snapshot."""
    state = engine.get_current_state(agent_id)
    return _to_serializable(state)


@app.get("/history/{agent_id}")
async def get_history(
    agent_id: str,
    last_event_id: str | None = Query(default=None),
    limit: int | None = Query(default=None),
):
    """Return the agent's event log.

    - If last_event_id is provided: return events after it.
    - If limit is provided (and last_event_id is not): return only the last N events.
    """
    events = engine.get_event_log(agent_id)
    if last_event_id:
        try:
            idx = next(i for i, e in enumerate(events) if getattr(e, "event_id", None) == last_event_id)
            events = events[idx + 1 :]
        except StopIteration:
            events = []
    elif limit is not None:
        try:
            n = int(limit)
            if n > 0:
                events = events[-n:]
        except (TypeError, ValueError):
            # If limit cannot be parsed as a positive integer, ignore it and return all events.
            pass
    return {"agent_id": agent_id, "events": [_to_serializable(e) for e in events]}


@app.post("/api/start_game", response_model=StartGameResponse)
async def start_game(req: StartGameRequest | None = None):
    """Initialize a new game session for one or more players."""
    scenario = (req.scenario if req and req.scenario is not None else "")
    force = bool(req.force) if req else False

    players: list[StartGamePlayer] = []
    if req and req.players:
        players = req.players
    else:
        n = int(req.num_players) if (req and req.num_players is not None) else 2
        if n < 1:
            n = 1
        players = [StartGamePlayer(agent_id=f"PLAYER_{i:03d}") for i in range(1, n + 1)]

    created: list[str] = []
    existing: list[str] = []

    # Keep dispatcher mappings in sync.
    provider_cfg = getattr(llm_dispatcher, "provider_config_map", None)
    provider_map = getattr(llm_dispatcher, "provider_map", None)

    for p in players:
        agent_id = (p.agent_id or "").strip()
        if not agent_id:
            continue

        already_started = any(getattr(e, "event_type", "") == "GameStarted" for e in engine.get_event_log(agent_id))
        if already_started and not force:
            existing.append(agent_id)
        else:
            evt = GameStarted(
                event_id=str(uuid.uuid4()),
                agent_id=agent_id,
                timestamp=datetime.now(),
                week=0,
                scenario=scenario or "",
            )
            engine.event_repository.save(evt)
            created.append(agent_id)

        # Ensure the dispatcher knows about this player.
        if isinstance(provider_cfg, dict):
            key = (p.provider_key or "default").strip() or "default"
            if isinstance(provider_map, dict) and key not in provider_map:
                key = "default"
            provider_cfg[agent_id] = {"provider_key": key}

    return StartGameResponse(
        ok=True,
        created=sorted(set(created)),
        existing=sorted(set(existing)),
        players=engine.list_agents(),
    )


@app.post("/api/advance_day")
async def advance_day(req: AdvanceDayRequest | None = None):
    """Advance the simulation by 1+ days."""
    days = (req.days if req and req.days is not None else default_days_from_env())
    agent_ids = (req.agent_ids if req and req.agent_ids else None)

    # Default behavior: advance all started players.
    if not agent_ids:
        started_agents = [a for a in engine.list_agents() if str(a).startswith("PLAYER_")]
        agent_ids = started_agents or ["PLAYER_001"]

    # Ensure each agent has a GameStarted event (same as test_tick/start_game)
    for agent_id in agent_ids:
        already_started = any(getattr(e, "event_type", "") == "GameStarted" for e in engine.get_event_log(agent_id))
        if not already_started:
            print(f"[ADVANCE_DAY] Auto-starting agent {agent_id}")
            evt = GameStarted(
                event_id=str(uuid.uuid4()),
                agent_id=agent_id,
                timestamp=datetime.now(),
                week=0,
                scenario="Auto-started via advance_day",
            )
            engine.event_repository.save(evt)
            
            # Also ensure dispatcher mapping exists
            provider_cfg = getattr(llm_dispatcher, "provider_config_map", None)
            if isinstance(provider_cfg, dict):
                provider_cfg.setdefault(agent_id, {"provider_key": "default"})

    perf_start = time.perf_counter()
    agents_label = agent_ids if agent_ids is not None else ["PLAYER_001"]
    print(f"[ADVANCE_DAY] start days={days} agents={agents_label}")

    result = await orchestrator.run_full_tick_cycle(agent_ids=agent_ids, days=days)
    elapsed_ms = (time.perf_counter() - perf_start) * 1000.0

    # Print summary
    _print_tick_summary(result)

    print(f"[ADVANCE_DAY] done elapsed_ms={elapsed_ms:.1f}")
    return result


def _print_tick_summary(result: dict):
    """Print a concise, human-readable summary per tick/agent."""
    try:
        ticks = result.get("ticks", []) if isinstance(result, dict) else []
        for i, tick in enumerate(ticks, 1):
            agents = (tick or {}).get("agents", {})
            for agent_id, data in (agents or {}).items():
                t = (data or {}).get("time", {})
                week = t.get("week")
                day = t.get("day")
                state = (data or {}).get("state", {})
                cash = (state or {}).get("cash_balance")
                events = (data or {}).get("events", {})
                time_events = (events or {}).get("time_advanced", [])
                autonomous_events = (events or {}).get("autonomous", [])

                gm_err = isinstance((data or {}).get("gm"), dict) and (data or {}).get("gm", {}).get("error")
                judge_err = isinstance((data or {}).get("judge"), dict) and (data or {}).get("judge", {}).get("error")
                player_err = isinstance((data or {}).get("player"), dict) and (data or {}).get("player", {}).get("error")
                errs = ",".join(
                    [x for x in ["gm" if gm_err else "", "judge" if judge_err else "", "player" if player_err else ""] if x]
                )

                cash_str = f"${float(cash):.2f}" if isinstance(cash, (int, float)) else str(cash)
                print(
                    f"[ADVANCE_DAY] tick={i} agent={agent_id} week={week} day={day} cash={cash_str} "
                    f"events(time={len(time_events)}, auto={len(autonomous_events)})" + (f" errors={errs}" if errs else "")
                )
    except Exception:
        # Logging failures should not prevent the response from being returned
        pass


@app.post("/api/submit_command")
async def submit_command(
    agent_id: str = Query(..., description="The agent executing the command"),
    command_name: str = Query(..., description="Name of the command (e.g., SET_PRICE, BUY_SUPPLIES)"),
    payload: dict = Body(default={}, description="Command-specific payload")
):
    """Execute a game command for an agent.
    
    This is the primary endpoint for UI players to execute game actions,
    providing parity with LLM player capabilities.
    """
    try:
        result = ApplicationFactory._handle_submit_command(engine, {
            "agent_id": agent_id,
            "command_name": command_name,
            "payload": payload
        })
        return result
    except Exception as e:
        return {"success": False, "message": str(e), "error": str(type(e).__name__)}


@app.post("/api/run_turn")
async def run_turn(agent_id: str = Query(..., description="The agent to run an AI turn for")):
    """Run an AI turn for the specified agent.
    
    Triggers the LLM dispatcher to execute a full player turn,
    including state analysis, tool usage, and command execution.
    """
    try:
        result = await llm_dispatcher.run_player_turn(agent_id, history_messages=[])
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e), "error_type": str(type(e).__name__)}


@app.get("/ui")
async def ui():
    """Single-page debug UI to view state, history, and advance-day results."""
    # Serve the static file
    static_path = Path(__file__).resolve().parent / "static" / "debug_ui.html"
    return FileResponse(static_path)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "players": engine.list_agents(),
    }
