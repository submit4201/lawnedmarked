"""
State models for the Laundromat Tycoon simulation.
These define the read-model (Projection) output.
The Projection Layer is the ONLY component authorized to mutate these structures.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class MachineType(Enum):
    """Types of laundromat equipment."""
    STANDARD_WASHER = "StandardWasher"
    INDUSTRIAL_WASHER = "IndustrialWasher"
    DELUXE_WASHER = "DeluxeWasher"
    DRYER = "Dryer"
    VENDING_MACHINE = "VendingMachine"


class MachineStatus(Enum):
    """Operational status of a machine."""
    OPERATIONAL = "OPERATIONAL"
    BROKEN = "BROKEN"
    IN_REPAIR = "IN_REPAIR"


class RegulatoryStatus(Enum):
    """Agent's regulatory oversight status."""
    NORMAL = "NORMAL"
    MONITORING = "MONITORING"
    WARNING = "WARNING"
    INVESTIGATION = "INVESTIGATION"


class VendorTier(Enum):
    """Vendor relationship tier (affects pricing and terms)."""
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3
    TIER_4 = 4


class PaymentHistoryType(Enum):
    """Payment history record types."""
    ON_TIME = "ON_TIME"
    LATE = "LATE"
    DEFAULT = "DEFAULT"


@dataclass
class MachineState:
    """Tracks a single physical washing or drying machine."""
    machine_id: str
    type: MachineType
    condition: float = 100.0  # 0.0 - 100.0
    last_maintenance_week: int = 0
    status: MachineStatus = MachineStatus.OPERATIONAL
    loads_processed_since_service: int = 0


@dataclass
class ScandalMarker:
    """Represents a persistent scandal/penalty on an agent."""
    scandal_id: str
    description: str
    severity: float  # 0.0 - 1.0
    duration_weeks: int
    decay_rate: float
    start_week: int


@dataclass
class Alliance:
    """Represents a formal alliance with a competitor."""
    alliance_id: str
    partner_agent_id: str
    alliance_type: str  # "PRICE_FIXING", "MARKET_DIVISION", etc.
    duration_weeks: int
    penalties_on_breach: float  # Monetary penalty
    start_week: int


@dataclass
class Fine:
    """Represents a fine or fee issued by the Judge/Regulator."""
    fine_id: str
    description: str
    amount: float
    issued_week: int
    due_date: int


@dataclass
class VendorRelationship:
    """Tracks the relationship with a specific supplier."""
    vendor_id: str
    tier: VendorTier = VendorTier.TIER_1
    weeks_at_tier: int = 0
    payment_history: List[PaymentHistoryType] = field(default_factory=list)
    is_exclusive_contract: bool = False
    exclusive_contract_end_week: Optional[int] = None


@dataclass
class StaffMember:
    """Represents an employee at a location."""
    staff_id: str
    staff_name: str
    role: str  # "Manager", "Attendant", "Cleaner"
    hourly_rate: float
    hired_week: int
    benefits: List[str] = field(default_factory=list)  # ["Health Insurance", "Bonus"]


@dataclass
class LocationState:
    """Tracks the physical assets and operational state of a single location."""
    location_id: str
    zone: str
    monthly_rent: float
    current_cleanliness: float = 80.0  # 0.0 - 100.0
    equipment: Dict[str, MachineState] = field(default_factory=dict)
    inventory_detergent: int = 1000  # Loads worth
    inventory_softener: int = 500  # Loads worth
    current_staff: List[StaffMember] = field(default_factory=list)
    active_pricing: Dict[str, float] = field(default_factory=lambda: {
        "StandardWash": 3.50,
        "PremiumWash": 5.00,
        "Dry": 2.00,
        "VendingItems": 1.50
    })
    vendor_relationships: Dict[str, VendorRelationship] = field(default_factory=dict)
    accumulated_revenue_week: float = 0.0
    accumulated_cogs_week: float = 0.0


@dataclass
class AgentState:
    """Tracks financial, social, and intangible assets tied to an agent."""
    agent_id: str
    current_week: int = 0
    current_day: int = 0
    cash_balance: float = 10000.0  # Starting balance
    line_of_credit_balance: float = 0.0
    line_of_credit_limit: float = 5000.0
    total_debt_owed: float = 0.0
    social_score: float = 50.0  # 0.0 - 100.0
    active_scandals: List[ScandalMarker] = field(default_factory=list)
    customer_loyalty_members: int = 0
    market_share_loads: float = 0.0  # Weekly loads processed
    current_tax_liability: float = 0.0
    regulatory_status: RegulatoryStatus = RegulatoryStatus.NORMAL
    credit_rating: int = 50  # 1 - 100
    active_alliances: List[Alliance] = field(default_factory=list)
    pending_fines: List[Fine] = field(default_factory=list)
    locations: Dict[str, LocationState] = field(default_factory=dict)
    private_notes: List[str] = field(default_factory=list)
    audit_entries_count: int = 0
    last_audit_event: str = ""


@dataclass
class GameState:
    """Top-level game state snapshot."""
    agent: AgentState
    agents: Dict[str, AgentState] = field(default_factory=dict)  # All agents (including NPCs)
