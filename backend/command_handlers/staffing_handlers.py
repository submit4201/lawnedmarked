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
        
        Payload expected:
        {
            "location_id": str,
            "staff_name": str,
            "role": str,  # "Manager", "Attendant", "Cleaner"
            "hourly_rate": float,
            "hiring_bonus": float (optional)
        }
        """
        location_id = command.payload.get("location_id")
        staff_name = command.payload.get("staff_name")
        role = command.payload.get("role", "Attendant")
        hourly_rate = command.payload.get("hourly_rate")
        hiring_bonus = command.payload.get("hiring_bonus", 0.0)
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if not staff_name or len(staff_name) == 0:
            raise InvalidStateError("Staff name is required")
        
        if hourly_rate <= 0:
            raise InvalidStateError("Hourly rate must be positive")
        
        if hiring_bonus < 0:
            raise InvalidStateError("Hiring bonus cannot be negative")
        
        total_cost = hiring_bonus
        if state.cash_balance < total_cost:
            raise InsufficientFundsError(f"Insufficient funds for hiring bonus")
        
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
        
        # Emit: FundsTransferred if bonus is paid
        if hiring_bonus > 0:
            bonus_event = FundsTransferred(
                event_id=str(uuid.uuid4()),
                event_type="FundsTransferred",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                amount=hiring_bonus,
                transaction_type="EXPENSE",
                description=f"Hiring bonus for {staff_name}",
            )
            events.append(bonus_event)
        
        return events


class FireStaffHandler(CommandHandler):
    """Handler for FIRE_STAFF command."""
    
    def handle(self, state: AgentState, command: FireStaffCommand) -> List[GameEvent]:
        """
        Validate and process staff termination.
        
        Payload expected:
        {
            "location_id": str,
            "staff_id": str,
            "severance_cost": float (optional)
        }
        """
        location_id = command.payload.get("location_id")
        staff_id = command.payload.get("staff_id")
        severance_cost = command.payload.get("severance_cost", 0.0)
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        location = state.locations[location_id]
        staff_exists = any(s.staff_id == staff_id for s in location.current_staff)
        if not staff_exists:
            raise InvalidStateError(f"Staff member {staff_id} not found at {location_id}")
        
        if severance_cost < 0:
            raise InvalidStateError("Severance cost cannot be negative")
        
        if state.cash_balance < severance_cost:
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
            severance_cost=severance_cost,
        )
        events.append(fire_event)
        
        # Emit: FundsTransferred for severance
        if severance_cost > 0:
            severance_event = FundsTransferred(
                event_id=str(uuid.uuid4()),
                event_type="FundsTransferred",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                amount=severance_cost,
                transaction_type="EXPENSE",
                description=f"Severance payment for {staff_id}",
            )
            events.append(severance_event)
        
        return events


class AdjustStaffWageHandler(CommandHandler):
    """Handler for ADJUST_STAFF_WAGE command."""
    
    def handle(self, state: AgentState, command: AdjustStaffWageCommand) -> List[GameEvent]:
        """
        Validate and process wage adjustment.
        
        Payload expected:
        {
            "location_id": str,
            "staff_id": str,
            "new_hourly_rate": float
        }
        """
        location_id = command.payload.get("location_id")
        staff_id = command.payload.get("staff_id")
        new_hourly_rate = command.payload.get("new_hourly_rate")
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        location = state.locations[location_id]
        staff_member = None
        for s in location.current_staff:
            if s.staff_id == staff_id:
                staff_member = s
                break
        
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
        
        Payload expected:
        {
            "location_id": str,
            "benefit_type": str,  # "HealthInsurance", "PaidTimeOff", "Tuition"
            "annual_cost_per_employee": float,
            "employee_count": int
        }
        """
        location_id = command.payload.get("location_id")
        benefit_type = command.payload.get("benefit_type")
        annual_cost_per_employee = command.payload.get("annual_cost_per_employee")
        employee_count = command.payload.get("employee_count")
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if not benefit_type:
            raise InvalidStateError("Benefit type is required")
        
        if annual_cost_per_employee <= 0:
            raise InvalidStateError("Annual cost must be positive")
        
        if employee_count <= 0:
            raise InvalidStateError("Employee count must be positive")
        
        total_cost = annual_cost_per_employee * employee_count
        if state.cash_balance < total_cost:
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
            annual_cost_per_employee=annual_cost_per_employee,
            employee_count=employee_count,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=total_cost,
            transaction_type="EXPENSE",
            description=f"Benefit implementation: {benefit_type} at {location_id}",
        )
        
        return [benefit_event, funds_event]


STAFFING_HANDLERS = {
    "HIRE_STAFF": HireStaffHandler(),
    "FIRE_STAFF": FireStaffHandler(),
    "ADJUST_STAFF_WAGE": AdjustStaffWageHandler(),
    "PROVIDE_BENEFITS": ProvideBenefitsHandler(),
}

__all__ = ["STAFFING_HANDLERS"]
