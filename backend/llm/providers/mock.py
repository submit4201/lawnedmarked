from __future__ import annotations

from typing import Any, Dict, List, Optional

from .llmproviderbase import LLMProviderBase, LLMProviderConfigBase


class MockLLM(LLMProviderBase):
    def __init__(self):
        super().__init__(LLMProviderConfigBase(name="mock"))

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        step_idx: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # Deterministic output: propose a SetPrice command.
        # Useful as a safe fallback when real providers are misconfigured.
        return {
            "role": "assistant",
            "content": "Command(SetPrice): {\"location_id\": \"LOC_001\", \"service_name\": \"StandardWash\", \"new_price\": 4.25}",
            "tool_calls": None,
        }
