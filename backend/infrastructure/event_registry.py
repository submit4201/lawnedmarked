"""
Event Registry - Event Type to Projection Handler Mapping.
Maps event types to their projection handlers.
The Projection Layer uses this to update state from events.
"""

from typing import Dict, Callable, List, Tuple
from core.events import GameEvent
from core.models import AgentState, LocationState


class ProjectionHandler:
    """
    Pure reducer function interface for event projection.
    Takes current state and event, returns updated state.
    
    Signature: (state: AgentState, event: GameEvent) -> AgentState
    """
    pass


class EventRegistry:
    """
    Maps event types to their projection handlers.
    Used by the Projection Layer (StateBuilder) to update state.
    """
    
    def __init__(self):
        self._handlers: Dict[str, Callable[[AgentState, GameEvent], AgentState]] = {}
    
    def register(self, event_type: str, handler: Callable) -> None:
        """
        Register a projection handler for an event type.
        
        Args:
            event_type: The event type string (e.g., "FundsTransferred")
            handler: The projection handler function
        """
        self._handlers[event_type] = handler
    
    def apply(self, state: AgentState, event: GameEvent) -> AgentState:
        """
        Apply an event to the current state.
        
        Args:
            state: Current state
            event: Event to apply
            
        Returns:
            Updated state
            
        Raises:
            NotImplementedError: If no handler is registered for this event type
        """
        event_type = event.event_type
        if event_type not in self._handlers:
            raise NotImplementedError(f"No projection handler for event type: {event_type}")
        
        handler = self._handlers[event_type]
        return handler(state, event)
    
    def is_registered(self, event_type: str) -> bool:
        """Check if an event type has a registered handler."""
        return event_type in self._handlers
    
    def get_registered_events(self) -> List[str]:
        """Return list of all registered event types."""
        return list(self._handlers.keys())


__all__ = ["EventRegistry", "ProjectionHandler"]
