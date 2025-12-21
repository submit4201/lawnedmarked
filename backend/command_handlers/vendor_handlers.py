"""
Vendor relationship command handlers.
"""

from typing import List, Tuple
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
    ExclusiveContractSigned,
    VendorTermsUpdated,
    FundsTransferred,
)
from core.models import AgentState, LocationState
from datetime import datetime
import uuid


class VendorHandlerBase(CommandHandler):
    """Base class with shared validation for vendor validations."""
    
    def validate_location(self, state: AgentState, location_id: str) -> LocationState:       
        if not location_id:
             raise InvalidStateError("Location ID is required")
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        return state.locations[location_id]

    def validate_funds(self, state: AgentState, amount: float, reason: str = ""):
        if amount < 0:
            raise InvalidStateError("Amount cannot be negative")
        if state.cash_balance < amount:
            raise InsufficientFundsError(f"Insufficient funds for {reason}")

    def create_event(self, event_type_class: type, state: AgentState, **kwargs) -> GameEvent:
        return event_type_class(
            event_id=str(uuid.uuid4()),
            event_type=event_type_class.__name__,
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            **kwargs
        )


class NegotiateVendorDealHandler(VendorHandlerBase):
    """Handler for NEGOTIATE_VENDOR_DEAL command."""
    
    def handle(self, state: AgentState, command: NegotiateVendorDealCommand) -> List[GameEvent]:
        payload = command.payload
        self.validate_location(state, payload.location_id)
        
        if not payload.vendor_id:
            raise InvalidStateError("Vendor ID is required")
        if not payload.proposal_text:
            raise InvalidStateError("A proposal/pitch is required for negotiation")
        
        negotiation_event = self.create_event(
            VendorNegotiationInitiated,
            state,
            location_id=payload.location_id or "",
            vendor_id=payload.vendor_id,
            proposal=f"Target: {payload.target_supply_type}, Discount: {payload.requested_discount*100}%. Proposal: {payload.proposal_text}",
        )
        
        return [negotiation_event]


class SignExclusiveContractHandler(VendorHandlerBase):
    """Handler for SIGN_EXCLUSIVE_CONTRACT command."""
    
    def handle(self, state: AgentState, command: SignExclusiveContractCommand) -> List[GameEvent]:
        payload = command.payload
        location = self.validate_location(state, payload.location_id)
        
        if not payload.vendor_id:
            raise InvalidStateError("Vendor ID is required")
        
        self.validate_funds(state, payload.upfront_fee, "contract signing")
        
        vendor_rel = location.vendor_relationships.get(payload.vendor_id)
        if vendor_rel and vendor_rel.is_exclusive_contract:
            raise InvalidStateError(f"Already have exclusive contract with {payload.vendor_id}")
        
        contract_event = self.create_event(
            ExclusiveContractSigned,
            state,
            location_id=payload.location_id,
            vendor_id=payload.vendor_id,
            contract_terms=str({"duration_weeks": payload.duration_weeks}),
            duration_weeks=payload.duration_weeks,
        )
        
        funds_event = self.create_event(
            FundsTransferred,
            state,
            amount=-payload.upfront_fee,
            transaction_type="EXPENSE",
            description=f"Exclusive contract signing: {payload.vendor_id}",
        )
        
        return [contract_event, funds_event]


class CancelVendorContractHandler(VendorHandlerBase):
    """Handler for CANCEL_VENDOR_CONTRACT command."""
    
    def handle(self, state: AgentState, command: CancelVendorContractCommand) -> List[GameEvent]:
        payload = command.payload
        location = self.validate_location(state, payload.location_id)
        
        early_termination_penalty = 250.0  # Default penalty
        self.validate_funds(state, early_termination_penalty, "termination penalty")
        
        vendor_rel = location.vendor_relationships.get(payload.vendor_id)
        if not vendor_rel or not vendor_rel.is_exclusive_contract:
            raise InvalidStateError(f"No exclusive contract to cancel with {payload.vendor_id}")
        
        terms_event = self.create_event(
            VendorTermsUpdated,
            state,
            location_id=payload.location_id,
            vendor_id=payload.vendor_id,
            change_description=f"Exclusive contract terminated: {payload.reason}",
            effective_week=state.current_week,
        )
        
        funds_event = self.create_event(
            FundsTransferred,
            state,
            amount=-early_termination_penalty,
            transaction_type="EXPENSE",
            description=f"Contract cancellation penalty: {payload.vendor_id}",
        )
        
        return [terms_event, funds_event]


VENDOR_HANDLERS = {
    "NEGOTIATE_VENDOR_DEAL": NegotiateVendorDealHandler(),
    "SIGN_EXCLUSIVE_CONTRACT": SignExclusiveContractHandler(),
    "CANCEL_VENDOR_CONTRACT": CancelVendorContractHandler(),
}

__all__ = ["VENDOR_HANDLERS"]
