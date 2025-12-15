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
            "alliance_type": str,  # "PriceFixing", "JointMarketing", "ResourceSharing"
            "alliance_cost": float,
            "duration_weeks": int
        }
        """
        partner_agent_id = command.payload.get("partner_agent_id")
        alliance_type = command.payload.get("alliance_type")
        alliance_cost = command.payload.get("alliance_cost", 0.0)
        duration_weeks = command.payload.get("duration_weeks", 52)
        
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
                amount=alliance_cost,
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
            "offer_price": float,
            "proposal_cost": float  # Cost to make the proposal
        }
        """
        target_agent_id = command.payload.get("target_agent_id")
        offer_price = command.payload.get("offer_price")
        proposal_cost = command.payload.get("proposal_cost", 1000.0)
        
        # Validation
        if not target_agent_id or target_agent_id == state.agent_id:
            raise InvalidStateError("Invalid target agent")
        
        if offer_price <= 0:
            raise InvalidStateError("Offer price must be positive")
        
        if proposal_cost <= 0:
            raise InvalidStateError("Proposal cost must be positive")
        
        if state.cash_balance < proposal_cost:
            raise InsufficientFundsError(f"Insufficient funds to make buyout proposal")
        
        # Emit: FundsTransferred (cost of proposal)
        # Note: Actual acquisition would happen via AcceptBuyoutOffer
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=proposal_cost,
            transaction_type="EXPENSE",
            description=f"Buyout proposal: ${offer_price} for {target_agent_id}",
        )
        
        return [funds_event]


class AcceptBuyoutOfferHandler(CommandHandler):
    """Handler for ACCEPT_BUYOUT_OFFER command."""
    
    def handle(self, state: AgentState, command: AcceptBuyoutOfferCommand) -> List[GameEvent]:
        """
        Validate and process buyout offer acceptance.
        
        Payload expected:
        {
            "acquiring_agent_id": str,
            "acquisition_price": float
        }
        """
        acquiring_agent_id = command.payload.get("acquiring_agent_id")
        acquisition_price = command.payload.get("acquisition_price")
        
        # Validation
        if not acquiring_agent_id or acquiring_agent_id == state.agent_id:
            raise InvalidStateError("Invalid acquiring agent")
        
        if acquisition_price <= 0:
            raise InvalidStateError("Acquisition price must be positive")
        
        # Emit: FundsTransferred (receiving proceeds from acquisition)
        proceeds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=acquisition_price,
            transaction_type="REVENUE",
            description=f"Acquisition proceeds from {acquiring_agent_id}",
        )
        
        return [proceeds_event]


COMPETITION_HANDLERS = {
    "ENTER_ALLIANCE": EnterAllianceHandler(),
    "PROPOSE_BUYOUT": ProposeBuyoutHandler(),
    "ACCEPT_BUYOUT_OFFER": AcceptBuyoutOfferHandler(),
}

__all__ = ["COMPETITION_HANDLERS"]
