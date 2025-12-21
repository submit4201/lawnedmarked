import os
import json
from typing import Any, Dict, Optional, List

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, FunctionTool

# Handle import of base class properly
try:
    from .llmproviderbase import LLMProviderBase, LLMProviderConfigBase
except ImportError:
    # If running as script
    from llmproviderbase import LLMProviderBase, LLMProviderConfigBase

class AzureAIProjectsConfig(LLMProviderConfigBase):
    def __init__(self):
        super().__init__(name="azure_ai_projects")
        # Defaults
        self.endpoint = os.getenv("AZURE_PROJECT_ENDPOINT", "https://sigal-openai.services.ai.azure.com/api/projects/sigal-openai-project")
        self.api_key = os.getenv("AZURE_PROJECT_API_KEY", "") # Empty default, prefer env var
        self.agent_name = os.getenv("AZURE_AGENT_NAME", "gpttycoonagent") 
        self.model = os.getenv("AZURE_AGENT_MODEL", "gpt-5-nano")

class AzureAIProjectsProvider(LLMProviderBase):
    def __init__(self, config: AzureAIProjectsConfig | None = None):
        super().__init__(config or AzureAIProjectsConfig())
        
        credential = DefaultAzureCredential()
        
        if self.config.api_key:
            print("[AzureAIProjectsProvider] Note: API Key provided but DefaultAzureCredential is preferred for AIProjectClient.")
            
        self._client = AIProjectClient(
            endpoint=self.config.endpoint,
            credential=credential,
        )

        # Pre-create a default agent version
        try:
             self._agent = self._client.agents.create_version(  
                agent_name=self.config.agent_name,
                definition=PromptAgentDefinition(
                        model=self.config.model,
                ),
            )
        except Exception as e:
            print(f"[AzureAIProjectsProvider] Failed to initialize default agent version: {e}")
            self._agent = None

        self._openai_client = self._client.get_openai_client()
            
    def _create_agent(self, tools: Optional[list[dict]] = None):
        azure_tools = []
        if tools:
            for ts in tools:
                fn_def = ts.get("function", ts)
                azure_tools.append(FunctionTool(
                    name=fn_def.get("name"),
                    parameters=fn_def.get("parameters"),
                    description=fn_def.get("description", ""),
                ))

        if not azure_tools and self._agent:
             return self._agent

        definition = PromptAgentDefinition(
            model=self.config.model,
            tools=azure_tools if azure_tools else None
        )
        
        return self._client.agents.create_version(
            agent_name=self.config.agent_name,
            definition=definition
        )

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        step_idx: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> dict:  
        agent = self._create_agent_version(tools)
        if not agent:
             return {"error": "Failed to create agent version"}

        openai_client = self._openai_client
        
        payload_messages = []
        for m in messages:
            content = m.get("content")
            role = m.get("role")
            
            if not isinstance(content, str) and content is not None:
                content = json.dumps(content)
            
            item = {
                "type": "message",
                "role": role,
                "content": content or ""
            }
            payload_messages.append(item)

        try:
            response = openai_client.responses.create(
                input=payload_messages,
                extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
            )
            
            content = getattr(response, "output_text", "")
            if not content and hasattr(response, "choices"):
                 content = response.choices[0].message.content
                 
            tool_calls = []
            if hasattr(response, "choices") and response.choices:
                msg = response.choices[0].message
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_calls.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        })
            
            return {
                "role": "assistant",
                "content": content or "",
                "tool_calls": tool_calls
            }
        except Exception as e:
            print(f"[AzureAIProjectsProvider] Chat failed: {e}")
            raise e

if __name__ == "__main__":
    # Test block
    try:
        agent_provider = AzureAIProjectsProvider()
        # Mock synchronous run for testing if chat was synchronous, but it is async in base. 
        # Here we just print config.
        print(f"Initialized provider for endpoint: {agent_provider.config.endpoint}")
    except Exception as e:
        print(f"Failed to init: {e}")
