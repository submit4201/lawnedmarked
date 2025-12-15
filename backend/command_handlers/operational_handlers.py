"""
Operational command handlers for equipment, maintenance, and supplies.
"""

from typing import List
from core.commands import (
    CommandHandler,
    Command,
    BuyEquipmentCommand,
    SellEquipmentCommand,
    PerformMaintenanceCommand,
    BuySuppliesCommand,
    OpenNewLocationCommand,
    FixMachineCommand,
    InsufficientFundsError,
    InvalidStateError,
    LocationNotFoundError,
)
from core.events import (
    GameEvent,
    EquipmentPurchased,
    EquipmentSold,
    EquipmentRepaired,
    SuppliesAcquired,
    NewLocationOpened,
    MachineStatusChanged,
    FundsTransferred,
)
from core.models import AgentState, LocationState, MachineState, MachineType, MachineStatus
from datetime import datetime
import uuid


class BuyEquipmentHandler(CommandHandler):
    """Handler for BUY_EQUIPMENT command."""
    
    def handle(self, state: AgentState, command: BuyEquipmentCommand) -> List[GameEvent]:
        """
        Validate and process equipment purchase.
        
        Payload expected:
        {
            "location_id": str,
            "machine_type": str,  # e.g., "StandardWasher", "Dryer"
            "purchase_price": float
        }
        """
        location_id = command.payload.get("location_id")
        machine_type = command.payload.get("machine_type")
        purchase_price = command.payload.get("purchase_price")
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if purchase_price <= 0:
            raise InvalidStateError("Purchase price must be positive")
        
        if state.cash_balance < purchase_price:
            raise InsufficientFundsError(f"Insufficient funds: need ${purchase_price}, have ${state.cash_balance}")
        
        # Create machine ID
        machine_id = str(uuid.uuid4())
        
        # Emit: EquipmentPurchased + FundsTransferred
        purchase_event = EquipmentPurchased(
            event_id=str(uuid.uuid4()),
            event_type="EquipmentPurchased",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            machine_id=machine_id,
            machine_type=machine_type,
            purchase_price=purchase_price,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=purchase_price,
            transaction_type="EXPENSE",
            description=f"Equipment purchase: {machine_type} at {location_id}",
        )
        
        return [purchase_event, funds_event]


class SellEquipmentHandler(CommandHandler):
    """Handler for SELL_EQUIPMENT command."""
    
    def handle(self, state: AgentState, command: SellEquipmentCommand) -> List[GameEvent]:
        """
        Validate and process equipment sale.
        
        Payload expected:
        {
            "location_id": str,
            "machine_id": str,
            "sale_price": float
        }
        """
        location_id = command.payload.get("location_id")
        machine_id = command.payload.get("machine_id")
        sale_price = command.payload.get("sale_price")
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        location = state.locations[location_id]
        if machine_id not in location.equipment:
            raise InvalidStateError(f"Machine {machine_id} not found at {location_id}")
        
        if sale_price < 0:
            raise InvalidStateError("Sale price cannot be negative")
        
        # Emit: EquipmentSold + FundsTransferred
        sale_event = EquipmentSold(
            event_id=str(uuid.uuid4()),
            event_type="EquipmentSold",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            machine_id=machine_id,
            sale_price=sale_price,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=sale_price,
            transaction_type="REVENUE",
            description=f"Equipment sale: {machine_id} from {location_id}",
        )
        
        return [sale_event, funds_event]


class PerformMaintenanceHandler(CommandHandler):
    """Handler for PERFORM_MAINTENANCE command."""
    
    def handle(self, state: AgentState, command: PerformMaintenanceCommand) -> List[GameEvent]:
        """
        Validate and process maintenance request.
        
        Payload expected:
        {
            "location_id": str,
            "machine_id": str,
            "maintenance_type": str,  # "Routine", "Deep", "Overhaul"
            "cost": float
        }
        """
        location_id = command.payload.get("location_id")
        machine_id = command.payload.get("machine_id")
        maintenance_type = command.payload.get("maintenance_type", "Routine")
        cost = command.payload.get("cost")
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        location = state.locations[location_id]
        if machine_id not in location.equipment:
            raise InvalidStateError(f"Machine {machine_id} not found")
        
        if cost <= 0:
            raise InvalidStateError("Maintenance cost must be positive")
        
        if state.cash_balance < cost:
            raise InsufficientFundsError(f"Insufficient funds for maintenance")
        
        # Emit: EquipmentRepaired + FundsTransferred
        repair_event = EquipmentRepaired(
            event_id=str(uuid.uuid4()),
            event_type="EquipmentRepaired",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            machine_id=machine_id,
            maintenance_type=maintenance_type,
            cost=cost,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=cost,
            transaction_type="EXPENSE",
            description=f"Maintenance {maintenance_type}: {machine_id} at {location_id}",
        )
        
        return [repair_event, funds_event]


class BuySuppliesHandler(CommandHandler):
    """Handler for BUY_SUPPLIES command."""
    
    def handle(self, state: AgentState, command: BuySuppliesCommand) -> List[GameEvent]:
        """
        Validate and process supplies purchase.
        
        Payload expected:
        {
            "location_id": str,
            "supply_type": str,  # "detergent", "softener"
            "quantity": int,
            "cost": float
        }
        """
        location_id = command.payload.get("location_id")
        supply_type = command.payload.get("supply_type")
        quantity = command.payload.get("quantity")
        cost = command.payload.get("cost")
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if quantity <= 0:
            raise InvalidStateError("Quantity must be positive")
        
        if cost <= 0:
            raise InvalidStateError("Cost must be positive")
        
        if state.cash_balance < cost:
            raise InsufficientFundsError(f"Insufficient funds for supplies")
        
        # Emit: SuppliesAcquired + FundsTransferred
        supply_event = SuppliesAcquired(
            event_id=str(uuid.uuid4()),
            event_type="SuppliesAcquired",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            supply_type=supply_type,
            quantity=quantity,
            cost=cost,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=cost,
            transaction_type="EXPENSE",
            description=f"Supplies purchase: {quantity} units of {supply_type}",
        )
        
        return [supply_event, funds_event]


class OpenNewLocationHandler(CommandHandler):
    """Handler for OPEN_NEW_LOCATION command."""
    
    def handle(self, state: AgentState, command: OpenNewLocationCommand) -> List[GameEvent]:
        """
        Validate and process new location opening.
        
        Payload expected:
        {
            "zone": str,
            "monthly_rent": float,
            "setup_cost": float
        }
        """
        zone = command.payload.get("zone")
        monthly_rent = command.payload.get("monthly_rent")
        setup_cost = command.payload.get("setup_cost")
        
        # Validation
        if not zone:
            raise InvalidStateError("Zone must be specified")
        
        if monthly_rent <= 0 or setup_cost <= 0:
            raise InvalidStateError("Rent and setup cost must be positive")
        
        total_cost = setup_cost
        if state.cash_balance < total_cost:
            raise InsufficientFundsError(f"Insufficient funds for location setup")
        
        location_id = str(uuid.uuid4())
        
        # Emit: NewLocationOpened + FundsTransferred
        location_event = NewLocationOpened(
            event_id=str(uuid.uuid4()),
            event_type="NewLocationOpened",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            zone=zone,
            monthly_rent=monthly_rent,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=setup_cost,
            transaction_type="EXPENSE",
            description=f"New location setup: {zone}",
        )
        
        return [location_event, funds_event]


class FixMachineHandler(CommandHandler):
    """Handler for FIX_MACHINE command (emergency repair)."""
    
    def handle(self, state: AgentState, command: FixMachineCommand) -> List[GameEvent]:
        """
        Validate and process emergency machine repair.
        
        Payload expected:
        {
            "location_id": str,
            "machine_id": str,
            "repair_cost": float
        }
        """
        location_id = command.payload.get("location_id")
        machine_id = command.payload.get("machine_id")
        repair_cost = command.payload.get("repair_cost")
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        location = state.locations[location_id]
        if machine_id not in location.equipment:
            raise InvalidStateError(f"Machine {machine_id} not found")
        
        if repair_cost <= 0:
            raise InvalidStateError("Repair cost must be positive")
        
        if state.cash_balance < repair_cost:
            raise InsufficientFundsError(f"Insufficient funds for emergency repair")
        
        # Emit: MachineStatusChanged + FundsTransferred
        status_event = MachineStatusChanged(
            event_id=str(uuid.uuid4()),
            event_type="MachineStatusChanged",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            machine_id=machine_id,
            new_status=MachineStatus.OPERATIONAL,
            reason="Emergency repair completed",
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=repair_cost,
            transaction_type="EXPENSE",
            description=f"Emergency repair: {machine_id} at {location_id}",
        )
        
        return [status_event, funds_event]


OPERATIONAL_HANDLERS = {
    "BUY_EQUIPMENT": BuyEquipmentHandler(),
    "SELL_EQUIPMENT": SellEquipmentHandler(),
    "PERFORM_MAINTENANCE": PerformMaintenanceHandler(),
    "BUY_SUPPLIES": BuySuppliesHandler(),
    "OPEN_NEW_LOCATION": OpenNewLocationHandler(),
    "FIX_MACHINE": FixMachineHandler(),
}

__all__ = ["OPERATIONAL_HANDLERS"]
