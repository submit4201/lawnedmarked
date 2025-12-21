from __future__ import annotations

from typing import Optional, Any, Dict

from .llmproviderbase import LLMProviderBase, LLMProviderConfigBase


class AzureOpenAIConfig(LLMProviderConfigBase):
    def __init__(self):
        super().__init__(name="azure_openai")
        self.api_key = ""
        self.endpoint = ""  # Azure endpoint, e.g. https://YOUR-RESOURCE.openai.azure.com/
        self.model = ""  # Azure deployment name
        # Optional: set via extra["api_version"]


class AzureOpenAIProvider(LLMProviderBase):
    def __init__(self, config: AzureOpenAIConfig | None = None):
        super().__init__(config or AzureOpenAIConfig())
        self._client = self._create_client()

    def _create_client(self):
        from openai import AsyncAzureOpenAI

        # ! Updated to newer API version for gpt-5 models
        api_version = (self.config.extra or {}).get("api_version") or "2025-01-01-preview"
        timeout_s = float((self.config.extra or {}).get("timeout_s", 60.0))
        return AsyncAzureOpenAI(
            api_key=self.config.api_key,
            azure_endpoint=self.config.endpoint,
            api_version=api_version,
            timeout=timeout_s,
        )

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
        # ! Minimal kwargs - only model and messages required
        # Some Azure models reject temperature or other params
        create_kwargs: Dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
        }
        
        # Only add tools if provided
        if tools is not None:
            create_kwargs["tools"] = tools

        # Only add optional params if explicitly set in extra
        extra = self.config.extra or {}
        for k in ["temperature", "max_tokens", "top_p"]:
            if k in extra:
                create_kwargs[k] = extra[k]

        try:
            resp = await self._client.chat.completions.create(**create_kwargs)
            msg = resp.choices[0].message if getattr(resp, "choices", None) else None
            content = getattr(msg, "content", "") if msg else ""
            tool_calls = getattr(msg, "tool_calls", None) if msg else None
            return {"role": "assistant", "content": content or "", "tool_calls": tool_calls}
        except Exception as e:
            # Log and re-raise with more context
            print(f"[AzureOpenAI] Error: {e}")
            raise

