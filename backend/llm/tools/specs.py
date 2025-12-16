from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ToolSchema:
    name: str
    description: str
    schema: Dict[str, Any]

GET_STATE = ToolSchema(
    name="get_state",
    description="Get current AgentState",
    schema={"type": "object", "properties": {"agent_id": {"type": "string"}}, "required": ["agent_id"]},
)

GET_HISTORY = ToolSchema(
    name="get_history",
    description="Get event history for agent",
    schema={"type": "object", "properties": {"agent_id": {"type": "string"}, "last_event_id": {"type": "string"}}, "required": ["agent_id"]},
)

SUBMIT_COMMAND = ToolSchema(
    name="submit_command",
    description="Submit a validated command",
    schema={"type": "object", "properties": {"agent_id": {"type": "string"}, "command_name": {"type": "string"}, "payload": {"type": "object"}}, "required": ["agent_id", "command_name", "payload"]},
)

END_OF_TURN = ToolSchema(
    name="end_of_turn",
    description="Persist notes and end the turn",
    schema={"type": "object", "properties": {"agent_id": {"type": "string"}, "notes": {"type": "string"}}, "required": ["agent_id", "notes"]},
)

COMMUNICATE = ToolSchema(
    name="communicate_to_agent",
    description="Send a message between agents",
    schema={"type": "object", "properties": {"agent_id": {"type": "string"}, "target": {"type": "string"}, "message": {"type": "string"}}, "required": ["agent_id", "target", "message"]},
)
