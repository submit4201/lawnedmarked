"""Main entry point for the Laundromat Tycoon backend.

This file is the orchestrator for the full Phase 4 loop when desired:
TimeAdvanced → GM injection → autonomous tick → Judge injection → player LLM.

The existing demo remains intact; the LLM orchestration helpers are added
as standalone functions.
"""

from application_factory import ApplicationFactory
from core.commands import SetPriceCommand, TakeLoanCommand, MakeDebtPaymentCommand
from core.models import LocationState


def _normalize(name: str) -> str:
    return str(name or "").replace(" ", "_").replace("-", "_").upper()


async def run_gm_turn(agent_id: str, current_state, game_master, dispatcher, game_engine) -> list:
    """Run the GM LLM and execute its injected world event (or do nothing).

    Expected GM output:
    - Command(INJECT_WORLD_EVENT): {"source_role":"GM","event_type":"...","event_fields":{...}}
    - or <|-ENDTURN-|>
    """
    from llm.prompts import extract_command_from_text
    from llm_factory import LLMCommandFactory

    history_messages = game_master.prepare_gm_context(current_state)
    result = await dispatcher.run_gm_turn(agent_id, history_messages)
    content = (result or {}).get("content", "") or ""

    if "<|-ENDTURN-|>" in content:
        return []

    extraction = extract_command_from_text(content)
    if _normalize(extraction.command_name) != "INJECT_WORLD_EVENT":
        raise ValueError("GM must output INJECT_WORLD_EVENT or <|-ENDTURN-|>")

    command = LLMCommandFactory.from_llm(
        agent_id=agent_id,
        command_name=extraction.command_name,
        payload_json=extraction.payload_json,
    )
    success, events, message = game_engine.execute_command(agent_id, command)
    if not success:
        raise RuntimeError(f"GM inject failed: {message}")
    return events


async def run_judge_turn(agent_id: str, current_state, recent_events, judge, dispatcher, game_engine) -> list:
    """Run the Judge LLM and execute its injected consequence event (or do nothing)."""
    from llm.prompts import extract_command_from_text
    from llm_factory import LLMCommandFactory

    history_messages = judge.prepare_judge_context(current_state, recent_events)
    result = await dispatcher.run_judge_turn(agent_id, history_messages)
    content = (result or {}).get("content", "") or ""

    if "<|-ENDTURN-|>" in content:
        return []

    extraction = extract_command_from_text(content)
    if _normalize(extraction.command_name) != "INJECT_WORLD_EVENT":
        raise ValueError("Judge must output INJECT_WORLD_EVENT or <|-ENDTURN-|>")

    command = LLMCommandFactory.from_llm(
        agent_id=agent_id,
        command_name=extraction.command_name,
        payload_json=extraction.payload_json,
    )
    success, events, message = game_engine.execute_command(agent_id, command)
    if not success:
        raise RuntimeError(f"Judge inject failed: {message}")
    return events


def main():
    """
    Demonstrate the game engine in action.
    """
    print("=" * 70)
    print("Laundromat Tycoon - Event Sourcing Backend")
    print("=" * 70)
    print()
    
    # Create the game engine and subsystems
    print("[INIT] Initializing game engine...")
    game_engine, game_master, judge = ApplicationFactory.create_game_engine()
    print(f"[INIT] ✓ Game engine ready")
    print(f"[INIT] ✓ Registered commands: {len(game_engine.get_registered_commands())}")
    print(f"[INIT] ✓ Registered events: {len(game_engine.get_registered_events())}")
    print()
    
    # Create an agent
    agent_id = "PLAYER_001"
    print(f"[SETUP] Creating player agent: {agent_id}")
    
    # Get initial state
    state = game_engine.get_current_state(agent_id)
    print(f"[SETUP] ✓ Initial cash balance: ${state.cash_balance:.2f}")
    print(f"[SETUP] ✓ Initial locations: {len(state.locations)}")
    print(f"[SETUP] ✓ Initial social score: {state.social_score:.1f}")
    print()
    
    # Note: Adding location via command would require BUY_EQUIPMENT or OPEN_NEW_LOCATION
    # For demo, we'll work with what we have or just show the system is working
    
    # Execute a sample command - take loan (doesn't require a location)
    print("[CMD] Executing TAKE_LOAN command...")
    loan_command = TakeLoanCommand(
        agent_id=agent_id,
        payload={
            "principal": 5000.0,
            "interest_rate": 0.05,
            "term_weeks": 26,
        },
    )
    
    success, events, message = game_engine.execute_command(agent_id, loan_command)
    print(f"[CMD] Success: {success}")
    print(f"[CMD] Message: {message}")
    print(f"[CMD] Events generated: {len(events)}")
    for event in events:
        print(f"       - {event.event_type}: {event.event_id}")
    print()
    
    # Execute another command - make debt payment
    print("[CMD] Executing MAKE_DEBT_PAYMENT command...")
    payment_command = MakeDebtPaymentCommand(
        agent_id=agent_id,
        payload={
            "loan_id": "LOAN_001",
            "payment_amount": 500.0,
        },
    )
    
    success, events, message = game_engine.execute_command(agent_id, payment_command)
    print(f"[CMD] Success: {success}")
    print(f"[CMD] Message: {message}")
    print(f"[CMD] Events generated: {len(events)}")
    for event in events:
        print(f"       - {event.event_type}: {event.event_id}")
    print()
    
    # Check updated state
    print("[STATE] Retrieving updated state...")
    updated_state = game_engine.get_current_state(agent_id)
    print(f"[STATE] ✓ Updated cash balance: ${updated_state.cash_balance:.2f}")
    print(f"[STATE] ✓ Total debt owed: ${updated_state.total_debt_owed:.2f}")
    print()
    
    # Display event log
    print("[LOG] Complete event log:")
    events = game_engine.get_event_log(agent_id)
    print(f"[LOG] Total events: {len(events)}")
    for i, event in enumerate(events, 1):
        print(f"       {i}. {event.event_type} @ week {event.week}")
    print()
    
    # Display registered commands
    print("[REGISTRY] Available commands:")
    commands = game_engine.get_registered_commands()
    for cmd in sorted(commands):
        print(f"       - {cmd}")
    print()
    
    print("=" * 70)
    print("Backend initialization and basic tests completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
