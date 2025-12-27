from __future__ import annotations
import re
import json
import uuid
from typing import List, Tuple, Dict, Any

class ResponseParser:
    """Handles parsing of LLM responses to extract structured data."""

    @staticmethod
    def extract_thought(content: str) -> str:
        if not content:
            return ""
        # Try to find everything after <|-THOUGHT-|> until the next tag or end of string
        m = re.search(r"<\|\-THOUGHT\-\|>\s*(.*?)\s*(?:<\|-|$)", content, re.S)
        if m:
            return m.group(1).strip()
        
        # Fallback: if no tag, just return the first 500 chars if not empty
        return content.strip()[:500]

    @staticmethod
    def extract_actions(content: str) -> List[Tuple[str, str]]:
        '''extract the actions section from the content
        <|-ACTIONS-|> ... <|-ENDACTIONS-|>
        and extract commands from inside it.
        Commands are in the format:
        Command(NAME): {json payload} 
        '''
        if not content:
            return []
        m = re.search(r"<\|\-ACTIONS\-\|>\s*(.*?)\s*<\|\-ENDACTIONS\-\|>", content, re.S)
        if m:
            actions_content = m.group(1).strip()
            command_pattern = re.compile(r"Command\((.*?)\):\s*(\{.*?\})", re.S)
            commands = command_pattern.findall(actions_content)
            result = []
            for name, payload in commands:
                result.append((name.strip(), payload.strip()))
            return result
        
        return []

    @staticmethod
    def extract_notes(content: str) -> str:
        if not content:
            return ""
        # Match <|-NOTES-|> and everything after it, but stop if we see <|-ENDNOTES-|> or <|-ENDTURN-|>
        m = re.search(
            r"<\|\-NOTES\-\|>\s*(.*?)(?:\s*<\|\-ENDNOTES\-\|>|\s*<\|\-ENDTURN-|>|$)",
            content,
            re.S,
        )
        if m:
            return m.group(1).strip()
        return ""

    @staticmethod
    def wants_end_turn(content: str, tool_name: str | None) -> bool:
        if tool_name == "end_of_turn":
            return True
        # Robust check for end turn tag, allowing for common typos like } instead of >
        return bool(re.search(r"<\|\-ENDTURN\-[\|>\}]", content or ""))

    @staticmethod
    def extract_tool_calls_from_text(text: str) -> list[dict]:
        """Extract <tool_call> tags from text and convert to OpenAI-style tool_calls."""
        if not text:
            return []

        calls = []
        pattern = r"<tool_call>\s*(.*?)\s*(?:</tool_call>|(?=<tool_call>)|$)"
        matches = re.finditer(pattern, text, re.S)
        
        for m in matches:
            tool_call = ResponseParser._parse_single_tool_call(m.group(1))
            if tool_call:
                calls.append(tool_call)
        return calls

    @staticmethod
    def _parse_single_tool_call(raw_content: str) -> dict | None:
        """Parse a single tool call content string."""
        try:
            json_str = ResponseParser._clean_json_content(raw_content)
            if not json_str:
                return None

            data = json.loads(json_str)
            name = data.get("name")
            args = data.get("arguments") or {}
            
            if name:
                return {
                    "id": f"call_{uuid.uuid4().hex[:8]}",
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": json.dumps(args) if isinstance(args, dict) else str(args)
                    }
                }
        except Exception as e:
            print(f"[LLM] Error parsing tool call: {e}")
        
        return None

    @staticmethod
    def _clean_json_content(raw_content: str) -> str | None:
        """Clean and extract JSON string from raw content."""
        clean = ResponseParser._strip_markdown_code_block(raw_content.strip())
        
        # Extract JSON object
        json_str = ResponseParser._extract_json_object(clean)
        if not json_str:
            return None
        
        # Handle escaped JSON if needed
        return ResponseParser._unescape_json_if_needed(json_str, clean)

    @staticmethod
    def _strip_markdown_code_block(content: str) -> str:
        """Remove markdown code block wrappers."""
        if not content.startswith("```"):
            return content
        clean = re.sub(r"^```(?:json)?\n", "", content)
        return re.sub(r"\n```$", "", clean)

    @staticmethod
    def _extract_json_object(content: str) -> str | None:
        """Extract JSON object from content by finding { } bounds."""
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            return None
        return content[start:end+1]

    @staticmethod
    def _unescape_json_if_needed(json_str: str, original_clean: str) -> str:
        """Handle escaped JSON strings."""
        if "\\\"" not in json_str:
            return json_str
        
        try:
            if original_clean.startswith("\"") and original_clean.endswith("\""):
                return json.loads(original_clean)
            return json_str.replace("\\\"", "\"").replace("\\\\", "\\")
        except Exception:
            return json_str

    @staticmethod
    def is_info_tool(name: str) -> bool:
        return name in {"tool_help", "get_history", "get_state", "get_inventory"}

    @staticmethod
    def is_session_tool(name: str) -> bool:
        return name in {"end_of_turn"}
    
    @staticmethod
    def is_command_tool(name: str) -> bool:
        # Avoid circular import by checking against known info/session tools
        # Ideally we check against registry but this is a helper for now
        return not (ResponseParser.is_info_tool(name) or ResponseParser.is_session_tool(name))
