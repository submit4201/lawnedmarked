"""LLM Command Factory/Mapper.

Maps LLM tool-call outputs (command_name + payload) into Command instances
that the GameEngine can execute.
"""

from dataclasses import asdict
from typing import Any, Dict, Type

from core.commands import (
    Command,
    SetPriceCommand,
    TakeLoanCommand,
    MakeDebtPaymentCommand,
    InvestInMarketingCommand,
    BuyEquipmentCommand,
    SellEquipmentCommand,
    PerformMaintenanceCommand,
    BuySuppliesCommand,
    OpenNewLocationCommand,
    FixMachineCommand,
    HireStaffCommand,
    FireStaffCommand,
    AdjustStaffWageCommand,
    ProvideBenefitsCommand,
    InitiateCharityCommand,
    ResolveScandalCommand,
    FileRegulatoryReportCommand,
    FileAppealCommand,
    MakeEthicalChoiceCommand,
    SubscribeLoyaltyProgramCommand,
    NegotiateVendorDealCommand,
    SignExclusiveContractCommand,
    CancelVendorContractCommand,
    EnterAllianceCommand,
    ProposeBuyoutCommand,
    AcceptBuyoutOfferCommand,
)

# Commands that are user-facing in the LLM
_COMMAND_CLASSES = [
    SetPriceCommand,
    TakeLoanCommand,
    MakeDebtPaymentCommand,
    InvestInMarketingCommand,
    BuyEquipmentCommand,
    SellEquipmentCommand,
    PerformMaintenanceCommand,
    BuySuppliesCommand,
    OpenNewLocationCommand,
    FixMachineCommand,
    HireStaffCommand,
    FireStaffCommand,
    AdjustStaffWageCommand,
    ProvideBenefitsCommand,
    InitiateCharityCommand,
    ResolveScandalCommand,
    FileRegulatoryReportCommand,
    FileAppealCommand,
    MakeEthicalChoiceCommand,
    SubscribeLoyaltyProgramCommand,
    NegotiateVendorDealCommand,
    SignExclusiveContractCommand,
    CancelVendorContractCommand,
    EnterAllianceCommand,
    ProposeBuyoutCommand,
    AcceptBuyoutOfferCommand,
]


def _normalize(name: str) -> str:
    return name.replace(" ", "_").replace("-", "_").upper()


# Build registry mapping normalized names to command classes
COMMAND_REGISTRY: Dict[str, Type[Command]] = {}
for cls in _COMMAND_CLASSES:
    # primary key: command_type
    command_type = _normalize(getattr(cls, "command_type", cls.__name__))
    COMMAND_REGISTRY.setdefault(command_type, cls)
    # alias: class name without Command suffix
    alias = cls.__name__.removesuffix("Command")
    COMMAND_REGISTRY.setdefault(_normalize(alias), cls)


class LLMCommandFactory:
    @staticmethod
    def from_llm(agent_id: str, command_name: str, **kwargs) -> Command:
        if not command_name:
            raise ValueError("command_name is required")
        if kwargs:
            print(f"LLMCommandFactory.from_llm: payload={kwargs}")
        key = _normalize(command_name)
        if key not in COMMAND_REGISTRY:
            raise ValueError(f"Unknown command_name '{command_name}'")
        cmd_cls = COMMAND_REGISTRY[key]
        if kwargs.get("payload_json"):
            # Support payload_json key for raw JSON payloads
            import json

            kwargs = json.loads(kwargs["payload_json"])
        payload_data = kwargs or {}
        payload_type = getattr(cmd_cls, "payload_type", None)
        if payload_type:
            payload_obj = payload_type(**payload_data)
            payload_data = asdict(payload_obj)

        return cmd_cls(agent_id=agent_id, payload=payload_data)


__all__ = ["LLMCommandFactory", "COMMAND_REGISTRY"]
