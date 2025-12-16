from typing import List, Dict, Any
from pathlib import Path
import json


class AuditEvent(dict):
    pass


class AuditLog:
    def __init__(self, log_path: str | None = None):
        self._events: List[AuditEvent] = []
        self._log_path = Path(log_path) if log_path else None
        if self._log_path:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: Dict[str, Any]) -> None:
        # Minimal safe logging: redact payloads if too large
        if "payload" in event and isinstance(event["payload"], dict) and len(str(event["payload"])) > 2000:
            event = {**event, "payload": "<redacted>"}
        audit_event = AuditEvent(event)
        self._events.append(audit_event)

        if self._log_path:
            try:
                with self._log_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(audit_event, ensure_ascii=False) + "\n")
            except Exception:
                # Don't crash on logging failures
                pass

    def list(self) -> List[AuditEvent]:
        return list(self._events)
