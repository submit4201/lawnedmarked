from __future__ import annotations

from typing import Any, Dict, Optional

from .llmproviderbase import LLMProviderBase, LLMProviderConfigBase


class FallbackProvider(LLMProviderBase):
    """Try multiple providers in order, falling back only on exceptions.

    This keeps the rest of the codebase simple: the dispatcher still selects a
    single provider_key, but that provider can internally retry via alternates.
    """

    def __init__(self, providers: list[LLMProviderBase], name: str = "fallback"):
        if not providers:
            raise ValueError("FallbackProvider requires at least one provider")
        super().__init__(LLMProviderConfigBase(name=name))
        self._providers = providers

    def client(self):
        # Best-effort: return the first provider's client.
        try:
            return self._providers[0].client()
        except Exception:
            return None

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        step_idx: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> dict:
        last_exc: Exception | None = None
        for provider in self._providers:
            try:
                return await provider.chat(
                    messages,
                    tools=tools,
                    step_idx=step_idx,
                    config=config,
                    **kwargs,
                )
            except Exception as exc:
                last_exc = exc
                continue
        raise last_exc or RuntimeError("All fallback providers failed")
