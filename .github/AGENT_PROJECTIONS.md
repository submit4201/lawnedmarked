# Event Projection Handler Development Guide

When implementing an event projection handler, remember: **projections are pure reducers with NO business logic**.

## Handler Anatomy

```python
from core.events import MyEvent
from core.models import AgentState
from copy import deepcopy

def handle_my_event(state: AgentState, event: MyEvent) -> AgentState:
    \"""
    Apply MyEvent to state.
    
    Pure reducer:
    - Read state immutably (conceptually)
    - Apply event mechanically
    - Return new/modified state
    \"""
    # Create new state (deepcopy preserves immutability semantics)
    new_state = deepcopy(state)
    
    # APPLY THE FACT (no business logic, no validation)
    new_state.cash_balance += event.amount
    new_state.timestamp = event.timestamp
    
    return new_state
```

## Critical Constraint: NO Business Logic

**WRONG** - Handler contains validation:
```python
def handle_set_price(state: AgentState, event: PriceSet) -> AgentState:
    new_state = deepcopy(state)
    
    # ❌ NO VALIDATION HERE
    if event.new_price < 0:
        raise InvalidStateError("...")  # WRONG!
    
    # ❌ NO IF/ELSE BRANCHING FOR RULES
    if state.market_condition == "RECESSION":
        new_state.max_price = event.new_price * 0.9
    else:
        new_state.max_price = event.new_price
    
    return new_state
```

**CORRECT** - Handler only applies facts:
```python
def handle_set_price(state: AgentState, event: PriceSet) -> AgentState:
    new_state = deepcopy(state)
    
    # ✅ ONLY apply the fact mechanically
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        location.active_pricing[event.service_name] = event.new_price
    
    return new_state
```

## Handler Patterns

### Pattern 1: Update Simple Field
```python
def handle_social_score_adjusted(state: AgentState, event: SocialScoreAdjusted) -> AgentState:
    new_state = deepcopy(state)
    new_state.social_score += event.adjustment
    # Clamp between 0-100 (mechanical fact, not business logic)
    new_state.social_score = max(0.0, min(100.0, new_state.social_score))
    return new_state
```

### Pattern 2: Update Nested Object
```python
def handle_price_set(state: AgentState, event: PriceSet) -> AgentState:
    new_state = deepcopy(state)
    
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        location.active_pricing[event.service_name] = event.new_price
    
    return new_state
```

### Pattern 3: Add to Collection
```python
def handle_scandal_started(state: AgentState, event: ScandalStarted) -> AgentState:
    from core.models import ScandalMarker
    
    new_state = deepcopy(state)
    
    scandal = ScandalMarker(
        scandal_id=event.scandal_id,
        description=event.description,
        severity=event.severity,
        duration_weeks=event.duration_weeks,
        decay_rate=0.1,
        start_week=state.current_week,
    )
    
    new_state.active_scandals.append(scandal)
    return new_state
```

### Pattern 4: Conditional Update (mechanical, not logic)
```python
def handle_regulatory_finding(state: AgentState, event: RegulatoryFinding) -> AgentState:
    from core.models import Fine
    
    new_state = deepcopy(state)
    
    # Mechanical application of the fact
    fine = Fine(
        fine_id=event.fine_id,
        description=event.description,
        amount=event.fine_amount,
        issued_week=state.current_week,
        due_date=event.due_date,
    )
    
    new_state.pending_fines.append(fine)
    return new_state
```

## Registration

After creating projection handlers, register them in `projection/handlers/core_handlers.py`:

```python
# core_handlers.py
CORE_EVENT_HANDLERS = {
    "TimeAdvanced": handle_time_advanced,
    "FundsTransferred": handle_funds_transferred,
    "LoanTaken": handle_loan_taken,
    "DebtPaymentProcessed": handle_debt_payment_processed,
    "SocialScoreAdjusted": handle_social_score_adjusted,
    "RegulatoryStatusUpdated": handle_regulatory_status_updated,
    "ScandalStarted": handle_scandal_started,
    "ScandalMarkerDecayed": handle_scandal_marker_decayed,
    "RegulatoryFinding": handle_regulatory_finding,
    "TaxLiabilityCalculated": handle_tax_liability_calculated,
    "PriceSet": handle_price_set,
    # Add new handlers here
}
```

The `EventRegistry` auto-discovers handlers via this dict. Every event type MUST have a handler.

## Key Rules

✅ **DO:**
- Apply events as mechanical facts
- Use deepcopy to preserve immutability semantics
- Update state fields directly within deepcopied object
- Handle missing resources gracefully (check existence before access)
- Clamp/normalize values if needed (mechanical, not rule-based)

❌ **DON'T:**
- Add business logic or validation
- Use if/else branching for game rules
- Modify the input state (always deepcopy)
- Raise exceptions (all validation is in Command Layer)
- Access EventRepository or other services
- Call other handlers

## Domain Organization

Projection handlers grouped by event domain in one central file:

**File:** `projection/handlers/core_handlers.py`

| Event Domain | Handlers |
|--------------|----------|
| Time | TimeAdvanced |
| Finance | FundsTransferred, LoanTaken, DebtPaymentProcessed, TaxLiabilityCalculated |
| State | SocialScoreAdjusted, RegulatoryStatusUpdated |
| Consequences | ScandalStarted, ScandalMarkerDecayed, RegulatoryFinding |
| Operations | PriceSet, (add more) |

As domains grow, consider splitting into separate files:
- `financial_handlers.py` - Money events
- `operational_handlers.py` - Equipment, maintenance
- `staffing_handlers.py` - Hiring, wages
- `social_handlers.py` - Ethics, reputation

Then aggregate in `__init__.py`:

```python
# projection/handlers/__init__.py
from .core_handlers import CORE_EVENT_HANDLERS
from .financial_handlers import FINANCIAL_HANDLERS
from .operational_handlers import OPERATIONAL_HANDLERS

ALL_EVENT_HANDLERS = {
    **CORE_EVENT_HANDLERS,
    **FINANCIAL_HANDLERS,
    **OPERATIONAL_HANDLERS,
}
```

## Testing Pattern

```python
from application_factory import ApplicationFactory
from core.events import MyEvent
from core.models import AgentState

# Get engine to verify projection
engine, _, _ = ApplicationFactory.create_game_engine()

# Create state manually for testing
state = AgentState(agent_id="TEST_001")
state.cash_balance = 1000.0

# Create event
event = FundsTransferred(
    event_id="e1",
    event_type="FundsTransferred",
    agent_id="TEST_001",
    timestamp=datetime.now(),
    week=0,
    amount=500.0,
    transaction_type="REVENUE",
    description="Test",
)

# Apply projection manually
from projection.handlers.core_handlers import handle_funds_transferred
new_state = handle_funds_transferred(state, event)

# Verify
assert new_state.cash_balance == 1500.0
assert state.cash_balance == 1000.0  # Original unchanged
```

## Deepcopy and Performance

For large state objects, deepcopy can be expensive. Optimization options:

### Option 1: Selective Copy (for performance-critical paths)
```python
def handle_small_update(state: AgentState, event: MyEvent) -> AgentState:
    # Instead of deepcopy entire state, construct minimal modified version
    new_state = AgentState(
        agent_id=state.agent_id,
        current_week=state.current_week,
        cash_balance=state.cash_balance + event.amount,  # Only modified field
        # Copy other fields
        line_of_credit_balance=state.line_of_credit_balance,
        # ... (remaining fields)
    )
    return new_state
```

### Option 2: Structural Sharing (Python 3.10+ dataclass frozen)
```python
from dataclasses import replace

def handle_with_replace(state: AgentState, event: MyEvent) -> AgentState:
    # dataclass.replace creates shallow copy, modifying only specified fields
    return replace(state, cash_balance=state.cash_balance + event.amount)
```

For now, deepcopy is safest and correct. Optimize only if profiling shows it's needed.

## Unhandled Events

If an event type has no handler, the StateBuilder raises `NotImplementedError`. Always register handlers for new events:

```python
# Will fail on apply if not registered
CORE_EVENT_HANDLERS = {
    "MyNewEvent": handle_my_new_event,  # Must add this
}
```
