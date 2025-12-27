
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """Standardized request object for LLM chat interactions."""
    messages: list[dict]
    tools: Optional[list[dict]] = None
    step_idx: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class LLMProviderConfigBase:
    """Shared configuration shape for all LLM providers.

    Providers may interpret fields differently (e.g., Azure uses deployment names),
    but the interface stays consistent.
    """

    name: str = ""
    api_key: str = ""
    endpoint: str = ""  # For OpenAI-compatible servers, include the /v1 suffix.
    model: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)


class LLMProviderBase:
    """Unified provider interface.

    All providers must implement `chat()` and return an OpenAI-like message dict:
    {"role": "assistant", "content": str, "tool_calls": Optional[list]}
    """

    def __init__(self, config: LLMProviderConfigBase):
        self.config = config
        self.api_key = getattr(config, "api_key", "")
        self.endpoint = getattr(config, "endpoint", "")
        self.model = getattr(config, "model", "")

    def call(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement call()")

    async def chat(self, request: ChatRequest) -> dict:
        raise NotImplementedError("Subclasses must implement chat(request: ChatRequest)")

    def client(self):
        """Return the underlying client instance (if any)."""
        return None