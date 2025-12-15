# Command Handler Development Guide

When implementing a new command handler, follow these patterns strictly.

## Handler Anatomy

```python
from core.commands import CommandHandler, Command, InsufficientFundsError, InvalidStateError
from core.models import AgentState
from core.events import GameEvent
from typing import List
from datetime import datetime
import uuid

class MyCommandHandler(CommandHandler):
    """
    Validate and process MY_COMMAND action.
    
    Payload expected:
    {
        "field_name": value,
        "another_field": value,
    }
    """
    
    def handle(self, state: AgentState, command: Command) -> List[GameEvent]:
        # PHASE 1: EXTRACT
        field_name = command.payload.get("field_name")
        
        # PHASE 2: VALIDATE
        if not self._is_valid_state(state):
            raise InvalidStateError("Required state missing")
        
        if field_name > 100:
            raise InvalidStateError("Field exceeds max value")
        
        if field_name < 0:
            raise InvalidStateError("Field must be positive")
        
        # PHASE 3: COMPUTE
        new_event = MyEvent(
            event_id=str(uuid.uuid4()),
            event_type="MyEvent",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            field_value=field_name,
        )
        
        # PHASE 4: EMIT
        return [new_event]  # Can emit 0+ events
    
    def _is_valid_state(self, state: AgentState) -> bool:
        """Helper for state validation."""
        return (
            state.agent_id and
            state.current_week >= 0
        )
```

## Validation Exceptions

Use domain-specific exceptions to reject invalid commands (no events emitted):

| Exception | When to Use | Example |
|-----------|------------|---------|
| `InsufficientFundsError` | Agent lacks cash/credit | `if state.cash_balance < amount: raise...` |
| `InvalidStateError` | Invalid parameter or missing resource | `if new_price < 0: raise...` |
| `CreditError` | Agent credit rating too low | `if state.credit_rating < 30: raise...` |
| `LocationNotFoundError` | Location ID doesn't exist | `if location_id not in state.locations: raise...` |

**Critical:** If validation fails, raise exception and return nothing. The handler must not emit any events on error.

## Pattern: Single Command → Multiple Events

A handler often emits related events to completely describe the transaction:

**Example: TAKE_LOAN (2 events)**
```python
def handle(self, state: AgentState, command: TakeLoanCommand) -> List[GameEvent]:
    principal = command.payload.get("principal")
    
    # Validate credit
    if state.credit_rating < 30:
        raise CreditError("Credit rating too low")
    
    # Emit two atomic facts
    loan_event = LoanTaken(
        event_id=str(uuid.uuid4()),
        event_type="LoanTaken",
        agent_id=state.agent_id,
        timestamp=datetime.now(),
        week=state.current_week,
        loan_id=str(uuid.uuid4()),
        principal=principal,
        interest_rate=0.05,
        term_weeks=26,
    )
    
    funds_event = FundsTransferred(
        event_id=str(uuid.uuid4()),
        event_type="FundsTransferred",
        agent_id=state.agent_id,
        timestamp=datetime.now(),
        week=state.current_week,
        amount=principal,
        transaction_type="LOAN",
        description=f"Loan disbursement",
    )
    
    return [loan_event, funds_event]
```

The StateBuilder applies both events sequentially, ensuring consistent state projection.

## Registration

After creating a handler, export it in `command_handlers/__init__.py`:

```python
from .financial_handlers import (
    SetPriceHandler,
    TakeLoanHandler,
    MakeDebtPaymentHandler,
)
from .operational_handlers import BuyEquipmentHandler

ALL_HANDLERS = {
    "SET_PRICE": SetPriceHandler(),
    "TAKE_LOAN": TakeLoanHandler(),
    "MAKE_DEBT_PAYMENT": MakeDebtPaymentHandler(),
    "BUY_EQUIPMENT": BuyEquipmentHandler(),
}
```

The `ApplicationFactory` auto-discovers handlers via `ALL_HANDLERS`. No changes to GameEngine needed.

## Key Rules

✅ **DO:**
- Read state immutably (don't mutate)
- Validate all inputs and state preconditions
- Return list of events (can be empty, 1, or many)
- Raise domain exceptions on invalid commands
- Use consistent event_id, agent_id, timestamp, week

❌ **DON'T:**
- Mutate the state object
- Call other handlers or make side effects
- Emit events on validation failure
- Create events without required fields (will fail dataclass validation)
- Modify EventRepository directly

## Domain Organization

Handlers grouped by business domain:

| File | Domain | Commands |
|------|--------|----------|
| `financial_handlers.py` | Finance | SET_PRICE, TAKE_LOAN, MAKE_DEBT_PAYMENT, INVEST_IN_MARKETING |
| `operational_handlers.py` | Equipment | BUY_EQUIPMENT, SELL_EQUIPMENT, PERFORM_MAINTENANCE, FIX_MACHINE |
| `staffing_handlers.py` | Employees | HIRE_STAFF, FIRE_STAFF, ADJUST_STAFF_WAGE, PROVIDE_BENEFITS |
| `vendor_handlers.py` | Suppliers | NEGOTIATE_VENDOR_DEAL, SIGN_EXCLUSIVE_CONTRACT, CANCEL_VENDOR_CONTRACT |
| `social_handlers.py` | Ethics/Reputation | INITIATE_CHARITY, RESOLVE_SCANDAL, MAKE_ETHICAL_CHOICE, FILE_REGULATORY_REPORT |
| `competition_handlers.py` | Competition | ENTER_ALLIANCE, PROPOSE_BUYOUT, ACCEPT_BUYOUT_OFFER |

Create new domain files as needed - don't dump everything into one file.

## Testing Pattern

```python
# In test file or main.py
from application_factory import ApplicationFactory
from core.commands import MyCommand

engine, _, _ = ApplicationFactory.create_game_engine()

# Setup
agent_id = "TEST_001"
state = engine.get_current_state(agent_id)

# Execute
command = MyCommand(
    agent_id=agent_id,
    payload={"field": "value"}
)

success, events, message = engine.execute_command(agent_id, command)

# Verify
assert success == True
assert len(events) == 2
assert events[0].event_type == "MyEvent"

# Check state projection
updated_state = engine.get_current_state(agent_id)
assert updated_state.field == expected_value
```

## Common Patterns

### Pattern 1: Conditional Multi-Event Emission
```python
events = []

if condition_1:
    events.append(Event1(...))

if condition_2:
    events.append(Event2(...))
    
return events  # 0, 1, or 2 events
```

### Pattern 2: Computed Fields
```python
# Validate input
amount = command.payload.get("amount")
if amount <= 0:
    raise InvalidStateError("Amount must be positive")

# Compute derived value
cost = amount * state.market_price

# Validate computed value
if cost > state.cash_balance:
    raise InsufficientFundsError("Cannot afford")

# Emit with computed value
return [MyEvent(..., cost=cost)]
```

### Pattern 3: Atomicity via Multiple Events
```python
# A single logical action produces multiple atomic facts
# This ensures the projection layer has all detail to reconstruct correctly

event1 = ResourceAcquired(...)  # Records what was acquired
event2 = FundsTransferred(...)  # Records the payment
event3 = InventoryUpdated(...)  # Records inventory change

return [event1, event2, event3]
```

All three events are applied to state sequentially by StateBuilder.
