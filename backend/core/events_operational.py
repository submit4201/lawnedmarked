from dataclasses import dataclass, field
from core.events import GameEvent

@dataclass(frozen=True)
class EquipmentPurchased(GameEvent):
    location_id: str = ""
    machine_id: str = ""
    machine_type: str = ""
    purchase_price: float = 0.0
    event_type: str = field(default="EquipmentPurchased")

@dataclass(frozen=True)
class EquipmentSold(GameEvent):
    location_id: str = ""
    machine_id: str = ""
    sale_price: float = 0.0
    event_type: str = field(default="EquipmentSold")

@dataclass(frozen=True)
class EquipmentRepaired(GameEvent):
    location_id: str = ""
    machine_id: str = ""
    maintenance_type: str = ""
    maintenance_cost: float = 0.0
    new_condition: float = 100.0
    event_type: str = field(default="EquipmentRepaired")

@dataclass(frozen=True)
class SuppliesAcquired(GameEvent):
    location_id: str = ""
    supply_type: str = ""
    quantity: int = 0
    cost: float = 0.0
    event_type: str = field(default="SuppliesAcquired")

@dataclass(frozen=True)
class StockoutStarted(GameEvent):
    location_id: str = ""
    inventory_type: str = ""
    event_type: str = field(default="StockoutStarted")

@dataclass(frozen=True)
class StockoutEnded(GameEvent):
    location_id: str = ""
    inventory_type: str = ""
    event_type: str = field(default="StockoutEnded")

@dataclass(frozen=True)
class NewLocationOpened(GameEvent):
    location_id: str = ""
    zone: str = ""
    monthly_rent: float = 0.0
    initial_investment: float = 0.0
    event_type: str = field(default="NewLocationOpened")

@dataclass(frozen=True)
class LocationListingAdded(GameEvent):
    listing_id: str = ""
    zone: str = ""
    monthly_rent: float = 0.0
    setup_cost: float = 0.0
    description: str = ""
    event_type: str = field(default="LocationListingAdded")

@dataclass(frozen=True)
class LocationListingRemoved(GameEvent):
    listing_id: str = ""
    event_type: str = field(default="LocationListingRemoved")

@dataclass(frozen=True)
class MachineStatusChanged(GameEvent):
    location_id: str = ""
    machine_id: str = ""
    new_status: str = ""
    reason: str = ""
    event_type: str = field(default="MachineStatusChanged")


__all__ = [
    "EquipmentPurchased",
    "EquipmentSold",
    "EquipmentRepaired",
    "SuppliesAcquired",
    "StockoutStarted",
    "StockoutEnded",
    "NewLocationOpened",
    "LocationListingAdded",
    "LocationListingRemoved",
    "MachineStatusChanged",
]