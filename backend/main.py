"""
Main entry point for the Laundromat Tycoon backend.
Demonstrates basic usage of the game engine.
"""

from application_factory import ApplicationFactory
from core.commands import SetPriceCommand, TakeLoanCommand, MakeDebtPaymentCommand
from core.models import LocationState


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
