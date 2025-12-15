from dataclasses import dataclass
from core.commands import Command, CommandPayload
from core.command_payloads import (
    BuyEquipmentPayload,
    SellEquipmentPayload,
    PerformMaintenancePayload,
    BuySuppliesPayload,
    OpenNewLocationPayload,
    FixMachinePayload,
)


# Operational domain commands

@dataclass
class BuyEquipmentCommand(Command):
    command_type: str = "BUY_EQUIPMENT"
    payload_type: type[CommandPayload] = BuyEquipmentPayload


@dataclass
class SellEquipmentCommand(Command):
    command_type: str = "SELL_EQUIPMENT"
    payload_type: type[CommandPayload] = SellEquipmentPayload


@dataclass
class PerformMaintenanceCommand(Command):
    command_type: str = "PERFORM_MAINTENANCE"
    payload_type: type[CommandPayload] = PerformMaintenancePayload


@dataclass
class BuySuppliesCommand(Command):
    command_type: str = "BUY_SUPPLIES"
    payload_type: type[CommandPayload] = BuySuppliesPayload


@dataclass
class OpenNewLocationCommand(Command):
    command_type: str = "OPEN_NEW_LOCATION"
    payload_type: type[CommandPayload] = OpenNewLocationPayload


@dataclass
class FixMachineCommand(Command):
    command_type: str = "FIX_MACHINE"
    payload_type: type[CommandPayload] = FixMachinePayload


__all__ = [
    "BuyEquipmentCommand",
    "SellEquipmentCommand",
    "PerformMaintenanceCommand",
    "BuySuppliesCommand",
    "OpenNewLocationCommand",
    "FixMachineCommand",
]