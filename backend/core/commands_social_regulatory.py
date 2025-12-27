from dataclasses import dataclass
from core.commands import Command, CommandPayload
from core.command_payloads import (
    InitiateCharityPayload,
    ResolveScandalPayload,
    FileRegulatoryReportPayload,
    FileAppealPayload,
    MakeEthicalChoicePayload,
    SubscribeLoyaltyProgramPayload,
    CommunicateToAgentPayload,
)


# Social & Regulatory domain commands

@dataclass
class CommunicateToAgentCommand(Command):
    command_type: str = "COMMUNICATE_TO_AGENT"
    payload_type: type[CommandPayload] = CommunicateToAgentPayload


@dataclass
class InitiateCharityCommand(Command):
    command_type: str = "INITIATE_CHARITY"
    payload_type: type[CommandPayload] = InitiateCharityPayload


@dataclass
class ResolveScandalCommand(Command):
    command_type: str = "RESOLVE_SCANDAL"
    payload_type: type[CommandPayload] = ResolveScandalPayload


@dataclass
class FileRegulatoryReportCommand(Command):
    command_type: str = "FILE_REGULATORY_REPORT"
    payload_type: type[CommandPayload] = FileRegulatoryReportPayload


@dataclass
class FileAppealCommand(Command):
    command_type: str = "FILE_APPEAL"
    payload_type: type[CommandPayload] = FileAppealPayload


@dataclass
class MakeEthicalChoiceCommand(Command):
    command_type: str = "MAKE_ETHICAL_CHOICE"
    payload_type: type[CommandPayload] = MakeEthicalChoicePayload


@dataclass
class SubscribeLoyaltyProgramCommand(Command):
    command_type: str = "SUBSCRIBE_LOYALTY_PROGRAM"
    payload_type: type[CommandPayload] = SubscribeLoyaltyProgramPayload


__all__ = [
    "CommunicateToAgentCommand",
    "InitiateCharityCommand",
    "ResolveScandalCommand",
    "FileRegulatoryReportCommand",
    "FileAppealCommand",
    "MakeEthicalChoiceCommand",
    "SubscribeLoyaltyProgramCommand",
]