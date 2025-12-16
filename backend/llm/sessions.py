from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class SessionRecord:
    agent_id: str
    notes: List[str] = field(default_factory=list)


class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, SessionRecord] = {}

    def get(self, agent_id: str) -> SessionRecord:
        if agent_id not in self._sessions:
            self._sessions[agent_id] = SessionRecord(agent_id=agent_id)
        return self._sessions[agent_id]

    def append_note(self, agent_id: str, note: str) -> None:
        rec = self.get(agent_id)
        rec.notes.append(note)

    def get_notes(self, agent_id: str) -> List[str]:
        return list(self.get(agent_id).notes)
