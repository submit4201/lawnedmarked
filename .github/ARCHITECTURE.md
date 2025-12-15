# Laundromat Tycoon: Architecture Overview

This document covers the three-layer event sourcing architecture and how components interact.

## Three-Layer Architecture

### 1. Command Layer (`backend/command_handlers/`)
- **Responsibility**: Validate player intent and emit events
- **Pattern**: Pure functions `(state: AgentState, command: Command) → List[GameEvent]`
- **Error Handling**: Raise domain exceptions (InsufficientFundsError, etc.) - no events emitted on failure
- **Examples**: `financial_handlers.py` (SetPrice, TakeLoan, MakeDebtPayment)

### 2. Event Sourcing Engine (`backend/engine/`)
- **EventRepository**: Immutable append-only log of all facts
- **GameEngine**: Orchestrates command dispatch + state reconstruction
- **Pattern**: Events are the ONLY source of truth
- **Guarantee**: State always reconstructed from event log in chronological order

### 3. Projection Layer (`backend/projection/`)
- **StateBuilder**: Rebuilds state by applying events sequentially
- **Projection Handlers**: Pure reducers `(state: AgentState, event: GameEvent) → AgentState`
- **Pattern**: NO business logic - only apply mechanical facts
- **Examples**: `core_handlers.py` (FundsTransferred, LoanTaken, etc.)

## Core Pipeline

```
Player Action
    ↓
CreateCommand (e.g., TakeLoanCommand)
    ↓
GameEngine.execute_command(agent_id, command)
    ↓
ActionRegistry dispatches → TakeLoanHandler.handle(state, command)
    ↓
Validation:
  ✅ Valid → Return List[GameEvent] (LoanTaken, FundsTransferred)
  ❌ Invalid → Raise DomainException (NO events saved)
    ↓
EventRepository.save(event) for each event
    ↓
StateBuilder.build_state(events) applies all events sequentially
    ↓
Return updated AgentState
```

## Data Flow

```
┌─ EventRepository (append-only log) ─┐
│  [Event1, Event2, Event3, ...]      │
│  ↑ (save)                           │
│  │                                  │
│  ├─ GameEngine.execute_command()    │
│  │   ├─ Get current state           │
│  │   ├─ ActionRegistry.execute()    │
│  │   ├─ Handler validates & emits   │
│  │   └─ Save new events             │
│  │                                  │
│  └─ StateBuilder (read)             │
│      ├─ Load all events             │
│      ├─ Apply each sequentially     │
│      └─ Return current state        │
└──────────────────────────────────────┘
```

## Registry Pattern

Two registries decouple core engine from specific handlers:

### ActionRegistry (Command → Handler)
```python
registry.register("SET_PRICE", SetPriceHandler())
registry.register("TAKE_LOAN", TakeLoanHandler())
# GameEngine calls:
events = registry.execute(state, command)  # Dispatches to correct handler
```

### EventRegistry (Event → Projection)
```python
registry.register("FundsTransferred", handle_funds_transferred)
registry.register("LoanTaken", handle_loan_taken)
# StateBuilder calls:
state = registry.apply(state, event)  # Dispatches to correct handler
```

## Modularity by Domain

Command handlers organized by business domain:
- `financial_handlers.py` - Money, loans, payments
- `operational_handlers.py` - Equipment, maintenance
- `staffing_handlers.py` - Hiring, wages, benefits
- `vendor_handlers.py` - Supplier relationships
- `social_handlers.py` - Ethics, reputation, charity
- `competition_handlers.py` - Alliances, buyouts

Same structure in projection handlers - event types grouped by domain.

## Open/Closed Principle

Adding a new command **requires no changes** to GameEngine, registries, or core:

```
New Feature Request: "UPGRADE_MACHINE"
  ↓
1. Define command in core/commands.py
2. Define events in core/events.py
3. Create handler in command_handlers/operational_handlers.py
4. Create projectors in projection/handlers/core_handlers.py
5. Export in command_handlers/__init__.py and projection/__init__.py
  ↓
GameEngine, ActionRegistry, EventRegistry unchanged ✓
ApplicationFactory auto-discovers via ALL_HANDLERS
```

## File Organization

```
backend/
├── core/
│   ├── models.py       # AgentState, LocationState, enums
│   ├── commands.py     # Command base + 26 command types
│   └── events.py       # GameEvent base + 60+ event types (frozen)
│
├── command_handlers/
│   ├── financial_handlers.py
│   ├── operational_handlers.py
│   ├── staffing_handlers.py
│   ├── vendor_handlers.py
│   ├── social_handlers.py
│   ├── competition_handlers.py
│   └── __init__.py     # Exports ALL_HANDLERS dict
│
├── projection/
│   ├── state_builder.py
│   └── handlers/
│       ├── core_handlers.py  # All event projectors
│       └── __init__.py
│
├── infrastructure/
│   ├── event_repository.py    # Immutable log
│   ├── action_registry.py     # Command dispatcher factory
│   └── event_registry.py      # Event projector factory
│
├── engine/
│   ├── game_engine.py         # Main orchestrator
│   └── autonomous_simulation.py
│
├── adjudication/
│   ├── game_master.py         # World state, narrative
│   └── judge.py               # Consequences, ethics
│
├── application_factory.py      # DI bootstrap
└── main.py                     # Demo
```
