from dataclasses import dataclass, field
from typing import Any, Dict, List
from core.events import GameEvent

@dataclass(frozen=True)
class AllianceFormed(GameEvent):
    alliance_id: str = ""
    partner_agent_id: str = ""
    alliance_type: str = ""
    duration_weeks: int = 0
    penalties_on_breach: float = 0.0
    event_type: str = field(default="AllianceFormed")

@dataclass(frozen=True)
class AllianceBreached(GameEvent):
    alliance_id: str = ""
    penalty_amount: float = 0.0
    event_type: str = field(default="AllianceBreached")

@dataclass(frozen=True)
class AgentAcquired(GameEvent):
    target_agent_id: str = ""
    acquisition_cost: float = 0.0
    assets_transferred: Dict[str, Any] = field(default_factory=dict)
    event_type: str = field(default="AgentAcquired")

@dataclass(frozen=True)
class CompetitorPriceChanged(GameEvent):
    competitor_id: str = ""
    location_id: str = ""
    service_type: str = ""
    new_price: float = 0.0
    event_type: str = field(default="CompetitorPriceChanged")

@dataclass(frozen=True)
class CompetitorExitedMarket(GameEvent):
    competitor_id: str = ""
    reason: str = ""
    event_type: str = field(default="CompetitorExitedMarket")

@dataclass(frozen=True)
class CommunicationIntercepted(GameEvent):
    parties_involved: List[str] = field(default_factory=list)
    communication_type: str = ""
    event_type: str = field(default="CommunicationIntercepted")
