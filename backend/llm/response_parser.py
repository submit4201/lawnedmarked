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
        calls = []
        # Match <tool_call> ... </tool_call> or <tool_call> ... (if tag is not closed)
        # We use a more robust pattern that captures everything between tags.
        pattern = r"<tool_call>\s*(.*?)\s*(?:</tool_call>|(?=<tool_call>)|$)"
        matches = re.finditer(pattern, text, re.S)
        
        for m in matches:
            try:
                raw_content = m.group(1).strip()
                # Remove markdown code blocks if present
                if raw_content.startswith("```"):
                    raw_content = re.sub(r"^```(?:json)?\n", "", raw_content)
                    raw_content = re.sub(r"\n```$", "", raw_content)
                
                # Try to find the first { and last } to extract JSON
                start = raw_content.find("{")
                end = raw_content.rfind("}")
                if start != -1 and end != -1:
                    json_str = raw_content[start:end+1]
                    
                    # Handle escaped JSON if the LLM wrapped it in a string
                    if "\\\"" in json_str:
                        try:
                            # Try to unescape by loading as a string first if it's wrapped in quotes
                            if raw_content.startswith("\"") and raw_content.endswith("\""):
                                json_str = json.loads(raw_content)
                            else:
                                # Manual unescape for common cases
                                json_str = json_str.replace("\\\"", "\"").replace("\\\\", "\\")
                        except:
                            pass

                    data = json.loads(json_str)
                    name = data.get("name")
                    args = data.get("arguments") or {}
                    if name:
                        calls.append({
                            "id": f"call_{uuid.uuid4().hex[:8]}",
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": json.dumps(args) if isinstance(args, dict) else str(args)
                            }
                        })
            except Exception as e:
                print(f"[LLM] Error parsing tool call: {e}")
                continue
        return calls

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
