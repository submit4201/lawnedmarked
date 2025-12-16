from dataclasses import dataclass
from typing import List

@dataclass
class AgentRole:
    name: str
    tools: List[str]

PLAYER_AGENT = AgentRole(name="player", tools=[
    "get_state",
    "get_history",
    "submit_command",
    "end_of_turn",
    "communicate_to_agent",
])

GM_AGENT = AgentRole(name="gamemaster", tools=[
    "get_state",
    "get_history",
    "end_of_turn",
    "communicate_to_agent",
])

JUDGE_AGENT = AgentRole(name="judge", tools=[
    "get_state",
    "get_history",
    "end_of_turn",
    "communicate_to_agent",
])
