"""
Autonomous Simulation - Engine-driven autonomous events.
The Engine Tick generates events for non-player-driven mechanics:
- Daily revenue processing
- Machine wear and degradation
- Weekly costs
- Tax calculations
- Scandal decay
- NPC behavior

All autonomous logic generates detailed events that feed into the projection layer.
"""

from typing import List
from datetime import datetime
from core.events import (
    GameEvent,
    DailyRevenueProcessed,
    WeeklyFixedCostsBilled,
    WeeklyWagesBilled,
    MachineWearUpdated,
    MonthlyInterestAccrued,
    TaxLiabilityCalculated,
    ScandalMarkerDecayed,
)
from core.models import AgentState, MachineStatus
import uuid


class AutonomousSimulation:
    """
    Generates autonomous simulation events for the daily/weekly/monthly tick.
    
    This layer runs AFTER the TimeAdvanced event and generates all the
    outcomes of elapsed time (wear, revenue, costs, etc.).
    """
    
    @staticmethod
    def process_daily_tick(state: AgentState, location_id: str) -> List[GameEvent]:
        """
        Process a single day's worth of operations for a location.
        
        Calculates:
        - Revenue from loads processed
        - Variable costs (supplies, utilities)
        - Customer attraction based on pricing and scandals
        
        Args:
            state: Current agent state
            location_id: Location to process
            
        Returns:
            List of generated events
        """
        events = []
        
        if location_id not in state.locations:
            return events
        
        location = state.locations[location_id]
        
        # Simple model: base loads + adjustments
        # This would be much more complex in reality
        base_loads = 20  # Average daily loads
        
        # Adjust for scandals (negative multiplier)
        scandal_multiplier = 1.0
        for scandal in state.active_scandals:
            scandal_multiplier *= (1.0 - scandal.severity * 0.1)
        
        # Calculate loads and revenue
        loads_processed = int(base_loads * scandal_multiplier)
        revenue_per_load = sum(location.active_pricing.values()) / len(location.active_pricing)
        total_revenue = loads_processed * revenue_per_load
        
        # Calculate costs
        supplies_cost = loads_processed * 0.50  # $0.50 per load
        utility_cost = loads_processed * 0.25   # $0.25 per load
        
        # Emit daily revenue event
        if loads_processed > 0:
            revenue_event = DailyRevenueProcessed(
                event_id=str(uuid.uuid4()),
                event_type="DailyRevenueProcessed",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                location_id=location_id,
                loads_processed=loads_processed,
                revenue_generated=total_revenue,
                utility_cost=utility_cost,
                supplies_cost=supplies_cost,
            )
            events.append(revenue_event)
        
        return events
    
    @staticmethod
    def process_weekly_costs(state: AgentState, location_id: str) -> List[GameEvent]:
        """
        Process weekly fixed costs and wages.
        
        Args:
            state: Current agent state
            location_id: Location to process
            
        Returns:
            List of generated events
        """
        events = []
        
        if location_id not in state.locations:
            return events
        
        location = state.locations[location_id]
        
        # Rent
        rent_event = WeeklyFixedCostsBilled(
            event_id=str(uuid.uuid4()),
            event_type="WeeklyFixedCostsBilled",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            rent_cost=location.monthly_rent / 4.33,  # Weekly portion
            insurance_cost=150.0,  # Example
            other_fixed_costs=50.0,  # Utilities, maintenance, etc.
        )
        events.append(rent_event)
        
        # Wages
        if location.current_staff:
            total_wages = sum(s.hourly_rate * 40 for s in location.current_staff)  # 40hr/week
            wages_event = WeeklyWagesBilled(
                event_id=str(uuid.uuid4()),
                event_type="WeeklyWagesBilled",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                location_id=location_id,
                total_wages=total_wages,
                staff_count=len(location.current_staff),
            )
            events.append(wages_event)
        
        return events
    
    @staticmethod
    def process_machine_wear(state: AgentState, location_id: str) -> List[GameEvent]:
        """
        Process machine wear and degradation.
        
        Args:
            state: Current agent state
            location_id: Location to process
            
        Returns:
            List of generated events
        """
        events = []
        
        if location_id not in state.locations:
            return events
        
        location = state.locations[location_id]
        
        for machine_id, machine in location.equipment.items():
            if machine.status != MachineStatus.OPERATIONAL:
                continue
            
            # Simple wear model
            # Machines degrade 1-3% per week based on usage
            wear_rate = (machine.loads_processed_since_service / 1000.0) * 0.02
            wear_rate = min(wear_rate, 0.03)  # Cap at 3% per week
            
            new_condition = max(0, machine.condition - (100 * wear_rate))
            
            # Emit wear event
            wear_event = MachineWearUpdated(
                event_id=str(uuid.uuid4()),
                event_type="MachineWearUpdated",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                location_id=location_id,
                machine_id=machine_id,
                new_condition=new_condition,
                loads_processed_since_service=machine.loads_processed_since_service,
            )
            events.append(wear_event)
        
        return events
    
    @staticmethod
    def process_monthly_interest(state: AgentState) -> List[GameEvent]:
        """
        Process monthly interest accrual on debt and LOC.
        
        Args:
            state: Current agent state
            
        Returns:
            List of generated events
        """
        events = []
        
        # Simple interest calculation (would be more complex in reality)
        if state.total_debt_owed > 0 or state.line_of_credit_balance > 0:
            loan_interest = state.total_debt_owed * 0.05 / 12  # 5% annual
            loc_interest = state.line_of_credit_balance * 0.08 / 12  # 8% annual
            total_interest = loan_interest + loc_interest
            
            interest_event = MonthlyInterestAccrued(
                event_id=str(uuid.uuid4()),
                event_type="MonthlyInterestAccrued",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                loan_amount=state.total_debt_owed,
                loc_amount=state.line_of_credit_balance,
                total_interest=total_interest,
            )
            events.append(interest_event)
        
        return events
    
    @staticmethod
    def process_scandal_decay(state: AgentState) -> List[GameEvent]:
        """
        Process weekly decay of scandal durations.
        
        Args:
            state: Current agent state
            
        Returns:
            List of generated events
        """
        events = []
        
        for scandal in state.active_scandals:
            new_weeks = scandal.duration_weeks - 1
            
            decay_event = ScandalMarkerDecayed(
                event_id=str(uuid.uuid4()),
                event_type="ScandalMarkerDecayed",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                scandal_id=scandal.scandal_id,
                remaining_weeks=max(0, new_weeks),
            )
            events.append(decay_event)
        
        return events


__all__ = ["AutonomousSimulation"]
