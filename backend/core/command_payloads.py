"""
Structured command payload definitions grouped by domain.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Literal


@dataclass(frozen=True)
class CommandPayload:
    """Base class for all command payloads."""
    location_id: str = "default_location"


# --- I. Financial & Debt Management Commands ---

@dataclass(frozen=True)
class SetPricePayload(CommandPayload):
    service_name: str
    new_price: float

    def __post_init__(self):
        if self.new_price < 0:
            raise ValueError("Price cannot be negative.")


@dataclass(frozen=True)
class TakeLoanPayload(CommandPayload):
    loan_type: Literal["LOC", "EQUIPMENT", "EXPANSION", "EMERGENCY"]
    amount: float


@dataclass(frozen=True)
class MakeDebtPaymentPayload(CommandPayload):
    debt_id: str
    amount: float


@dataclass(frozen=True)
class InvestInMarketingPayload(CommandPayload):
    campaign_type: Literal["FLYERS", "SOCIAL_MEDIA", "NEWSPAPER_AD", "SPONSORSHIP"]
    cost: float


# --- II. Operational & Maintenance Commands ---

@dataclass(frozen=True)
class BuyEquipmentPayload(CommandPayload):
    equipment_type: str
    vendor_id: str
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive.")


@dataclass(frozen=True)
class SellEquipmentPayload(CommandPayload):
    machine_id: str
    sale_price: float


@dataclass(frozen=True)
class PerformMaintenancePayload(CommandPayload):
    maintenance_type: Literal["ROUTINE", "DEEP_SERVICE", "OVERHAUL", "PREMISES_CLEANING"]
    equipment_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BuySuppliesPayload(CommandPayload):
    supply_type: str
    vendor_id: str
    quantity_loads: int


@dataclass(frozen=True)
class OpenNewLocationPayload(CommandPayload):
    zone: str
    monthly_rent: float


@dataclass(frozen=True)
class FixMachinePayload(CommandPayload):
    machine_id: str
    maintenance_cost: float
    new_condition: float


# --- III. Staffing & HR Commands ---

@dataclass(frozen=True)
class HireStaffPayload(CommandPayload):
    role: Literal["ATTENDANT", "TECHNICIAN", "MANAGER"]
    name: str
    salary_per_hour: float


@dataclass(frozen=True)
class FireStaffPayload(CommandPayload):
    staff_id: str
    reason: str


@dataclass(frozen=True)
class AdjustStaffWagePayload(CommandPayload):
    staff_id: str
    new_salary_per_hour: float


@dataclass(frozen=True)
class ProvideBenefitsPayload(CommandPayload):
    benefit_type: Literal["HEALTH_PLAN", "PROFIT_SHARING", "FLEXIBLE_SCHEDULE"]
    cost: float


# --- IV. Social, Ethics, and Regulatory Commands ---

@dataclass(frozen=True)
class InitiateCharityPayload(CommandPayload):
    contribution_type: Literal["DONATION", "FREE_LAUNDRY_DAY", "SPONSORSHIP"]
    amount: float


@dataclass(frozen=True)
class ResolveScandalPayload(CommandPayload):
    resolution_type: Literal[
        "PUBLIC_APOLOGY",
        "COMMUNITY_OUTREACH",
        "PR_FIRM_ENGAGEMENT",
        "VICTIM_COMPENSATION",
    ]
    scandal_id: str
    cost: float


@dataclass(frozen=True)
class FileRegulatoryReportPayload(CommandPayload):
    report_type: Literal["TAX_QUARTERLY", "MARKET_QUARTERLY", "COMPLIANCE_PLAN"]
    is_on_time: bool


@dataclass(frozen=True)
class FileAppealPayload(CommandPayload):
    case_id: str
    legal_fee: float = 500.0


@dataclass(frozen=True)
class MakeEthicalChoicePayload(CommandPayload):
    dilemma_id: str
    choice: str


@dataclass(frozen=True)
class SubscribeLoyaltyProgramPayload(CommandPayload):
    program_name: str
    member_count: int


# --- V. Relationship & Acquisition Commands ---

@dataclass(frozen=True)
class NegotiateVendorDealPayload(CommandPayload):
    vendor_id: str
    proposal: str


@dataclass(frozen=True)
class SignExclusiveContractPayload(CommandPayload):
    vendor_id: str
    duration_weeks: int
    volume_commitment_loads: int


@dataclass(frozen=True)
class CancelVendorContractPayload(CommandPayload):
    vendor_id: str
    reason: str = ""


@dataclass(frozen=True)
class EnterAlliancePayload(CommandPayload):
    partner_agent_id: str
    alliance_type: Literal[
        "INFORMAL",
        "FORMAL_PARTNERSHIP",
        "STRATEGIC_ALLIANCE",
        "JOINT_VENTURE",
    ]
    terms: Dict[str, Any]


@dataclass(frozen=True)
class ProposeBuyoutPayload(CommandPayload):
    target_agent_id: str
    offer_amount: float
    is_hostile_attempt: bool


@dataclass(frozen=True)
class AcceptBuyoutOfferPayload(CommandPayload):
    offer_id: str
    notes: str = ""


# --- VI. Communications Command ---

@dataclass(frozen=True)
class CommunicateToAgentPayload(CommandPayload):
    recipient_agent_id: str
    message_content: str
    channel: Literal["DIRECT", "PUBLIC", "PROPOSAL"]


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
]
