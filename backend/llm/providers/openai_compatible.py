from __future__ import annotations

from typing import Any, Dict, Optional

from .llmproviderbase import LLMProviderBase, LLMProviderConfigBase


class OpenAICompatibleProvider(LLMProviderBase):
    """Provider for OpenAI-compatible chat completion endpoints.

    Uses the official `openai` Python client with a custom `base_url`.
    """

    def __init__(self, config: LLMProviderConfigBase):
        super().__init__(config)
        self._client = self._create_client()

    def _create_client(self):
        from openai import OpenAI

        base_url = (self.config.endpoint or "").rstrip("/")
        return OpenAI(api_key=self.config.api_key or "sk-no-key-required", base_url=base_url or None)

    def client(self):
        return self._client

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        step_idx: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> dict:
        # NOTE: openai client is sync; we call it from an async method.
        # This is fine for the current local/dev usage. If we need true async,
        # we can swap to httpx or run in a thread pool.
        create_kwargs: Dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": float(self.config.extra.get("temperature", 0.2)),
        }
        if tools is not None:
            create_kwargs["tools"] = tools

        # Allow arbitrary pass-through (max_tokens, top_p, etc.) via config.extra
        for k, v in (self.config.extra or {}).items():
            if k in {"temperature"}:
                continue
            if k not in create_kwargs:
                create_kwargs[k] = v

        resp = self._client.chat.completions.create(**create_kwargs)
        msg = resp.choices[0].message if getattr(resp, "choices", None) else None
        content = getattr(msg, "content", "") if msg else ""
        tool_calls = getattr(msg, "tool_calls", None) if msg else None
        return {"role": "assistant", "content": content or "", "tool_calls": tool_calls}
