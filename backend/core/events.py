"""
Event Sourcing infrastructure aggregator.
Events are immutable facts and are organized by domain modules.
This file exposes the base `GameEvent` and re-exports domain events.
"""

from dataclasses import dataclass, field
from typing import Any, Dict
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
from .events_time import *
from .events_financial import *
from .events_operational import *
from .events_staffing import *
from .events_social_regulatory import *
from .events_vendor import *
from .events_competition import *


@dataclass(frozen=True)
class EquipmentRepaired(GameEvent):
    """Records condition increase after maintenance."""
    location_id: str = ""
    machine_id: str = ""
    maintenance_type: str = ""
    maintenance_cost: float = 0.0
    new_condition: float = 100.0
    event_type: str = field(default="EquipmentRepaired")


@dataclass(frozen=True)
class SuppliesAcquired(GameEvent):
    """Records inventory addition after delivery."""
    location_id: str = ""
    supply_type: str = ""
    quantity: int = 0
    cost: float = 0.0
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
    severance_cost: float = 0.0
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
    annual_cost_per_employee: float = 0.0
    employee_count: int = 0
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
    rating: float = 0.0
    review_text: str = ""
    event_type: str = field(default="CustomerReviewSubmitted")


@dataclass(frozen=True)
class LoyaltyMemberRegistered(GameEvent):
    """Records a new customer joining the loyalty program."""
    location_id: str = ""
    member_count: int = 0
    program_year: int = 0
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
    location_id: str = ""
    vendor_id: str = ""
    proposed_discount: float = 0.0
    negotiation_succeeded: bool = False
    reason: str = ""
    event_type: str = field(default="VendorNegotiationResult")


@dataclass(frozen=True)
class ExclusiveContractSigned(GameEvent):
    """Records the new exclusive commitment."""
    location_id: str = ""
    vendor_id: str = ""
    contract_terms: str = ""
    duration_weeks: int = 0
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
    location_id: str = ""
    vendor_id: str = ""
    change_description: str = ""
    effective_week: int = 0
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
    partner_agent_id: str = ""
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
