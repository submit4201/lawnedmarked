from dataclasses import dataclass, field
from core.events import GameEvent

@dataclass(frozen=True)
class FundsTransferred(GameEvent):
    amount: float = 0.0
    transaction_type: str = ""
    description: str = ""
    event_type: str = field(default="FundsTransferred")


__all__ = [
    "PriceSet",
    "LoanTaken",
    "DebtPaymentProcessed",
    "FundsTransferred",
    "MarketingInvested",
    "TaxLiabilityCalculated",
]

@dataclass(frozen=True)
class LoanTaken(GameEvent):
    loan_id: str = ""
    principal: float = 0.0
    interest_rate: float = 0.0
    term_weeks: int = 0
    event_type: str = field(default="LoanTaken")

@dataclass(frozen=True)
class DebtPaymentProcessed(GameEvent):
    loan_id: str = ""
    payment_amount: float = 0.0
    principal_reduction: float = 0.0
    interest_paid: float = 0.0
    remaining_balance: float = 0.0
    event_type: str = field(default="DebtPaymentProcessed")

@dataclass(frozen=True)
class DefaultRecorded(GameEvent):
    loan_id: str = ""
    amount_owed: float = 0.0
    penalty_amount: float = 0.0
    event_type: str = field(default="DefaultRecorded")

@dataclass(frozen=True)
class PriceSet(GameEvent):
    location_id: str = ""
    service_type: str = ""
    new_price: float = 0.0
    event_type: str = field(default="PriceSet")

@dataclass(frozen=True)
class MarketingBoostApplied(GameEvent):
    location_id: str = ""
    marketing_cost: float = 0.0
    customer_attraction_boost: float = 0.0
    duration_weeks: int = 0
    event_type: str = field(default="MarketingBoostApplied")

@dataclass(frozen=True)
class TaxLiabilityCalculated(GameEvent):
    taxable_income: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    event_type: str = field(default="TaxLiabilityCalculated")

@dataclass(frozen=True)
class TaxBracketAdjusted(GameEvent):
    new_tax_rate: float = 0.0
    reason: str = ""
    event_type: str = field(default="TaxBracketAdjusted")
