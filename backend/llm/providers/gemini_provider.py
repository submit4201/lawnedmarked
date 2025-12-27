from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import aiohttp

from .llmproviderbase import LLMProviderBase, LLMProviderConfigBase


class GeminiConfig(LLMProviderConfigBase):
    def __init__(self):
        super().__init__(name="gemini")
        # Prefer explicit GEMINI_* env vars via providers.factory.
        self.api_key = ""
        self.endpoint = "https://generativelanguage.googleapis.com"
        self.model = "gemini-2.0-flash"


class GeminiProvider(LLMProviderBase):
    """Google Gemini REST provider.

    Uses the Generative Language API `generateContent` endpoint.

    Notes:
    - Supports basic text generation.
    - Supports function calling when `tools` are provided in OpenAI-function schema.
    """

    def __init__(self, config: GeminiConfig | None = None):
        super().__init__(config or GeminiConfig())

    def _extract_tool_declaration(self, tool_dict: dict) -> Dict[str, Any] | None:
        """Extract a single tool declaration from OpenAI format."""
        if not isinstance(tool_dict, dict) or tool_dict.get("type") != "function":
            return None
        
        fn = tool_dict.get("function") or {}
        name = fn.get("name")
        if not name:
            return None
        
        return {
            "name": name,
            "description": fn.get("description", "") or "",
            "parameters": fn.get("parameters", {"type": "object"}) or {"type": "object"},
        }

    def _openai_tools_to_gemini(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """Convert OpenAI tool format to Gemini function declarations."""
        if not tools:
            return None
        
        decls = [
            decl for t in tools 
            if (decl := self._extract_tool_declaration(t)) is not None
        ]
        
        return [{"functionDeclarations": decls}] if decls else None

    def _convert_message_role(self, role: str, content: str, tool_name: str | None = None) -> tuple[str, str]:
        """Convert OpenAI role to Gemini role and potentially modify content."""
        if role == "assistant":
            return "model", content
        elif role == "user":
            return "user", content
        elif role == "tool":
            prefix = f"TOOL_RESULT({tool_name}): " if tool_name else "TOOL_RESULT: "
            return "user", prefix + content
        else:
            # Fallback: treat unknown roles as user content
            return "user", content

    def _process_message_content(self, content: Any) -> str:
        """Ensure message content is a string."""
        if content is None:
            return ""
        if not isinstance(content, str):
            return json.dumps(content, default=str)
        return content

    def _openai_messages_to_gemini(self, messages: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
        """Convert OpenAI messages format to Gemini contents format."""
        system_parts: List[str] = []
        contents: List[Dict[str, Any]] = []

        for m in messages or []:
            role = (m.get("role") or "").strip().lower()
            content = self._process_message_content(m.get("content"))

            if role == "system":
                if content.strip():
                    system_parts.append(content.strip())
                continue

            g_role, g_content = self._convert_message_role(role, content, m.get("name"))
            contents.append({"role": g_role, "parts": [{"text": g_content}]})

        return ("\n\n".join(system_parts).strip(), contents)

    # Config key mappings: (source_key, target_key, type_func)
    _CONFIG_MAPPINGS = [
        ("temperature", "temperature", float),
        ("max_output_tokens", "maxOutputTokens", int),
    ]

    def _build_generation_config(self, extra: dict) -> Dict[str, Any]:
        """Build generation config from extra parameters."""
        config: Dict[str, Any] = {}
        for source_key, target_key, type_func in self._CONFIG_MAPPINGS:
            if source_key in extra:
                try:
                    config[target_key] = type_func(extra[source_key])
                except (TypeError, ValueError):
                    pass
        return config

    def _build_payload(
        self, 
        contents: List[Dict[str, Any]], 
        system_instruction: str,
        gemini_tools: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Build the request payload for Gemini API."""
        payload: Dict[str, Any] = {"contents": contents}
        
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        if gemini_tools:
            payload["tools"] = gemini_tools
        
        extra = getattr(self.config, "extra", {}) or {}
        generation_config = self._build_generation_config(extra)
        if generation_config:
            payload["generationConfig"] = generation_config
        
        return payload

    async def _make_api_request(self, url: str, params: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make the HTTP request to Gemini API."""
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    raise RuntimeError(f"Gemini HTTP {resp.status}: {text[:500]}")
                return json.loads(text) if text else {}

    def _parse_response_parts(self, parts: List[Any]) -> tuple[List[str], List[Dict[str, Any]]]:
        """Parse response parts to extract text and tool calls."""
        out_text_parts: List[str] = []
        tool_calls: List[Dict[str, Any]] = []

        for p in parts:
            if not isinstance(p, dict):
                continue
            
            text = self._extract_text_from_part(p)
            if text:
                out_text_parts.append(text)
            
            tool_call = self._extract_tool_call_from_part(p, len(tool_calls))
            if tool_call:
                tool_calls.append(tool_call)

        return out_text_parts, tool_calls

    def _extract_text_from_part(self, part: dict) -> str | None:
        """Extract text content from a response part."""
        if "text" in part and isinstance(part.get("text"), str):
            return part.get("text") or ""
        return None

    def _extract_tool_call_from_part(self, part: dict, index: int) -> dict | None:
        """Extract tool call from a response part."""
        fc = part.get("functionCall")
        if isinstance(fc, dict) and fc.get("name"):
            return {
                "id": f"gemini-fn-{index+1}",
                "type": "function",
                "function": {
                    "name": fc.get("name"),
                    "arguments": json.dumps(fc.get("args") or {}, ensure_ascii=False),
                },
            }
        return None

    def _format_response(self, data: Dict[str, Any]) -> dict:
        """Format Gemini API response to OpenAI-compatible format."""
        candidates = data.get("candidates") or []
        if not candidates:
            return {"role": "assistant", "content": "", "tool_calls": None}

        content_obj = (candidates[0] or {}).get("content") or {}
        parts = content_obj.get("parts") or []

        out_text_parts, tool_calls = self._parse_response_parts(parts)

        content_out = "".join(out_text_parts).strip()
        res = {"role": "assistant", "content": content_out}
        if tool_calls:
            res["tool_calls"] = tool_calls
        return res

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        step_idx: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> dict:
        api_key = (self.config.api_key or "").strip()
        if not api_key:
            raise RuntimeError("Gemini api_key is missing (set GEMINI_API_KEY)")

        endpoint = (self.config.endpoint or "").rstrip("/")
        model = (self.config.model or "").strip() or "gemini-1.5-flash"

        system_instruction, contents = self._openai_messages_to_gemini(messages)
        gemini_tools = self._openai_tools_to_gemini(tools)
        payload = self._build_payload(contents, system_instruction, gemini_tools)

        url = f"{endpoint}/v1beta/models/{model}:generateContent"
        params = {"key": api_key}

        data = await self._make_api_request(url, params, payload)
        return self._format_response(data)
