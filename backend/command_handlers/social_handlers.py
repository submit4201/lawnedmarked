"""
Social, ethics, and regulatory command handlers.
"""

from typing import List
from core.commands import (
    CommandHandler,
    Command,
    InitiateCharityCommand,
    ResolveScandalCommand,
    FileRegulatoryReportCommand,
    FileAppealCommand,
    MakeEthicalChoiceCommand,
    SubscribeLoyaltyProgramCommand,
    InsufficientFundsError,
    InvalidStateError,
    LocationNotFoundError,
)
from core.events import (
    GameEvent,
    SocialScoreAdjusted,
    FundsTransferred,
    DilemmaResolved,
    LoyaltyMemberRegistered,
)
from core.models import AgentState
from datetime import datetime
import uuid


class InitiateCharityHandler(CommandHandler):
    """Handler for INITIATE_CHARITY command."""
    
    def handle(self, state: AgentState, command: InitiateCharityCommand) -> List[GameEvent]:
        """
        Validate and process charity initiative.
        
        Payload expected:
        {
            "charity_type": str,  # "Community", "Education", "Environmental"
            "donation_amount": float,
            "description": str
        }
        """
        charity_type = command.payload.get("charity_type")
        donation_amount = command.payload.get("donation_amount")
        description = command.payload.get("description", "")
        
        # Validation
        if not charity_type:
            raise InvalidStateError("Charity type is required")
        
        if donation_amount <= 0:
            raise InvalidStateError("Donation amount must be positive")
        
        if state.cash_balance < donation_amount:
            raise InsufficientFundsError(f"Insufficient funds for charity")
        
        # Social score boost: ~1 point per $100 donated
        social_boost = min(50.0, donation_amount / 100.0)
        
        # Emit: FundsTransferred + SocialScoreAdjusted
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=donation_amount,
            transaction_type="EXPENSE",
            description=f"Charity donation ({charity_type}): {description}",
        )
        
        social_event = SocialScoreAdjusted(
            event_id=str(uuid.uuid4()),
            event_type="SocialScoreAdjusted",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            adjustment=social_boost,
            reason=f"Charity initiative: {charity_type}",
        )
        
        return [funds_event, social_event]


class ResolveScandalHandler(CommandHandler):
    """Handler for RESOLVE_SCANDAL command."""
    
    def handle(self, state: AgentState, command: ResolveScandalCommand) -> List[GameEvent]:
        """
        Validate and process scandal resolution (PR campaign, compensation).
        
        Payload expected:
        {
            "scandal_id": str,
            "resolution_cost": float
        }
        """
        scandal_id = command.payload.get("scandal_id")
        resolution_cost = command.payload.get("resolution_cost")
        
        # Validation
        if not scandal_id:
            raise InvalidStateError("Scandal ID is required")
        
        if resolution_cost <= 0:
            raise InvalidStateError("Resolution cost must be positive")
        
        if state.cash_balance < resolution_cost:
            raise InsufficientFundsError(f"Insufficient funds to resolve scandal")
        
        # Find the scandal
        scandal = None
        for s in state.active_scandals:
            if s.scandal_id == scandal_id:
                scandal = s
                break
        
        if scandal is None:
            raise InvalidStateError(f"Scandal {scandal_id} not found")
        
        # Cost correlates to reduction in severity
        severity_reduction = min(scandal.severity, resolution_cost / 1000.0)
        
        # Emit: FundsTransferred + SocialScoreAdjusted
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=resolution_cost,
            transaction_type="EXPENSE",
            description=f"Scandal resolution: {scandal_id}",
        )
        
        social_event = SocialScoreAdjusted(
            event_id=str(uuid.uuid4()),
            event_type="SocialScoreAdjusted",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            adjustment=severity_reduction * 10.0,  # Convert to social points
            reason=f"Resolved scandal: {scandal_id}",
        )
        
        return [funds_event, social_event]


class FileRegulatoryReportHandler(CommandHandler):
    """Handler for FILE_REGULATORY_REPORT command."""
    
    def handle(self, state: AgentState, command: FileRegulatoryReportCommand) -> List[GameEvent]:
        """
        Validate and process regulatory report filing.
        
        Payload expected:
        {
            "report_type": str,  # "TaxReturn", "ComplianceReport", "SafetyAudit"
            "filing_cost": float (optional)
        }
        """
        report_type = command.payload.get("report_type")
        filing_cost = command.payload.get("filing_cost", 0.0)
        
        # Validation
        if not report_type:
            raise InvalidStateError("Report type is required")
        
        if filing_cost < 0:
            raise InvalidStateError("Filing cost cannot be negative")
        
        if state.cash_balance < filing_cost:
            raise InsufficientFundsError(f"Insufficient funds for report filing")
        
        # Filing demonstrates compliance - slight social boost
        social_boost = 2.0
        
        events = []
        
        if filing_cost > 0:
            funds_event = FundsTransferred(
                event_id=str(uuid.uuid4()),
                event_type="FundsTransferred",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                amount=filing_cost,
                transaction_type="EXPENSE",
                description=f"Regulatory report filing: {report_type}",
            )
            events.append(funds_event)
        
        social_event = SocialScoreAdjusted(
            event_id=str(uuid.uuid4()),
            event_type="SocialScoreAdjusted",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            adjustment=social_boost,
            reason=f"Filed {report_type} - demonstrated compliance",
        )
        events.append(social_event)
        
        return events


class FileAppealHandler(CommandHandler):
    """Handler for FILE_APPEAL command."""
    
    def handle(self, state: AgentState, command: FileAppealCommand) -> List[GameEvent]:
        """
        Validate and process appeal of a fine/finding.
        
        Payload expected:
        {
            "fine_id": str,
            "appeal_cost": float,
            "appeal_argument": str
        }
        """
        fine_id = command.payload.get("fine_id")
        appeal_cost = command.payload.get("appeal_cost")
        appeal_argument = command.payload.get("appeal_argument", "")
        
        # Validation
        if not fine_id:
            raise InvalidStateError("Fine ID is required")
        
        if appeal_cost <= 0:
            raise InvalidStateError("Appeal cost must be positive")
        
        if state.cash_balance < appeal_cost:
            raise InsufficientFundsError(f"Insufficient funds for appeal")
        
        # Find the fine
        fine = None
        for f in state.pending_fines:
            if f.fine_id == fine_id:
                fine = f
                break
        
        if fine is None:
            raise InvalidStateError(f"Fine {fine_id} not found")
        
        # Emit: FundsTransferred
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=appeal_cost,
            transaction_type="EXPENSE",
            description=f"Appeal filing cost for fine {fine_id}",
        )
        
        return [funds_event]


class MakeEthicalChoiceHandler(CommandHandler):
    """Handler for MAKE_ETHICAL_CHOICE command."""
    
    def handle(self, state: AgentState, command: MakeEthicalChoiceCommand) -> List[GameEvent]:
        """
        Validate and record ethical dilemma resolution.
        
        Payload expected:
        {
            "dilemma_id": str,
            "choice": str,  # e.g., "EthicalOption", "ProfitOption"
            "chosen_option_cost": float (optional - cost of ethical choice)
        }
        """
        dilemma_id = command.payload.get("dilemma_id")
        choice = command.payload.get("choice")
        chosen_option_cost = command.payload.get("chosen_option_cost", 0.0)
        
        # Validation
        if not dilemma_id or not choice:
            raise InvalidStateError("Dilemma ID and choice are required")
        
        if chosen_option_cost < 0:
            raise InvalidStateError("Cost cannot be negative")
        
        if state.cash_balance < chosen_option_cost:
            raise InsufficientFundsError(f"Insufficient funds for chosen option")
        
        # Determine social impact based on choice
        is_ethical = "ethical" in choice.lower() or "yes" in choice.lower()
        social_adjustment = 10.0 if is_ethical else -5.0
        
        # Emit: DilemmaResolved + SocialScoreAdjusted + optional FundsTransferred
        dilemma_event = DilemmaResolved(
            event_id=str(uuid.uuid4()),
            event_type="DilemmaResolved",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            dilemma_id=dilemma_id,
            chosen_option=choice,
        )
        
        social_event = SocialScoreAdjusted(
            event_id=str(uuid.uuid4()),
            event_type="SocialScoreAdjusted",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            adjustment=social_adjustment,
            reason=f"Ethical choice made: {choice}",
        )
        
        events = [dilemma_event, social_event]
        
        if chosen_option_cost > 0:
            funds_event = FundsTransferred(
                event_id=str(uuid.uuid4()),
                event_type="FundsTransferred",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                amount=chosen_option_cost,
                transaction_type="EXPENSE",
                description=f"Cost of choice: {choice}",
            )
            events.append(funds_event)
        
        return events


class SubscribeLoyaltyProgramHandler(CommandHandler):
    """Handler for SUBSCRIBE_LOYALTY_PROGRAM command."""
    
    def handle(self, state: AgentState, command: SubscribeLoyaltyProgramCommand) -> List[GameEvent]:
        """
        Validate and process loyalty program subscription.
        
        Payload expected:
        {
            "location_id": str,
            "program_cost": float,
            "expected_member_count": int
        }
        """
        location_id = command.payload.get("location_id")
        program_cost = command.payload.get("program_cost")
        expected_member_count = command.payload.get("expected_member_count", 100)
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if program_cost <= 0:
            raise InvalidStateError("Program cost must be positive")
        
        if expected_member_count <= 0:
            raise InvalidStateError("Expected member count must be positive")
        
        if state.cash_balance < program_cost:
            raise InsufficientFundsError(f"Insufficient funds for loyalty program")
        
        # Emit: FundsTransferred + LoyaltyMemberRegistered
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=program_cost,
            transaction_type="EXPENSE",
            description=f"Loyalty program setup at {location_id}",
        )
        
        loyalty_event = LoyaltyMemberRegistered(
            event_id=str(uuid.uuid4()),
            event_type="LoyaltyMemberRegistered",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            member_count=expected_member_count,
            program_year=state.current_week // 52,  # Estimate year
        )
        
        return [funds_event, loyalty_event]


SOCIAL_HANDLERS = {
    "INITIATE_CHARITY": InitiateCharityHandler(),
    "RESOLVE_SCANDAL": ResolveScandalHandler(),
    "FILE_REGULATORY_REPORT": FileRegulatoryReportHandler(),
    "FILE_APPEAL": FileAppealHandler(),
    "MAKE_ETHICAL_CHOICE": MakeEthicalChoiceHandler(),
    "SUBSCRIBE_LOYALTY_PROGRAM": SubscribeLoyaltyProgramHandler(),
}

__all__ = ["SOCIAL_HANDLERS"]
