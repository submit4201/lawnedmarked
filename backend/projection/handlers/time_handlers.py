"""
Time-based projection handlers (weekly/daily cycles).
"""

from copy import deepcopy
from core.models import AgentState
from core.events import (
    TimeAdvanced,
    DailyRevenueProcessed,
    WeeklyFixedCostsBilled,
    WeeklyWagesBilled,
)


def handle_time_advanced(state: AgentState, event: TimeAdvanced) -> AgentState:
    """Update the week counter when time advances."""
    new_state = deepcopy(state)
    new_state.current_day = event.day
    return new_state


def handle_daily_revenue_processed(state: AgentState, event: DailyRevenueProcessed) -> AgentState:
    """Apply daily revenue, variable costs, and basic inventory consumption."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        location.accumulated_revenue_week += event.revenue_generated
        location.accumulated_cogs_week += event.utility_cost + event.supplies_cost
        # Mechanical inventory consumption model
        location.inventory_detergent = max(0, location.inventory_detergent - event.loads_processed)
        location.inventory_softener = max(0, location.inventory_softener - event.loads_processed // 2)
    new_state.cash_balance += event.revenue_generated
    new_state.cash_balance -= event.utility_cost + event.supplies_cost
    return new_state


def handle_weekly_fixed_costs_billed(state: AgentState, event: WeeklyFixedCostsBilled) -> AgentState:
    """Apply weekly fixed costs (rent, insurance, other)."""
    new_state = deepcopy(state)
    total_cost = event.rent_cost + event.insurance_cost + event.other_fixed_costs
    new_state.cash_balance -= total_cost
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        location.accumulated_cogs_week += total_cost
    return new_state


def handle_weekly_wages_billed(state: AgentState, event: WeeklyWagesBilled) -> AgentState:
    """Apply weekly wage expenses to cash and location COGS."""
    new_state = deepcopy(state)
    new_state.cash_balance -= event.total_wages
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        location.accumulated_cogs_week += event.total_wages
    return new_state


TIME_EVENT_HANDLERS = {
    "TimeAdvanced": handle_time_advanced,
    "DailyRevenueProcessed": handle_daily_revenue_processed,
    "WeeklyFixedCostsBilled": handle_weekly_fixed_costs_billed,
    "WeeklyWagesBilled": handle_weekly_wages_billed,
}

__all__ = [
    "TIME_EVENT_HANDLERS",
    "handle_time_advanced",
    "handle_daily_revenue_processed",
    "handle_weekly_fixed_costs_billed",
    "handle_weekly_wages_billed",
]
