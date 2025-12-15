"""
Vendor relationship projection handlers.
"""

from copy import deepcopy
from core.models import AgentState, VendorRelationship, VendorTier
from core.events import (
    VendorNegotiationResult,
    ExclusiveContractSigned,
    VendorTermsUpdated,
    VendorTierPromoted,
    VendorTierDemoted,
    VendorPriceFluctuated,
    DeliveryDisruption,
)


def handle_vendor_negotiation_result(state: AgentState, event: VendorNegotiationResult) -> AgentState:
    """Update vendor relationship based on negotiation outcome."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        vendor_rel = location.vendor_relationships.get(event.vendor_id)
        if vendor_rel is None:
            vendor_rel = VendorRelationship(
                vendor_id=event.vendor_id,
                tier=VendorTier.TIER_1,
                weeks_at_tier=0,
                payment_history=[],
                is_exclusive_contract=False,
            )
            location.vendor_relationships[event.vendor_id] = vendor_rel
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
        if vendor_rel and "terminated" in event.change_description.lower():
            vendor_rel.is_exclusive_contract = False
    return new_state


def handle_vendor_tier_promoted(state: AgentState, event: VendorTierPromoted) -> AgentState:
    """Upgrade vendor relationship tier across locations."""
    new_state = deepcopy(state)
    for location in new_state.locations.values():
        vendor_rel = location.vendor_relationships.get(event.vendor_id)
        if vendor_rel:
            try:
                vendor_rel.tier = vendor_rel.tier.__class__(event.new_tier)
            except Exception:
                vendor_rel.tier = vendor_rel.tier
    return new_state


def handle_vendor_tier_demoted(state: AgentState, event: VendorTierDemoted) -> AgentState:
    """Downgrade vendor relationship tier across locations."""
    new_state = deepcopy(state)
    for location in new_state.locations.values():
        vendor_rel = location.vendor_relationships.get(event.vendor_id)
        if vendor_rel:
            try:
                vendor_rel.tier = vendor_rel.tier.__class__(event.new_tier)
            except Exception:
                vendor_rel.tier = vendor_rel.tier
    return new_state


def handle_vendor_price_fluctuated(state: AgentState, event: VendorPriceFluctuated) -> AgentState:
    """Placeholder for vendor price changes (no direct state change yet)."""
    return deepcopy(state)


def handle_delivery_disruption(state: AgentState, event: DeliveryDisruption) -> AgentState:
    """Placeholder for delivery disruptions (no direct state change yet)."""
    return deepcopy(state)


VENDOR_EVENT_HANDLERS = {
    "VendorNegotiationResult": handle_vendor_negotiation_result,
    "ExclusiveContractSigned": handle_exclusive_contract_signed,
    "VendorTermsUpdated": handle_vendor_terms_updated,
    "VendorTierPromoted": handle_vendor_tier_promoted,
    "VendorTierDemoted": handle_vendor_tier_demoted,
    "VendorPriceFluctuated": handle_vendor_price_fluctuated,
    "DeliveryDisruption": handle_delivery_disruption,
}

__all__ = [
    "VENDOR_EVENT_HANDLERS",
    "handle_vendor_negotiation_result",
    "handle_exclusive_contract_signed",
    "handle_vendor_terms_updated",
    "handle_vendor_tier_promoted",
    "handle_vendor_tier_demoted",
    "handle_vendor_price_fluctuated",
    "handle_delivery_disruption",
]
