import pytest
from unittest.mock import MagicMock, AsyncMock
from backend.application_factory import ApplicationFactory
from backend.llm.dispatcher import LLMDispatcher

# --- ApplicationFactory Tests ---

def test_filter_events_by_id_found():
    events = [MagicMock(event_id="e1"), MagicMock(event_id="e2"), MagicMock(event_id="e3")]
    # Should perform strict equality check based on implementation
    # events[1] has id="e2"
    result = ApplicationFactory._filter_events_by_id(events, "e2")
    assert len(result) == 1
    assert result[0].event_id == "e3"

def test_filter_events_by_id_not_found():
    events = [MagicMock(event_id="e1"), MagicMock(event_id="e2")]
    result = ApplicationFactory._filter_events_by_id(events, "e99")
    assert result == []

def test_filter_events_by_id_none():
    events = [MagicMock(event_id="e1")]
    result = ApplicationFactory._filter_events_by_id(events, None)
    assert len(result) == 1

def test_apply_event_limit():
    events = list(range(10))
    result = ApplicationFactory._apply_event_limit(events, 3)
    assert result == [7, 8, 9]

def test_apply_event_limit_none():
    events = list(range(10))
    result = ApplicationFactory._apply_event_limit(events, None)
    assert len(result) == 10

def test_apply_event_limit_invalid():
    events = list(range(5))
    result = ApplicationFactory._apply_event_limit(events, "invalid")
    assert len(result) == 5

# --- LLMDispatcher Tests ---

class MockDispatcher(LLMDispatcher):
    def __init__(self):
        # minimal init for testing methods
        pass
    
    def _extract_message_content(self, m):
        return m.get("role", "user"), m.get("content", "")

    def _handle_system_message(self, content, system_parts):
        super()._handle_system_message(content, system_parts)

    def _handle_assistant_message(self, m, content):
        return super()._handle_assistant_message(m, content)

    def _handle_tool_message(self, m, content):
        return super()._handle_tool_message(m, content)

def test_normalize_single_message_user():
    d = LLMDispatcher(provider_map={}, provider_config_map={})
    sys_parts = []
    msg = {"role": "user", "content": "hello"}
    norm = d._normalize_single_message(msg, sys_parts)
    assert norm["role"] == "user"
    assert norm["content"] == "hello"

def test_normalize_single_message_system():
    d = LLMDispatcher(provider_map={}, provider_config_map={})
    sys_parts = []
    msg = {"role": "system", "content": "sys prompt"}
    norm = d._normalize_single_message(msg, sys_parts)
    assert norm is None
    assert sys_parts == ["sys prompt"]

def test_normalize_single_message_assistant_tool_calls_no_content():
    d = LLMDispatcher(provider_map={}, provider_config_map={})
    sys_parts = []
    msg = {"role": "assistant", "content": "", "tool_calls": [{"id": "1"}]}
    norm = d._normalize_single_message(msg, sys_parts)
    assert norm["role"] == "assistant"
    assert norm["content"] == "Executing tool calls..."

def test_normalize_single_message_tool():
    d = LLMDispatcher(provider_map={}, provider_config_map={})
    sys_parts = []
    msg = {"role": "tool", "name": "my_tool", "content": "result"}
    norm = d._normalize_single_message(msg, sys_parts)
    assert norm["role"] == "user"
    assert "TOOL_RESULT(my_tool): result" in norm["content"]

# --- AzureAIProjectsProvider Tests ---

class MockAzureProvider:
    # Minimal mock of the provider for testing helpers
    def _build_chat_payload(self, messages):
        # Import staticmethod or just implement logic same as class? 
        # Better to import the actual class if possible, but for unit testing verifying logic duplication or behavior:
        from backend.llm.providers.aiprojectspro import AzureAIProjectsProvider
        return AzureAIProjectsProvider._build_chat_payload(self, messages)

    def _parse_chat_response(self, response):
        from backend.llm.providers.aiprojectspro import AzureAIProjectsProvider
        return AzureAIProjectsProvider._parse_chat_response(self, response)

def test_azure_build_chat_payload():
    provider = MockAzureProvider()
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": {"some": "json"}}
    ]
    payload = provider._build_chat_payload(messages)
    assert len(payload) == 2
    assert payload[0]["type"] == "message"
    assert payload[0]["content"] == "hello"
    assert payload[1]["content"] == '{"some": "json"}'

def test_azure_parse_chat_response():
    from backend.llm.providers.aiprojectspro import AzureAIProjectsProvider, AzureAIProjectsConfig
    
    # Create real provider with minimal config
    config = AzureAIProjectsConfig()
    provider = AzureAIProjectsProvider.__new__(AzureAIProjectsProvider)
    provider.config = config
    
    # Mock response object structure
    class MockMessage:
        content = "response text"
        tool_calls = []
    
    class MockChoice:
        message = MockMessage()
        
    class MockResponse:
        output_text = ""
        choices = [MockChoice()]
        
    response = MockResponse()
    result = provider._parse_chat_response(response)
    
    assert result["role"] == "assistant"
    assert result["content"] == "response text"
    assert result["tool_calls"] == []


# --- Factory Registry Test ---
def test_factory_registry():
    from backend.llm.providers.factory import create_provider_from_env, LocalProvider, OpenAIProvider
    import os
    
    # Test local registry
    p, name = create_provider_from_env("local")
    assert isinstance(p, LocalProvider)
    
    # Test implicit OpenAI default
    os.environ["LLM_API_KEY"] = "sk-test"
    p2, name2 = create_provider_from_env("unknown_but_has_key")
    assert isinstance(p2, OpenAIProvider)
    del os.environ["LLM_API_KEY"]


# --- TurnLogger Refactor Test ---
def test_turn_logger_refactor(tmp_path):
    from backend.llm.turn_logger import TurnLogger, TurnContext
    logger = TurnLogger(log_dir=tmp_path)
    ctx = TurnContext("agent1", 0, "content", tool_calls=[{"function": {"name": "test"}}])
    logger.log_turn(ctx)
    
    files = list(tmp_path.glob("*.md"))
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert "Turn Log: agent1" in content
    assert "Tool Calls" in content
    assert "**test**" in content


# --- ResponseParser Refactor Test ---
def test_response_parser_refactor():
    from backend.llm.response_parser import ResponseParser
    text = '<tool_call>{"name": "test", "arguments": {"a": 1}}</tool_call>'
    calls = ResponseParser.extract_tool_calls_from_text(text)
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "test"
    assert '"a": 1' in calls[0]["function"]["arguments"]


# --- GeminiProvider Refactor Test ---
def test_gemini_provider_refactor():
    from backend.llm.providers.gemini_provider import GeminiProvider
    p = GeminiProvider()
    
    # Test _build_generation_config
    conf = p._build_generation_config({"temperature": "0.7", "max_output_tokens": "100"})
    assert conf["temperature"] == 0.7
    assert conf["maxOutputTokens"] == 100
    
    # Test _parse_response_parts
    parts = [{"text": "hello"}, {"functionCall": {"name": "foo", "args": {}}}]
    text, calls = p._parse_response_parts(parts)
    assert "hello" in text
    assert calls[0]["function"]["name"] == "foo"


# --- TurnOrchestrator Refactor Test ---
def test_turn_orchestrator_packet_builder():
    from backend.turn_orchestrator import _build_player_turn_packet
    class MockState:
        locations = {}
        cash_balance = 100.0
        current_week = 1
    
    packet = _build_player_turn_packet(MockState(), [])
    assert packet["finances"]["cash_balance"] == 100.0
    assert packet["time"]["week"] == 1
    assert "locations" in packet


# --- Vendor Handler Refactor Test ---
def test_vendor_handler_refactor():
    from backend.projection.handlers.vendor_handlers import handle_vendor_negotiation_result
    from core.models import AgentState, VendorRelationship
    from core.events import VendorNegotiationResult
    from datetime import datetime
    
    # Create a mock location with vendor_relationships dict
    class MockLocation:
        def __init__(self):
            self.vendor_relationships = {}
    
    # Removed 'agents' argument which does not exist on AgentState
    state = AgentState(agent_id="test_agent", locations={"loc1": MockLocation()})
    event = VendorNegotiationResult(
        event_id="evt_1", 
        agent_id="test_agent",
        timestamp=datetime.now(),
        week=1, 
        location_id="loc1", 
        vendor_id="v1",
        negotiation_succeeded=True, 
        proposed_discount=0.1
    )
    
    new_state = handle_vendor_negotiation_result(state, event)
    rel = new_state.locations["loc1"].vendor_relationships["v1"]
    assert rel.weeks_at_tier == 1
    assert rel.current_price_per_unit == 0.9


# --- Scan Todos Refactor Test ---
def test_scan_todos_refactor():
    from tools.scan_todos import _scan_line_for_todos
    # Corrected pattern to match [ ] as per rules
    res = _scan_line_for_todos("# [ ] fix this", "file.py", 10)
    assert res is not None
    assert "[TODO]" in res
    assert "fix this" in res

