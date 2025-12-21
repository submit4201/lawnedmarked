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
    
    EQUIPMENT_PRICES = {
        "StandardWasher": 1500.0,
        "IndustrialWasher": 3500.0,
        "DeluxeWasher": 2500.0,
        "Dryer": 1200.0,
        "VendingMachine": 800.0
    }
    
    def handle(self, state: AgentState, command: BuyEquipmentCommand) -> List[GameEvent]:
        """
        Validate and process equipment purchase.
        """
        from core.command_payloads import BuyEquipmentPayload
        payload: BuyEquipmentPayload = command.payload
        location_id = payload.location_id
        equipment_type = payload.equipment_type
        vendor_id = payload.vendor_id
        quantity = payload.quantity
        
        # Validation
        if not location_id:
            raise InvalidStateError("Location ID is required for equipment purchase")
            
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if quantity <= 0:
            raise InvalidStateError("Quantity must be positive")
        
        price_per_unit = self.EQUIPMENT_PRICES.get(equipment_type, 2000.0)
        total_price = price_per_unit * quantity
        
        if state.cash_balance < total_price:
            raise InsufficientFundsError(f"Insufficient funds: need ${total_price}, have ${state.cash_balance}")
        
        events = []
        for _ in range(quantity):
            # Create machine ID
            machine_id = str(uuid.uuid4())
            
            # Emit: EquipmentPurchased
            events.append(EquipmentPurchased(
                event_id=str(uuid.uuid4()),
                event_type="EquipmentPurchased",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                location_id=location_id,
                machine_id=machine_id,
                machine_type=equipment_type,
                purchase_price=price_per_unit,
            ))
        
        # Emit: FundsTransferred
        events.append(FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=-total_price,
            transaction_type="EXPENSE",
            description=f"Equipment purchase: {quantity}x {equipment_type} at {location_id} from {vendor_id}",
        ))
        
        return events


class SellEquipmentHandler(CommandHandler):
    """Handler for SELL_EQUIPMENT command."""
    
    def handle(self, state: AgentState, command: SellEquipmentCommand) -> List[GameEvent]:
        """
        Validate and process equipment sale.
        """
        from core.command_payloads import SellEquipmentPayload
        payload: SellEquipmentPayload = command.payload
        location_id = payload.location_id
        machine_id = payload.machine_id
        sale_price = payload.sale_price
        
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
    
    MAINTENANCE_COSTS = {
        "ROUTINE": 50.0,
        "DEEP_SERVICE": 150.0,
        "OVERHAUL": 500.0,
        "PREMISES_CLEANING": 100.0
    }
    
    def handle(self, state: AgentState, command: PerformMaintenanceCommand) -> List[GameEvent]:
        """
        Validate and process maintenance request.
        """
        from core.command_payloads import PerformMaintenancePayload
        payload: PerformMaintenancePayload = command.payload
        location_id = payload.location_id
        maintenance_type = payload.maintenance_type
        equipment_ids = payload.equipment_ids
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        location = state.locations[location_id]
        
        # If it's premises cleaning, it doesn't need equipment_ids
        if maintenance_type == "PREMISES_CLEANING":
            cost = self.MAINTENANCE_COSTS["PREMISES_CLEANING"]
            if state.cash_balance < cost:
                raise InsufficientFundsError(f"Insufficient funds for premises cleaning")
            
            # For now, we don't have a specific event for premises cleaning, 
            # but we can emit a FundsTransferred and maybe a custom event later.
            funds_event = FundsTransferred(
                event_id=str(uuid.uuid4()),
                event_type="FundsTransferred",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                amount=-cost,
                transaction_type="EXPENSE",
                description=f"Premises cleaning at {location_id}",
            )
            return [funds_event]

        # For equipment maintenance
        if not equipment_ids:
            raise InvalidStateError("Equipment IDs are required for machine maintenance")
        
        events = []
        total_cost = 0
        cost_per_unit = self.MAINTENANCE_COSTS.get(maintenance_type, 50.0)
        
        for machine_id in equipment_ids:
            if machine_id not in location.equipment:
                raise InvalidStateError(f"Machine {machine_id} not found at {location_id}")
            
            total_cost += cost_per_unit
            
            # Emit: EquipmentRepaired
            events.append(EquipmentRepaired(
                event_id=str(uuid.uuid4()),
                event_type="EquipmentRepaired",
                agent_id=state.agent_id,
                timestamp=datetime.now(),
                week=state.current_week,
                location_id=location_id,
                machine_id=machine_id,
                maintenance_type=maintenance_type,
                maintenance_cost=cost_per_unit,
                new_condition=100.0,
            ))
        
        if state.cash_balance < total_cost:
            raise InsufficientFundsError(f"Insufficient funds for maintenance: need ${total_cost}")
        
        # Emit: FundsTransferred
        events.append(FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=-total_cost,
            transaction_type="EXPENSE",
            description=f"Maintenance {maintenance_type} for {len(equipment_ids)} machines at {location_id}",
        ))
        
        return events


class BuySuppliesHandler(CommandHandler):
    """Handler for BUY_SUPPLIES command."""
    
    SUPPLY_PRICES = {
        "detergent": 0.50,  # per load
        "softener": 0.30,   # per load
    }
    
    def handle(self, state: AgentState, command: BuySuppliesCommand) -> List[GameEvent]:
        """
        Validate and process supplies purchase.
        """
        from core.command_payloads import BuySuppliesPayload
        payload: BuySuppliesPayload = command.payload
        location_id = payload.location_id
        supply_type = payload.supply_type
        vendor_id = payload.vendor_id
        quantity_loads = payload.quantity_loads
        
        # Validation
        if location_id not in state.locations:
            raise LocationNotFoundError(f"Location {location_id} not found")
        
        if quantity_loads <= 0:
            raise InvalidStateError("Quantity must be positive")
        
        price_per_load = self.SUPPLY_PRICES.get(supply_type, 0.40)
        total_cost = price_per_load * quantity_loads
        
        if state.cash_balance < total_cost:
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
            quantity=quantity_loads,
            cost=total_cost,
        )
        
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=-total_cost,
            transaction_type="EXPENSE",
            description=f"Supplies purchase: {quantity_loads} loads of {supply_type} at {location_id} from {vendor_id}",
        )
        
        return [supply_event, funds_event]


class OpenNewLocationHandler(CommandHandler):
    """Handler for OPEN_NEW_LOCATION command."""
    
    def handle(self, state: AgentState, command: OpenNewLocationCommand) -> List[GameEvent]:
        """
        Validate and process new location opening.
        Agent must purchase from available listings.
        """
        from core.command_payloads import OpenNewLocationPayload
        from core.events import LocationListingRemoved
        
        payload: OpenNewLocationPayload = command.payload
        zone = payload.zone
        monthly_rent = payload.monthly_rent
        setup_cost = payload.setup_cost
        
        # Validation
        if not zone:
            raise InvalidStateError("Zone must be specified")
        
        if monthly_rent <= 0 or setup_cost <= 0:
            raise InvalidStateError("Rent and setup cost must be positive")
        
        total_cost = setup_cost
        if state.cash_balance < total_cost:
            raise InsufficientFundsError(f"Insufficient funds for location setup")
        
        location_id = str(uuid.uuid4())
        events = []
        
        # Emit: NewLocationOpened
        location_event = NewLocationOpened(
            event_id=str(uuid.uuid4()),
            event_type="NewLocationOpened",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            zone=zone,
            monthly_rent=monthly_rent,
            initial_investment=setup_cost,
        )
        events.append(location_event)
        
        # Emit: FundsTransferred for setup cost
        funds_event = FundsTransferred(
            event_id=str(uuid.uuid4()),
            event_type="FundsTransferred",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            amount=-setup_cost,
            transaction_type="EXPENSE",
            description=f"New location setup: {zone}",
        )
        events.append(funds_event)
        
        return events


class FixMachineHandler(CommandHandler):
    """Handler for FIX_MACHINE command (emergency repair)."""
    
    def handle(self, state: AgentState, command: FixMachineCommand) -> List[GameEvent]:
        """
        Validate and process emergency machine repair.
        """
        from core.command_payloads import FixMachinePayload
        payload: FixMachinePayload = command.payload
        location_id = payload.location_id
        machine_id = payload.machine_id
        repair_cost = payload.maintenance_cost
        
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
            amount=-repair_cost,
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
