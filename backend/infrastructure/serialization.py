"""
Shared serialization utilities for converting dataclass/enum/datetime structures to JSON-safe payloads.

This module consolidates serialization logic previously duplicated across:
- server.py
- application_factory.py
- turn_orchestrator.py

Usage:
    from infrastructure.serialization import to_serializable
    json_safe = to_serializable(my_dataclass_instance)
"""

from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import Any


from functools import singledispatch
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any


@singledispatch
def to_serializable(obj: Any) -> Any:
    """
    Convert dataclass/enum/datetime-heavy structures to JSON-safe payloads.
    
    Uses singledispatch for extensible type handling.
    
    Args:
        obj: Any Python object to serialize
        
    Returns:
        JSON-serializable representation of the object
    """
    # Dataclasses are not a type but a structure, so we check explicitly in default
    if is_dataclass(obj):
        return {k: to_serializable(v) for k, v in asdict(obj).items()}
    return obj

@to_serializable.register
def _(obj: Enum):
    return obj.value

@to_serializable.register
def _(obj: datetime):
    return obj.isoformat()

@to_serializable.register
def _(obj: list):
    return [to_serializable(v) for v in obj]

@to_serializable.register
def _(obj: dict):
    return {k: to_serializable(v) for k, v in obj.items()}

# ! Legacy alias for backward compatibility
_to_serializable = to_serializable


__all__ = ["to_serializable", "_to_serializable"]
