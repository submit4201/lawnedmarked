

from llm.providers import LLMProviderConfig, LLMProvider


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
        from openai import OpenAI
        return OpenAI(api_key=self.config.api_key, base_url=self.config.endpoint)
    
    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Send messages to local LLM and get response."""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            tools=tools,
            temperature=0.2,
        )
        msg = response.choices[0].message if response.choices else None
        content = msg.content if msg else ""
        tool_calls = getattr(msg, "tool_calls", None) if msg else None
        return {"role": "assistant", "content": content, "tool_calls": tool_calls}