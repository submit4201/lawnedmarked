from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, FunctionTool
from typing import Any, Dict, Optional

# Assuming this module is in the same package as llmproviderbase
# If this fails, we might need 'from .llmproviderbase' or check sys.path
try:
    from llmproviderbase import LLMProviderBase, LLMProviderConfigBase
except ImportError:
    from .llmproviderbase import LLMProviderBase, LLMProviderConfigBase

class AzureAIProjectsConfig(LLMProviderConfigBase):
    def __init__(self):
        super().__init__(name="azure_ai_projects")
        # Defaults for 'sigal-openai' project
        self.endpoint = "https://sigal-openai.services.ai.azure.com/api/projects/sigal-openai-project"
        self.api_key = "5vvx5XByPdYHXw9HNG5kOYpkFbrTq8PeRIKIoixz8LtVbA7FdL1pJQQJ99BJACHYHv6XJ3w3AAABACOGbLHs"
        self.agent_name = "gpttycoonagent" 
        self.model = "gpt-5-nano"

class AzureAIProjectsProvider(LLMProviderBase):
    def __init__(self, config: AzureAIProjectsConfig | None = None):
        super().__init__(config or AzureAIProjectsConfig())
        
        credential = DefaultAzureCredential()
        
        # NOTE: AIProjectClient (Azure Agent Service) typically requires Token Auth (Entra ID) for management operations.
        # AzureKeyCredential is not supported by the underlying BearerTokenCredentialPolicy used by this SDK.
        if self.config.api_key:
            print("[AzureAIProjectsProvider] Warning: An API Key was provided, but AIProjectClient requires DefaultAzureCredential (Token Auth). The API Key will be ignored for agent creation.")
            
        self._client = AIProjectClient(
            endpoint=self.config.endpoint,
            credential=credential,
        )

        self._agent = self._client.agents.create_version(  
            agent_name=self.config.agent_name,
            definition=PromptAgentDefinition(
                    model=self.config.model,
            ),
        )

        self._openai_client = self._client.get_openai_client()
        def get_token(self):
            return self._openai_client.get_token()
        # create the chat message
        def _chat(self, messages: list[dict]):
            response = self._openai_client.responses.create(
                input=payload_messages,
                extra_body={"agent": {"name": self._agent.name, "type": "agent_reference"}},
            )
            return response
            
    def _create_agent(self, tools: Optional[list[dict]] = None):
        azure_tools = []
        if tools:
            for ts in tools:
                # Handle both wrapped {"type": "function", "function": ...} and raw dicts
                fn_def = ts.get("function", ts)
                
                azure_tools.append(FunctionTool(
                    name=fn_def.get("name"),
                    parameters=fn_def.get("parameters"),
                    description=fn_def.get("description", ""),
                ))

        # Create a new version/agent with the specific tools for this turn
        if not azure_tools and self._agent:
             return self._agent

        # If we have tools, create a new version with them
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
        agent = self._create_agent(tools)
        openai_client = self._openai_client
        
        # Convert messages to the format expected by the API
        payload_messages = []
        for m in messages:
            content = m.get("content")
            role = m.get("role")
            
            # Handle non-string content
            if not isinstance(content, str) and content is not None:
                import json
                content = json.dumps(content)
            
            # Default type
            item_type = "message"
            
            # If this is a tool output (role=tool), we might need specific handling types
            # But usually 'message' works for basic text. 
            # If we need 'function_call_output', that requires more complex mapping of call_ids.
            # For now, treat everything as text messages to avoid complexity unless it breaks.
            
            item = {
                "type": item_type,
                "role": role,
                "content": content or ""
            }
            payload_messages.append(item)

        try:
            # print(f"[LLMProAI] Sending {len(payload_messages)} messages to agent '{agent.name}' with {len(tools or [])} tools")
            
            response = openai_client.responses.create(
                input=payload_messages,
                extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
            )
            
            # Extract content
            content = getattr(response, "output_text", "")
            if not content and hasattr(response, "choices"):
                 content = response.choices[0].message.content
                 
            # Extract tool calls (if any)
            # Inspect structure for 'function_call' or 'tool_calls'
            tool_calls = []
            
            # Check for native function_calls in response object attributes
            # The SDK might structure this differently.
            # Looking at common patterns: `response.choices[0].message.tool_calls`
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
            print(f"[LLMProAI] Chat failed: {e}")
            raise e
    

    def _get_openai_client(self):
        return self.client.get_openai_client()
    
    def _get_agent(self):
        return self.client.agents.get(self.config.agent_name)   
    
    def _get_response(self):
        return self.client.responses.create(    
            input=[{"role": "user", "content": "Tell me a one line story"}],
            extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
        )

#example
if   __name__ == "__main__":
    agent = AzureAIProjectsProvider()
    chat = agent.chat
    response = chat([{"role": "user", "content": "Tell me a one line joke"}])
    print(response)
