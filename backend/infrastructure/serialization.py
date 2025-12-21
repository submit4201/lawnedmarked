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


def to_serializable(obj: Any) -> Any:
    """
    Convert dataclass/enum/datetime-heavy structures to JSON-safe payloads.
    
    Recursively processes:
    - Enum -> enum.value
    - datetime -> ISO format string
    - dataclass -> dict (via asdict)
    - list -> recursively processed list
    - dict -> recursively processed dict
    - other -> passed through unchanged
    
    Args:
        obj: Any Python object to serialize
        
    Returns:
        JSON-serializable representation of the object
        
    Example:
        >>> from core.models import AgentState
        >>> state = AgentState(agent_id="P001")
        >>> json_data = to_serializable(state)
        >>> import json
        >>> json.dumps(json_data)  # Works!
    """
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_serializable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [to_serializable(v) for v in obj]
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    return obj


# ! Legacy alias for backward compatibility
# * Some modules may still reference _to_serializable
_to_serializable = to_serializable


__all__ = ["to_serializable", "_to_serializable"]
