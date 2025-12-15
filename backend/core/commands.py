"""
Command infrastructure.
Commands represent player intentions and must be validated by handlers.
Handlers are pure functions: (state, payload) -> List[GameEvent]
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from abc import ABC, abstractmethod
from core.events import GameEvent
from core.models import AgentState


@dataclass
class Command(ABC):
    """Base class for all player commands."""
    command_type: str = ""
    agent_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


class CommandHandler(ABC):
    """
    Pure function interface for command handling.
    Handlers read state immutably and return a list of events.
    
    Signature: (state: AgentState, command: Command) -> List[GameEvent]
    """
    
    @abstractmethod
    def handle(self, state: AgentState, command: Command) -> List[GameEvent]:
        """
        Validate and process a command, returning generated events.
        
        Args:
            state: Current agent state (read-only)
            command: The command being processed
            
        Returns:
            List of events describing the outcome
            
        Raises:
            DomainException: If validation fails (no events are emitted)
        """
        pass


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


# ==================== Specific Command Classes ====================

@dataclass
class SetPriceCommand(Command):
    """Player sets a price for a service."""
    command_type: str = "SET_PRICE"


@dataclass
class TakeLoanCommand(Command):
    """Player requests a loan or draws on line of credit."""
    command_type: str = "TAKE_LOAN"


@dataclass
class MakeDebtPaymentCommand(Command):
    """Player pays down debt principal and interest."""
    command_type: str = "MAKE_DEBT_PAYMENT"


@dataclass
class InvestInMarketingCommand(Command):
    """Player spends cash on a marketing campaign."""
    command_type: str = "INVEST_IN_MARKETING"


@dataclass
class BuyEquipmentCommand(Command):
    """Player purchases a machine."""
    command_type: str = "BUY_EQUIPMENT"


@dataclass
class SellEquipmentCommand(Command):
    """Player sells used equipment."""
    command_type: str = "SELL_EQUIPMENT"


@dataclass
class PerformMaintenanceCommand(Command):
    """Player schedules routine, deep, or overhaul service."""
    command_type: str = "PERFORM_MAINTENANCE"


@dataclass
class BuySuppliesCommand(Command):
    """Player orders bulk detergent or consumables."""
    command_type: str = "BUY_SUPPLIES"


@dataclass
class OpenNewLocationCommand(Command):
    """Player initiates opening a new laundromat."""
    command_type: str = "OPEN_NEW_LOCATION"


@dataclass
class FixMachineCommand(Command):
    """Player requests emergency repair of a machine."""
    command_type: str = "FIX_MACHINE"


@dataclass
class HireStaffCommand(Command):
    """Player hires an employee."""
    command_type: str = "HIRE_STAFF"


@dataclass
class FireStaffCommand(Command):
    """Player terminates an employee."""
    command_type: str = "FIRE_STAFF"


@dataclass
class AdjustStaffWageCommand(Command):
    """Player changes an employee's hourly rate."""
    command_type: str = "ADJUST_STAFF_WAGE"


@dataclass
class ProvideBenefitsCommand(Command):
    """Player implements a new staff benefit."""
    command_type: str = "PROVIDE_BENEFITS"


@dataclass
class InitiateCharityCommand(Command):
    """Player spends money on community/social projects."""
    command_type: str = "INITIATE_CHARITY"


@dataclass
class ResolveScandalCommand(Command):
    """Player spends money on PR or victim compensation."""
    command_type: str = "RESOLVE_SCANDAL"


@dataclass
class FileRegulatoryReportCommand(Command):
    """Player submits a required tax or compliance report."""
    command_type: str = "FILE_REGULATORY_REPORT"


@dataclass
class FileAppealCommand(Command):
    """Player appeals a fine or finding from the Judge."""
    command_type: str = "FILE_APPEAL"


@dataclass
class MakeEthicalChoiceCommand(Command):
    """Player records choice on a dilemma."""
    command_type: str = "MAKE_ETHICAL_CHOICE"


@dataclass
class SubscribeLoyaltyProgramCommand(Command):
    """Player initiates/subscribes to a loyalty program."""
    command_type: str = "SUBSCRIBE_LOYALTY_PROGRAM"


@dataclass
class NegotiateVendorDealCommand(Command):
    """Player initiates negotiation for custom terms."""
    command_type: str = "NEGOTIATE_VENDOR_DEAL"


@dataclass
class SignExclusiveContractCommand(Command):
    """Player locks in a vendor for specific terms."""
    command_type: str = "SIGN_EXCLUSIVE_CONTRACT"


@dataclass
class CancelVendorContractCommand(Command):
    """Player terminates an existing exclusive contract."""
    command_type: str = "CANCEL_VENDOR_CONTRACT"


@dataclass
class EnterAllianceCommand(Command):
    """Player proposes a formal alliance."""
    command_type: str = "ENTER_ALLIANCE"


@dataclass
class ProposeBuyoutCommand(Command):
    """Player offers to acquire a competitor."""
    command_type: str = "PROPOSE_BUYOUT"


@dataclass
class AcceptBuyoutOfferCommand(Command):
    """Target agent accepts an acquisition offer."""
    command_type: str = "ACCEPT_BUYOUT_OFFER"
