from __future__ import annotations

from .llmproviderbase import LLMProviderConfigBase
from .openai_provider import OpenAIProvider


class OllamaConfig(LLMProviderConfigBase):
    def __init__(self):
        super().__init__(name="ollama")
        self.api_key = "ollama"  # not required by Ollama
        # Ollama exposes an OpenAI-compatible API at /v1
        self.endpoint = "http://127.0.0.1:11434/v1"
        self.model = ""  # e.g. "llama3.1" or "qwen2.5:7b"


class OllamaProvider(OpenAIProvider):
    def __init__(self, config: OllamaConfig | None = None):
        super().__init__(config or OllamaConfig())
