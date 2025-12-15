# AI Agent Instructions - Index

**Laundromat Tycoon** is an event-sourced simulation with strict architectural principles. This index guides agents to domain-specific instructions following the **modularity principle**.

## Quick Start

1. Read **[Architecture Overview](ARCHITECTURE.md)** - 3-layer design and core concepts
2. Read **[rules.md](../rules.md)** - Mandatory constraints (Event Immutability, Purity, etc.)
3. Pick your domain below 👇

## Domain-Specific Guides

| Domain | Purpose | Guide |
|--------|---------|-------|
| **Command Handlers** | Validate player intent, emit events | [AGENT_COMMANDS.md](AGENT_COMMANDS.md) |
| **Event Projections** | Apply events to state (reducers) | [AGENT_PROJECTIONS.md](AGENT_PROJECTIONS.md) |
| **Event Definitions** | Define new immutable events | [AGENT_EVENTS.md](AGENT_EVENTS.md) |
| **State Models** | AgentState, LocationState, GameState | [AGENT_STATE.md](AGENT_STATE.md) |
| **Game Engine** | Command dispatch, state reconstruction | [AGENT_ENGINE.md](AGENT_ENGINE.md) |
| **Adjudication** | GameMaster, Judge systems | [AGENT_ADJUDICATION.md](AGENT_ADJUDICATION.md) |
| **Debugging** | Troubleshooting workflow | [AGENT_DEBUGGING.md](AGENT_DEBUGGING.md) |

## Architecture Principles (TL;DR)

```
Command → Event → State
   ↓        ↓      ↓
 Validate  Immutable  Derived
 (Handler) (Log)     (Projection)
```

- **Events are facts** (frozen, immutable)
- **State is derived** (read-only state input, event list output)
- **Handlers are pure** (no side effects)
- **Registries are factories** (ActionRegistry, EventRegistry)

## Running the Backend

```bash
cd backend
python main.py  # See live Command → Event → State flow
```

## Key Constraints

✅ **DO**: Write pure handlers, validate in commands, register new types
❌ **DON'T**: Mutate state directly, add business logic to projections, modify registries
