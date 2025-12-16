from typing import List, Dict
from .prompts import SystemPrompts
from .prompt_registry import PromptRegistry
from .tools.registry import ToolRegistry
from .sessions import SessionStore


def player_messages(agent_id: str, history: List[Dict], session_store: SessionStore) -> List[Dict]:
    notes = session_store.get_notes(agent_id) if session_store else []
    # Keep the system prompt minimal; detailed schemas are discoverable via tool_help.
    tools_data = [
        {"name": "tool_help"},
        {"name": "get_state"},
        {"name": "get_history"},
        {"name": "end_of_turn"},
    ]

    system = PromptRegistry.get_system_prompt(
        template_name="player_system.j2",
        tools=tools_data,
        agent_name=agent_id,
        agent_goal="maximize profit",
    ) or ""
    messages = [{"role": "system", "content": system}]
    if notes:
        messages.append({"role": "system", "content": f"Private Notes: {notes}"})
    # Server will append a dynamic user message with context; no extra turn header here.
    return messages + history


def gm_messages(agent_id: str, history: List[Dict], session_store: SessionStore) -> List[Dict]:
    notes = session_store.get_notes(agent_id) if session_store else []
    system = SystemPrompts.GM_SYSTEM + "\n" + SystemPrompts.TOOL_POLICY
    messages = [{"role": "system", "content": system}]
    if notes:
        messages.append({"role": "system", "content": f"Private Notes: {notes}"})
    return messages + history


def judge_messages(agent_id: str, history: List[Dict], session_store: SessionStore) -> List[Dict]:
    notes = session_store.get_notes(agent_id) if session_store else []
    system = SystemPrompts.JUDGE_SYSTEM + "\n" + SystemPrompts.TOOL_POLICY
    messages = [{"role": "system", "content": system}]
    if notes:
        messages.append({"role": "system", "content": f"Private Notes: {notes}"})
    return messages + history
