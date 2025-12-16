"""
Game Engine - Core orchestration and command execution.
The GameEngine is the main entry point for all game logic.
It enforces the Command -> Event -> State flow.
"""

from typing import List, Tuple
from datetime import datetime
import uuid

from core.commands import Command, DomainException
from core.events import GameEvent, TimeAdvanced
from core.models import AgentState
from infrastructure.event_repository import EventRepository
from infrastructure.action_registry import ActionRegistry
from infrastructure.event_registry import EventRegistry
from projection.state_builder import StateBuilder


class GameEngine:
    """
    Main game engine orchestrating all state transitions.
    
    Responsibilities:
    - Command dispatch and validation
    - Event persistence
    - State reconstruction
    - Time management
    - Autonomous simulation triggers
    
    Design Principle: Pure orchestration, no business logic.
    All logic is delegated to handlers (Command Layer) and projections.
    """
    
    def __init__(
        self,
        event_repository: EventRepository,
        action_registry: ActionRegistry,
        event_registry: EventRegistry,
        state_builder: StateBuilder,
    ):
        """
        Initialize the game engine.
        
        Args:
            event_repository: Persistence layer for events
            action_registry: Command handler dispatcher
            event_registry: Projection handler registry
            state_builder: State reconstruction engine
        """
        self.event_repository = event_repository
        self.action_registry = action_registry
        self.event_registry = event_registry
        self.state_builder = state_builder
    
    def get_current_state(self, agent_id: str) -> AgentState:
        """
        Reconstruct the current state for an agent.
        
        This is the ONLY way to get the current state.
        All state is derived from the event log.
        
        Args:
            agent_id: The agent's ID
            
        Returns:
            The current AgentState
        """
        # Load all events
        events = self.event_repository.load_all()
        
        # Filter to only events for this agent
        agent_events = [e for e in events if isinstance(e, GameEvent) and e.agent_id == agent_id]
        
        # Build state from events (preserving agent_id)
        return self.state_builder.build_state(agent_events, agent_id=agent_id)
    
    def execute_command(
        self,
        agent_id: str,
        command: Command,
    ) -> Tuple[bool, List[GameEvent], str]:
        """
        Execute a player command.
        
        This is the main entry point for player actions.
        
        Process:
        1. Get current state for the agent
        2. Dispatch command to appropriate handler
        3. Validate and generate events
        4. Persist events to repository
        5. Return success/failure status and generated events
        
        Args:
            agent_id: The agent executing the command
            command: The command to execute
            
        Returns:
            Tuple of (success, events, message)
            - success: bool indicating if command was processed
            - events: List of generated GameEvents
            - message: Status message
        """
        # Get current state
        state = self.get_current_state(agent_id)
        
        # Validate agent matches
        if state.agent_id != agent_id:
            return False, [], f"Agent ID mismatch"
        
        # Execute command handler
        try:
            events = self.action_registry.execute(state, command)
            
            # Persist events
            for event in events:
                self.event_repository.save(event)
            
            return True, events, f"Command {command.command_type} succeeded"
            
        except DomainException as e:
            # Domain validation failure - no events emitted
            return False, [], f"Validation failed: {str(e)}"
        
        except KeyError as e:
            # Command not registered
            return False, [], f"Unknown command: {str(e)}"
        
        except Exception as e:
            # Unexpected error
            return False, [], f"Engine error: {str(e)}"
    
    def advance_time(self, agent_id: str, day: int, week: int) -> Tuple[bool, List[GameEvent]]:
        """
        Advance simulation time.
        
        This MUST be called before any autonomous simulation.
        The TimeAdvanced event is the first event of each time step.
        
        Args:
            agent_id: The agent whose time advances
            day: The new day number
            week: The new week number
            
        Returns:
            Tuple of (success, events)
        """
        event = TimeAdvanced(
            event_id=str(uuid.uuid4()),
            event_type="TimeAdvanced",
            agent_id=agent_id,
            timestamp=datetime.now(),
            week=week,
            day=day,
        )
        
        self.event_repository.save(event)
        
        return True, [event]
    
    def get_event_log(self, agent_id: str) -> List[GameEvent]:
        """
        Retrieve the complete event log for an agent.
        
        Returns:
            List of all events in chronological order
        """
        all_events = self.event_repository.load_all()
        agent_events = [e for e in all_events if isinstance(e, GameEvent) and e.agent_id == agent_id]
        return agent_events
    
    def get_registered_commands(self) -> List[str]:
        """Get list of all registered command types."""
        return self.action_registry.get_registered_commands()
    
    def get_registered_events(self) -> List[str]:
        """Get list of all registered event types."""
        return self.event_registry.get_registered_events()

    def list_agents(self) -> List[str]:
        """Return a list of agent_ids that have events in the repository."""
        events = self.event_repository.load_all()
        return sorted({e.agent_id for e in events if isinstance(e, GameEvent)})


__all__ = ["GameEngine"]
