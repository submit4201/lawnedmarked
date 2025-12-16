from dataclasses import dataclass
from typing import Dict


@dataclass
class EndOfTurnNote:
    agent_id: str
    notes: str


class EndOfTurnTool:
    def __init__(self, session_store: "SessionStore"):
        self.session_store = session_store

    def handler(self, payload: Dict) -> Dict:
        note = EndOfTurnNote(agent_id=payload.get("agent_id", ""), notes=payload.get("notes", ""))
        self.session_store.append_note(note.agent_id, note.notes)
        return {"ok": True}
