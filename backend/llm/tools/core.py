from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class ToolSpec:
    name: str
    description: str
    schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]


class ToolExecutor:
    def __init__(self, tools: List[ToolSpec], audit_log: Any | None = None):
        self.tools = {t.name: t for t in tools}
        self.audit_log = audit_log

    def execute(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.tools:
            result = {"error": f"Unknown tool {tool_name}"}
            if self.audit_log:
                self.audit_log.append(
                    {"type": "LLMToolInvoked", "name": tool_name, "payload": payload, "result": result}
                )
            return result

        spec = self.tools[tool_name]
        result = spec.handler(payload)
        if self.audit_log:
            self.audit_log.append(
                {"type": "LLMToolInvoked", "name": tool_name, "payload": payload, "result": result}
            )
        return result
