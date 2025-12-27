"""
Staffing command handlers for employee management and labor costs.
"""

from typing import List
from core.commands import (
    CommandHandler,
    Command,
    HireStaffCommand,
    FireStaffCommand,
    AdjustStaffWageCommand,
    ProvideBenefitsCommand,
    InsufficientFundsError,
    InvalidStateError,
    LocationNotFoundError,
)
from core.events import (
    GameEvent,
    StaffHired,
    StaffFired,
    WageAdjusted,
    BenefitImplemented,
    FundsTransferred,
)
from core.models import AgentState, StaffMember
from datetime import datetime
import uuid


class HireStaffHandler(CommandHandler):
    """Handler for HIRE_STAFF command."""
    
    def handle(self, state: AgentState, command: HireStaffCommand) -> List[GameEvent]:
        """
        Validate and process staff hiring.
        """
        payload: HireStaffPayload = command.payload
        location_id = payload.location_id
        staff_name = payload.name
        role = payload.role
        hourly_rate = payload.salary_per_hour
        
        # Validation
        if not location_id:
            raise InvalidStateError("Location ID is required for hiring staff")

        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if not staff_name or len(staff_name) == 0:
            raise InvalidStateError("Staff name is required")
        
        if hourly_rate is None or hourly_rate <= 0:
            raise InvalidStateError("Salary per hour must be positive")
        
        staff_id = str(uuid.uuid4())
        events = []
        
        # Emit: StaffHired
        hire_event = StaffHired(
            event_id=str(uuid.uuid4()),
            event_type="StaffHired",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            staff_id=staff_id,
            staff_name=staff_name,
            role=role,
            hourly_rate=hourly_rate,
        )
        events.append(hire_event)
        
        return events


class FireStaffHandler(CommandHandler):
    """Handler for FIRE_STAFF command."""
    
    def handle(self, state: AgentState, command: FireStaffCommand) -> List[GameEvent]:
        """
        Validate and process staff termination.
        """
        payload: FireStaffPayload = command.payload
        location_id = payload.location_id
        staff_id = payload.staff_id
        severance_pay = payload.severance_pay
        
        # Validation
        if not location_id:
            raise InvalidStateError("Location ID is required for firing staff")

        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if not staff_id:
            raise InvalidStateError("Staff ID is required")
            
        location = state.locations[location_id]
        staff_member = next((s for s in location.current_staff if s.staff_id == staff_id), None)
        
        if not staff_member:
            raise InvalidStateError(f"Staff member {staff_id} not found at location {location_id}")
        
        if severance_pay < 0:
            raise InvalidStateError("Severance pay cannot be negative")
        
        if state.cash_balance < severance_pay:
            raise InsufficientFundsError(f"Insufficient funds for severance")
        
        events = []
        
        # Emit: StaffFired
        fire_event = StaffFired(
            event_id=str(uuid.uuid4()),
            event_type="StaffFired",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            staff_id=staff_id,
            severance_cost=severance_pay,
        )
        events.append(fire_event)
        
        # Emit: FundsTransferred for severance
        if severance_pay > 0:
            severance_event = FundsTransferred(
                event_id=str(uuid.uuid4()),
                event_type="FundsTransferred",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                amount=-severance_pay,
                transaction_type="EXPENSE",
                description=f"Severance pay for staff {staff_id}",
            )
            events.append(severance_event)
        
        return events


class AdjustStaffWageHandler(CommandHandler):
    """Handler for ADJUST_STAFF_WAGE command."""
    
    def handle(self, state: AgentState, command: AdjustStaffWageCommand) -> List[GameEvent]:
        """
        Validate and process wage adjustment.
        """
        payload: AdjustStaffWagePayload = command.payload
        location_id = payload.location_id
        staff_id = payload.staff_id
        new_hourly_rate = payload.new_hourly_rate
        
        # Validation
        if not location_id:
            raise InvalidStateError("Location ID is required for wage adjustment")

        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        location = state.locations[location_id]
        staff_member = next((s for s in location.current_staff if s.staff_id == staff_id), None)
        
        if staff_member is None:
            raise InvalidStateError(f"Staff member {staff_id} not found")
        
        if new_hourly_rate <= 0:
            raise InvalidStateError("Hourly rate must be positive")
        
        # Emit: WageAdjusted
        wage_event = WageAdjusted(
            event_id=str(uuid.uuid4()),
            event_type="WageAdjusted",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            staff_id=staff_id,
            old_rate=staff_member.hourly_rate,
            new_rate=new_hourly_rate,
        )
        
        return [wage_event]


class ProvideBenefitsHandler(CommandHandler):
    """Handler for PROVIDE_BENEFITS command."""
    
    def handle(self, state: AgentState, command: ProvideBenefitsCommand) -> List[GameEvent]:
        """
        Validate and process benefit implementation.
        """
        payload: ProvideBenefitsPayload = command.payload
        location_id = payload.location_id
        staff_id = payload.staff_id
        benefit_type = payload.benefit_type
        monthly_cost = payload.monthly_cost
        
        # Validation
        if not location_id:
            raise InvalidStateError("Location ID is required for providing benefits")

        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if not staff_id:
            raise InvalidStateError("Staff ID is required")
            
        location = state.locations[location_id]
        staff_member = next((s for s in location.current_staff if s.staff_id == staff_id), None)
        
        if not staff_member:
            raise InvalidStateError(f"Staff member {staff_id} not found at location {location_id}")
            
        if monthly_cost < 0:
            raise InvalidStateError("Benefit cost cannot be negative")
        
        if state.cash_balance < monthly_cost:
            raise InsufficientFundsError(f"Insufficient funds for benefit program")
        
        # Emit: BenefitImplemented + FundsTransferred
        benefit_event = BenefitImplemented(
            event_id=str(uuid.uuid4()),
            event_type="BenefitImplemented",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            benefit_type=benefit_type,
            annual_cost_per_employee=monthly_cost * 12, 
            employee_count=1,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=-monthly_cost,
            transaction_type="EXPENSE",
            description=f"Benefit implementation: {benefit_type} for staff {staff_id}",
        )
        
        return [benefit_event, funds_event]


STAFFING_HANDLERS = {
    "HIRE_STAFF": HireStaffHandler(),
    "FIRE_STAFF": FireStaffHandler(),
    "ADJUST_STAFF_WAGE": AdjustStaffWageHandler(),
    "PROVIDE_BENEFITS": ProvideBenefitsHandler(),
}

__all__ = ["STAFFING_HANDLERS"]
