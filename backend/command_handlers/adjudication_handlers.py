"""Adjudication command handlers.

These handlers are used by non-player LLM agents (GM/Judge) to inject facts
into the world using the standard Command → Event → State pipeline.
"""

from __future__ import annotations

from dataclasses import is_dataclass
from datetime import datetime
from typing import Any, Dict, List, Type
import uuid

from core.commands import Command, CommandHandler, InvalidStateError
from core.events import GameEvent
from core.models import AgentState


def _discover_event_types() -> Dict[str, Type[GameEvent]]:
    """Build a mapping from event_type/classname to event class."""
    from core import events as events_module

    mapping: Dict[str, Type[GameEvent]] = {}
    for _, obj in vars(events_module).items():
        if not isinstance(obj, type):
            continue
        if not issubclass(obj, GameEvent):
            continue
        if obj is GameEvent:
            continue
        if not is_dataclass(obj):
            continue

        # Primary key: declared event_type default (if present) else class name.
        try:
            default_event_type = getattr(obj, "event_type", None)
        except Exception:
            default_event_type = None

        if isinstance(default_event_type, str) and default_event_type:
            mapping.setdefault(default_event_type, obj)
        mapping.setdefault(obj.__name__, obj)

    return mapping


_EVENT_TYPES = _discover_event_types()


# Conservative allow-lists: GM can inject world/narrative; Judge can inject consequences.
_GM_ALLOWED = {
    "VendorPriceFluctuated",
    "CustomerReviewSubmitted",
    "DeliveryDisruption",
    "DilemmaTriggered",
    "CompetitorPriceChanged",
    "CompetitorExitedMarket",
    "VendorNegotiationResult",
    "VendorTermsUpdated",
}

_JUDGE_ALLOWED = {
    "ScandalStarted",
    "RegulatoryFinding",
    "RegulatoryStatusUpdated",
    "InvestigationStarted",
    "InvestigationStageAdvanced",
}


class InjectWorldEventHandler(CommandHandler):
    """Validate and inject a single allowed event type."""

    def handle(self, state: AgentState, command: Command) -> List[GameEvent]:
        # ! Use getattr for typed payloads
        source_role = str(getattr(command.payload, "source_role", "")).upper()
        event_type = str(getattr(command.payload, "event_type", "")).strip()
        event_fields: Dict[str, Any] = getattr(command.payload, "event_fields", {}) or {}

        if source_role not in {"GM", "JUDGE"}:
            raise InvalidStateError("source_role must be 'GM' or 'JUDGE'")

        if not event_type:
            raise InvalidStateError("event_type is required")

        allowed = _GM_ALLOWED if source_role == "GM" else _JUDGE_ALLOWED
        if event_type not in allowed:
            raise InvalidStateError(f"event_type '{event_type}' is not allowed for {source_role}")

        if event_type not in _EVENT_TYPES:
            raise InvalidStateError(f"Unknown event_type '{event_type}'")

        event_cls = _EVENT_TYPES[event_type]

        try:
            event = event_cls(
                event_id=str(uuid.uuid4()),
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                **event_fields,
            )
        except TypeError as exc:
            raise InvalidStateError(f"Invalid event_fields for {event_type}: {exc}")

        return [event]


ADJUDICATION_HANDLERS = {
    "INJECT_WORLD_EVENT": InjectWorldEventHandler(),
}


__all__ = ["ADJUDICATION_HANDLERS", "InjectWorldEventHandler"]
