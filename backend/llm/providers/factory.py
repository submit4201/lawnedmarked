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

def _create_local_provider(name, api_key, endpoint, model, extra):
    cfg = localConfig()
    cfg.api_key = os.getenv("LOCAL_api_key", cfg.api_key)
    cfg.endpoint = (os.getenv("LOCAL_base_url", os.getenv("LOCAL_ENDPOINT", cfg.endpoint)) or "").strip()
    cfg.model = (os.getenv("LOCAL_deployment_name", cfg.model) or "").strip()
    
    endpoint_lower = (cfg.endpoint or "").lower()
    if any(bad in endpoint_lower for bad in ("localhost:8000", "127.0.0.1:8000")):
        print(f"[LLM][local][warn] LOCAL endpoint appears to point at root backend: {cfg.endpoint}")
    cfg.extra.update(extra)
    return LocalProvider(config=cfg), f"LocalProvider:{cfg.model} @ {cfg.endpoint}"

def _create_ollama_provider(name, api_key, endpoint, model, extra):
    cfg = OllamaConfig()
    cfg.endpoint = endpoint or cfg.endpoint
    cfg.model = model or cfg.model
    cfg.api_key = api_key or cfg.api_key
    cfg.extra.update(extra)
    return OllamaProvider(config=cfg), f"OllamaProvider:{cfg.model} @ {cfg.endpoint}"

def _create_lmstudio_provider(name, api_key, endpoint, model, extra):
    cfg = LMStudioConfig()
    cfg.endpoint = endpoint or cfg.endpoint
    cfg.model = model or cfg.model
    cfg.api_key = api_key or cfg.api_key
    cfg.extra.update(extra)
    return LMStudioProvider(config=cfg), f"LMStudioProvider:{cfg.model} @ {cfg.endpoint}"

def _create_gemini_provider(name, api_key, endpoint, model, extra):
    cfg = GeminiConfig()
    cfg.api_key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", api_key or cfg.api_key))
    cfg.endpoint = endpoint or cfg.endpoint
    cfg.model = model or cfg.model
    cfg.extra.update(extra)
    return GeminiProvider(config=cfg), f"GeminiProvider:{cfg.model} @ {cfg.endpoint}"

def _create_azure_projects_provider(name, api_key, endpoint, model, extra):
    cfg = AzureAIProjectsConfig()
    # Ensure keys are respected if passed
    cfg.api_key = api_key or cfg.api_key
    cfg.endpoint = endpoint or cfg.endpoint
    cfg.model = model or "gpt-5-nano"
    cfg.extra.update(extra)
    return AzureAIProjectsProvider(config=cfg), f"AzureAIProjectsProvider({name}):{cfg.model} @ {cfg.endpoint}"

def _create_azure_inference_provider(name, api_key, endpoint, model, extra):
    cfg = AzureAIInferenceConfig()
    cfg.api_key = api_key
    cfg.endpoint = endpoint
    cfg.model = model
    cfg.extra.update(extra)
    return AzureAIInferenceProvider(config=cfg), f"AzureAIInferenceProvider({name}):{cfg.model} @ {cfg.endpoint}"

def _create_azure_openai_provider(name, api_key, endpoint, model, extra):
    cfg = AzureOpenAIConfig()
    cfg.api_key = api_key
    cfg.endpoint = endpoint
    cfg.model = model
    cfg.extra.update(extra)
    return AzureOpenAIProvider(config=cfg), f"AzureOpenAIProvider({name}):{cfg.model} @ {cfg.endpoint}"

def _create_openai_provider(name, api_key, endpoint, model, extra):
    cfg = OpenAIConfig()
    cfg.api_key = api_key
    cfg.endpoint = endpoint
    cfg.model = model
    cfg.extra.update(extra)
    return OpenAIProvider(config=cfg), f"OpenAIProvider({name}):{cfg.model or 'default'} @ {cfg.endpoint or 'openai.com'}"


def create_provider_from_env(name: str | None = None) -> tuple[LLMProviderBase, str]:
    """Create a provider from environment variables dynamically."""
    name = (name or os.getenv("LLM_PROVIDER") or "local").strip().lower()

    if name == "mock":
        return MockLLM(), "MockLLM"
    if name == "human":
        return HumanProvider(), "HumanPlayer"

    # 1. Gather configuration
    # For azure_openai, also check AZURE_ prefix as fallback
    if name in ("azure_openai", "azure"):
        api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_api_key") or os.getenv("AZURE_API_KEY") or ""
        endpoint = os.getenv("AZURE_OPENAI_BASE_URL") or os.getenv("AZURE_base_url") or os.getenv("AZURE_ENDPOINT") or ""
        model = os.getenv("AZURE_OPENAI_DEPLOYMENT") or os.getenv("AZURE_deployment_name") or os.getenv("AZURE_MODEL") or ""
    else:
        api_key = _get_env(name, "api_key", "")
        endpoint = (_get_env(name, "base_url", _get_env(name, "endpoint", "")) or "").strip()
        model = _get_env(name, "model", _get_env(name, "deployment", _get_env(name, "deployment_name", "")))
    
    extra = _parse_extra_json(os.getenv("LLM_EXTRA_JSON"))
    api_version = _get_env(name, "api_version") or os.getenv("AZURE_api_version")
    if api_version:
        extra["api_version"] = api_version

    # Registry of explicit providers
    registry = {
        "local": _create_local_provider,
        "ollama": _create_ollama_provider,
        "lmstudio": _create_lmstudio_provider,
        "gemini": _create_gemini_provider,
        "projects": _create_azure_projects_provider,
        "azure_openai": _create_azure_openai_provider,
        "azure": _create_azure_openai_provider, # alias
        "azure_ai_inference": _create_azure_inference_provider,
    }

    if name in registry:
        return registry[name](name, api_key, endpoint, model, extra)

    # 3. Dynamic Type Detection
    url = (endpoint or "").lower()
    if any(x in url for x in ["openai.azure.com", "cognitiveservices.azure.com"]):
         return _create_azure_openai_provider(name, api_key, endpoint, model, extra)

    if any(x in url for x in ["models.ai.azure.com", "services.ai.azure.com"]):
         return _create_azure_inference_provider(name, api_key, endpoint, model, extra)

    # Default to OpenAI
    if endpoint or api_key:
         return _create_openai_provider(name, api_key, endpoint, model, extra)

    return MockLLM(), f"MockLLM (unknown provider {name})"
