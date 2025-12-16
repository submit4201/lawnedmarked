
class LLMProviderConfigBase:
    api_key: str
    endpoint: str
    model: str


class LLMProviderBase:
    def __init__(self, config: LLMProviderConfigBase):
        self.api_key = config.api_key
        self.endpoint = config.endpoint
        self.model = config.model

    def call(self, prompt: str) -> str:
        """
        Call the LLM with a prompt and return the response.
        
        Args:
            prompt: The input prompt for the LLM
            
        Returns:
            The LLM's response text
            
        Raises:
            NotImplementedError: Subclasses must implement this method
        """
        raise NotImplementedError("Subclasses must implement call()")

    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Call the LLM with chat messages.

        Args:
            messages: List of message dicts for chat-based LLMs
            tools: Optional OpenAI-style tool definitions

        Returns:
            The LLM's response as a dict
        """
        raise NotImplementedError("Subclasses must implement chat()")

    def client(self):
        """Return the underlying LLM client instance, if applicable."""
        return None