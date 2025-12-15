"""
Event Sourcing infrastructure.
Events are immutable facts that describe state changes.
All fields in events MUST be immutable (frozen dataclasses).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from datetime import datetime
from abc import ABC


@dataclass(frozen=True)
class GameEvent(ABC):
    """
    Base class for all immutable game events.
    Every event is a fact that happened and cannot be changed.
    """
    event_id: str
    agent_id: str
    timestamp: datetime
    week: int
    event_type: str = field(default="GameEvent")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "week": self.week
        }


# ==================== Time & Engine Events ====================

@dataclass(frozen=True)
class TimeAdvanced(GameEvent):
    """Records the progression of simulation time."""
    day: int = 0
    event_type: str = field(default="TimeAdvanced")


@dataclass(frozen=True)
class DailyRevenueProcessed(GameEvent):
    """Records daily revenue, loads processed, and variable costs."""
    location_id: str = ""
    loads_processed: int = 0
    revenue_generated: float = 0.0
    utility_cost: float = 0.0
    supplies_cost: float = 0.0
    event_type: str = field(default="DailyRevenueProcessed")


@dataclass(frozen=True)
class WeeklyFixedCostsBilled(GameEvent):
    """Records weekly fixed costs (rent, insurance, etc.)."""
    location_id: str = ""
    rent_cost: float = 0.0
    insurance_cost: float = 0.0
    other_fixed_costs: float = 0.0
    event_type: str = field(default="WeeklyFixedCostsBilled")


@dataclass(frozen=True)
class MonthlyInterestAccrued(GameEvent):
    """Records interest added to loans and line of credit."""
    loan_amount: float = 0.0
    loc_amount: float = 0.0
    total_interest: float = 0.0
    event_type: str = field(default="MonthlyInterestAccrued")


@dataclass(frozen=True)
class MachineWearUpdated(GameEvent):
    """Records machine condition degradation."""
    location_id: str = ""
    machine_id: str = ""
    new_condition: float = 0.0
    loads_processed_since_service: int = 0
    event_type: str = field(default="MachineWearUpdated")


@dataclass(frozen=True)
class MachineBrokenDown(GameEvent):
    """Records a machine becoming unusable."""
    location_id: str = ""
    machine_id: str = ""
    reason: str = ""
    event_type: str = field(default="MachineBrokenDown")


@dataclass(frozen=True)
class WeeklyWagesBilled(GameEvent):
    """Records total labor cost for the week."""
    location_id: str = ""
    total_wages: float = 0.0
    staff_count: int = 0
    event_type: str = field(default="WeeklyWagesBilled")


@dataclass(frozen=True)
class TaxLiabilityCalculated(GameEvent):
    """Records the amount of tax owed (quarterly)."""
    taxable_income: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    event_type: str = field(default="TaxLiabilityCalculated")


@dataclass(frozen=True)
class TaxBracketAdjusted(GameEvent):
    """Records a change in tax rate due to world events."""
    new_tax_rate: float = 0.0
    reason: str = ""
    event_type: str = field(default="TaxBracketAdjusted")


# ==================== Financial & Pricing Events ====================

@dataclass(frozen=True)
class FundsTransferred(GameEvent):
    """The fundamental financial fact: money movement (Debit/Credit)."""
    amount: float = 0.0
    transaction_type: str = ""
    description: str = ""
    event_type: str = field(default="FundsTransferred")


@dataclass(frozen=True)
class LoanTaken(GameEvent):
    """Records the successful acquisition of a new loan."""
    loan_id: str = ""
    principal: float = 0.0
    interest_rate: float = 0.0
    term_weeks: int = 0
    event_type: str = field(default="LoanTaken")


@dataclass(frozen=True)
class DebtPaymentProcessed(GameEvent):
    """Records a payment and reduction in principal/interest."""
    loan_id: str = ""
    payment_amount: float = 0.0
    principal_reduction: float = 0.0
    interest_paid: float = 0.0
    remaining_balance: float = 0.0
    event_type: str = field(default="DebtPaymentProcessed")


@dataclass(frozen=True)
class DefaultRecorded(GameEvent):
    """Records failure to pay debt, triggering consequences."""
    loan_id: str = ""
    amount_owed: float = 0.0
    penalty_amount: float = 0.0
    event_type: str = field(default="DefaultRecorded")


@dataclass(frozen=True)
class PriceSet(GameEvent):
    """Records a price set for a specific service."""
    location_id: str = ""
    service_type: str = ""
    new_price: float = 0.0
    event_type: str = field(default="PriceSet")


@dataclass(frozen=True)
class MarketingBoostApplied(GameEvent):
    """Records the positive effect of marketing spend."""
    location_id: str = ""
    marketing_cost: float = 0.0
    customer_attraction_boost: float = 0.0
    duration_weeks: int = 0
    event_type: str = field(default="MarketingBoostApplied")


# ==================== Operational & Equipment Events ====================

@dataclass(frozen=True)
class EquipmentPurchased(GameEvent):
    """Records the addition of a new machine unit."""
    location_id: str = ""
    machine_id: str = ""
    machine_type: str = ""
    purchase_price: float = 0.0
    event_type: str = field(default="EquipmentPurchased")


@dataclass(frozen=True)
class EquipmentSold(GameEvent):
    """Records equipment removal and the received cash."""
    location_id: str = ""
    machine_id: str = ""
    sale_price: float = 0.0
    event_type: str = field(default="EquipmentSold")


@dataclass(frozen=True)
class EquipmentRepaired(GameEvent):
    """Records condition increase after maintenance."""
    location_id: str = ""
    machine_id: str = ""
    new_condition: float = 0.0
    maintenance_type: str = ""
    maintenance_cost: float = 0.0
    event_type: str = field(default="EquipmentRepaired")


@dataclass(frozen=True)
class SuppliesAcquired(GameEvent):
    """Records inventory addition after delivery."""
    location_id: str = ""
    detergent_acquired: int = 0
    softener_acquired: int = 0
    acquisition_cost: float = 0.0
    event_type: str = field(default="SuppliesAcquired")


@dataclass(frozen=True)
class StockoutStarted(GameEvent):
    """Inventory hits zero, starting penalties."""
    location_id: str = ""
    inventory_type: str = ""
    event_type: str = field(default="StockoutStarted")


@dataclass(frozen=True)
class StockoutEnded(GameEvent):
    """Inventory is restocked, ending penalties."""
    location_id: str = ""
    inventory_type: str = ""
    event_type: str = field(default="StockoutEnded")


@dataclass(frozen=True)
class NewLocationOpened(GameEvent):
    """Records the successful opening of a new site."""
    location_id: str = ""
    zone: str = ""
    initial_investment: float = 0.0
    event_type: str = field(default="NewLocationOpened")


@dataclass(frozen=True)
class MachineStatusChanged(GameEvent):
    """Records a machine moving to 'IN_REPAIR' or 'OPERATIONAL'."""
    location_id: str = ""
    machine_id: str = ""
    new_status: str = ""
    reason: str = ""
    event_type: str = field(default="MachineStatusChanged")


# ==================== Staffing & HR Events ====================

@dataclass(frozen=True)
class StaffHired(GameEvent):
    """Records the new employee's entry into the system."""
    location_id: str = ""
    staff_id: str = ""
    staff_name: str = ""
    role: str = ""
    hourly_rate: float = 0.0
    event_type: str = field(default="StaffHired")


@dataclass(frozen=True)
class StaffFired(GameEvent):
    """Records termination (may trigger fines/lawsuits from Judge)."""
    location_id: str = ""
    staff_id: str = ""
    reason: str = ""
    event_type: str = field(default="StaffFired")


@dataclass(frozen=True)
class StaffQuit(GameEvent):
    """Employee leaves autonomously due to low wages/bad conditions."""
    location_id: str = ""
    staff_id: str = ""
    reason: str = ""
    event_type: str = field(default="StaffQuit")


@dataclass(frozen=True)
class WageAdjusted(GameEvent):
    """Records a change in hourly rate for a staff member."""
    location_id: str = ""
    staff_id: str = ""
    old_rate: float = 0.0
    new_rate: float = 0.0
    event_type: str = field(default="WageAdjusted")


@dataclass(frozen=True)
class BenefitImplemented(GameEvent):
    """Records the initiation of a staff benefit plan."""
    location_id: str = ""
    benefit_type: str = ""
    cost_per_employee_per_week: float = 0.0
    event_type: str = field(default="BenefitImplemented")


# ==================== Social, Ethics, & Regulatory Events ====================

@dataclass(frozen=True)
class SocialScoreAdjusted(GameEvent):
    """Records any change to the overall Social Score."""
    adjustment: float = 0.0
    reason: str = ""
    event_type: str = field(default="SocialScoreAdjusted")


@dataclass(frozen=True)
class ScandalStarted(GameEvent):
    """Creates a persistent negative marker on the AgentState."""
    scandal_id: str = ""
    description: str = ""
    severity: float = 0.0
    duration_weeks: int = 0
    event_type: str = field(default="ScandalStarted")


@dataclass(frozen=True)
class ScandalMarkerDecayed(GameEvent):
    """Records the weekly reduction of a scandal's duration."""
    scandal_id: str = ""
    remaining_weeks: int = 0
    event_type: str = field(default="ScandalMarkerDecayed")


@dataclass(frozen=True)
class RegulatoryFinding(GameEvent):
    """Records a fine, penalty, or compliance issue."""
    fine_id: str = ""
    description: str = ""
    fine_amount: float = 0.0
    due_date: int = 0
    event_type: str = field(default="RegulatoryFinding")


@dataclass(frozen=True)
class RegulatoryStatusUpdated(GameEvent):
    """Changes the agent's market share oversight status."""
    new_status: str = ""
    reason: str = ""
    event_type: str = field(default="RegulatoryStatusUpdated")


@dataclass(frozen=True)
class DilemmaTriggered(GameEvent):
    """Presents an ethical choice to the player."""
    dilemma_id: str = ""
    description: str = ""
    options: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    event_type: str = field(default="DilemmaTriggered")


@dataclass(frozen=True)
class DilemmaResolved(GameEvent):
    """Records the player's choice on a dilemma."""
    dilemma_id: str = ""
    chosen_option: str = ""
    event_type: str = field(default="DilemmaResolved")


@dataclass(frozen=True)
class InvestigationStarted(GameEvent):
    """Judge initiates a formal regulatory inquiry."""
    investigation_id: str = ""
    reason: str = ""
    severity: str = ""
    event_type: str = field(default="InvestigationStarted")


@dataclass(frozen=True)
class InvestigationStageAdvanced(GameEvent):
    """Records progression through the legal process."""
    investigation_id: str = ""
    current_stage: str = ""
    event_type: str = field(default="InvestigationStageAdvanced")


@dataclass(frozen=True)
class CustomerReviewSubmitted(GameEvent):
    """Records a customer's specific review rating."""
    location_id: str = ""
    rating: int = 0
    review_text: str = ""
    event_type: str = field(default="CustomerReviewSubmitted")


@dataclass(frozen=True)
class LoyaltyMemberRegistered(GameEvent):
    """Records a new customer joining the loyalty program."""
    location_id: str = ""
    customer_id: str = ""
    event_type: str = field(default="LoyaltyMemberRegistered")


# ==================== Vendor Relationship Events ====================

@dataclass(frozen=True)
class VendorTierPromoted(GameEvent):
    """Relationship tier upgraded based on volume/history."""
    vendor_id: str = ""
    new_tier: int = 0
    reason: str = ""
    event_type: str = field(default="VendorTierPromoted")


@dataclass(frozen=True)
class VendorTierDemoted(GameEvent):
    """Relationship tier downgraded due to late payment/breach."""
    vendor_id: str = ""
    new_tier: int = 0
    reason: str = ""
    event_type: str = field(default="VendorTierDemoted")


@dataclass(frozen=True)
class VendorPriceFluctuated(GameEvent):
    """Records a change in a vendor's supply cost."""
    vendor_id: str = ""
    old_price_per_unit: float = 0.0
    new_price_per_unit: float = 0.0
    event_type: str = field(default="VendorPriceFluctuated")


@dataclass(frozen=True)
class VendorNegotiationResult(GameEvent):
    """Records the outcome of a negotiation attempt."""
    vendor_id: str = ""
    success: bool = False
    negotiated_terms: Dict[str, Any] = field(default_factory=dict)
    event_type: str = field(default="VendorNegotiationResult")


@dataclass(frozen=True)
class ExclusiveContractSigned(GameEvent):
    """Records the new exclusive commitment."""
    vendor_id: str = ""
    contract_duration_weeks: int = 0
    terms: Dict[str, Any] = field(default_factory=dict)
    event_type: str = field(default="ExclusiveContractSigned")


@dataclass(frozen=True)
class DeliveryDisruption(GameEvent):
    """Records a delay, partial shipment, or quality issue."""
    vendor_id: str = ""
    disruption_type: str = ""
    impact_description: str = ""
    event_type: str = field(default="DeliveryDisruption")


@dataclass(frozen=True)
class VendorTermsUpdated(GameEvent):
    """Records new negotiated price/terms applied."""
    vendor_id: str = ""
    new_terms: Dict[str, Any] = field(default_factory=dict)
    event_type: str = field(default="VendorTermsUpdated")


@dataclass(frozen=True)
class CancelVendorContract(GameEvent):
    """Records termination of an exclusive contract."""
    vendor_id: str = ""
    penalty_amount: float = 0.0
    event_type: str = field(default="CancelVendorContract")


# ==================== Competition & Acquisition Events ====================

@dataclass(frozen=True)
class AllianceFormed(GameEvent):
    """Records the creation of a formal alliance."""
    alliance_id: str = ""
    partner_id: str = ""
    alliance_type: str = ""
    duration_weeks: int = 0
    penalties_on_breach: float = 0.0
    event_type: str = field(default="AllianceFormed")


@dataclass(frozen=True)
class AllianceBreached(GameEvent):
    """Records a violation of alliance terms."""
    alliance_id: str = ""
    penalty_amount: float = 0.0
    event_type: str = field(default="AllianceBreached")


@dataclass(frozen=True)
class AgentAcquired(GameEvent):
    """Records a successful acquisition/merger."""
    target_agent_id: str = ""
    acquisition_cost: float = 0.0
    assets_transferred: Dict[str, Any] = field(default_factory=dict)
    event_type: str = field(default="AgentAcquired")


@dataclass(frozen=True)
class CompetitorPriceChanged(GameEvent):
    """Records a competitor's pricing decision."""
    competitor_id: str = ""
    location_id: str = ""
    service_type: str = ""
    new_price: float = 0.0
    event_type: str = field(default="CompetitorPriceChanged")


@dataclass(frozen=True)
class CompetitorExitedMarket(GameEvent):
    """Records an NPC competitor going bankrupt or being acquired."""
    competitor_id: str = ""
    reason: str = ""
    event_type: str = field(default="CompetitorExitedMarket")


@dataclass(frozen=True)
class CommunicationIntercepted(GameEvent):
    """Records that a private message was detected (collusion/price fixing)."""
    parties_involved: List[str] = field(default_factory=list)
    communication_type: str = ""
    event_type: str = field(default="CommunicationIntercepted")
