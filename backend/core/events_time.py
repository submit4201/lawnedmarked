from dataclasses import dataclass, field
from core.events import GameEvent

@dataclass(frozen=True)
class TimeAdvanced(GameEvent):
    week: int = 0
    day: int = 0
    event_type: str = field(default="TimeAdvanced")

@dataclass(frozen=True)
class DailyRevenueProcessed(GameEvent):
    location_id: str = ""
    loads_processed: int = 0
    revenue_generated: float = 0.0
    utility_cost: float = 0.0
    supplies_cost: float = 0.0
    event_type: str = field(default="DailyRevenueProcessed")

@dataclass(frozen=True)
class WeeklyFixedCostsBilled(GameEvent):
    location_id: str = ""
    rent_cost: float = 0.0
    insurance_cost: float = 0.0
    other_fixed_costs: float = 0.0
    event_type: str = field(default="WeeklyFixedCostsBilled")

@dataclass(frozen=True)
class WeeklyWagesBilled(GameEvent):
    location_id: str = ""
    total_wages: float = 0.0
    staff_count: int = 0
    event_type: str = field(default="WeeklyWagesBilled")

@dataclass(frozen=True)
class MonthlyInterestAccrued(GameEvent):
    loan_amount: float = 0.0
    loc_amount: float = 0.0
    total_interest: float = 0.0
    event_type: str = field(default="MonthlyInterestAccrued")

@dataclass(frozen=True)
class MachineWearUpdated(GameEvent):
    location_id: str = ""
    machine_id: str = ""
    new_condition: float = 0.0
    loads_processed_since_service: int = 0
    event_type: str = field(default="MachineWearUpdated")

@dataclass(frozen=True)
class MachineBrokenDown(GameEvent):
    location_id: str = ""
    machine_id: str = ""
    reason: str = ""
    event_type: str = field(default="MachineBrokenDown")
