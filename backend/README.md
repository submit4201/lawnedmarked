# Backend

## Running the Backend
# Laundromat Tycoon - Event Sourcing Backend

A comprehensive event-sourced backend for the Laundromat Tycoon simulation game, implementing the architectural principles and rules defined in `rules.md` and the state models from `state.md`.

## Architecture Overview

This backend implements a **strict Event Sourcing architecture** with clear separation of concerns:

### Core Components

1. **Command Layer** (`command_handlers/`)
   - Validates player intentions
   - Pure functions: `(state, command) -> List[GameEvent]`
   - Raises `DomainException` on validation failures (no events emitted)
   - Handlers registered in `ActionRegistry`

2. **Event Sourcing Infrastructure** (`infrastructure/`)
   - **EventRepository**: Immutable append-only event log
   - **ActionRegistry**: Command type → Handler factory and dispatcher
   - **EventRegistry**: Event type → Projection handler mapping

3. **Projection Layer** (`projection/`)
   - **StateBuilder**: Reconstructs state from event log sequentially
   - **Handlers**: Pure reducers that apply events to state
   - Only component authorized to mutate state models

4. **Game Engine** (`engine/`)
   - **GameEngine**: Main orchestrator
   - **AutonomousSimulation**: Generates engine-tick events (wear, revenue, costs)
   - Enforces Command → Event → State pipeline

5. **Adjudication Layer** (`adjudication/`)
   - **GameMaster**: World state, NPC behavior, narrative events
   - **Judge**: Consequence resolution, ethics testing, regulations
   - Operates asynchronously by reading event log

## Project Structure

```
backend/
├── core/
│   ├── models.py          # State models (AgentState, LocationState, etc.)
│   ├── events.py          # Immutable event definitions
│   ├── commands.py        # Command and handler interfaces
│   └── __init__.py
├── infrastructure/
│   ├── event_repository.py    # Event persistence (in-memory, file-based)
│   ├── action_registry.py     # Command dispatcher factory
│   ├── event_registry.py      # Projection handler registry
│   └── __init__.py
├── projection/
│   ├── state_builder.py       # State reconstruction engine
│   ├── handlers/
│   │   ├── core_handlers.py   # Core financial/admin handlers
│   │   └── __init__.py
│   └── __init__.py
├── command_handlers/
│   ├── financial_handlers.py  # SET_PRICE, TAKE_LOAN, etc.
│   ├── placeholder_handlers.py # Stubs for future handlers
│   └── __init__.py
├── engine/
│   ├── game_engine.py         # Main orchestrator
│   ├── autonomous_simulation.py # Engine-tick revenue/wear/costs
│   └── __init__.py
├── adjudication/
│   ├── game_master.py         # World state and narrative
│   ├── judge.py               # Consequences and regulations
│   └── __init__.py
├── application_factory.py     # Dependency injection and bootstrap
├── main.py                    # Entry point and demo
└── __init__.py
```

## Key Design Principles

### 1. Event Immutability
All `GameEvent` objects are frozen dataclasses. Once created, they cannot be modified.

```python
@dataclass(frozen=True)
class FundsTransferred(GameEvent):
    amount: float
    transaction_type: str
    # ...
```

### 2. Pure Functions
Command handlers and projection handlers are pure functions with no side effects.

```python
def handle(self, state: AgentState, command: Command) -> List[GameEvent]:
    # Read state immutably
    # Return new events (never mutate state)
    return [event1, event2]
```

### 3. Single Source of Truth
The `EventRepository` is the ONLY authoritative source. State is always reconstructed from events.

```python
# CORRECT: State derived from events
state = state_builder.build_state(events)

# WRONG: Direct state mutation (never do this)
state.cash_balance = 5000  # ❌ Never mutate directly
```

### 4. Projection Layer Purity
The projection layer applies events to state—NO business logic or branching.

```python
def handle_funds_transferred(state: AgentState, event: FundsTransferred) -> AgentState:
    # Pure reducer: input state + event → output state
    new_state = deepcopy(state)
    new_state.cash_balance += event.amount  # Apply fact
    return new_state
```

### 5. Open/Closed Principle
New commands or events can be added WITHOUT modifying existing code.

```python
# Add a new command handler
new_handler = MyNewHandler()
action_registry.register("MY_COMMAND", new_handler)

# The GameEngine doesn't change—it uses the registry
```

## Running the Backend

### Prerequisites
- Python 3.9+
- No external dependencies (pure Python)

### Basic Usage

```python
from application_factory import ApplicationFactory
from core.commands import SetPriceCommand

Quick start:
```bash
# Install deps
python -m pip install -r requirements.txt

# Start API server (use python -m to avoid PATH issues)
python -m uvicorn server:app --host 0.0.0.0 --port 9000

# Health check
curl http://localhost:9000/health
```

Notes:
- If port 8000 is busy, prefer port 9000.
- Endpoints: /game/turn/{agent_id}, /state/get/{agent_id}, /state/get_history/{agent_id}, /health.
state = game_engine.get_current_state("PLAYER_001")

# Execute a command
command = SetPriceCommand(
    agent_id="PLAYER_001",
    payload={
        "location_id": "LOC_001",
        "service_name": "StandardWash",
        "new_price": 4.50,
    }
)

success, events, message = game_engine.execute_command("PLAYER_001", command)

# Retrieve updated state (automatically reconstructed from events)
updated_state = game_engine.get_current_state("PLAYER_001")
```

### Run Demo

```bash
cd backend
python main.py
```

Output:
```
======================================================================
Laundromat Tycoon - Event Sourcing Backend
======================================================================

[INIT] Initializing game engine...
[INIT] ✓ Game engine ready
[INIT] ✓ Registered commands: 25
[INIT] ✓ Registered events: 40

[SETUP] Creating player agent: PLAYER_001
[SETUP] ✓ Initial cash balance: $10000.00
[SETUP] ✓ Initial locations: 0
[SETUP] ✓ Initial social score: 50.0

...
```

## Event Flow Example

### SetPrice Command Flow:

```
1. PLAYER issues SET_PRICE command
   ↓
2. GameEngine.execute_command() is called
   ├─ Gets current state from StateBuilder
   ├─ Dispatches to ActionRegistry
   ↓
3. SetPriceHandler.handle() validates and returns events
   └─ Returns [PriceSet event]
   ↓
4. GameEngine persists event to EventRepository
   ├─ EventRepository appends to immutable log
   ↓
5. Caller retrieves updated state
   └─ StateBuilder rebuilds from all events
      ├─ Applies each event sequentially
      ├─ PriceSet event updates location.active_pricing
      └─ Returns current AgentState with new pricing
```

## Command Handlers

### Implemented

- **SET_PRICE**: Set service pricing at a location
- **TAKE_LOAN**: Request a loan (validates credit rating)
- **MAKE_DEBT_PAYMENT**: Pay down debt principal
- **INVEST_IN_MARKETING**: Spend on marketing campaigns

### Placeholder (To Be Implemented)

- Operational: BUY_EQUIPMENT, SELL_EQUIPMENT, PERFORM_MAINTENANCE, etc.
- Staffing: HIRE_STAFF, FIRE_STAFF, ADJUST_STAFF_WAGE, etc.
- Social: INITIATE_CHARITY, RESOLVE_SCANDAL, FILE_REGULATORY_REPORT, etc.
- Vendor: NEGOTIATE_VENDOR_DEAL, SIGN_EXCLUSIVE_CONTRACT, etc.
- Competition: ENTER_ALLIANCE, PROPOSE_BUYOUT, etc.

## Event Handlers

### Implemented (Core)

- TimeAdvanced
- FundsTransferred
- LoanTaken, DebtPaymentProcessed
- SocialScoreAdjusted
- RegulatoryStatusUpdated
- ScandalStarted, ScandalMarkerDecayed
- RegulatoryFinding
- TaxLiabilityCalculated
- PriceSet

### To Be Implemented

Other ~60 event types from [commandeventlist.md](../commandeventlist.md)

## Extension Guide

### Adding a New Command

1. Define the command class in `core/commands.py`:
```python
@dataclass
class MyNewCommand(Command):
    command_type: str = "MY_NEW_COMMAND"
```

2. Create a handler in `command_handlers/my_handlers.py`:
```python
class MyNewHandler(CommandHandler):
    def handle(self, state: AgentState, command: Command) -> List[GameEvent]:
        # Validate
        if not valid:
            raise InvalidStateError("...")
        
        # Return events
        return [MyNewEvent(...)]
```

3. Register in `command_handlers/__init__.py`:
```python
from command_handlers.my_handlers import MyNewHandler
ALL_HANDLERS["MY_NEW_COMMAND"] = MyNewHandler()
```

The GameEngine automatically picks it up—no changes needed!

### Adding a New Event Type

1. Define the event in `core/events.py`:
```python
@dataclass(frozen=True)
class MyNewEvent(GameEvent):
    field1: str
    field2: float
    event_type: str = "MyNewEvent"
```

2. Create a projection handler in `projection/handlers/my_handlers.py`:
```python
def handle_my_new_event(state: AgentState, event: MyNewEvent) -> AgentState:
    new_state = deepcopy(state)
    # Update state based on event
    return new_state
```

3. Register in `projection/handlers/__init__.py`:
```python
MY_HANDLERS = {
    "MyNewEvent": handle_my_new_event,
}
```

## Testing

The system is designed for easy testing:

```python
def test_set_price():
    engine, _, _ = ApplicationFactory.create_game_engine()
    
    # Setup
    agent_id = "TEST_001"
    command = SetPriceCommand(...)
    
    # Execute
    success, events, msg = engine.execute_command(agent_id, command)
    
    # Verify
    assert success
    assert len(events) == 1
    assert events[0].event_type == "PriceSet"
    
    # Verify state projection
    state = engine.get_current_state(agent_id)
    assert state.locations["LOC_001"].active_pricing["StandardWash"] == 4.50
```

## Compliance with rules.md

This implementation strictly adheres to all mandatory rules:

✅ **Event Immutability** - All events are frozen dataclasses  
✅ **Pure Functions** - Handlers are pure (no side effects)  
✅ **Single Source of Truth** - EventRepository is authoritative  
✅ **No Branching in Projections** - Handlers only apply facts  
✅ **OCP** - New commands/events don't require engine changes  
✅ **Modularity** - Separate files for each domain  
✅ **Dependency Rule** - High-level modules use registries (abstractions)  
✅ **No Direct State Access** - Only via GameEngine  
✅ **Timestamping** - All events are timestamped  
✅ **Chronological Order** - Events are applied sequentially  

## Next Steps

1. **Implement remaining command handlers** (operational, staffing, social, vendor, competition)
2. **Implement remaining event handlers** for all 60+ event types
3. **Add persistence layer** (file-based or database backend)
4. **Implement adjudication triggers** in GameEngine post-command
5. **Build REST API** for LLM integration
6. **Create state snapshot export** for LLM consumption
7. **Add comprehensive test suite**

## License

Part of the Laundromat Tycoon project.
