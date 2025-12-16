from typing import Dict

from .registry import ToolRegistry


class ToolHelpTool:
    """Return categorized tool help to reduce prompt token usage."""

    def handler(self, payload: Dict) -> Dict:
        category = payload.get("category")
        name = payload.get("name")
        include_schema = bool(payload.get("include_schema", False))
        if name:
            return ToolRegistry.describe(name=name, include_schema=include_schema)
        return ToolRegistry.list_summary(category=category)
