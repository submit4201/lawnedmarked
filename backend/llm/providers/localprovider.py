

from .llmproviderbase import LLMProviderConfigBase as LLMProviderConfig
from .llmproviderbase import LLMProviderBase as LLMProvider


class localConfig(LLMProviderConfig):
    def __init__(self):
        super().__init__()
        self.api_key = "sk-no-key-required"  # not used for local
        self.endpoint = "http://localhost:8007/v1"
        # Default to the model exposed by llmquickserver (from /v1/models)
        # Example returned ID: C:\\Users\\dickdick\\gitrepos\\llmquickserver\\Echo9Zulu_gemma-3-12b-it-OpenVINO\\gemma-3-12b-it-int4_asym-ov
        self.model = "C:\\Users\\dickdick\\gitrepos\\llmquickserver\\Echo9Zulu_gemma-3-12b-it-OpenVINO\\gemma-3-12b-it-int4_asym-ov"
    

class LocalProvider(LLMProvider):
    """Local quick LLM server compatible with OpenAI API"""
    
    def __init__(self, config=None):
        if config is None:
            config = localConfig()
        super().__init__(config)
        self.config = config  # keep a reference for diagnostics
        self.client = self._create_client()

    def _create_client(self):
        from openai import AsyncOpenAI

        timeout_s = float(getattr(self.config, "extra", {}).get("timeout_s", 30.0))
        base_url = (self.config.endpoint or "").rstrip("/")
        client = AsyncOpenAI(api_key=self.config.api_key, base_url=base_url, timeout=timeout_s)
        print(f"[LLM][local] client created endpoint={base_url!r} timeout_s={timeout_s}")
        return client
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        step_idx: int | None = None,
        config: dict | None = None,
        **kwargs,
    ) -> dict:
        """Send messages to local LLM and get response."""
        from time import perf_counter

        t0 = perf_counter()
        endpoint = (self.config.endpoint or "").rstrip("/")
        tool_count = len(tools) if tools else 0
        print(
            f"[LLM][local] request step={step_idx} model={self.config.model!r} endpoint={endpoint!r} tools={tool_count}"
        )

        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            tools=tools,
            temperature=float(getattr(self.config, "extra", {}).get("temperature", 0.2)),
            stop=["\nuser", "\n[SYSTEM:", "\nTOOL_RESULT"],
        )
        msg = response.choices[0].message if response.choices else None
        content = msg.content if msg else ""
        tool_calls = getattr(msg, "tool_calls", None) if msg else None
        dt_ms = int((perf_counter() - t0) * 1000)
        preview = (content or "").replace("\n", " ")[:160]
        print(f"[LLM][local] response step={step_idx} elapsed_ms={dt_ms} content_len={len(content or '')} preview={preview!r}")
        return {"role": "assistant", "content": content, "tool_calls": tool_calls}