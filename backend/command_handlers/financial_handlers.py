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
            "service_name": str | list[str],
            "new_price": float | list[float]
        }
        """
        # ! Updated to use attribute access for typed payloads
        location_id = getattr(command.payload, "location_id", None)
        service_names = getattr(command.payload, "service_name", None)
        new_prices = getattr(command.payload, "new_price", None)
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        # Normalize to lists
        if isinstance(service_names, str):
            service_names = [service_names]
        if isinstance(new_prices, (int, float)):
            new_prices = [float(new_prices)]
            
        if not service_names or not new_prices:
            raise InvalidStateError("Service name and price are required")
            
        if len(service_names) != len(new_prices):
            raise InvalidStateError("Number of service names must match number of prices")
            
        events = []
        for service_name, new_price in zip(service_names, new_prices):
            if new_price < 0:
                raise InvalidStateError(f"Price for {service_name} cannot be negative")
                
            events.append(PriceSet(
                event_id=str(uuid.uuid4()),
                event_type="PriceSet",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                location_id=location_id,
                service_name=service_name,
                new_price=new_price,
            ))
            
        return events


class TakeLoanHandler(CommandHandler):
    """
    Handler for TAKE_LOAN command.
    Validates credit and emits LoanTaken event.
    """
    
    LOAN_TERMS = {
        "LOC": {"interest_rate": 0.08, "term_weeks": 0},  # Revolving
        "EQUIPMENT": {"interest_rate": 0.06, "term_weeks": 52},
        "EXPANSION": {"interest_rate": 0.05, "term_weeks": 104},
        "EMERGENCY": {"interest_rate": 0.12, "term_weeks": 12},
    }
    
    def handle(self, state: AgentState, command: TakeLoanCommand) -> List[GameEvent]:
        """
        Validate and process loan request.
        
        Payload expected:
        {
            "loan_type": str,  # "LOC", "EQUIPMENT", "EXPANSION", "EMERGENCY"
            "amount": float
        }
        """
        # ! Updated to use attribute access for typed payloads
        loan_type = getattr(command.payload, "loan_type", "LOC")
        amount = getattr(command.payload, "amount", None)
        
        # Validation: check credit rating for eligibility
        if state.credit_rating < 30:
            raise CreditError("Credit rating too low to qualify for loan")
        
        if amount is None or amount <= 0:
            raise InvalidStateError("Loan amount must be positive")
        
        terms = self.LOAN_TERMS.get(loan_type, self.LOAN_TERMS["LOC"])
        interest_rate = terms["interest_rate"]
        term_weeks = terms["term_weeks"]
        
        # Create events: LoanTaken + FundsTransferred
        loan_id = str(uuid.uuid4())
        
        loan_event = LoanTaken(
            event_id=str(uuid.uuid4()),
            event_type="LoanTaken",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            loan_id=loan_id,
            principal=amount,
            interest_rate=interest_rate,
            term_weeks=term_weeks,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=amount,
            transaction_type="LOAN",
            description=f"Loan disbursement: {loan_type} ({loan_id})",
        )
        
        return [loan_event, funds_event]


class MakeDebtPaymentHandler(CommandHandler):
    """Handler for MAKE_DEBT_PAYMENT command."""
    
    def handle(self, state: AgentState, command: MakeDebtPaymentCommand) -> List[GameEvent]:
        """
        Validate and process debt payment.
        
        Payload expected:
        {
            "debt_id": str,
            "amount": float
        }
        """
        # ! Updated to use attribute access for typed payloads
        loan_id = getattr(command.payload, "debt_id", None)
        payment_amount = getattr(command.payload, "amount", None)
        
        # Validation
        if payment_amount is None or payment_amount < 0:
            raise InvalidStateError("Payment must be positive")
            
        if payment_amount > state.cash_balance:
            raise InsufficientFundsError("Insufficient funds for payment")
        
        # In a real system, you'd look up the loan details
        # For now, we'll make simple assumptions
        principal_reduction = payment_amount * 0.8
        interest_paid = payment_amount * 0.2
        remaining_balance = max(0, state.total_debt_owed - principal_reduction)
        
        # Emit: DebtPaymentProcessed + FundsTransferred
        payment_event = DebtPaymentProcessed(
            event_id=str(uuid.uuid4()),
            event_type="DebtPaymentProcessed",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            loan_id=loan_id,
            amount_paid=payment_amount,
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
            amount=-payment_amount,
            transaction_type="PAYMENT",
            description=f"Debt payment for {loan_id}",
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
            "campaign_type": str,  # "FLYERS", "SOCIAL_MEDIA", "NEWSPAPER_AD", "SPONSORSHIP"
            "cost": float
        }
        """
        # ! Updated to use attribute access for typed payloads
        location_id = getattr(command.payload, "location_id", None)
        campaign_type = getattr(command.payload, "campaign_type", "FLYERS")
        marketing_cost = getattr(command.payload, "cost", None)
        duration_weeks = 4  # Default duration
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if marketing_cost is None or marketing_cost < 0:
            raise InvalidStateError("Marketing cost must be positive")
            
        if marketing_cost > state.cash_balance:
            raise InsufficientFundsError("Insufficient funds for marketing")
        
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
            campaign_type=campaign_type,
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
            amount=-marketing_cost,
            transaction_type="EXPENSE",
            description=f"Marketing campaign: {campaign_type} at {location_id}",
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
