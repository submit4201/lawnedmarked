"""
Financial projection handlers.
"""

from copy import deepcopy
from core.models import AgentState
from core.events import (
    FundsTransferred,
    LoanTaken,
    DebtPaymentProcessed,
    MarketingBoostApplied,
    TaxLiabilityCalculated,
    MonthlyInterestAccrued,
    TaxBracketAdjusted,
    DefaultRecorded,
)


def handle_funds_transferred(state: AgentState, event: FundsTransferred) -> AgentState:
    """Adjust cash balance based on transaction type."""
    new_state = deepcopy(state)
    if event.transaction_type in ["REVENUE", "LOAN", "REFUND"]:
        new_state.cash_balance += event.amount
    elif event.transaction_type in ["EXPENSE", "PAYMENT"]:
        new_state.cash_balance -= event.amount
    else:
        raise ValueError(f"Unknown transaction type: {event.transaction_type}")
    return new_state


def handle_loan_taken(state: AgentState, event: LoanTaken) -> AgentState:
    """Record a new loan and increase outstanding debt."""
    new_state = deepcopy(state)
    new_state.total_debt_owed += event.principal
    return new_state


def handle_debt_payment_processed(state: AgentState, event: DebtPaymentProcessed) -> AgentState:
    """Reduce outstanding debt by principal reduction."""
    new_state = deepcopy(state)
    new_state.total_debt_owed -= event.principal_reduction
    return new_state


def handle_marketing_boost_applied(state: AgentState, event: MarketingBoostApplied) -> AgentState:
    """Apply marketing boost directly to social score."""
    new_state = deepcopy(state)
    new_state.social_score += event.customer_attraction_boost
    new_state.social_score = max(0.0, min(100.0, new_state.social_score))
    return new_state


def handle_tax_liability_calculated(state: AgentState, event: TaxLiabilityCalculated) -> AgentState:
    """Accrue calculated tax liability."""
    new_state = deepcopy(state)
    new_state.current_tax_liability += event.tax_amount
    return new_state


def handle_monthly_interest_accrued(state: AgentState, event: MonthlyInterestAccrued) -> AgentState:
    """Accrue interest onto outstanding debts."""
    new_state = deepcopy(state)
    new_state.total_debt_owed += event.total_interest
    return new_state


def handle_tax_bracket_adjusted(state: AgentState, event: TaxBracketAdjusted) -> AgentState:
    """Placeholder tax bracket handler (no direct state mutation yet)."""
    return deepcopy(state)


def handle_default_recorded(state: AgentState, event: DefaultRecorded) -> AgentState:
    """Record defaulted debt and penalties."""
    new_state = deepcopy(state)
    new_state.total_debt_owed += event.amount_owed + event.penalty_amount
    return new_state


FINANCIAL_EVENT_HANDLERS = {
    "FundsTransferred": handle_funds_transferred,
    "LoanTaken": handle_loan_taken,
    "DebtPaymentProcessed": handle_debt_payment_processed,
    "MarketingBoostApplied": handle_marketing_boost_applied,
    "TaxLiabilityCalculated": handle_tax_liability_calculated,
    "MonthlyInterestAccrued": handle_monthly_interest_accrued,
    "TaxBracketAdjusted": handle_tax_bracket_adjusted,
    "DefaultRecorded": handle_default_recorded,
}

__all__ = [
    "FINANCIAL_EVENT_HANDLERS",
    "handle_funds_transferred",
    "handle_loan_taken",
    "handle_debt_payment_processed",
    "handle_marketing_boost_applied",
    "handle_tax_liability_calculated",
    "handle_monthly_interest_accrued",
    "handle_tax_bracket_adjusted",
    "handle_default_recorded",
]
