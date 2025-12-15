from dataclasses import dataclass
from core.commands import Command, CommandPayload
from core.command_payloads import (
    EnterAlliancePayload,
    ProposeBuyoutPayload,
    AcceptBuyoutOfferPayload,
)


# Competition domain commands

@dataclass
class EnterAllianceCommand(Command):
    command_type: str = "ENTER_ALLIANCE"
    payload_type: type[CommandPayload] = EnterAlliancePayload


@dataclass
class ProposeBuyoutCommand(Command):
    command_type: str = "PROPOSE_BUYOUT"
    payload_type: type[CommandPayload] = ProposeBuyoutPayload


@dataclass
class AcceptBuyoutOfferCommand(Command):
    command_type: str = "ACCEPT_BUYOUT_OFFER"
    payload_type: type[CommandPayload] = AcceptBuyoutOfferPayload


__all__ = [
    "EnterAllianceCommand",
    "ProposeBuyoutCommand",
    "AcceptBuyoutOfferCommand",
]