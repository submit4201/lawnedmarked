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

    # Supported OpenAI-compatible parameters
    DIRECT_PARAMS = frozenset({
        "max_tokens", "temperature", "top_p", "frequency_penalty",
        "presence_penalty", "stop", "seed", "response_format", "tool_choice",
        "parallel_tool_calls", "logprobs", "top_logprobs", "n", "user", "stream",
    })

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        step_idx: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> dict:
        complete_kwargs = self._build_chat_kwargs(messages, tools, kwargs)
        resp = await self._client.complete(**complete_kwargs)
        return self._parse_response(resp)

    def _build_chat_kwargs(
        self, 
        messages: list[dict], 
        tools: Optional[list[dict]], 
        call_kwargs: dict
    ) -> Dict[str, Any]:
        """Build kwargs dict for chat completion call."""
        temperature = float((self.config.extra or {}).get("temperature", 0.2))
        
        complete_kwargs: Dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
        }

        if self.config.model:
            complete_kwargs["model"] = self.config.model

        if tools is not None:
            complete_kwargs["tools"] = tools

        # Process extra config
        model_extras = self._process_extra_config(complete_kwargs)
        if model_extras:
            complete_kwargs["model_extras"] = model_extras

        # Per-call overrides
        for k, v in call_kwargs.items():
            if k not in complete_kwargs:
                complete_kwargs[k] = v

        return complete_kwargs

    def _process_extra_config(self, complete_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Process extra config into direct params or model extras."""
        extras = dict(self.config.extra or {})
        extras.pop("api_version", None)

        model_extras: Dict[str, Any] = {}
        for k, v in extras.items():
            if k == "temperature":
                continue
            if k in self.DIRECT_PARAMS and k not in complete_kwargs:
                complete_kwargs[k] = v
            else:
                model_extras[k] = v
        return model_extras

    def _parse_response(self, resp: Any) -> dict:
        """Parse response into OpenAI-compatible format."""
        msg = resp.choices[0].message if getattr(resp, "choices", None) else None
        content = getattr(msg, "content", "") if msg else ""
        tool_calls = getattr(msg, "tool_calls", None) if msg else None
        return {"role": "assistant", "content": content or "", "tool_calls": tool_calls}
