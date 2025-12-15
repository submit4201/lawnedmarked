from dataclasses import dataclass
from core.commands import Command, CommandPayload
from core.command_payloads import (
    HireStaffPayload,
    FireStaffPayload,
    AdjustStaffWagePayload,
    ProvideBenefitsPayload,
)


# Staffing domain commands

@dataclass
class HireStaffCommand(Command):
    command_type: str = "HIRE_STAFF"
    payload_type: type[CommandPayload] = HireStaffPayload


@dataclass
class FireStaffCommand(Command):
    command_type: str = "FIRE_STAFF"
    payload_type: type[CommandPayload] = FireStaffPayload


@dataclass
class AdjustStaffWageCommand(Command):
    command_type: str = "ADJUST_STAFF_WAGE"
    payload_type: type[CommandPayload] = AdjustStaffWagePayload


@dataclass
class ProvideBenefitsCommand(Command):
    command_type: str = "PROVIDE_BENEFITS"
    payload_type: type[CommandPayload] = ProvideBenefitsPayload


__all__ = [
    "HireStaffCommand",
    "FireStaffCommand",
    "AdjustStaffWageCommand",
    "ProvideBenefitsCommand",
]