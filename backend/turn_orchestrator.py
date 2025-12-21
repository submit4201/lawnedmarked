"""Turn orchestrator.

Runs the full simulation tick cycle via a single call:
- Advance time (TimeAdvanced is first event)
- Autonomous simulation (revenue/costs/wear)
- GM LLM injection (optional; INJECT_WORLD_EVENT)
- Judge LLM injection (optional; INJECT_WORLD_EVENT)
- Player/competitor LLM turns (optional; transactional commands)

This module contains orchestration only; domain rules remain in command handlers.
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Tuple

from engine.autonomous_simulation import AutonomousSimulation
from engine.game_engine import GameEngine
from infrastructure.serialization import to_serializable as _to_serializable


def _next_time(day: int, week: int) -> Tuple[int, int]:
    new_day = day + 1
    new_week = week
    if new_day >= 7:
        new_day = 0
        new_week = week + 1
    return new_day, new_week


def _event_brief(event: Any) -> Dict[str, Any]:
    """Create a small, stable summary for an event."""
    data: Dict[str, Any] = {
        "event_type": getattr(event, "event_type", ""),
        "event_id": getattr(event, "event_id", ""),
        "week": getattr(event, "week", None),
    }
    # Include a handful of common fields when present.
    for k in (
        "day",
        "location_id",
        "amount",
        "transaction_type",
        "description",
        "loads_processed",
        "revenue_generated",
        "utility_cost",
        "supplies_cost",
        "rating",
        "review_text",
        "fine_amount",
        "due_date",
    ):
        if hasattr(event, k):
            data[k] = getattr(event, k)
    return _to_serializable(data)


def _build_location_data(state: Any) -> List[Dict[str, Any]]:
    locs = []
    for loc_id, loc in (getattr(state, "locations", {}) or {}).items():
        pricing = getattr(loc, "active_pricing", {}) or {}
        equipment = getattr(loc, "equipment", {}) or {}
        staff = getattr(loc, "current_staff", []) or []
        locs.append(
            {
                "location_id": loc_id,
                "zone": getattr(loc, "zone", ""),
                "monthly_rent": getattr(loc, "monthly_rent", None),
                "cleanliness": getattr(loc, "current_cleanliness", None),
                "equipment_count": len(equipment) if hasattr(equipment, "__len__") else None,
                "staff_count": len(staff) if hasattr(staff, "__len__") else None,
                "pricing": {
                    k: pricing.get(k)
                    for k in ("StandardWash", "PremiumWash", "Dry", "VendingItems")
                    if k in pricing
                },
                "inventory": {
                    "detergent": getattr(loc, "inventory_detergent", None),
                    "softener": getattr(loc, "inventory_softener", None),
                },
            }
        )
    return locs

def _build_finances_data(state: Any) -> Dict[str, Any]:
    return {
        "cash_balance": getattr(state, "cash_balance", 0.0),
        "line_of_credit_balance": getattr(state, "line_of_credit_balance", 0.0),
        "line_of_credit_limit": getattr(state, "line_of_credit_limit", 0.0),
        "total_debt_owed": getattr(state, "total_debt_owed", 0.0),
        "current_tax_liability": getattr(state, "current_tax_liability", 0.0),
    }

def _build_reputation_data(state: Any) -> Dict[str, Any]:
    return {
        "social_score": getattr(state, "social_score", 0.0),
        "regulatory_status": getattr(state, "regulatory_status", ""),
        "credit_rating": getattr(state, "credit_rating", 0),
    }

def _build_player_turn_packet(state: Any, recent_events: List[Any]) -> Dict[str, Any]:
    packet = {
        "time": {"week": getattr(state, "current_week", 0), "day": getattr(state, "current_day", 0)},
        "finances": _build_finances_data(state),
        "reputation": _build_reputation_data(state),
        "locations": _build_location_data(state),
        "recent_events": [_event_brief(e) for e in (recent_events or [])][-10:],
    }
    return _to_serializable(packet)


class TurnOrchestrator:
    def __init__(self, game_engine: GameEngine, llm_dispatcher: Any, game_master: Any, judge: Any):
        self.game_engine = game_engine
        self.llm_dispatcher = llm_dispatcher
        self.game_master = game_master
        self.judge = judge

    async def run_full_tick_cycle(
        self,
        agent_ids: Optional[List[str]] = None,
        days: int = 1,
    ) -> Dict[str, Any]:
        """Run 1+ simulation ticks and return a structured summary."""

        if days <= 0:
            raise ValueError("days must be >= 1")

        if not agent_ids:
            agent_ids = ["PLAYER_001"]

        self._ensure_dispatcher_config(agent_ids)

        summary: Dict[str, Any] = {
            "days": days,
            "agent_ids": list(agent_ids),
            "ticks": [],
        }

        for _ in range(days):
            tick_data: Dict[str, Any] = {"agents": {}}
            for agent_id in agent_ids:
                tick_data["agents"][agent_id] = await self._process_agent_tick(agent_id)
            summary["ticks"].append(tick_data)

        return summary

    def _ensure_dispatcher_config(self, agent_ids: List[str]):
        if self.llm_dispatcher is not None:
            cfg = getattr(self.llm_dispatcher, "provider_config_map", None)
            if isinstance(cfg, dict):
                for agent_id in agent_ids:
                    cfg.setdefault(agent_id, {"provider_key": "default"})

    async def _process_agent_tick(self, agent_id: str) -> Dict[str, Any]:
        before = self.game_engine.get_current_state(agent_id)
        current_day = int(getattr(before, "current_day", 0))
        current_week = int(getattr(before, "current_week", 0))
        new_day, new_week = _next_time(current_day, current_week)

        _ok, time_events = self.game_engine.advance_time(agent_id=agent_id, day=new_day, week=new_week)
        time_event = time_events[0]

        # Autonomous events
        generated_events = self._run_autonomous_events(agent_id, new_day, new_week)
        for evt in generated_events:
            self.game_engine.event_repository.save(evt)

        # System Agents (GM, Judge)
        gm_result = await self._run_gm_turn(agent_id)
        judge_result = await self._run_judge_turn(agent_id, time_event, generated_events)

        # Player Turn
        player_result = await self._run_player_turn(agent_id, time_event, generated_events)

        # Final State
        after = self.game_engine.get_current_state(agent_id)

        return {
            "time": {"week": new_week, "day": new_day},
            "events": {
                "time_advanced": [e.event_type for e in time_events],
                "autonomous": [e.event_type for e in generated_events],
            },
            "gm": gm_result,
            "judge": judge_result,
            "player": player_result,
            "state": _to_serializable(after),
        }

    def _run_autonomous_events(self, agent_id: str, new_day: int, new_week: int) -> List[Any]:
        state = self.game_engine.get_current_state(agent_id)
        generated_events = []
        for location_id in list(state.locations.keys()):
            generated_events.extend(AutonomousSimulation.process_daily_tick(state, location_id))

            if new_day == 0:
                generated_events.extend(AutonomousSimulation.process_weekly_costs(state, location_id))
                generated_events.extend(AutonomousSimulation.process_machine_wear(state, location_id))

        if new_day == 0:
            generated_events.extend(AutonomousSimulation.process_scandal_decay(state))
            if new_week > 0 and (new_week % 4) == 0:
                generated_events.extend(AutonomousSimulation.process_monthly_interest(state))
        
        return generated_events

    async def _run_gm_turn(self, agent_id: str) -> Any:
        if self.llm_dispatcher is None:
            return None
        
        state = self.game_engine.get_current_state(agent_id)
        try:
            gm_ctx = self.game_master.prepare_gm_context(state)
            return await self.llm_dispatcher.run_gm_turn(agent_id, gm_ctx)
        except Exception as exc:
            return {"error": str(exc)}

    async def _run_judge_turn(self, agent_id: str, time_event: Any, generated_events: List[Any]) -> Any:
        if self.llm_dispatcher is None:
            return None
        
        state = self.game_engine.get_current_state(agent_id)
        try:
            recent = [time_event, *generated_events]
            judge_ctx = self.judge.prepare_judge_context(state, recent)
            if hasattr(self.llm_dispatcher, 'run_judge_turn'):
                 return await self.llm_dispatcher.run_judge_turn(agent_id, judge_ctx)
            return None # run_judge_turn might not exist in dispatcher yet, optional
        except Exception as exc:
            return {"error": str(exc)}

    async def _run_player_turn(self, agent_id: str, time_event: Any, generated_events: List[Any]) -> Any:
        if self.llm_dispatcher is None:
            return None

        state = self.game_engine.get_current_state(agent_id)
        try:
            recent_for_player = [time_event, *generated_events]
            context_packet = _build_player_turn_packet(state, recent_for_player)
            context_msg = "TURN_PACKET: " + json.dumps(context_packet, default=str)
            return await self.llm_dispatcher.run_player_turn(
                agent_id,
                history_messages=[{"role": "user", "content": context_msg}],
            )
        except Exception as exc:
            return {"error": str(exc)}


def default_days_from_env() -> int:
    value = os.getenv("SIM_TICKS_PER_CALL") or os.getenv("SIM_DAYS_PER_CALL") or "1"
    try:
        parsed = int(value)
        return parsed if parsed > 0 else 1
    except Exception:
        return 1
