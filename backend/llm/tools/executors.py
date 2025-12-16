from __future__ import annotations

from typing import Dict, Any, Callable

from ..sessions import SessionStore
from .registry import ToolRegistry

class ToolRouter:
    def __init__(self, session_store: SessionStore, api_client: Callable[[str, Dict[str, Any]], Dict[str, Any]]):
        self.session_store = session_store
        self.api_client = api_client

    def get_state(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        agent_id = payload.get("agent_id")
        return self.api_client("GET_STATE", {"agent_id": agent_id})

    def get_history(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        agent_id = payload.get("agent_id")
        return self.api_client("GET_HISTORY", {"agent_id": agent_id, "last_event_id": payload.get("last_event_id")})

    def submit_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # payload must include: agent_id, command_name, payload
        return self.api_client("SUBMIT_COMMAND", payload)

    def end_of_turn(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        agent_id = payload.get("agent_id")
        notes = payload.get("notes", "")
        self.session_store.append_note(agent_id, notes)
        # Persisting notes as an event is handled by the api_client (server layer)
        return self.api_client("END_OF_TURN", {"agent_id": agent_id, "notes": notes})

    def communicate_to_agent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.api_client("COMMUNICATE", payload)

    def execute(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route tool calls by name.

        Supported:
        - tool_help
        - get_state
        - get_history
        - end_of_turn
        - Any registered command_type (e.g., SET_PRICE) as a transactional command
        """
        tool = (name or "").strip()
        if not tool:
            return {"error": "Tool name is required"}

        if tool == "tool_help":
            category = payload.get("category")
            name = payload.get("name")
            include_schema = bool(payload.get("include_schema", False))
            if name:
                return ToolRegistry.describe(name=name, include_schema=include_schema)
            return ToolRegistry.list_summary(category=category)

        if tool == "get_state":
            return self.get_state(payload)

        if tool == "get_history":
            return self.get_history(payload)

        if tool == "end_of_turn":
            return self.end_of_turn(payload)

        # Transactional: treat tool name as command_type
        # Flattened payload fields become the command payload.
        agent_id = payload.get("agent_id")
        if not agent_id:
            return {"error": "agent_id is required"}

        cmd_payload = dict(payload)
        cmd_payload.pop("agent_id", None)
        return self.submit_command({"agent_id": agent_id, "command_name": tool, "payload": cmd_payload})
