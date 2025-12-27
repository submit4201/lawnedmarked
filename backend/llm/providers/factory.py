from __future__ import annotations

import json
import os
from typing import Any, Dict

from .llmproviderbase import LLMProviderBase, LLMProviderConfigBase
from .localprovider import LocalProvider, localConfig
from .mock import MockLLM
from .openai_provider import OpenAIProvider, OpenAIConfig
from .azure_openai_provider import AzureOpenAIProvider, AzureOpenAIConfig
from .azure_ai_inference_provider import AzureAIInferenceProvider, AzureAIInferenceConfig
from .ollama_provider import OllamaProvider, OllamaConfig
from .lmstudio_provider import LMStudioProvider, LMStudioConfig
from .gemini_provider import GeminiProvider, GeminiConfig
from .aiprojectspro import AzureAIProjectsProvider, AzureAIProjectsConfig

# Alias for backward compatibility or explicit requests
LLMProAIProvider = AzureAIProjectsProvider
LLMProAIConfig = AzureAIProjectsConfig


def _parse_extra_json(value: str | None) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _get_env(prefix: str, key: str, default: Any = None) -> Any:
    """Try PREFIX_KEY, then LLM_KEY, then default."""
    p_key = f"{prefix.upper()}_{key.upper()}"
    l_key = f"LLM_{key.upper()}"
    return os.getenv(p_key, os.getenv(l_key, default))


class HumanProvider(LLMProviderBase):
    """A 'human' provider that just signals it's waiting for manual input."""
    def __init__(self, config: Any = None):
        super().__init__(config or LLMProviderConfigBase(name="human"))

    async def chat(self, messages: list[dict], **kwargs) -> dict:
        return {
            "role": "assistant",
            "content": "Awaiting human input...",
            "tool_calls": [],
            "metadata": {"is_human": True}
        }

from dataclasses import dataclass, field

@dataclass
class ProviderContext:
    """Encapsulates provider configuration gathered from environment."""
    name: str
    api_key: str
    endpoint: str
    model: str
    extra: Dict[str, Any] = field(default_factory=dict)


def _create_local_provider(ctx: ProviderContext):
    cfg = localConfig()
    cfg.api_key = os.getenv("LOCAL_api_key", cfg.api_key)
    cfg.endpoint = (os.getenv("LOCAL_base_url", os.getenv("LOCAL_ENDPOINT", cfg.endpoint)) or "").strip()
    cfg.model = (os.getenv("LOCAL_deployment_name", cfg.model) or "").strip()
    
    endpoint_lower = (cfg.endpoint or "").lower()
    if any(bad in endpoint_lower for bad in ("localhost:8000", "127.0.0.1:8000")):
        print(f"[LLM][local][warn] LOCAL endpoint appears to point at root backend: {cfg.endpoint}")
    cfg.extra.update(ctx.extra)
    return LocalProvider(config=cfg), f"LocalProvider:{cfg.model} @ {cfg.endpoint}"

def _create_ollama_provider(ctx: ProviderContext):
    cfg = OllamaConfig()
    cfg.endpoint = ctx.endpoint or cfg.endpoint
    cfg.model = ctx.model or cfg.model
    cfg.api_key = ctx.api_key or cfg.api_key
    cfg.extra.update(ctx.extra)
    return OllamaProvider(config=cfg), f"OllamaProvider:{cfg.model} @ {cfg.endpoint}"

def _create_lmstudio_provider(ctx: ProviderContext):
    cfg = LMStudioConfig()
    cfg.endpoint = ctx.endpoint or cfg.endpoint
    cfg.model = ctx.model or cfg.model
    cfg.api_key = ctx.api_key or cfg.api_key
    cfg.extra.update(ctx.extra)
    return LMStudioProvider(config=cfg), f"LMStudioProvider:{cfg.model} @ {cfg.endpoint}"

def _create_gemini_provider(ctx: ProviderContext):
    cfg = GeminiConfig()
    cfg.api_key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ctx.api_key or cfg.api_key))
    cfg.endpoint = ctx.endpoint or cfg.endpoint
    cfg.model = ctx.model or cfg.model
    cfg.extra.update(ctx.extra)
    return GeminiProvider(config=cfg), f"GeminiProvider:{cfg.model} @ {cfg.endpoint}"

def _create_azure_projects_provider(ctx: ProviderContext):
    cfg = AzureAIProjectsConfig()
    cfg.api_key = ctx.api_key or cfg.api_key
    cfg.endpoint = ctx.endpoint or cfg.endpoint
    cfg.model = ctx.model or "gpt-5-nano"
    cfg.extra.update(ctx.extra)
    return AzureAIProjectsProvider(config=cfg), f"AzureAIProjectsProvider({ctx.name}):{cfg.model} @ {cfg.endpoint}"

def _create_azure_inference_provider(ctx: ProviderContext):
    cfg = AzureAIInferenceConfig()
    cfg.api_key = ctx.api_key
    cfg.endpoint = ctx.endpoint
    cfg.model = ctx.model
    cfg.extra.update(ctx.extra)
    return AzureAIInferenceProvider(config=cfg), f"AzureAIInferenceProvider({ctx.name}):{cfg.model} @ {cfg.endpoint}"

def _create_azure_openai_provider(ctx: ProviderContext):
    cfg = AzureOpenAIConfig()
    cfg.api_key = ctx.api_key
    cfg.endpoint = ctx.endpoint
    cfg.model = ctx.model
    cfg.extra.update(ctx.extra)
    return AzureOpenAIProvider(config=cfg), f"AzureOpenAIProvider({ctx.name}):{cfg.model} @ {cfg.endpoint}"

def _create_openai_provider(ctx: ProviderContext):
    cfg = OpenAIConfig()
    cfg.api_key = ctx.api_key
    cfg.endpoint = ctx.endpoint
    cfg.model = ctx.model
    cfg.extra.update(ctx.extra)
    return OpenAIProvider(config=cfg), f"OpenAIProvider({ctx.name}):{cfg.model or 'default'} @ {cfg.endpoint or 'openai.com'}"


def create_provider_from_env(name: str | None = None) -> tuple[LLMProviderBase, str]:
    """Create a provider from environment variables dynamically."""
    name = (name or os.getenv("LLM_PROVIDER") or "local").strip().lower()

    # Special providers that don't need context
    if name == "mock":
        return MockLLM(), "MockLLM"
    if name == "human":
        return HumanProvider(), "HumanPlayer"

    ctx = _build_provider_context(name)

    # Registry lookup
    if name in _PROVIDER_REGISTRY:
        return _PROVIDER_REGISTRY[name](ctx)

    # Dynamic Type Detection via URL patterns
    detected = _detect_provider_from_url(ctx.endpoint)
    if detected:
        return detected(ctx)

    # Default to OpenAI if credentials exist
    if ctx.endpoint or ctx.api_key:
        return _create_openai_provider(ctx)

    return MockLLM(), f"MockLLM (unknown provider {name})"


# Provider registry for explicit names
_PROVIDER_REGISTRY = {
    "local": _create_local_provider,
    "ollama": _create_ollama_provider,
    "lmstudio": _create_lmstudio_provider,
    "gemini": _create_gemini_provider,
    "projects": _create_azure_projects_provider,
    "azure_openai": _create_azure_openai_provider,
    "azure": _create_azure_openai_provider,
    "azure_ai_inference": _create_azure_inference_provider,
}

# URL pattern → provider mapping for dynamic detection
_URL_PATTERNS = [
    (["openai.azure.com", "cognitiveservices.azure.com"], _create_azure_openai_provider),
    (["models.ai.azure.com", "services.ai.azure.com"], _create_azure_inference_provider),
]


def _detect_provider_from_url(endpoint: str):
    """Detect provider type from URL patterns."""
    url = (endpoint or "").lower()
    for patterns, creator in _URL_PATTERNS:
        if any(p in url for p in patterns):
            return creator
    return None


def _build_provider_context(name: str) -> ProviderContext:
    """Build ProviderContext from environment variables."""
    if name in ("azure_openai", "azure"):
        api_key, endpoint, model = _get_azure_env_vars()
    else:
        api_key, endpoint, model = _get_generic_env_vars(name)
    
    extra = _parse_extra_json(os.getenv("LLM_EXTRA_JSON"))
    api_version = _get_env(name, "api_version") or os.getenv("AZURE_api_version")
    if api_version:
        extra["api_version"] = api_version

    return ProviderContext(name=name, api_key=api_key, endpoint=endpoint, model=model, extra=extra)


# Azure environment variable fallback order
_AZURE_ENV_KEYS = {
    "api_key": ["AZURE_OPENAI_API_KEY", "AZURE_api_key", "AZURE_API_KEY"],
    "endpoint": ["AZURE_OPENAI_BASE_URL", "AZURE_base_url", "AZURE_ENDPOINT"],
    "model": ["AZURE_OPENAI_DEPLOYMENT", "AZURE_deployment_name", "AZURE_MODEL"],
}


def _get_first_env(*keys: str, default: str = "") -> str:
    """Get first non-empty environment variable from list of keys."""
    for key in keys:
        val = os.getenv(key)
        if val:
            return val
    return default


def _get_azure_env_vars() -> tuple[str, str, str]:
    """Get Azure-specific environment variables."""
    return (
        _get_first_env(*_AZURE_ENV_KEYS["api_key"]),
        _get_first_env(*_AZURE_ENV_KEYS["endpoint"]),
        _get_first_env(*_AZURE_ENV_KEYS["model"]),
    )


def _get_generic_env_vars(name: str) -> tuple[str, str, str]:
    """Get generic environment variables for non-Azure providers."""
    api_key = _get_env(name, "api_key", "")
    endpoint = (_get_env(name, "base_url", _get_env(name, "endpoint", "")) or "").strip()
    model = _get_env(name, "model", _get_env(name, "deployment", _get_env(name, "deployment_name", "")))
    return api_key, endpoint, model
