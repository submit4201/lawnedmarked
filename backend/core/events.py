"""
Event Sourcing infrastructure aggregator.
Events are immutable facts and are organized by domain modules.
This file exposes the base `GameEvent` and re-exports domain events.
"""

from dataclasses import dataclass, field
from typing import Any, Dict
from datetime import datetime
from abc import ABC


@dataclass(frozen=True)
class GameEvent(ABC):
    """
    Base class for all immutable game events.
    Every event is a fact that happened and cannot be changed.
    """
    event_id: str
    agent_id: str
    timestamp: datetime
    week: int
    event_type: str = field(default="GameEvent")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "week": self.week
        }
from .events_time import *
from .events_financial import *
from .events_operational import *
from .events_staffing import *
from .events_social_regulatory import *
from .events_vendor import *
from .events_competition import *









