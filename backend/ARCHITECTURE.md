# Backend Implementation - Architecture Document

This document provides a detailed overview of the backend structure and how it implements the rules from `rules.md`.

## 1. Separation of Concerns

The backend is organized into distinct layers that do NOT depend on each other circularly:

### Layer Hierarchy (dependencies flow downward):

```
GameEngine (Orchestration)
├── ActionRegistry (Command Dispatcher)
├── EventRegistry (Projection Dispatcher)
├── EventRepository (Event Log)
├── StateBuilder (State Reconstruction)
│   └── Projection Handlers
├── GameMaster (Narrative)
└── Judge (Consequences)
        │
        └── Core Models (AgentState, LocationState, etc.)
```

### Why This Design?

- **GameEngine** knows about registries and repository, but NOT about specific handlers
- **Registries** are abstractions—new handlers can be added without changing GameEngine
- **Repository** has no business logic—only append and load operations
- **Projection handlers** are pure functions isolated in the projection module
- **Command handlers** are pure functions isolated in the command_handlers module

## 2. Immutability & Events

### Event Design

Every event is an immutable fact:

```python
@dataclass(frozen=True)
class PriceSet(GameEvent):
    location_id: str
    service_name: str
    new_price: float
    event_type: str = "PriceSet"
```

**Key points:**
- `frozen=True` prevents any field modification after creation
- All fields are immutable (strings, floats, ints, tuples, frozen dicts)
- Nested objects (if any) must also be immutable
- Event ID, timestamp, agent_id are always included for traceability

### Event Persistence

Events are stored in the `EventRepository` in strict chronological order:

```python
# Append an event
event = PriceSet(...)
event_repository.save(event)  # Only append, never modify

# Load all events
events = event_repository.load_all()  # Returns complete log in order
```

**The repository MUST NOT:**
- Filter events
- Sort events
- Delete events
- Provide any business logic queries

## 3. Pure Command Handlers

### Command Handler Signature

```python
def handle(self, state: AgentState, command: Command) -> List[GameEvent]:
    # 1. Read state (IMMUTABLE)
    if state.cash_balance < 1000:
        raise InsufficientFundsError("Not enough cash")
    
    # 2. Return events (describe what happened)
    return [FundsTransferred(...), PriceSet(...)]
```

### Purity Constraints

Handlers **MUST:**
- ✅ Read state without modification
- ✅ Return a list of events describing outcomes
- ✅ Raise `DomainException` on validation failure
- ✅ Be deterministic (same input → same output)

Handlers **MUST NOT:**
- ❌ Mutate the input state
- ❌ Access databases, files, or external APIs
- ❌ Emit events AND then modify state
- ❌ Perform I/O operations

### Validation vs. Execution

```python
class SetPriceHandler(CommandHandler):
    def handle(self, state: AgentState, command: Command) -> List[GameEvent]:
        location_id = command.payload.get("location_id")
        new_price = command.payload.get("new_price")
        
        # VALIDATION (fails with exception, no events)
        if location_id not in state.locations:
            raise LocationNotFoundError(...)  # ❌ Stop here, no events
        
        if new_price < 0:
            raise InvalidStateError(...)  # ❌ Stop here, no events
        
        # EXECUTION (emit event)
        return [PriceSet(...)]  # ✅ Validation passed, emit fact
```

## 4. Projection Layer (State Reconstruction)

### How State is Built

1. **Start with initial state:**
```python
initial_state = AgentState(agent_id="P001", cash_balance=10000.0, ...)
```

2. **Load all events from the log:**
```python
events = event_repository.load_all()
# [TimeAdvanced, FundsTransferred, LoanTaken, DebtPaymentProcessed, ...]
```

3. **Apply events sequentially:**
```python
state = initial_state
for event in events:
    # Get the handler for this event type
    handler = event_registry.get_handler(event.event_type)
    # Apply the event: event + state → new_state
    state = handler(state, event)
```

### Example: FundsTransferred Event

```python
def handle_funds_transferred(state: AgentState, event: FundsTransferred) -> AgentState:
    """Pure reducer: event + state → new_state"""
    new_state = deepcopy(state)
    
    # Apply the fact of money movement
    if event.transaction_type in ["REVENUE", "LOAN"]:
        new_state.cash_balance += event.amount
    elif event.transaction_type in ["EXPENSE", "PAYMENT"]:
        new_state.cash_balance -= event.amount
    
    return new_state
```

### Why No Branching?

The projection layer **MUST NOT** contain any `if` statements related to game rules:

```python
# ❌ WRONG: Business logic in projection
def handle_event(state, event):
    if state.cash_balance < 5000:
        # Some special rule...
        state.credit_rating -= 5
    return state

# ✅ RIGHT: Pure application of facts
def handle_event(state, event):
    # Event contains the computed consequence
    state.credit_rating = event.new_rating
    return state
```

The rule logic is in the **Command Handler** or **Judge**, not the projection.

## 5. GameEngine Orchestration

### Command Execution Flow

```python
# Player issues command
command = SetPriceCommand(agent_id="P001", payload={...})

# Engine executes
success, events, message = game_engine.execute_command("P001", command)

# Internally:
# 1. state = get_current_state(agent_id)  # Reconstruct from log
# 2. events = action_registry.execute(state, command)  # Dispatch to handler
# 3. for event in events: event_repository.save(event)  # Persist
# 4. return success, events, message
```

### State Query

```python
# CORRECT: State is always reconstructed from events
current_state = game_engine.get_current_state(agent_id)

# The engine:
# 1. Loads all events from repository
# 2. Filters to this agent's events
# 3. Rebuilds state from scratch
# 4. Returns the current snapshot
```

### Why Reconstruct Every Time?

- **Guarantees correctness**: State is always derived from authoritative log
- **Enables auditing**: Can replay from any point in history
- **Simplifies testing**: No state caching/invalidation logic
- **Allows debugging**: "What state led to this decision?"

For performance, in production, you'd add caching/snapshots—but the principle remains: state is computed from events.

## 6. ActionRegistry (Command Dispatcher)

```python
class ActionRegistry:
    def __init__(self):
        self._handlers = {}
    
    def register(self, command_type: str, handler: CommandHandler):
        self._handlers[command_type] = handler
    
    def execute(self, state, command):
        if command.command_type not in self._handlers:
            raise KeyError(f"No handler for {command.command_type}")
        
        handler = self._handlers[command.command_type]
        return handler.handle(state, command)
```

**Benefit:** New handlers are registered without modifying GameEngine:

```python
# Can be done in application startup, or dynamically
registry.register("NEW_COMMAND", NewHandler())
# GameEngine automatically supports it—no changes needed!
```

## 7. EventRegistry (Projection Dispatcher)

```python
class EventRegistry:
    def __init__(self):
        self._handlers = {}
    
    def register(self, event_type: str, handler):
        self._handlers[event_type] = handler
    
    def apply(self, state, event):
        if event.event_type not in self._handlers:
            raise NotImplementedError(f"No handler for {event.event_type}")
        
        handler = self._handlers[event.event_type]
        return handler(state, event)
```

**Benefit:** State reconstruction works for any event, as long as a handler is registered. Adding new event types is decoupled from the StateBuilder.

## 8. GameMaster (Narrative Layer)

The GameMaster operates **outside** the main GameEngine loop:

```python
# After command execution
success, events, msg = game_engine.execute_command(agent_id, cmd)

# GameMaster evaluates world state and injects narrative events
if success:
    state = game_engine.get_current_state(agent_id)
    narrative_events = game_master.check_and_trigger_events(state)
    for event in narrative_events:
        event_repository.save(event)  # Add to log as facts
```

**Key:** The GameMaster doesn't modify state—it emits new events that become facts in the log.

### Example: Customer Review

```python
def _generate_customer_review(self, state: AgentState, location_id: str):
    location = state.locations[location_id]
    
    # Analyze: cleanliness affects review
    cleanliness = location.current_cleanliness
    rating = int(1 + (cleanliness / 100.0 * 4))
    
    # Emit fact: a customer gave this rating
    return CustomerReviewSubmitted(
        location_id=location_id,
        rating=rating,
        review_text="...",
    )
```

This event, when applied by the projection layer, becomes part of the state (can be aggregated for average rating, etc.).

## 9. Judge (Consequence Layer)

The Judge triggers **after** specific events:

```python
# Command emitted a violation-related event
if event.event_type == "PriceSet":
    state = game_engine.get_current_state(agent_id)
    
    # Judge evaluates consequences
    consequence_events = judge.evaluate_action_consequences(state, event)
    
    # Consequences become facts in the log
    for event in consequence_events:
        event_repository.save(event)
```

### Example: Predatory Pricing Penalty

```python
def _check_predatory_pricing(self, state, event):
    if event.new_price < cost_per_load * 0.8:
        # Emit consequence events
        return [
            RegulatoryFinding(fine_id=..., amount=500),
            RegulatoryStatusUpdated(new_status="WARNING"),
        ]
    return []
```

The Judge's output events are **also** facts in the log that update state.

## 10. Compliance Checklist

Using this design:

| Rule | Implementation | Status |
| --- | --- | --- |
| Event Immutability | `@dataclass(frozen=True)` on all GameEvent | ✅ |
| Pure Functions | Handlers read state, return events | ✅ |
| Single Source of Truth | EventRepository is only state source | ✅ |
| No Branching in Projections | Projection handlers apply facts only | ✅ |
| OCP | Registries allow extension without modification | ✅ |
| Modularity | Separate modules for each concern | ✅ |
| Dependency Rule | High-level (GameEngine) depends on abstractions (registries) | ✅ |
| No Direct State Access | Only via GameEngine | ✅ |
| Timestamping | All events include timestamp and week | ✅ |
| Chronological Order | StateBuilder applies events sequentially | ✅ |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│         LLM / External Interface            │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌──────────────────────────────┐
│      GameEngine              │
│  - execute_command()         │
│  - advance_time()            │
│  - get_current_state()       │
└──────────┬──────────┬────────┘
           │          │
    ┌──────▼───┐  ┌───▼──────┐
    │ Action   │  │  Event   │
    │ Registry │  │ Registry │
    │          │  │          │
    │ Cmd→Hdlr │  │ Evt→Hdlr │
    └──────┬───┘  └───┬──────┘
           │          │
     ┌─────▼──────────▼──────┐
     │ EventRepository       │
     │ - save(event)         │
     │ - load_all()          │
     │ - [event log]         │
     └─────┬─────────────────┘
           │
    ┌──────▼──────────┐
    │ StateBuilder    │
    │ - build_state() │
    └─────────────────┘

┌──────────────────────────────┐
│  GameMaster                  │
│  - check_and_trigger_events()│
│  (Narrative generation)      │
└─────────────────────────────┐
                              │
┌──────────────────────────────────┐
│  Judge                           │
│  - evaluate_consequences()       │
│  (Regulatory enforcement)        │
└──────────────────────────────────┘
```

---

## Next Implementation Steps

1. **Implement all command handlers** (26 command types from commandeventlist.md)
2. **Implement all event handlers** (60+ event types)
3. **Add database persistence** (e.g., PostgreSQL + SQLAlchemy)
4. **Add REST API layer** for LLM integration
5. **Implement full GameMaster logic** with state analysis
6. **Implement full Judge logic** with comprehensive rules
7. **Add comprehensive test suite**
8. **Performance optimization** (snapshots, caching)

---

**Author:** AI Assistant  
**Date:** December 2025  
**Status:** Foundation Layer Complete
