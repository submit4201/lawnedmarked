"""
Event Repository - The immutable event log.
This is the ONLY source of truth for all state changes.
It exposes only save() and load_all(), with NO filtering or business logic.
"""

from typing import List
from abc import ABC, abstractmethod
import json
from pathlib import Path
from datetime import datetime
from core.events import GameEvent


class EventRepository(ABC):
    """Abstract interface for event persistence."""
    
    @abstractmethod
    def save(self, event: GameEvent) -> None:
        """
        Append an immutable event to the log.
        This is the ONLY write operation allowed.
        
        Args:
            event: The GameEvent to persist
        """
        pass
    
    @abstractmethod
    def load_all(self) -> List[GameEvent]:
        """
        Load all events from the log in chronological order.
        This is the ONLY read operation allowed.
        
        Returns:
            Complete list of all events in order
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all events (for testing only)."""
        pass


class InMemoryEventRepository(EventRepository):
    """
    Simple in-memory implementation for development and testing.
    NOT suitable for production.
    """
    
    def __init__(self):
        self._events: List[GameEvent] = []
    
    def save(self, event: GameEvent) -> None:
        """Append event to in-memory list."""
        self._events.append(event)
    
    def load_all(self) -> List[GameEvent]:
        """Return copy of all events."""
        return list(self._events)
    
    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()


class FileEventRepository(EventRepository):
    """
    File-based implementation using JSON lines format.
    Each event is persisted as a JSON object, one per line.
    """
    
    def __init__(self, filepath: str = "./events.jsonl"):
        self.filepath = Path(filepath)
        # Create file if it doesn't exist
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        if not self.filepath.exists():
            self.filepath.touch()
    
    def save(self, event: GameEvent) -> None:
        """Append event to JSON lines file."""
        event_dict = self._event_to_dict(event)
        with open(self.filepath, 'a') as f:
            json.dump(event_dict, f)
            f.write('\n')
    
    def load_all(self) -> List[GameEvent]:
        """Load all events from file."""
        events = []
        if not self.filepath.exists():
            return events
        
        with open(self.filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    event_dict = json.loads(line)
                    events.append(event_dict)
        
        # Note: In a real implementation, you'd reconstruct GameEvent objects
        # from the dictionaries. For now, we return the raw dicts.
        return events
    
    def clear(self) -> None:
        """Clear all events from file."""
        self.filepath.write_text('')
    
    @staticmethod
    def _event_to_dict(event: GameEvent) -> dict:
        """Convert GameEvent to dictionary for serialization."""
        return event.to_dict() if hasattr(event, 'to_dict') else vars(event)


__all__ = ["EventRepository", "InMemoryEventRepository", "FileEventRepository"]
