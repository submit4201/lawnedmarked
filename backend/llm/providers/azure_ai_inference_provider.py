from __future__ import annotations

from typing import Any, Dict, Optional

from .llmproviderbase import LLMProviderBase, LLMProviderConfigBase


class AzureAIInferenceConfig(LLMProviderConfigBase):
    def __init__(self):
        super().__init__(name="azure_ai_inference")
        self.api_key = ""
        # Endpoint examples:
        # - Azure AI Foundry deployment: https://<host>.<region>.models.ai.azure.com
        # - Azure OpenAI (deployment-scoped): https://<resource>.openai.azure.com/openai/deployments/<deployment>
        self.endpoint = ""
        self.model = ""  # Optional for Foundry endpoints; required for GitHub Models endpoints
        # Optional: set via extra["api_version"] (AOAI only)


class AzureAIInferenceProvider(LLMProviderBase):
    """Azure AI Inference provider.

    Uses the `azure-ai-inference` SDK (async client) and returns an OpenAI-like
    message dict: {"role": "assistant", "content": str, "tool_calls": Optional[list]}.
    """

    def __init__(self, config: AzureAIInferenceConfig | None = None):
        super().__init__(config or AzureAIInferenceConfig())
        self._client = self._create_client()

    def _create_client(self):
        from azure.ai.inference.aio import ChatCompletionsClient
        from azure.core.credentials import AzureKeyCredential

        api_version = (self.config.extra or {}).get("api_version")

        # `api_version` is only relevant for Azure OpenAI endpoints.
        if api_version:
            return ChatCompletionsClient(
                endpoint=self.config.endpoint,
                credential=AzureKeyCredential(self.config.api_key),
                api_version=str(api_version),
            )

        return ChatCompletionsClient(
            endpoint=self.config.endpoint,
            credential=AzureKeyCredential(self.config.api_key),
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
        # The azure-ai-inference client supports passing messages as a list of dicts
        # in OpenAI chat format: [{"role": "user", "content": "..."}, ...]

        direct_keys = {
            # Common OpenAI chat-completions params supported by Azure AI Inference.
            "max_tokens",
            "temperature",
            "top_p",
            "frequency_penalty",
            "presence_penalty",
            "stop",
            "seed",
            "response_format",
            "tool_choice",
            "parallel_tool_calls",
            "logprobs",
            "top_logprobs",
            "n",
            "user",
            "stream",
        }

        temperature = float((self.config.extra or {}).get("temperature", 0.2))

        complete_kwargs: Dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
        }

        # `model` is optional for some endpoints, but required for GitHub Models.
        if self.config.model:
            complete_kwargs["model"] = self.config.model

        if tools is not None:
            complete_kwargs["tools"] = tools

        extras = dict(self.config.extra or {})
        extras.pop("api_version", None)

        model_extras: Dict[str, Any] = {}
        for k, v in extras.items():
            if k == "temperature":
                continue
            if k in direct_keys and k not in complete_kwargs:
                complete_kwargs[k] = v
            else:
                model_extras[k] = v

        if model_extras:
            # For model-specific parameters, Azure AI Inference supports pass-through.
            complete_kwargs["model_extras"] = model_extras

        # Allow explicit per-call overrides via kwargs.
        for k, v in kwargs.items():
            if k not in complete_kwargs:
                complete_kwargs[k] = v

        resp = await self._client.complete(**complete_kwargs)
        msg = resp.choices[0].message if getattr(resp, "choices", None) else None
        content = getattr(msg, "content", "") if msg else ""
        tool_calls = getattr(msg, "tool_calls", None) if msg else None
        return {"role": "assistant", "content": content or "", "tool_calls": tool_calls}
