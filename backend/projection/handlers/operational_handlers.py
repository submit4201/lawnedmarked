"""
Operational projection handlers (pricing, equipment, inventory).
"""

from copy import deepcopy
from core.models import AgentState, LocationState, MachineState, MachineStatus, MachineType
from core.events import (
    PriceSet,
    EquipmentPurchased,
    EquipmentSold,
    EquipmentRepaired,
    SuppliesAcquired,
    NewLocationOpened,
    MachineStatusChanged,
    MachineBrokenDown,
    MachineWearUpdated,
    StockoutStarted,
    StockoutEnded,
)


def handle_price_set(state: AgentState, event: PriceSet) -> AgentState:
    """Update the pricing for a service at a location."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        location.active_pricing[event.service_type] = event.new_price
    return new_state


def handle_equipment_purchased(state: AgentState, event: EquipmentPurchased) -> AgentState:
    """Add a new machine to a location."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        machine = MachineState(
            machine_id=event.machine_id,
            type=MachineType(event.machine_type) if isinstance(event.machine_type, str) else event.machine_type,
            condition=100.0,
            status=MachineStatus.OPERATIONAL,
            last_maintenance_week=state.current_week,
            loads_processed_since_service=0,
        )
        location.equipment[event.machine_id] = machine
    return new_state


def handle_equipment_sold(state: AgentState, event: EquipmentSold) -> AgentState:
    """Remove a machine from a location."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        if event.machine_id in location.equipment:
            del location.equipment[event.machine_id]
    return new_state


def handle_equipment_repaired(state: AgentState, event: EquipmentRepaired) -> AgentState:
    """Repair a machine, restoring its condition."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        if event.machine_id in location.equipment:
            machine = location.equipment[event.machine_id]
            machine.condition = event.new_condition
            machine.status = MachineStatus.OPERATIONAL
            machine.last_maintenance_week = state.current_week
            machine.loads_processed_since_service = 0
    return new_state


def handle_supplies_acquired(state: AgentState, event: SuppliesAcquired) -> AgentState:
    """Add supplies to inventory at a location."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        if event.supply_type == "detergent":
            location.inventory_detergent += event.quantity
        elif event.supply_type == "softener":
            location.inventory_softener += event.quantity
    return new_state


def handle_new_location_opened(state: AgentState, event: NewLocationOpened) -> AgentState:
    """Create a new location and attach baseline state."""
    new_state = deepcopy(state)
    new_location = LocationState(
        location_id=event.location_id,
        zone=event.zone,
        monthly_rent=event.monthly_rent,
    )
    new_state.locations[event.location_id] = new_location
    return new_state


def handle_machine_status_changed(state: AgentState, event: MachineStatusChanged) -> AgentState:
    """Update machine status (OPERATIONAL, BROKEN, IN_REPAIR)."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        if event.machine_id in location.equipment:
            machine = location.equipment[event.machine_id]
            machine.status = event.new_status
    return new_state


def handle_machine_broken_down(state: AgentState, event: MachineBrokenDown) -> AgentState:
    """Mark a machine as broken."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        if event.machine_id in location.equipment:
            machine = location.equipment[event.machine_id]
            machine.status = MachineStatus.BROKEN
    return new_state


def handle_machine_wear_updated(state: AgentState, event: MachineWearUpdated) -> AgentState:
    """Apply wear degradation to a machine and mark broken if depleted."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        if event.machine_id in location.equipment:
            machine = location.equipment[event.machine_id]
            machine.condition = event.new_condition
            machine.loads_processed_since_service = event.loads_processed_since_service
            if machine.condition <= 0:
                machine.status = MachineStatus.BROKEN
    return new_state


def handle_stockout_started(state: AgentState, event: StockoutStarted) -> AgentState:
    """Placeholder stockout handler (mechanical no-op)."""
    return deepcopy(state)


def handle_stockout_ended(state: AgentState, event: StockoutEnded) -> AgentState:
    """Placeholder stockout end handler (mechanical no-op)."""
    return deepcopy(state)


OPERATIONAL_EVENT_HANDLERS = {
    "PriceSet": handle_price_set,
    "EquipmentPurchased": handle_equipment_purchased,
    "EquipmentSold": handle_equipment_sold,
    "EquipmentRepaired": handle_equipment_repaired,
    "SuppliesAcquired": handle_supplies_acquired,
    "NewLocationOpened": handle_new_location_opened,
    "MachineStatusChanged": handle_machine_status_changed,
    "MachineBrokenDown": handle_machine_broken_down,
    "MachineWearUpdated": handle_machine_wear_updated,
    "StockoutStarted": handle_stockout_started,
    "StockoutEnded": handle_stockout_ended,
}

__all__ = [
    "OPERATIONAL_EVENT_HANDLERS",
    "handle_price_set",
    "handle_equipment_purchased",
    "handle_equipment_sold",
    "handle_equipment_repaired",
    "handle_supplies_acquired",
    "handle_new_location_opened",
    "handle_machine_status_changed",
    "handle_machine_broken_down",
    "handle_machine_wear_updated",
    "handle_stockout_started",
    "handle_stockout_ended",
]
