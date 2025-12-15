"""
Financial command handlers.
These handlers validate financial commands and emit events.
All handlers follow the signature: (state, command) -> List[GameEvent]
"""

from typing import List
from core.commands import (
    CommandHandler,
    Command,
    SetPriceCommand,
    TakeLoanCommand,
    MakeDebtPaymentCommand,
    InvestInMarketingCommand,
    InsufficientFundsError,
    InvalidStateError,
    CreditError,
    LocationNotFoundError,
)
from core.events import (
    GameEvent,
    PriceSet,
    FundsTransferred,
    LoanTaken,
    DebtPaymentProcessed,
    MarketingBoostApplied,
)
from core.models import AgentState
from datetime import datetime
import uuid


class SetPriceHandler(CommandHandler):
    """
    Handler for SET_PRICE command.
    Validates location exists and updates pricing.
    """
    
    def handle(self, state: AgentState, command: SetPriceCommand) -> List[GameEvent]:
        """
        Validate and process price change.
        
        Payload expected:
        {
            "location_id": str,
            "service_type": str,
            "new_price": float
        }
        """
        location_id = command.payload.get("location_id")
        service_type = command.payload.get("service_type")
        new_price = command.payload.get("new_price")
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if new_price < 0:
            raise InvalidStateError("Price cannot be negative")
        
        # Emit event
        event = PriceSet(
            event_id=str(uuid.uuid4()),
            event_type="PriceSet",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            service_type=service_type,
            new_price=new_price,
        )
        
        return [event]


class TakeLoanHandler(CommandHandler):
    """
    Handler for TAKE_LOAN command.
    Validates credit and emits LoanTaken event.
    """
    
    def handle(self, state: AgentState, command: TakeLoanCommand) -> List[GameEvent]:
        """
        Validate and process loan request.
        
        Payload expected:
        {
            "principal": float,
            "interest_rate": float,
            "term_weeks": int
        }
        """
        principal = command.payload.get("principal")
        interest_rate = command.payload.get("interest_rate", 0.05)
        term_weeks = command.payload.get("term_weeks", 26)
        
        # Validation: check credit rating for eligibility
        if state.credit_rating < 30:
            raise CreditError("Credit rating too low to qualify for loan")
        
        if principal < 0:
            raise InvalidStateError("Loan principal must be positive")
        
        # Create events: LoanTaken + FundsTransferred
        loan_id = str(uuid.uuid4())
        
        loan_event = LoanTaken(
            event_id=str(uuid.uuid4()),
            event_type="LoanTaken",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            loan_id=loan_id,
            principal=principal,
            interest_rate=interest_rate,
            term_weeks=term_weeks,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=principal,
            transaction_type="LOAN",
            description=f"Loan {loan_id}: {principal}",
        )
        
        return [loan_event, funds_event]


class MakeDebtPaymentHandler(CommandHandler):
    """Handler for MAKE_DEBT_PAYMENT command."""
    
    def handle(self, state: AgentState, command: MakeDebtPaymentCommand) -> List[GameEvent]:
        """
        Validate and process debt payment.
        
        Payload expected:
        {
            "loan_id": str,
            "payment_amount": float
        }
        """
        loan_id = command.payload.get("loan_id")
        payment_amount = command.payload.get("payment_amount")
        
        # Validation
        if payment_amount > state.cash_balance:
            raise InsufficientFundsError("Insufficient funds for payment")
        
        if payment_amount < 0:
            raise InvalidStateError("Payment must be positive")
        
        # In a real system, you'd look up the loan details
        # For now, we'll make simple assumptions
        principal_reduction = payment_amount * 0.8
        interest_paid = payment_amount * 0.2
        remaining_balance = max(0, state.total_debt_owed - principal_reduction)
        
        # Emit events
        payment_event = DebtPaymentProcessed(
            event_id=str(uuid.uuid4()),
            event_type="DebtPaymentProcessed",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            loan_id=loan_id,
            payment_amount=payment_amount,
            principal_reduction=principal_reduction,
            interest_paid=interest_paid,
            remaining_balance=remaining_balance,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=payment_amount,
            transaction_type="PAYMENT",
            description=f"Debt payment for loan {loan_id}",
        )
        
        return [payment_event, funds_event]


class InvestInMarketingHandler(CommandHandler):
    """Handler for INVEST_IN_MARKETING command."""
    
    def handle(self, state: AgentState, command: InvestInMarketingCommand) -> List[GameEvent]:
        """
        Validate and process marketing investment.
        
        Payload expected:
        {
            "location_id": str,
            "marketing_cost": float,
            "duration_weeks": int
        }
        """
        location_id = command.payload.get("location_id")
        marketing_cost = command.payload.get("marketing_cost")
        duration_weeks = command.payload.get("duration_weeks", 4)
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if marketing_cost > state.cash_balance:
            raise InsufficientFundsError("Insufficient funds for marketing")
        
        if marketing_cost < 0:
            raise InvalidStateError("Marketing cost must be positive")
        
        # Calculate boost (simple linear model)
        # 100 dollars = 5% customer boost
        customer_attraction_boost = (marketing_cost / 100.0) * 5.0
        
        # Emit events
        marketing_event = MarketingBoostApplied(
            event_id=str(uuid.uuid4()),
            event_type="MarketingBoostApplied",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            marketing_cost=marketing_cost,
            customer_attraction_boost=customer_attraction_boost,
            duration_weeks=duration_weeks,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=marketing_cost,
            transaction_type="EXPENSE",
            description=f"Marketing campaign at {location_id}",
        )
        
        return [marketing_event, funds_event]


# Financial Handler Registry
FINANCIAL_HANDLERS = {
    "SET_PRICE": SetPriceHandler(),
    "TAKE_LOAN": TakeLoanHandler(),
    "MAKE_DEBT_PAYMENT": MakeDebtPaymentHandler(),
    "INVEST_IN_MARKETING": InvestInMarketingHandler(),
}


__all__ = ["FINANCIAL_HANDLERS"]
