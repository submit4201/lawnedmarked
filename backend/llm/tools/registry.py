from __future__ import annotations

from dataclasses import dataclass
from dataclasses import MISSING
from typing import Any, Dict, List, Optional, get_args, get_origin


@dataclass(frozen=True)
class ToolInfo:
    name: str
    category: str
    description: str
    schema: Dict[str, Any]


class ToolRegistry:
    """Central place to describe tools, their categories, and schemas."""

    CATEGORY_INFORMATIONAL = "informational"
    CATEGORY_TRANSACTIONAL = "transactional"
    CATEGORY_COMMUNICATION = "communication"
    CATEGORY_SESSION = "session"

    @classmethod
    def _json_schema_for_type(cls, typ: Any) -> Dict[str, Any]:
        origin = get_origin(typ)
        args = get_args(typ)

        # List[T]
        if origin is list or origin is List:
            item_type = args[0] if args else Any
            return {"type": "array", "items": cls._json_schema_for_type(item_type)}

        # Dict[K,V]
        if origin is dict or origin is Dict:
            return {"type": "object"}

        # Literal
        if origin is getattr(__import__("typing"), "Literal", None):
            return {"type": "string", "enum": list(args)}

        # Union / Optional
        if origin is getattr(__import__("typing"), "Union", None) or str(typ).startswith("typing.Union"):
            non_none = [a for a in args if a is not type(None)]  # noqa: E721
            if len(non_none) == 1:
                return cls._json_schema_for_type(non_none[0])
            return {"type": "object"}

        # Python 3.10+ | unions
        if getattr(typ, "__origin__", None) is None and hasattr(typ, "__args__") and getattr(typ, "__module__", "") == "types":
            non_none = [a for a in typ.__args__ if a is not type(None)]  # noqa: E721
            if len(non_none) == 1:
                return cls._json_schema_for_type(non_none[0])
            return {"type": "object"}

        # Primitives
        if typ is str:
            return {"type": "string"}
        if typ is int:
            return {"type": "integer"}
        if typ is float:
            return {"type": "number"}
        if typ is bool:
            return {"type": "boolean"}

        return {"type": "object"}

    @classmethod
    def _schema_for_payload_dataclass(cls, payload_type: Any) -> Dict[str, Any]:
        props: Dict[str, Any] = {}
        required: List[str] = []

        fields = getattr(payload_type, "__dataclass_fields__", {}) or {}
        for fname, f in fields.items():
            props[fname] = cls._json_schema_for_type(getattr(f, "type", Any))
            has_default = not (f.default is MISSING and getattr(f, "default_factory", MISSING) is MISSING)
            if not has_default:
                required.append(fname)

        return {"type": "object", "properties": props, "required": required}

    @classmethod
    def get_all_tools(cls) -> List[ToolInfo]:
        tools: List[ToolInfo] = [
            ToolInfo(
                name="tool_help",
                category=cls.CATEGORY_INFORMATIONAL,
                description="List tool categories/tools or show detailed help for a specific tool.",
                schema={
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Optional category filter"},
                        "name": {"type": "string", "description": "Optional tool name to describe"},
                        "include_schema": {
                            "type": "boolean",
                            "description": "Include JSON schema in output",
                            "default": False,
                        },
                    },
                    "required": [],
                },
            ),
            ToolInfo(
                name="get_state",
                category=cls.CATEGORY_INFORMATIONAL,
                description="Get the current state snapshot for an agent.",
                schema={
                    "type": "object",
                    "properties": {"agent_id": {"type": "string"}},
                    "required": ["agent_id"],
                },
            ),
            ToolInfo(
                name="get_history",
                category=cls.CATEGORY_INFORMATIONAL,
                description="Get the event history for an agent (optionally after last_event_id).",
                schema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "last_event_id": {"type": "string"},
                    },
                    "required": ["agent_id"],
                },
            ),
            ToolInfo(
                name="end_of_turn",
                category=cls.CATEGORY_SESSION,
                description="Save private notes for the next turn.",
                schema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "notes": {"type": "string", "description": "Notes to persist"},
                    },
                    "required": ["agent_id", "notes"],
                },
            ),
        ]

        # Transactional tools: expose every registered command as a tool.
        try:
            from llm_factory import COMMAND_REGISTRY

            seen: Dict[str, Any] = {}
            for _, cmd_cls in COMMAND_REGISTRY.items():
                cmd_type = getattr(cmd_cls, "command_type", None) or ""
                if not cmd_type or cmd_type in seen:
                    continue
                seen[cmd_type] = cmd_cls

            for cmd_type in sorted(seen.keys()):
                cmd_cls = seen[cmd_type]
                payload_type = getattr(cmd_cls, "payload_type", None)
                payload_schema = cls._schema_for_payload_dataclass(payload_type) if payload_type else {"type": "object"}

                # Flatten payload fields at top-level (alongside agent_id)
                props = {"agent_id": {"type": "string"}}
                required = ["agent_id"]
                props.update(payload_schema.get("properties", {}))
                required.extend(payload_schema.get("required", []))

                tools.append(
                    ToolInfo(
                        name=cmd_type,
                        category=cls.CATEGORY_TRANSACTIONAL,
                        description=f"Execute the {cmd_type} command.",
                        schema={"type": "object", "properties": props, "required": required},
                    )
                )
        except Exception:
            # If registry can't load (import order), keep base tools.
            pass

        return tools

    @classmethod
    def categories(cls) -> List[str]:
        return sorted({t.category for t in cls.get_all_tools()})

    @classmethod
    def by_name(cls, name: str) -> Optional[ToolInfo]:
        name_norm = (name or "").strip()
        for t in cls.get_all_tools():
            if t.name == name_norm:
                return t
        return None

    @classmethod
    def list_summary(cls, category: Optional[str] = None) -> Dict[str, Any]:
        tools = cls.get_all_tools()
        if category:
            tools = [t for t in tools if t.category == category]
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for t in tools:
            grouped.setdefault(t.category, []).append({"name": t.name, "description": t.description})
        for cat in grouped:
            grouped[cat] = sorted(grouped[cat], key=lambda x: x["name"])
        return {"categories": cls.categories(), "tools": grouped}

    @classmethod
    def describe(cls, name: str, include_schema: bool = False) -> Dict[str, Any]:
        t = cls.by_name(name)
        if not t:
            return {"error": f"Unknown tool '{name}'", "available": [x.name for x in cls.get_all_tools()]}
        data: Dict[str, Any] = {"name": t.name, "category": t.category, "description": t.description}
        if include_schema:
            data["schema"] = t.schema
        return data

    @classmethod
    def as_openai_tools(cls) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.schema,
                },
            }
            for t in cls.get_all_tools()
        ]
