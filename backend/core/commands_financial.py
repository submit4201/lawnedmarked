from dataclasses import dataclass
from core.commands import Command, CommandPayload
from core.command_payloads import (
    SetPricePayload,
    TakeLoanPayload,
    MakeDebtPaymentPayload,
    InvestInMarketingPayload,
)


# Financial domain commands

@dataclass
class SetPriceCommand(Command):
    command_type: str = "SET_PRICE"
    payload_type: type[CommandPayload] = SetPricePayload


@dataclass
class TakeLoanCommand(Command):
    command_type: str = "TAKE_LOAN"
    payload_type: type[CommandPayload] = TakeLoanPayload


@dataclass
class MakeDebtPaymentCommand(Command):
    command_type: str = "MAKE_DEBT_PAYMENT"
    payload_type: type[CommandPayload] = MakeDebtPaymentPayload


@dataclass
class InvestInMarketingCommand(Command):
    command_type: str = "INVEST_IN_MARKETING"
    payload_type: type[CommandPayload] = InvestInMarketingPayload


__all__ = [
    "SetPriceCommand",
    "TakeLoanCommand",
    "MakeDebtPaymentCommand",
    "InvestInMarketingCommand",
]