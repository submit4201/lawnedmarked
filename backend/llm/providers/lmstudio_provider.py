from __future__ import annotations

from .llmproviderbase import LLMProviderConfigBase
from .openai_compatible import OpenAICompatibleProvider


class LMStudioConfig(LLMProviderConfigBase):
    def __init__(self):
        super().__init__(name="lmstudio")
        self.api_key = "lm-studio"  # not required; placeholder
        self.endpoint = "http://127.0.0.1:1234/v1"
        self.model = ""  # must be configured


class LMStudioProvider(OpenAICompatibleProvider):
    def __init__(self, config: LMStudioConfig | None = None):
        super().__init__(config or LMStudioConfig())
