"""
Application Factory and Bootstrap.
Initializes all components and wires them together.
"""

from core.models import AgentState
from infrastructure.event_repository import InMemoryEventRepository, EventRepository
from infrastructure.action_registry import ActionRegistry
from infrastructure.event_registry import EventRegistry
from projection.state_builder import StateBuilder
from projection.handlers.core_handlers import CORE_EVENT_HANDLERS
from command_handlers import ALL_HANDLERS
from engine.game_engine import GameEngine
from adjudication.game_master import GameMaster
from adjudication.judge import Judge


class ApplicationFactory:
    """
    Factory for creating and configuring the complete game application.
    
    Follows the principle of Dependency Injection:
    All components are created and wired together in a single place.
    """
    
    @staticmethod
    def create_game_engine(
        event_repository: EventRepository = None,
    ) -> tuple:
        """
        Create and initialize a complete game engine with all subsystems.
        
        Args:
            event_repository: Optional custom repository. Defaults to InMemory.
            
        Returns:
            Tuple of (game_engine, game_master, judge)
        """
        # Use default repository if not provided
        if event_repository is None:
            event_repository = InMemoryEventRepository()
        
        # Create registries
        action_registry = ActionRegistry()
        event_registry = EventRegistry()
        
        # Register all command handlers
        ApplicationFactory._register_command_handlers(action_registry)
        
        # Register all event projection handlers
        ApplicationFactory._register_event_handlers(event_registry)
        
        # Create state builder
        initial_state = AgentState(agent_id="TEMPLATE")
        state_builder = StateBuilder(event_registry, initial_state)
        
        # Create game engine
        game_engine = GameEngine(
            event_repository=event_repository,
            action_registry=action_registry,
            event_registry=event_registry,
            state_builder=state_builder,
        )
        
        # Create adjudication subsystems
        game_master = GameMaster(event_repository)
        judge = Judge(event_repository)
        
        return game_engine, game_master, judge
    
    @staticmethod
    def _register_command_handlers(registry: ActionRegistry) -> None:
        """Register all command handlers with the ActionRegistry."""
        for command_type, handler in ALL_HANDLERS.items():
            registry.register(command_type, handler)
    
    @staticmethod
    def _register_event_handlers(registry: EventRegistry) -> None:
        """Register all event projection handlers with the EventRegistry."""
        for event_type, handler in CORE_EVENT_HANDLERS.items():
            registry.register(event_type, handler)


__all__ = ["ApplicationFactory"]
