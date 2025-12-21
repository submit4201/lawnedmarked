"""
Competition and alliance command handlers.
"""

from typing import List
from core.commands import (
    CommandHandler,
    Command,
    EnterAllianceCommand,
    ProposeBuyoutCommand,
    AcceptBuyoutOfferCommand,
    InsufficientFundsError,
    InvalidStateError,
)
from core.events import (
    GameEvent,
    AllianceFormed,
    FundsTransferred,
)
from core.models import AgentState, Alliance
from datetime import datetime
import uuid


class EnterAllianceHandler(CommandHandler):
    """Handler for ENTER_ALLIANCE command."""
    
    def handle(self, state: AgentState, command: EnterAllianceCommand) -> List[GameEvent]:
        """
        Validate and process alliance formation.
        
        Payload expected:
        {
            "partner_agent_id": str,
            "alliance_type": str,  # "INFORMAL", "FORMAL_PARTNERSHIP", etc.
            "terms": dict
        }
        """
        partner_agent_id = getattr(command.payload, "partner_agent_id", None)
        alliance_type = getattr(command.payload, "alliance_type", None)
        terms = getattr(command.payload, "terms", {})
        
        # Extract from terms or use defaults
        alliance_cost = terms.get("cost", 0.0)
        duration_weeks = terms.get("duration_weeks", 52)
        
        # Validation
        if not partner_agent_id or partner_agent_id == state.agent_id:
            raise InvalidStateError("Invalid partner agent")
        
        if not alliance_type:
            raise InvalidStateError("Alliance type is required")
        
        if alliance_cost < 0:
            raise InvalidStateError("Alliance cost cannot be negative")
        
        if duration_weeks <= 0:
            raise InvalidStateError("Duration must be positive")
        
        if state.cash_balance < alliance_cost:
            raise InsufficientFundsError(f"Insufficient funds for alliance formation")
        
        # Check for existing alliance with partner
        if hasattr(state, "active_alliances"):
            for existing in state.active_alliances:
                if existing.partner_agent_id == partner_agent_id:
                    raise InvalidStateError(f"Already have alliance with {partner_agent_id}")
        
        alliance_id = str(uuid.uuid4())
        
        # Emit: AllianceFormed + FundsTransferred (if cost > 0)
        alliance_event = AllianceFormed(
            event_id=str(uuid.uuid4()),
            event_type="AllianceFormed",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            alliance_id=alliance_id,
            partner_agent_id=partner_agent_id,
            alliance_type=alliance_type,
            duration_weeks=duration_weeks,
        )
        
        events = [alliance_event]
        
        if alliance_cost > 0:
            funds_event = FundsTransferred(
                event_id=str(uuid.uuid4()),
                event_type="FundsTransferred",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                amount=-alliance_cost, # Negative for expense
                transaction_type="EXPENSE",
                description=f"Alliance formation with {partner_agent_id}",
            )
            events.append(funds_event)
        
        return events


class ProposeBuyoutHandler(CommandHandler):
    """Handler for PROPOSE_BUYOUT command."""
    
    def handle(self, state: AgentState, command: ProposeBuyoutCommand) -> List[GameEvent]:
        """
        Validate and process buyout proposal.
        
        Payload expected:
        {
            "target_agent_id": str,
            "offer_amount": float,
            "is_hostile_attempt": bool
        }
        """
        target_agent_id = getattr(command.payload, "target_agent_id", None)
        offer_amount = getattr(command.payload, "offer_amount", None)
        is_hostile = getattr(command.payload, "is_hostile_attempt", False)
        
        # Proposal cost (legal fees, etc.)
        proposal_cost = 5000.0 if is_hostile else 1000.0
        
        # Validation
        if not target_agent_id or target_agent_id == state.agent_id:
            raise InvalidStateError("Invalid target agent")
        
        if offer_amount <= 0:
            raise InvalidStateError("Offer amount must be positive")
        
        if state.cash_balance < proposal_cost:
            raise InsufficientFundsError(f"Insufficient funds to make buyout proposal")
        
        # Emit: FundsTransferred (cost of proposal)
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=-proposal_cost,
            transaction_type="EXPENSE",
            description=f"Buyout proposal: ${offer_amount} for {target_agent_id} (Hostile: {is_hostile})",
        )
        
        return [funds_event]


class AcceptBuyoutOfferHandler(CommandHandler):
    """Handler for ACCEPT_BUYOUT_OFFER command."""
    
    def handle(self, state: AgentState, command: AcceptBuyoutOfferCommand) -> List[GameEvent]:
        """
        Validate and process buyout offer acceptance.
        
        Payload expected:
        {
            "offer_id": str,
            "notes": str
        }
        """
        offer_id = getattr(command.payload, "offer_id", None)
        
        # In a real system, we'd look up the offer_id to get the price.
        # For now, we'll assume a placeholder price or that the GM will adjudicate.
        # But since we need to emit a fact, let's assume it's a valid offer.
        
        # Emit: FundsTransferred (placeholder for now, GM would usually trigger this)
        proceeds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=0.0, # Placeholder
            transaction_type="REVENUE",
            description=f"Accepted buyout offer {offer_id}",
        )
        
        return [proceeds_event]


COMPETITION_HANDLERS = {
    "ENTER_ALLIANCE": EnterAllianceHandler(),
    "PROPOSE_BUYOUT": ProposeBuyoutHandler(),
    "ACCEPT_BUYOUT_OFFER": AcceptBuyoutOfferHandler(),
}

__all__ = ["COMPETITION_HANDLERS"]
