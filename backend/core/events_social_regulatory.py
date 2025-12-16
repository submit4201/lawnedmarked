from dataclasses import dataclass, field
from typing import Any, Dict, List
from core.events import GameEvent

@dataclass(frozen=True)
class SocialScoreAdjusted(GameEvent):
    adjustment: float = 0.0
    reason: str = ""
    event_type: str = field(default="SocialScoreAdjusted")

@dataclass(frozen=True)
class ScandalStarted(GameEvent):
    scandal_id: str = ""
    description: str = ""
    severity: float = 0.0
    duration_weeks: int = 0
    event_type: str = field(default="ScandalStarted")

@dataclass(frozen=True)
class ScandalMarkerDecayed(GameEvent):
    scandal_id: str = ""
    remaining_weeks: int = 0
    event_type: str = field(default="ScandalMarkerDecayed")

@dataclass(frozen=True)
class RegulatoryFinding(GameEvent):
    fine_id: str = ""
    description: str = ""
    fine_amount: float = 0.0
    due_date: int = 0
    event_type: str = field(default="RegulatoryFinding")

@dataclass(frozen=True)
class RegulatoryStatusUpdated(GameEvent):
    new_status: str = ""
    reason: str = ""
    event_type: str = field(default="RegulatoryStatusUpdated")

@dataclass(frozen=True)
class DilemmaTriggered(GameEvent):
    dilemma_id: str = ""
    description: str = ""
    options: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    event_type: str = field(default="DilemmaTriggered")

@dataclass(frozen=True)
class DilemmaResolved(GameEvent):
    dilemma_id: str = ""
    chosen_option: str = ""
    event_type: str = field(default="DilemmaResolved")

@dataclass(frozen=True)
class InvestigationStarted(GameEvent):
    investigation_id: str = ""
    reason: str = ""
    severity: str = ""
    event_type: str = field(default="InvestigationStarted")

@dataclass(frozen=True)
class InvestigationStageAdvanced(GameEvent):
    investigation_id: str = ""
    current_stage: str = ""
    event_type: str = field(default="InvestigationStageAdvanced")

@dataclass(frozen=True)
class CustomerReviewSubmitted(GameEvent):
    location_id: str = ""
    rating: float = 0.0
    review_text: str = ""
    event_type: str = field(default="CustomerReviewSubmitted")

@dataclass(frozen=True)
class LoyaltyMemberRegistered(GameEvent):
    location_id: str = ""
    member_count: int = 0
    program_year: int = 0
    event_type: str = field(default="LoyaltyMemberRegistered")

@dataclass(frozen=True)
class EndOfTurnNotesSaved(GameEvent):
    notes: str = ""
    event_type: str = field(default="EndOfTurnNotesSaved")

@dataclass(frozen=True)
class AuditSnapshotRecorded(GameEvent):
    entries_count: int = 0
    last_event_type: str = ""
    event_type: str = field(default="AuditSnapshotRecorded")


__all__ = [
    "SocialScoreAdjusted",
    "ScandalStarted",
    "ScandalMarkerDecayed",
    "RegulatoryFinding",
    "RegulatoryStatusUpdated",
    "DilemmaTriggered",
    "DilemmaResolved",
    "InvestigationStarted",
    "InvestigationStageAdvanced",
    "CustomerReviewSubmitted",
    "LoyaltyMemberRegistered",
    "EndOfTurnNotesSaved",
    "AuditSnapshotRecorded",
]