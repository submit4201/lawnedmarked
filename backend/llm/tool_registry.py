from __future__ import annotations

"""Legacy compatibility shim.

The canonical `ToolRegistry` now lives in `llm/tools/registry.py`.
"""

from .tools.registry import ToolRegistry

__all__ = ["ToolRegistry"]
