from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class LLMProviderConfig:
    name: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    model: Optional[str] = None
    extra: Dict[str, Any] = None


class LLMProvider:
    def __init__(self, config: LLMProviderConfig):
        self.config = config

    async def chat(self, messages: list[dict]) -> dict:
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    async def chat(self, messages: list[dict]) -> dict:
        # Placeholder implementation with basic retry/backoff scaffold
        for attempt in range(3):
            try:
                return {"role": "assistant", "content": "[mock-openai]"}
            except Exception:
                if attempt == 2:
                    raise
        return {"role": "assistant", "content": "[mock-openai]"}


class AzureOpenAIProvider(LLMProvider):
    async def chat(self, messages: list[dict]) -> dict:
        return {"role": "assistant", "content": "[mock-azure-openai]"}


class OllamaProvider(LLMProvider):
    async def chat(self, messages: list[dict]) -> dict:
        # Call local HTTP endpoint in production
        return {"role": "assistant", "content": "[mock-ollama]"}


class LMStudioProvider(LLMProvider):
    async def chat(self, messages: list[dict]) -> dict:
        import httpx
        import asyncio
        import logging

        logger = logging.getLogger("uvicorn")

        # Buffer to prevent back-to-back overload on local model
        await asyncio.sleep(2.0)

        url = (self.config.endpoint or "http://127.0.0.1:1234").rstrip("/") + "/v1/chat/completions"
        
        # Default parameters
        params = {
            "model": self.config.model or "google/gemma-3n-e4b",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": -1,
            "stream": False
        }
        
        # Override with extra config if present
        if self.config.extra:
            params.update(self.config.extra)

        # Single attempt with long timeout - no retries to avoid crashing local model
        async with httpx.AsyncClient(timeout=300.0) as client:
            logger.info(f"Sending request to LLM with {len(messages)} messages...")
            resp = await client.post(url, json=params)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"role": "assistant", "content": content}


# Deterministic local mock for tests
class MockLLM(LLMProvider):
    def __init__(self):
        super().__init__(LLMProviderConfig(name="mock"))

    async def chat(self, messages: list[dict]) -> dict:
        return {
            "role": "assistant",
            "content": "Command(SetPrice): {\"location_id\": \"LOC_001\", \"service_name\": \"StandardWash\", \"new_price\": 4.25}"
        }
