from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class MockLLM:
    name: str = "mock-llm"

    async def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        # Deterministic output: propose a SetPrice command
        return {
            "role": "assistant",
            "content": "Command(SetPrice): {\"location_id\": \"LOC_001\", \"service_name\": \"StandardWash\", \"new_price\": 4.25}"
        }
