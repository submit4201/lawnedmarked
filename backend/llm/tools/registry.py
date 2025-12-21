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
        # Mapping of command types to concise descriptions.
        COMMAND_DESCRIPTIONS = {
            "SET_PRICE": "Set the price for a specific service at a location.",
            "TAKE_LOAN": "Apply for a loan (LOC, EQUIPMENT, EXPANSION, EMERGENCY).",
            "MAKE_DEBT_PAYMENT": "Make a payment towards an existing debt.",
            "INVEST_IN_MARKETING": "Spend money on marketing campaigns to increase traffic.",
            "BUY_EQUIPMENT": "Purchase new equipment from a vendor.",
            "SELL_EQUIPMENT": "Sell existing equipment for cash.",
            "PERFORM_MAINTENANCE": "Perform maintenance on machines or premises.",
            "BUY_SUPPLIES": "Purchase detergent or softener from a vendor.",
            "OPEN_NEW_LOCATION": "Open a new laundromat location in a specific zone.",
            "FIX_MACHINE": "Repair a broken machine.",
            "HIRE_STAFF": "Hire a new employee (ATTENDANT, TECHNICIAN, MANAGER).",
            "FIRE_STAFF": "Terminate an employee's contract.",
            "ADJUST_STAFF_WAGE": "Change an employee's hourly salary.",
            "PROVIDE_BENEFITS": "Offer benefits to employees to improve morale.",
            "NEGOTIATE_VENDOR_DEAL": "Negotiate better terms with a supplier.",
            "COMMUNICATE_TO_AGENT": "Send a message or proposal to another agent or the GM.",
            "SIGN_EXCLUSIVE_CONTRACT": "Sign an exclusive deal with a vendor for discounts.",
            "CANCEL_VENDOR_CONTRACT": "Terminate a contract with a vendor.",
            "INITIATE_CHARITY": "Donate to charity to improve social score.",
            "RESOLVE_SCANDAL": "Take action to mitigate a public scandal.",
            "MAKE_ETHICAL_CHOICE": "Respond to an ethical dilemma.",
            "FILE_REGULATORY_REPORT": "Submit required documentation to regulators.",
            "ENTER_ALLIANCE": "Form a strategic alliance with another agent.",
            "PROPOSE_BUYOUT": "Offer to buy out another agent's business.",
            "ACCEPT_BUYOUT_OFFER": "Accept a buyout offer from another agent.",
            "SUBSCRIBE_LOYALTY_PROGRAM": "Enroll in a customer loyalty program.",
            "FILE_APPEAL": "Appeal a regulatory fine or decision.",
            "INJECT_WORLD_EVENT": "System tool to inject events into the simulation.",
        }

        # ! Example usage for each command - returned by tool_help when querying specific tool
        COMMAND_EXAMPLES = {
            "SET_PRICE": {"location_id": "loc_downtown", "service": "StandardWash", "price": 3.50},
            "TAKE_LOAN": {"loan_type": "LOC", "amount": 5000.0},
            "MAKE_DEBT_PAYMENT": {"debt_id": "loan_001", "amount": 500.0},
            "INVEST_IN_MARKETING": {"location_id": "loc_downtown", "campaign_type": "LOCAL_ADS", "budget": 200.0},
            "BUY_EQUIPMENT": {"location_id": "loc_downtown", "equipment_type": "WASHER", "vendor_id": "vendor_001"},
            "SELL_EQUIPMENT": {"location_id": "loc_downtown", "machine_id": "washer_001"},
            "PERFORM_MAINTENANCE": {"location_id": "loc_downtown", "machine_id": "washer_001", "maintenance_type": "ROUTINE"},
            "BUY_SUPPLIES": {"location_id": "loc_downtown", "supply_type": "DETERGENT", "quantity": 100, "vendor_id": "vendor_001"},
            "OPEN_NEW_LOCATION": {"zone": "DOWNTOWN", "listing_id": "listing_001"},
            "FIX_MACHINE": {"location_id": "loc_downtown", "machine_id": "washer_001"},
            "HIRE_STAFF": {"location_id": "loc_downtown", "role": "ATTENDANT", "name": "John Doe"},
            "FIRE_STAFF": {"location_id": "loc_downtown", "staff_id": "staff_001"},
            "ADJUST_STAFF_WAGE": {"location_id": "loc_downtown", "staff_id": "staff_001", "new_wage": 15.0},
            "PROVIDE_BENEFITS": {"benefit_type": "HEALTH_INSURANCE", "coverage_level": "BASIC"},
            "NEGOTIATE_VENDOR_DEAL": {"vendor_id": "vendor_001", "requested_discount": 0.10},
            "COMMUNICATE_TO_AGENT": {"target_agent_id": "PLAYER_002", "message": "Would you like to form an alliance?"},
            "SIGN_EXCLUSIVE_CONTRACT": {"vendor_id": "vendor_001", "duration_weeks": 12},
            "CANCEL_VENDOR_CONTRACT": {"vendor_id": "vendor_001"},
            "INITIATE_CHARITY": {"charity_type": "LOCAL_SHELTER", "amount": 500.0},
            "RESOLVE_SCANDAL": {"scandal_id": "scandal_001", "resolution_type": "PUBLIC_APOLOGY"},
            "MAKE_ETHICAL_CHOICE": {"dilemma_id": "dilemma_001", "choice": "ETHICAL"},
            "FILE_REGULATORY_REPORT": {"report_type": "QUARTERLY_FINANCIAL"},
            "ENTER_ALLIANCE": {"target_agent_id": "PLAYER_002", "alliance_type": "PRICE_FIXING"},
            "PROPOSE_BUYOUT": {"target_agent_id": "PLAYER_002", "offer_amount": 50000.0},
            "ACCEPT_BUYOUT_OFFER": {"offer_id": "offer_001"},
            "SUBSCRIBE_LOYALTY_PROGRAM": {"program_id": "loyalty_001"},
            "FILE_APPEAL": {"fine_id": "fine_001", "reason": "Procedural error in inspection"},
        }
        
        # Store examples for access by describe()
        cls._COMMAND_EXAMPLES = COMMAND_EXAMPLES

        # ! Minimal tool set - state/history already in system prompt
        # Only tool_help (for discovering commands) and end_of_turn (for session)
        tools: List[ToolInfo] = [
            ToolInfo(
                name="tool_help",
                category=cls.CATEGORY_INFORMATIONAL,
                description="Get schema, required arguments, and example for ANY tool. Call with {name: 'TOOL_NAME'} to learn how to use it. Call without args to list all tools by category.",
                schema={
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Filter by category: informational, transactional, session"},
                        "name": {"type": "string", "description": "Tool name to get detailed schema and example for"},
                    },
                    "required": [],
                },
            ),
            ToolInfo(
                name="end_of_turn",
                category=cls.CATEGORY_SESSION,
                description="End your turn and save notes for your future self. REQUIRED at end of each turn.",
                schema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "notes": {"type": "string", "description": "Strategic notes to remember next turn"},
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

                desc = COMMAND_DESCRIPTIONS.get(cmd_type, f"Execute the {cmd_type} command.")
                tools.append(
                    ToolInfo(
                        name=cmd_type,
                        category=cls.CATEGORY_TRANSACTIONAL,
                        description=desc,
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
        # ! Always include schema and example when describing a specific tool
        # This is the primary way the LLM learns how to use tools
        t = cls.by_name(name)
        if not t:
            return {"error": f"Unknown tool '{name}'", "available": [x.name for x in cls.get_all_tools()]}
        
        # Ensure examples are loaded
        cls.get_all_tools()
        
        data: Dict[str, Any] = {
            "name": t.name, 
            "category": t.category, 
            "description": t.description,
            "schema": t.schema,  # Always include schema for clarity
        }
        
        # Add example if available
        examples = getattr(cls, "_COMMAND_EXAMPLES", {})
        if name in examples:
            data["example"] = {
                "agent_id": "YOUR_AGENT_ID",
                **examples[name]
            }
            data["usage_hint"] = f"Call {name} with arguments like the example. Replace YOUR_AGENT_ID with your actual agent_id."
        
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

    @classmethod
    def as_openai_tools_only(cls, names: List[str]) -> List[Dict[str, Any]]:
        """Return OpenAI tool schemas for a specific allow-list of tool names."""
        wanted = {str(n).strip() for n in (names or []) if str(n).strip()}
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
            if t.name in wanted
        ]

    @classmethod
    def as_openai_tools_minimal(cls) -> List[Dict[str, Any]]:
        """Minimal tool set for player turns to keep prompts small.

        Transactional actions should be emitted via text fallback: Command(NAME): {json}.
        """
        return cls.as_openai_tools_only(["tool_help", "get_state", "get_history", "end_of_turn"])
