from dataclasses import dataclass, field
from core.events import GameEvent

@dataclass(frozen=True)
class StaffHired(GameEvent):
    location_id: str = ""
    staff_id: str = ""
    staff_name: str = ""
    role: str = ""
    hourly_rate: float = 0.0
    event_type: str = field(default="StaffHired")

@dataclass(frozen=True)
class StaffFired(GameEvent):
    location_id: str = ""
    staff_id: str = ""
    reason: str = ""
    severance_cost: float = 0.0
    event_type: str = field(default="StaffFired")

@dataclass(frozen=True)
class StaffQuit(GameEvent):
    location_id: str = ""
    staff_id: str = ""
    reason: str = ""
    event_type: str = field(default="StaffQuit")

@dataclass(frozen=True)
class WageAdjusted(GameEvent):
    location_id: str = ""
    staff_id: str = ""
    old_rate: float = 0.0
    new_rate: float = 0.0
    event_type: str = field(default="WageAdjusted")

@dataclass(frozen=True)
class BenefitImplemented(GameEvent):
    location_id: str = ""
    benefit_type: str = ""
    annual_cost_per_employee: float = 0.0
    employee_count: int = 0
    event_type: str = field(default="BenefitImplemented")


__all__ = [
    "StaffHired",
    "StaffFired",
    "StaffQuit",
    "WageAdjusted",
    "BenefitImplemented",
]