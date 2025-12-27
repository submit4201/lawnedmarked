from __future__ import annotations

from typing import Optional, Any, Dict

from .llmproviderbase import LLMProviderBase, LLMProviderConfigBase


class OpenAIConfig(LLMProviderConfigBase):
    def __init__(self):
        super().__init__(name="openai")
        self.api_key = ""
        self.endpoint = ""  # leave empty for OpenAI default
        self.model = "gpt-4o-mini"


class OpenAIProvider(LLMProviderBase):
    def __init__(self, config: OpenAIConfig | None = None):
        super().__init__(config or OpenAIConfig())
        self._client = self._create_client()

    def _create_client(self):
        from openai import AsyncOpenAI

        base_url = (self.config.endpoint or "").rstrip("/")
        timeout_s = float((self.config.extra or {}).get("timeout_s", 30.0))
        return AsyncOpenAI(api_key=self.config.api_key, base_url=base_url or None, timeout=timeout_s)

    def client(self):
        return self._client

    async def chat(self, request: "ChatRequest") -> dict:
        create_kwargs: Dict[str, Any] = {
            "model": self.config.model,
            "messages": request.messages,
            "temperature": float(self.config.extra.get("temperature", 0.2)),
        }
        if request.tools is not None:
            create_kwargs["tools"] = request.tools

        for k, v in (self.config.extra or {}).items():
            if k in {"temperature"}:
                continue
            if k not in create_kwargs:
                create_kwargs[k] = v

        resp = await self._client.chat.completions.create(**create_kwargs)
        msg = resp.choices[0].message if getattr(resp, "choices", None) else None
        content = getattr(msg, "content", "") if msg else ""
        tool_calls = getattr(msg, "tool_calls", None) if msg else None
        return {"role": "assistant", "content": content or "", "tool_calls": tool_calls}
