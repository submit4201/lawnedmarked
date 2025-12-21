"""
Command aggregator and exceptions.
Defines base `Command` and re-exports domain command classes.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from abc import ABC, abstractmethod
from core.models import AgentState
from core.events import GameEvent
from .command_payloads import CommandPayload


@dataclass
class Command(ABC):
    """Base class for all player commands."""
    command_type: str = ""
    agent_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    payload_type: type[CommandPayload] | None = None


class CommandHandler(ABC):
    """Pure command handler interface."""

    @abstractmethod
    def handle(self, state: AgentState, command: Command) -> List[GameEvent]:
        """Validate and process a command, returning generated events."""
        raise NotImplementedError


# ==================== Domain Exceptions ====================

class DomainException(Exception):
    """Base exception for domain validation failures."""
    pass


class InsufficientFundsError(DomainException):
    """Raised when an agent lacks the cash/credit to perform an action."""
    pass


class InvalidStateError(DomainException):
    """Raised when an action is invalid for the current state."""
    pass


class LocationNotFoundError(DomainException):
    """Raised when a location doesn't exist."""
    pass


class StaffNotFoundError(DomainException):
    """Raised when staff member doesn't exist."""
    pass


class MachineNotFoundError(DomainException):
    """Raised when a machine doesn't exist."""
    pass


class InventoryError(DomainException):
    """Raised for inventory-related failures."""
    pass


class CreditError(DomainException):
    """Raised for credit/debt-related failures."""
    pass


class VendorError(DomainException):
    """Raised for vendor-related failures."""
    pass


class RegulationError(DomainException):
    """Raised for regulatory violations."""
    pass


from .commands_financial import (
    SetPriceCommand,
    TakeLoanCommand,
    MakeDebtPaymentCommand,
    InvestInMarketingCommand,
)
from .commands_operational import (
    BuyEquipmentCommand,
    SellEquipmentCommand,
    PerformMaintenanceCommand,
    BuySuppliesCommand,
    OpenNewLocationCommand,
    FixMachineCommand,
)
from .commands_staffing import (
    HireStaffCommand,
    FireStaffCommand,
    AdjustStaffWageCommand,
    ProvideBenefitsCommand,
)
from .commands_social_regulatory import (
    CommunicateToAgentCommand,
    InitiateCharityCommand,
    ResolveScandalCommand,
    FileRegulatoryReportCommand,
    FileAppealCommand,
    MakeEthicalChoiceCommand,
    SubscribeLoyaltyProgramCommand,
)
from .commands_vendor import (
    NegotiateVendorDealCommand,
    SignExclusiveContractCommand,
    CancelVendorContractCommand,
)
from .commands_competition import (
    EnterAllianceCommand,
    ProposeBuyoutCommand,
    AcceptBuyoutOfferCommand,
)

from .commands_adjudication import (
    InjectWorldEventCommand,
)


__all__ = [
    # Base
    "Command",
    "CommandHandler",
    # Exceptions
    "DomainException",
    "InsufficientFundsError",
    "InvalidStateError",
    "LocationNotFoundError",
    "StaffNotFoundError",
    "MachineNotFoundError",
    "InventoryError",
    "CreditError",
    "VendorError",
    "RegulationError",
    # Financial
    "SetPriceCommand",
    "TakeLoanCommand",
    "MakeDebtPaymentCommand",
    "InvestInMarketingCommand",
    # Operational
    "BuyEquipmentCommand",
    "SellEquipmentCommand",
    "PerformMaintenanceCommand",
    "BuySuppliesCommand",
    "OpenNewLocationCommand",
    "FixMachineCommand",
    # Staffing
    "HireStaffCommand",
    "FireStaffCommand",
    "AdjustStaffWageCommand",
    "ProvideBenefitsCommand",
    # Social/Regulatory
    "CommunicateToAgentCommand",
    "InitiateCharityCommand",
    "ResolveScandalCommand",
    "FileRegulatoryReportCommand",
    "FileAppealCommand",
    "MakeEthicalChoiceCommand",
    "SubscribeLoyaltyProgramCommand",
    # Vendor
    "NegotiateVendorDealCommand",
    "SignExclusiveContractCommand",
    "CancelVendorContractCommand",
    # Competition
    "EnterAllianceCommand",
    "ProposeBuyoutCommand",
    "AcceptBuyoutOfferCommand",
    # Adjudication
    "InjectWorldEventCommand",
]
