"""
Structured command payload definitions grouped by domain.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Literal


@dataclass(frozen=True, kw_only=True)
class CommandPayload:
    """Base class for all command payloads.

    kw_only ensures base defaults don't conflict with required subclass fields.
    """
    location_id: str | None = None


# --- I. Financial & Debt Management Commands ---

@dataclass(frozen=True, kw_only=True)
class SetPricePayload(CommandPayload):
    service_name: str
    new_price: float

    def __post_init__(self):
        if self.new_price < 0:
            raise ValueError("Price cannot be negative.")


@dataclass(frozen=True, kw_only=True)
class TakeLoanPayload(CommandPayload):
    loan_type: Literal["LOC", "EQUIPMENT", "EXPANSION", "EMERGENCY"]
    amount: float


@dataclass(frozen=True, kw_only=True)
class MakeDebtPaymentPayload(CommandPayload):
    debt_id: str
    amount: float


@dataclass(frozen=True, kw_only=True)
class InvestInMarketingPayload(CommandPayload):
    campaign_type: Literal["FLYERS", "SOCIAL_MEDIA", "NEWSPAPER_AD", "SPONSORSHIP"]
    cost: float


# --- II. Operational & Maintenance Commands ---

@dataclass(frozen=True, kw_only=True)
class BuyEquipmentPayload(CommandPayload):
    location_id: str
    equipment_type: str
    vendor_id: str
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive.")


@dataclass(frozen=True, kw_only=True)
class SellEquipmentPayload(CommandPayload):
    location_id: str
    machine_id: str
    sale_price: float


@dataclass(frozen=True, kw_only=True)
class PerformMaintenancePayload(CommandPayload):
    location_id: str
    maintenance_type: Literal["ROUTINE", "DEEP_SERVICE", "OVERHAUL", "PREMISES_CLEANING"]
    equipment_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class BuySuppliesPayload(CommandPayload):
    location_id: str
    supply_type: str
    vendor_id: str
    quantity_loads: int


@dataclass(frozen=True, kw_only=True)
class OpenNewLocationPayload(CommandPayload):
    zone: str
    monthly_rent: float
    setup_cost: float


@dataclass(frozen=True, kw_only=True)
class FixMachinePayload(CommandPayload):
    location_id: str
    machine_id: str
    maintenance_cost: float
    new_condition: float


# --- III. Staffing & HR Commands ---

@dataclass(frozen=True, kw_only=True)
class HireStaffPayload(CommandPayload):
    location_id: str
    role: Literal["ATTENDANT", "TECHNICIAN", "MANAGER"]
    name: str
    salary_per_hour: float


@dataclass(frozen=True, kw_only=True)
class FireStaffPayload(CommandPayload):
    location_id: str
    staff_id: str
    severance_pay: float = 0.0


@dataclass(frozen=True, kw_only=True)
class AdjustStaffWagePayload(CommandPayload):
    location_id: str
    staff_id: str
    new_hourly_rate: float


@dataclass(frozen=True, kw_only=True)
class ProvideBenefitsPayload(CommandPayload):
    location_id: str
    staff_id: str
    benefit_type: Literal["HEALTH_PLAN", "PROFIT_SHARING", "FLEXIBLE_SCHEDULE"]
    monthly_cost: float


# --- IV. Social, Ethics, and Regulatory Commands ---

@dataclass(frozen=True, kw_only=True)
class InitiateCharityPayload(CommandPayload):
    charity_name: str
    donation_amount: float


@dataclass(frozen=True, kw_only=True)
class ResolveScandalPayload(CommandPayload):
    resolution_strategy: Literal[
        "PUBLIC_APOLOGY",
        "COMMUNITY_OUTREACH",
        "PR_FIRM_ENGAGEMENT",
        "VICTIM_COMPENSATION",
    ]
    scandal_id: str
    cost: float


@dataclass(frozen=True, kw_only=True)
class FileRegulatoryReportPayload(CommandPayload):
    report_type: Literal["TAX_QUARTERLY", "MARKET_QUARTERLY", "COMPLIANCE_PLAN"]
    filing_cost: float = 0.0
    is_on_time: bool = True  # Defaulting, handler doesn't seem to check this yet


@dataclass(frozen=True, kw_only=True)
class FileAppealPayload(CommandPayload):
    fine_id: str
    appeal_cost: float = 500.0
    appeal_argument: str = ""


@dataclass(frozen=True, kw_only=True)
class MakeEthicalChoicePayload(CommandPayload):
    dilemma_id: str
    choice: str
    chosen_option_cost: float = 0.0


@dataclass(frozen=True, kw_only=True)
class SubscribeLoyaltyProgramPayload(CommandPayload):
    program_cost: float
    expected_member_count: int


# --- V. Relationship & Acquisition Commands ---

@dataclass(frozen=True, kw_only=True)
class NegotiateVendorDealPayload(CommandPayload):
    vendor_id: str
    proposal_text: str
    target_supply_type: str = "detergent"
    requested_discount: float = 0.0


@dataclass(frozen=True, kw_only=True)
class SignExclusiveContractPayload(CommandPayload):
    vendor_id: str
    duration_weeks: int = 52
    upfront_fee: float = 500.0


@dataclass(frozen=True, kw_only=True)
class CancelVendorContractPayload(CommandPayload):
    vendor_id: str
    reason: str = "No reason provided"


@dataclass(frozen=True, kw_only=True)
class EnterAlliancePayload(CommandPayload):
    partner_agent_id: str
    alliance_type: Literal[
        "INFORMAL",
        "FORMAL_PARTNERSHIP",
        "STRATEGIC_ALLIANCE",
        "JOINT_VENTURE",
    ]
    terms: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class ProposeBuyoutPayload(CommandPayload):
    target_agent_id: str
    offer_amount: float
    is_hostile_attempt: bool


@dataclass(frozen=True, kw_only=True)
class AcceptBuyoutOfferPayload(CommandPayload):
    offer_id: str
    notes: str = ""


# --- VI. Communications Command ---

@dataclass(frozen=True, kw_only=True)
class CommunicateToAgentPayload(CommandPayload):
    recipient_agent_id: str
    message_content: str
    channel: Literal["DIRECT", "PUBLIC", "PROPOSAL"]


# --- VII. Adjudication / God Tool Commands ---


@dataclass(frozen=True, kw_only=True)
class InjectWorldEventPayload(CommandPayload):
    """Inject a single event into the world.

    Used only by GM/Judge agents. The handler will validate the event_type is allowed
    and will construct the corresponding immutable GameEvent instance.
    """

    source_role: Literal["GM", "JUDGE"]
    event_type: str
    event_fields: Dict[str, Any] = field(default_factory=dict)


__all__ = [
    "CommandPayload",
    "SetPricePayload",
    "TakeLoanPayload",
    "MakeDebtPaymentPayload",
    "InvestInMarketingPayload",
    "BuyEquipmentPayload",
    "SellEquipmentPayload",
    "PerformMaintenancePayload",
    "BuySuppliesPayload",
    "OpenNewLocationPayload",
    "FixMachinePayload",
    "HireStaffPayload",
    "FireStaffPayload",
    "AdjustStaffWagePayload",
    "ProvideBenefitsPayload",
    "InitiateCharityPayload",
    "ResolveScandalPayload",
    "FileRegulatoryReportPayload",
    "FileAppealPayload",
    "MakeEthicalChoicePayload",
    "SubscribeLoyaltyProgramPayload",
    "NegotiateVendorDealPayload",
    "SignExclusiveContractPayload",
    "CancelVendorContractPayload",
    "EnterAlliancePayload",
    "ProposeBuyoutPayload",
    "AcceptBuyoutOfferPayload",
    "CommunicateToAgentPayload",
    "InjectWorldEventPayload",
]
