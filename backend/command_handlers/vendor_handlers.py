"""
Vendor relationship command handlers.
"""

from typing import List
from core.commands import (
    CommandHandler,
    Command,
    NegotiateVendorDealCommand,
    SignExclusiveContractCommand,
    CancelVendorContractCommand,
    InsufficientFundsError,
    InvalidStateError,
    LocationNotFoundError,
)
from core.events import (
    GameEvent,
    VendorNegotiationInitiated,
    VendorNegotiationResult,
    ExclusiveContractSigned,
    VendorTermsUpdated,
    FundsTransferred,
)
from core.models import AgentState, VendorRelationship
from datetime import datetime
import uuid


class NegotiateVendorDealHandler(CommandHandler):
    """Handler for NEGOTIATE_VENDOR_DEAL command."""
    
    def handle(self, state: AgentState, command: NegotiateVendorDealCommand) -> List[GameEvent]:
        """
        Validate and process vendor negotiation initiation.
        The actual result is adjudicated by the GM based on the proposal.
        """
        payload: NegotiateVendorDealPayload = command.payload
        location_id = payload.location_id
        vendor_id = payload.vendor_id
        proposal = payload.proposal_text
        target_supply_type = payload.target_supply_type
        requested_discount = payload.requested_discount
        
        # Validation
        if location_id and location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if not vendor_id:
            raise InvalidStateError("Vendor ID is required")
        
        if not proposal:
            raise InvalidStateError("A proposal/pitch is required for negotiation")
        
        # Emit: VendorNegotiationInitiated
        negotiation_event = VendorNegotiationInitiated(
            event_id=str(uuid.uuid4()),
            event_type="VendorNegotiationInitiated",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id or "",
            vendor_id=vendor_id,
            proposal=f"Target: {target_supply_type}, Discount: {requested_discount*100}%. Proposal: {proposal}",
        )
        
        return [negotiation_event]


class SignExclusiveContractHandler(CommandHandler):
    """Handler for SIGN_EXCLUSIVE_CONTRACT command."""
    
    def handle(self, state: AgentState, command: SignExclusiveContractCommand) -> List[GameEvent]:
        """
        Validate and process exclusive contract signing.
        """
        payload: SignExclusiveContractPayload = command.payload
        location_id = payload.location_id
        vendor_id = payload.vendor_id
        duration_weeks = payload.duration_weeks
        upfront_fee = payload.upfront_fee
        
        # Validation
        if not location_id:
            raise InvalidStateError("Location ID is required for exclusive contracts")
            
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if not vendor_id:
            raise InvalidStateError("Vendor ID is required")
        
        if upfront_fee < 0:
            raise InvalidStateError("Upfront fee cannot be negative")
        
        if state.cash_balance < upfront_fee:
            raise InsufficientFundsError(f"Insufficient funds for contract signing")
        
        location = state.locations[location_id]
        vendor_rel = location.vendor_relationships.get(vendor_id)
        
        if vendor_rel and vendor_rel.is_exclusive_contract:
            raise InvalidStateError(f"Already have exclusive contract with {vendor_id}")
        
        # Emit: ExclusiveContractSigned + FundsTransferred
        contract_event = ExclusiveContractSigned(
            event_id=str(uuid.uuid4()),
            event_type="ExclusiveContractSigned",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            vendor_id=vendor_id,
            contract_terms=str({"duration_weeks": duration_weeks}),  # Serialize dict
            duration_weeks=duration_weeks,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=-upfront_fee,
            transaction_type="EXPENSE",
            description=f"Exclusive contract signing: {vendor_id}",
        )
        
        return [contract_event, funds_event]


class CancelVendorContractHandler(CommandHandler):
    """Handler for CANCEL_VENDOR_CONTRACT command."""
    
    def handle(self, state: AgentState, command: CancelVendorContractCommand) -> List[GameEvent]:
        """
        Validate and process contract cancellation.
        """
        payload: CancelVendorContractPayload = command.payload
        location_id = payload.location_id
        vendor_id = payload.vendor_id
        termination_reason = payload.reason
        early_termination_penalty = 250.0  # Default penalty
        
        # Validation
        if not location_id:
            raise InvalidStateError("Location ID is required for contract cancellation")

        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        location = state.locations[location_id]
        vendor_rel = location.vendor_relationships.get(vendor_id)
        
        if not vendor_rel or not vendor_rel.is_exclusive_contract:
            raise InvalidStateError(f"No exclusive contract to cancel with {vendor_id}")
        
        if state.cash_balance < early_termination_penalty:
            raise InsufficientFundsError(f"Insufficient funds for termination penalty")
        
        # Emit: VendorTermsUpdated + FundsTransferred
        terms_event = VendorTermsUpdated(
            event_id=str(uuid.uuid4()),
            event_type="VendorTermsUpdated",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            vendor_id=vendor_id,
            change_description=f"Exclusive contract terminated: {termination_reason}",
            effective_week=state.current_week,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=-early_termination_penalty,
            transaction_type="EXPENSE",
            description=f"Contract cancellation penalty: {vendor_id}",
        )
        
        return [terms_event, funds_event]


VENDOR_HANDLERS = {
    "NEGOTIATE_VENDOR_DEAL": NegotiateVendorDealHandler(),
    "SIGN_EXCLUSIVE_CONTRACT": SignExclusiveContractHandler(),
    "CANCEL_VENDOR_CONTRACT": CancelVendorContractHandler(),
}

__all__ = ["VENDOR_HANDLERS"]
