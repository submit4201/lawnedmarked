"""
Staffing projection handlers.
"""

from copy import deepcopy
from core.models import AgentState, StaffMember
from core.events import StaffHired, StaffFired, WageAdjusted, BenefitImplemented, StaffQuit


def handle_staff_hired(state: AgentState, event: StaffHired) -> AgentState:
    """Add a new staff member to a location."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        staff = StaffMember(
            staff_id=event.staff_id,
            staff_name=event.staff_name,
            role=event.role,
            hourly_rate=event.hourly_rate,
            hired_week=state.current_week,
        )
        location.current_staff.append(staff)
    return new_state


def handle_staff_fired(state: AgentState, event: StaffFired) -> AgentState:
    """Remove a staff member from a location."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        location.current_staff = [s for s in location.current_staff if s.staff_id != event.staff_id]
    return new_state


def handle_wage_adjusted(state: AgentState, event: WageAdjusted) -> AgentState:
    """Update a staff member's hourly rate."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        for staff in location.current_staff:
            if staff.staff_id == event.staff_id:
                staff.hourly_rate = event.new_rate
                break
    return new_state


def handle_benefit_implemented(state: AgentState, event: BenefitImplemented) -> AgentState:
    """Record benefit implementation (cost tracked via FundsTransferred)."""
    return deepcopy(state)


def handle_staff_quit(state: AgentState, event: StaffQuit) -> AgentState:
    """Remove a staff member who quits."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        location.current_staff = [s for s in location.current_staff if s.staff_id != event.staff_id]
    return new_state


STAFFING_EVENT_HANDLERS = {
    "StaffHired": handle_staff_hired,
    "StaffFired": handle_staff_fired,
    "WageAdjusted": handle_wage_adjusted,
    "BenefitImplemented": handle_benefit_implemented,
    "StaffQuit": handle_staff_quit,
}

__all__ = [
    "STAFFING_EVENT_HANDLERS",
    "handle_staff_hired",
    "handle_staff_fired",
    "handle_wage_adjusted",
    "handle_benefit_implemented",
    "handle_staff_quit",
]
