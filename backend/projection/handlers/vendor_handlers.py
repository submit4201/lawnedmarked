"""
Vendor relationship projection handlers.
"""

from copy import deepcopy
from core.models import AgentState, VendorRelationship, VendorTier
from core.events import (
    VendorNegotiationInitiated,
    VendorNegotiationResult,
    ExclusiveContractSigned,
    VendorTermsUpdated,
    VendorTierPromoted,
    VendorTierDemoted,
    VendorPriceFluctuated,
    DeliveryDisruption,
)


def handle_vendor_negotiation_initiated(state: AgentState, event: VendorNegotiationInitiated) -> AgentState:
    """Record that a negotiation was initiated (no-op for state)."""
    return deepcopy(state)


def handle_vendor_negotiation_result(state: AgentState, event: VendorNegotiationResult) -> AgentState:
    """Update vendor relationship based on negotiation outcome."""
    new_state = deepcopy(state)
    if event.location_id not in new_state.locations:
        return new_state

    location = new_state.locations[event.location_id]
    vendor_rel = _get_or_create_relationship(location, event.vendor_id, event.location_id)
    
    if event.negotiation_succeeded:
        _handle_negotiation_success(vendor_rel, event.proposed_discount)
        
    return new_state

def _get_or_create_relationship(location: Any, vendor_id: str, location_id: str) -> VendorRelationship:
    """Get existing relationship or create a new default one."""
    vendor_rel = location.vendor_relationships.get(vendor_id)
    if vendor_rel is None:
        vendor_rel = VendorRelationship(
            vendor_id=vendor_id,
            tier=VendorTier.TIER_1,
            weeks_at_tier=0,
            payment_history=[],
            is_exclusive_contract=False,
        )
        location.vendor_relationships[vendor_id] = vendor_rel
    return vendor_rel

def _handle_negotiation_success(vendor_rel: VendorRelationship, discount: float):
    """Apply success effects to the relationship."""
    vendor_rel.weeks_at_tier += 1
    # Apply discount if provided (e.g., 0.1 means 10% off)
    if discount > 0:
        # Baseline is 1.0, so 0.1 discount makes it 0.9
        vendor_rel.current_price_per_unit = max(0.1, 1.0 - discount)


def handle_exclusive_contract_signed(state: AgentState, event: ExclusiveContractSigned) -> AgentState:
    """Mark vendor relationship as exclusive."""
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
    """Upgrade vendor relationship tier across locations.
    
    The event.new_tier must be a valid VendorTier enum value.
    If invalid, a ValueError is raised (fail-fast principle).
    """
    new_state = deepcopy(state)
    for location in new_state.locations.values():
        vendor_rel = location.vendor_relationships.get(event.vendor_id)
        if vendor_rel:
            vendor_rel.tier = vendor_rel.tier.__class__(event.new_tier)
    return new_state


def handle_vendor_tier_demoted(state: AgentState, event: VendorTierDemoted) -> AgentState:
    """Downgrade vendor relationship tier across locations.
    
    The event.new_tier must be a valid VendorTier enum value.
    If invalid, a ValueError is raised (fail-fast principle).
    """
    new_state = deepcopy(state)
    for location in new_state.locations.values():
        vendor_rel = location.vendor_relationships.get(event.vendor_id)
        if vendor_rel:
            vendor_rel.tier = vendor_rel.tier.__class__(event.new_tier)
    return new_state


def handle_vendor_price_fluctuated(state: AgentState, event: VendorPriceFluctuated) -> AgentState:
    """Update vendor price across all locations."""
    new_state = deepcopy(state)
    for location in new_state.locations.values():
        vendor_rel = location.vendor_relationships.get(event.vendor_id)
        if vendor_rel:
            vendor_rel.current_price_per_unit = event.new_price_per_unit
    return new_state


def handle_delivery_disruption(state: AgentState, event: DeliveryDisruption) -> AgentState:
    """Mark vendor as disrupted across all locations."""
    new_state = deepcopy(state)
    for location in new_state.locations.values():
        vendor_rel = location.vendor_relationships.get(event.vendor_id)
        if vendor_rel:
            vendor_rel.is_disrupted = True
    return new_state


VENDOR_EVENT_HANDLERS = {
    "VendorNegotiationInitiated": handle_vendor_negotiation_initiated,
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
