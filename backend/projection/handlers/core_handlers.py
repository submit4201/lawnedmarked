"""
Projection handlers for all game events.
These handlers MUST be pure functions with no side effects.
They read state immutably and return updated state.

Organized by domain:
- Financial handlers: FundsTransferred, LoanTaken, DebtPaymentProcessed, MarketingBoostApplied
- Operational handlers: EquipmentPurchased, EquipmentSold, EquipmentRepaired, SuppliesAcquired, NewLocationOpened, MachineStatusChanged
- Staffing handlers: StaffHired, StaffFired, WageAdjusted, BenefitImplemented
- Social handlers: SocialScoreAdjusted, DilemmaResolved, LoyaltyMemberRegistered
- Vendor handlers: VendorNegotiationResult, ExclusiveContractSigned, VendorTermsUpdated
- Regulatory handlers: RegulatoryStatusUpdated, RegulatoryFinding, ScandalStarted, ScandalMarkerDecayed
- Time handlers: TimeAdvanced
"""

from copy import deepcopy
from core.models import (
    AgentState,
    LocationState,
    MachineState,
    ScandalMarker,
    Fine,
    StaffMember,
    Alliance,
    MachineStatus,
    MachineType,
)
from core.events import (
    TimeAdvanced,
    FundsTransferred,
    LoanTaken,
    DebtPaymentProcessed,
    MarketingBoostApplied,
    PriceSet,
    SocialScoreAdjusted,
    RegulatoryStatusUpdated,
    ScandalStarted,
    ScandalMarkerDecayed,
    RegulatoryFinding,
    TaxLiabilityCalculated,
    EquipmentPurchased,
    EquipmentSold,
    EquipmentRepaired,
    SuppliesAcquired,
    NewLocationOpened,
    MachineStatusChanged,
    StaffHired,
    StaffFired,
    WageAdjusted,
    BenefitImplemented,
    DilemmaResolved,
    LoyaltyMemberRegistered,
    VendorNegotiationResult,
    ExclusiveContractSigned,
    VendorTermsUpdated,
    AllianceFormed,
)


# =============================================================================
# TIME HANDLERS
# =============================================================================

def handle_time_advanced(state: AgentState, event: TimeAdvanced) -> AgentState:
    """Update the week and day counters."""
    new_state = deepcopy(state)
    new_state.current_week = event.week
    return new_state


# =============================================================================
# FINANCIAL HANDLERS
# =============================================================================

def handle_funds_transferred(state: AgentState, event: FundsTransferred) -> AgentState:
    """
    Core accounting handler - adjusts cash_balance.
    This is the fundamental fact of money movement.
    """
    new_state = deepcopy(state)
    
    # Determine debit/credit based on transaction type
    if event.transaction_type in ["REVENUE", "LOAN", "REFUND"]:
        new_state.cash_balance += event.amount
    elif event.transaction_type in ["EXPENSE", "PAYMENT"]:
        new_state.cash_balance -= event.amount
    else:
        raise ValueError(f"Unknown transaction type: {event.transaction_type}")
    
    return new_state


def handle_loan_taken(state: AgentState, event: LoanTaken) -> AgentState:
    """Record a new loan and increase total_debt_owed."""
    new_state = deepcopy(state)
    new_state.total_debt_owed += event.principal
    return new_state


def handle_debt_payment_processed(state: AgentState, event: DebtPaymentProcessed) -> AgentState:
    """Reduce total_debt_owed by the principal reduction amount."""
    new_state = deepcopy(state)
    new_state.total_debt_owed -= event.principal_reduction
    return new_state


def handle_marketing_boost_applied(state: AgentState, event: MarketingBoostApplied) -> AgentState:
    """Apply marketing boost to social score."""
    new_state = deepcopy(state)
    new_state.social_score += event.social_boost
    new_state.social_score = max(0.0, min(100.0, new_state.social_score))
    return new_state


def handle_tax_liability_calculated(state: AgentState, event: TaxLiabilityCalculated) -> AgentState:
    """Add tax liability to current_tax_liability."""
    new_state = deepcopy(state)
    new_state.current_tax_liability += event.tax_amount
    return new_state


# =============================================================================
# OPERATIONAL HANDLERS
# =============================================================================

def handle_price_set(state: AgentState, event: PriceSet) -> AgentState:
    """Update the pricing for a service at a location."""
    new_state = deepcopy(state)
    
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        location.active_pricing[event.service_type] = event.new_price
    
    return new_state


def handle_equipment_purchased(state: AgentState, event: EquipmentPurchased) -> AgentState:
    """Add a new machine to a location."""
    new_state = deepcopy(state)
    
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        machine = MachineState(
            machine_id=event.machine_id,
            type=MachineType(event.machine_type) if isinstance(event.machine_type, str) else event.machine_type,
            condition=100.0,  # New machine is in perfect condition
            status=MachineStatus.OPERATIONAL,
            last_maintenance_week=state.current_week,
            loads_processed_since_service=0,
        )
        location.equipment[event.machine_id] = machine
    
    return new_state


def handle_equipment_sold(state: AgentState, event: EquipmentSold) -> AgentState:
    """Remove a machine from a location."""
    new_state = deepcopy(state)
    
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        if event.machine_id in location.equipment:
            del location.equipment[event.machine_id]
    
    return new_state


def handle_equipment_repaired(state: AgentState, event: EquipmentRepaired) -> AgentState:
    """Repair a machine, restoring its condition."""
    new_state = deepcopy(state)
    
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        if event.machine_id in location.equipment:
            machine = location.equipment[event.machine_id]
            machine.condition = 100.0  # Restore to full condition
            machine.status = MachineStatus.OPERATIONAL
            machine.last_maintenance_week = state.current_week
            machine.loads_processed_since_service = 0
    
    return new_state


def handle_supplies_acquired(state: AgentState, event: SuppliesAcquired) -> AgentState:
    """Add supplies to inventory at a location."""
    new_state = deepcopy(state)
    
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        if event.supply_type == "detergent":
            location.inventory_detergent += event.quantity
        elif event.supply_type == "softener":
            location.inventory_softener += event.quantity
    
    return new_state


def handle_new_location_opened(state: AgentState, event: NewLocationOpened) -> AgentState:
    """Create a new location."""
    new_state = deepcopy(state)
    
    new_location = LocationState(
        location_id=event.location_id,
        zone=event.zone,
        monthly_rent=event.monthly_rent,
    )
    new_state.locations[event.location_id] = new_location
    
    return new_state


def handle_machine_status_changed(state: AgentState, event: MachineStatusChanged) -> AgentState:
    """Update machine status (OPERATIONAL, BROKEN, IN_REPAIR)."""
    new_state = deepcopy(state)
    
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        if event.machine_id in location.equipment:
            machine = location.equipment[event.machine_id]
            machine.status = event.new_status
    
    return new_state


# =============================================================================
# STAFFING HANDLERS
# =============================================================================

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
        location.current_staff = [
            s for s in location.current_staff if s.staff_id != event.staff_id
        ]
    
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
    """Record benefit implementation (increases staff satisfaction, cost impact via FundsTransferred)."""
    # This is primarily recorded via the FundsTransferred event
    # The projection just passes through without additional state changes
    new_state = deepcopy(state)
    return new_state


# =============================================================================
# SOCIAL & REGULATORY HANDLERS
# =============================================================================

def handle_social_score_adjusted(state: AgentState, event: SocialScoreAdjusted) -> AgentState:
    """Update the social score."""
    new_state = deepcopy(state)
    new_state.social_score += event.adjustment
    # Clamp between 0 and 100
    new_state.social_score = max(0.0, min(100.0, new_state.social_score))
    return new_state


def handle_regulatory_status_updated(state: AgentState, event: RegulatoryStatusUpdated) -> AgentState:
    """Update the regulatory status."""
    new_state = deepcopy(state)
    new_state.regulatory_status = event.new_status
    return new_state


def handle_scandal_started(state: AgentState, event: ScandalStarted) -> AgentState:
    """Add a new scandal marker to active_scandals."""
    new_state = deepcopy(state)
    scandal = ScandalMarker(
        scandal_id=event.scandal_id,
        description=event.description,
        severity=event.severity,
        duration_weeks=event.duration_weeks,
        decay_rate=0.1,  # Default decay rate per week
        start_week=state.current_week,
    )
    new_state.active_scandals.append(scandal)
    return new_state


def handle_scandal_marker_decayed(state: AgentState, event: ScandalMarkerDecayed) -> AgentState:
    """Reduce a scandal's remaining duration."""
    new_state = deepcopy(state)
    
    # Find the scandal and update its duration
    for scandal in new_state.active_scandals:
        if scandal.scandal_id == event.scandal_id:
            scandal.duration_weeks = event.remaining_weeks
            if scandal.duration_weeks <= 0:
                # Remove if duration expires
                new_state.active_scandals.remove(scandal)
            break
    
    return new_state


def handle_regulatory_finding(state: AgentState, event: RegulatoryFinding) -> AgentState:
    """Add a pending fine to the agent."""
    new_state = deepcopy(state)
    fine = Fine(
        fine_id=event.fine_id,
        description=event.description,
        amount=event.fine_amount,
        issued_week=state.current_week,
        due_date=event.due_date,
    )
    new_state.pending_fines.append(fine)
    return new_state


def handle_dilemma_resolved(state: AgentState, event: DilemmaResolved) -> AgentState:
    """Record the player's ethical dilemma choice."""
    # This is primarily tracked via SocialScoreAdjusted event
    new_state = deepcopy(state)
    return new_state


def handle_loyalty_member_registered(state: AgentState, event: LoyaltyMemberRegistered) -> AgentState:
    """Register loyalty program members."""
    new_state = deepcopy(state)
    new_state.customer_loyalty_members += event.member_count
    return new_state


# =============================================================================
# VENDOR HANDLERS
# =============================================================================

def handle_vendor_negotiation_result(state: AgentState, event: VendorNegotiationResult) -> AgentState:
    """Update vendor relationship based on negotiation outcome."""
    new_state = deepcopy(state)
    
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        vendor_rel = location.vendor_relationships.get(event.vendor_id)
        
        if vendor_rel is None:
            # Create new relationship if doesn't exist
            vendor_rel = VendorRelationship(
                vendor_id=event.vendor_id,
                tier=1,
                weeks_at_tier=0,
                payment_history=[],
                is_exclusive_contract=False,
            )
            location.vendor_relationships[event.vendor_id] = vendor_rel
        
        # Success improves the relationship
        if event.negotiation_succeeded:
            vendor_rel.weeks_at_tier += 1
    
    return new_state


def handle_exclusive_contract_signed(state: AgentState, event: ExclusiveContractSigned) -> AgentState:
    """Mark vendor relationship as exclusive."""
    new_state = deepcopy(state)
    
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        vendor_rel = location.vendor_relationships.get(event.vendor_id)
        
        if vendor_rel is None:
            vendor_rel = VendorRelationship(
                vendor_id=event.vendor_id,
                tier=1,
                weeks_at_tier=0,
                payment_history=[],
                is_exclusive_contract=True,
            )
        else:
            vendor_rel.is_exclusive_contract = True
        
        location.vendor_relationships[event.vendor_id] = vendor_rel
    
    return new_state


def handle_vendor_terms_updated(state: AgentState, event: VendorTermsUpdated) -> AgentState:
    """Update vendor relationship terms."""
    new_state = deepcopy(state)
    
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        vendor_rel = location.vendor_relationships.get(event.vendor_id)
        
        if vendor_rel:
            # Update terms based on change description
            if "terminated" in event.change_description.lower():
                vendor_rel.is_exclusive_contract = False
    
    return new_state


# =============================================================================
# COMPETITION HANDLERS
# =============================================================================

def handle_alliance_formed(state: AgentState, event: AllianceFormed) -> AgentState:
    """Record a new alliance."""
    new_state = deepcopy(state)
    
    alliance = Alliance(
        alliance_id=event.alliance_id,
        partner_agent_id=event.partner_agent_id,
        alliance_type=event.alliance_type,
        duration_weeks=event.duration_weeks,
        start_week=state.current_week,
    )
    new_state.active_alliances.append(alliance)
    
    return new_state


# =============================================================================
# PROJECTION HANDLER REGISTRY
# =============================================================================

CORE_EVENT_HANDLERS = {
    # Time
    "TimeAdvanced": handle_time_advanced,
    
    # Financial
    "FundsTransferred": handle_funds_transferred,
    "LoanTaken": handle_loan_taken,
    "DebtPaymentProcessed": handle_debt_payment_processed,
    "MarketingBoostApplied": handle_marketing_boost_applied,
    "TaxLiabilityCalculated": handle_tax_liability_calculated,
    
    # Operational
    "PriceSet": handle_price_set,
    "EquipmentPurchased": handle_equipment_purchased,
    "EquipmentSold": handle_equipment_sold,
    "EquipmentRepaired": handle_equipment_repaired,
    "SuppliesAcquired": handle_supplies_acquired,
    "NewLocationOpened": handle_new_location_opened,
    "MachineStatusChanged": handle_machine_status_changed,
    
    # Staffing
    "StaffHired": handle_staff_hired,
    "StaffFired": handle_staff_fired,
    "WageAdjusted": handle_wage_adjusted,
    "BenefitImplemented": handle_benefit_implemented,
    
    # Social & Regulatory
    "SocialScoreAdjusted": handle_social_score_adjusted,
    "RegulatoryStatusUpdated": handle_regulatory_status_updated,
    "ScandalStarted": handle_scandal_started,
    "ScandalMarkerDecayed": handle_scandal_marker_decayed,
    "RegulatoryFinding": handle_regulatory_finding,
    "DilemmaResolved": handle_dilemma_resolved,
    "LoyaltyMemberRegistered": handle_loyalty_member_registered,
    
    # Vendor
    "VendorNegotiationResult": handle_vendor_negotiation_result,
    "ExclusiveContractSigned": handle_exclusive_contract_signed,
    "VendorTermsUpdated": handle_vendor_terms_updated,
    
    # Competition
    "AllianceFormed": handle_alliance_formed,
}


__all__ = ["CORE_EVENT_HANDLERS"]

