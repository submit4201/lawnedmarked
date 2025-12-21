from dataclasses import dataclass, field
from core.events import GameEvent

@dataclass(frozen=True)
class VendorTierPromoted(GameEvent):
    vendor_id: str = ""
    new_tier: int = 0
    reason: str = ""
    event_type: str = field(default="VendorTierPromoted")

@dataclass(frozen=True)
class VendorTierDemoted(GameEvent):
    vendor_id: str = ""
    new_tier: int = 0
    reason: str = ""
    event_type: str = field(default="VendorTierDemoted")

@dataclass(frozen=True)
class VendorPriceFluctuated(GameEvent):
    vendor_id: str = ""
    old_price_per_unit: float = 0.0
    new_price_per_unit: float = 0.0
    event_type: str = field(default="VendorPriceFluctuated")

@dataclass(frozen=True)
class VendorNegotiationInitiated(GameEvent):
    location_id: str = ""
    vendor_id: str = ""
    proposal: str = ""
    event_type: str = field(default="VendorNegotiationInitiated")

@dataclass(frozen=True)
class VendorNegotiationResult(GameEvent):
    location_id: str = ""
    vendor_id: str = ""
    proposed_discount: float = 0.0
    negotiation_succeeded: bool = False
    reason: str = ""
    event_type: str = field(default="VendorNegotiationResult")

@dataclass(frozen=True)
class ExclusiveContractSigned(GameEvent):
    location_id: str = ""
    vendor_id: str = ""
    contract_terms: str = ""
    duration_weeks: int = 0
    event_type: str = field(default="ExclusiveContractSigned")

@dataclass(frozen=True)
class DeliveryDisruption(GameEvent):
    vendor_id: str = ""
    disruption_type: str = ""
    impact_description: str = ""
    event_type: str = field(default="DeliveryDisruption")

@dataclass(frozen=True)
class VendorTermsUpdated(GameEvent):
    location_id: str = ""
    vendor_id: str = ""
    change_description: str = ""
    effective_week: int = 0
    event_type: str = field(default="VendorTermsUpdated")

@dataclass(frozen=True)
class CancelVendorContract(GameEvent):
    vendor_id: str = ""
    penalty_amount: float = 0.0
    event_type: str = field(default="CancelVendorContract")


__all__ = [
    "VendorTierPromoted",
    "VendorTierDemoted",
    "VendorPriceFluctuated",
    "VendorNegotiationInitiated",
    "VendorNegotiationResult",
    "ExclusiveContractSigned",
    "DeliveryDisruption",
    "VendorTermsUpdated",
    "CancelVendorContract",
]