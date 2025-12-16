from dataclasses import dataclass
from .providers import LLMProviderConfig


@dataclass
class LLMConfig:
    provider: LLMProviderConfig
