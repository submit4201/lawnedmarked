"""
State Builder - Reconstructs state from event log.
Applies events sequentially to build the current state snapshot.
This is the ONLY way to construct the current state.
"""

from typing import List
from copy import deepcopy
from core.models import AgentState
from core.events import GameEvent
from infrastructure.event_registry import EventRegistry


class StateBuilder:
    """
    Reconstructs the current state snapshot by applying all events
    from the event log in chronological order.
    
    Best Practice: Events MUST be applied sequentially.
    Skipping or reordering events is forbidden.
    """
    
    def __init__(self, event_registry: EventRegistry, initial_state: AgentState):
        """
        Args:
            event_registry: The EventRegistry with projection handlers
            initial_state: The initial state to build from
        """
        self.event_registry = event_registry
        self.initial_state = initial_state
    
    def build_state(self, events: List[GameEvent], agent_id: str = None) -> AgentState:
        """
        Reconstruct state by applying events sequentially.
        
        Args:
            events: List of events in chronological order
            agent_id: Optional agent ID to set on initial state
            
        Returns:
            The reconstructed state snapshot
            
        Raises:
            NotImplementedError: If an event type has no handler
        """
        # Start from the initial state
        state = deepcopy(self.initial_state)
        
        # Set agent_id if provided or if events contain it
        if agent_id:
            state.agent_id = agent_id
        elif events and len(events) > 0:
            state.agent_id = events[0].agent_id
        
        # Apply each event in order
        for event in events:
            state = self.event_registry.apply(state, event)
        
        return state
    
    def get_initial_state(self, agent_id: str) -> AgentState:
        """
        Create a fresh initial state for a new agent.
        
        Args:
            agent_id: The agent's unique identifier
            
        Returns:
            Fresh AgentState with default values
        """
        initial = deepcopy(self.initial_state)
        initial.agent_id = agent_id
        return initial


__all__ = ["StateBuilder"]
