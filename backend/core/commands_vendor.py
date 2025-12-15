from dataclasses import dataclass
from core.commands import Command, CommandPayload
from core.command_payloads import (
    NegotiateVendorDealPayload,
    SignExclusiveContractPayload,
    CancelVendorContractPayload,
)


# Vendor domain commands

@dataclass
class NegotiateVendorDealCommand(Command):
    command_type: str = "NEGOTIATE_VENDOR_DEAL"
    payload_type: type[CommandPayload] = NegotiateVendorDealPayload


@dataclass
class SignExclusiveContractCommand(Command):
    command_type: str = "SIGN_EXCLUSIVE_CONTRACT"
    payload_type: type[CommandPayload] = SignExclusiveContractPayload


@dataclass
class CancelVendorContractCommand(Command):
    command_type: str = "CANCEL_VENDOR_CONTRACT"
    payload_type: type[CommandPayload] = CancelVendorContractPayload


__all__ = [
    "NegotiateVendorDealCommand",
    "SignExclusiveContractCommand",
    "CancelVendorContractCommand",
]