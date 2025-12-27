from typing import List, Dict
from .prompts import SystemPrompts
from .prompt_registry import PromptRegistry
from .tools.registry import ToolRegistry
from .sessions import SessionStore


def player_messages(agent_id: str, history: List[Dict], session_store: SessionStore, state: Dict = None, competitor_events: List[Dict] = None) -> List[Dict]:
    notes = session_store.get_notes(agent_id) if session_store else []
    # Provide all tools to the template so the model knows what's available.
    tools_data = [{"name": t.name} for t in ToolRegistry.get_all_tools()]

    system = PromptRegistry.get_system_prompt(
        template_name="player_system.j2",
        tools=tools_data,
        agent_name=agent_id,
        state=state,
        competitor_events=competitor_events,
    ) or ""
    messages = [{"role": "system", "content": system}]
    if notes:
        messages.append({"role": "system", "content": f"Private Notes: {notes}"})
    # Server will append a dynamic user message with context; no extra turn header here.
    return messages + history

def turn_message(agent_id: str, used_actions: List[Dict], history: List[Dict], session_store: SessionStore) -> List[Dict]:
    notes = session_store.get_notes(agent_id) if session_store else []
    state = {}
    if session_store:
        state = session_store.get_state(agent_id) or {}
    system = PromptRegistry.get_turn_prompt(
        template_name="player_turn.j2",
        used_tools=ToolRegistry.list_summary(),
        used_actions=used_actions,
        notes="\n".join(notes) if notes else "",
        state=state,
        agent_name=agent_id,
    ) or ""
    messages = [{"role": "system", "content": system}]
    if notes:
        messages.append({"role": "system", "content": f"Private Notes: {notes}"})
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
