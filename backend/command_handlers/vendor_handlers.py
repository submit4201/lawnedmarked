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
    VendorNegotiationResult,
    ExclusiveContractSigned,
    VendorTermsUpdated,
    FundsTransferred,
)
from core.models import AgentState, VendorRelationship
from datetime import datetime
import uuid
import random


class NegotiateVendorDealHandler(CommandHandler):
    """Handler for NEGOTIATE_VENDOR_DEAL command."""
    
    def handle(self, state: AgentState, command: NegotiateVendorDealCommand) -> List[GameEvent]:
        """
        Validate and process vendor negotiation.
        
        Payload expected:
        {
            "location_id": str,
            "vendor_id": str,
            "proposed_discount": float,  # e.g., 0.05 for 5% discount
            "negotiation_cost": float  # Cost of negotiation effort (optional)
        }
        """
        location_id = command.payload.get("location_id")
        vendor_id = command.payload.get("vendor_id")
        proposed_discount = command.payload.get("proposed_discount", 0.0)
        negotiation_cost = command.payload.get("negotiation_cost", 100.0)
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if not vendor_id:
            raise InvalidStateError("Vendor ID is required")
        
        if proposed_discount < 0 or proposed_discount >= 1.0:
            raise InvalidStateError("Discount must be between 0 and 1")
        
        if negotiation_cost < 0:
            raise InvalidStateError("Negotiation cost cannot be negative")
        
        if state.cash_balance < negotiation_cost:
            raise InsufficientFundsError(f"Insufficient funds for negotiation")
        
        location = state.locations[location_id]
        
        # Determine success based on proposed discount and vendor tier
        vendor_rel = location.vendor_relationships.get(vendor_id)
        vendor_tier = vendor_rel.tier if vendor_rel else 1
        
        # Higher discount is harder; higher tier helps
        success_chance = 0.5 + (vendor_tier * 0.1) - (proposed_discount * 0.5)
        success_chance = max(0.1, min(0.9, success_chance))  # Clamp 10-90%
        
        negotiation_succeeded = random.random() < success_chance
        
        # Emit: VendorNegotiationResult + FundsTransferred
        negotiation_event = VendorNegotiationResult(
            event_id=str(uuid.uuid4()),
            event_type="VendorNegotiationResult",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            vendor_id=vendor_id,
            proposed_discount=proposed_discount,
            negotiation_succeeded=negotiation_succeeded,
            reason="Negotiation attempt" + (" succeeded" if negotiation_succeeded else " failed"),
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=negotiation_cost,
            transaction_type="EXPENSE",
            description=f"Vendor negotiation cost: {vendor_id}",
        )
        
        return [negotiation_event, funds_event]


class SignExclusiveContractHandler(CommandHandler):
    """Handler for SIGN_EXCLUSIVE_CONTRACT command."""
    
    def handle(self, state: AgentState, command: SignExclusiveContractCommand) -> List[GameEvent]:
        """
        Validate and process exclusive contract signing.
        
        Payload expected:
        {
            "location_id": str,
            "vendor_id": str,
            "contract_terms": dict,  # e.g., {"discount": 0.1, "min_monthly_volume": 1000}
            "signing_cost": float
        }
        """
        location_id = command.payload.get("location_id")
        vendor_id = command.payload.get("vendor_id")
        contract_terms = command.payload.get("contract_terms", {})
        signing_cost = command.payload.get("signing_cost", 500.0)
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if not vendor_id:
            raise InvalidStateError("Vendor ID is required")
        
        if signing_cost <= 0:
            raise InvalidStateError("Signing cost must be positive")
        
        if state.cash_balance < signing_cost:
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
            contract_terms=str(contract_terms),  # Serialize dict
            duration_weeks=52,  # 1-year default
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=signing_cost,
            transaction_type="EXPENSE",
            description=f"Exclusive contract signing: {vendor_id}",
        )
        
        return [contract_event, funds_event]


class CancelVendorContractHandler(CommandHandler):
    """Handler for CANCEL_VENDOR_CONTRACT command."""
    
    def handle(self, state: AgentState, command: CancelVendorContractCommand) -> List[GameEvent]:
        """
        Validate and process contract cancellation.
        
        Payload expected:
        {
            "location_id": str,
            "vendor_id": str,
            "early_termination_penalty": float (optional)
        }
        """
        location_id = command.payload.get("location_id")
        vendor_id = command.payload.get("vendor_id")
        early_termination_penalty = command.payload.get("early_termination_penalty", 0.0)
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        location = state.locations[location_id]
        vendor_rel = location.vendor_relationships.get(vendor_id)
        
        if not vendor_rel or not vendor_rel.is_exclusive_contract:
            raise InvalidStateError(f"No exclusive contract to cancel with {vendor_id}")
        
        if early_termination_penalty < 0:
            raise InvalidStateError("Penalty cannot be negative")
        
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
            change_description="Exclusive contract terminated",
            effective_week=state.current_week,
        )
        
        events = [terms_event]
        
        if early_termination_penalty > 0:
            penalty_event = FundsTransferred(
                event_id=str(uuid.uuid4()),
                event_type="FundsTransferred",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                amount=early_termination_penalty,
                transaction_type="EXPENSE",
                description=f"Contract cancellation penalty: {vendor_id}",
            )
            events.append(penalty_event)
        
        return events


VENDOR_HANDLERS = {
    "NEGOTIATE_VENDOR_DEAL": NegotiateVendorDealHandler(),
    "SIGN_EXCLUSIVE_CONTRACT": SignExclusiveContractHandler(),
    "CANCEL_VENDOR_CONTRACT": CancelVendorContractHandler(),
}

__all__ = ["VENDOR_HANDLERS"]
