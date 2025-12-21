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

    def _openai_tools_to_gemini(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        if not tools:
            return None
        decls: List[Dict[str, Any]] = []
        for t in tools:
            if not isinstance(t, dict):
                continue
            if t.get("type") != "function":
                continue
            fn = t.get("function") or {}
            name = fn.get("name")
            if not name:
                continue
            decls.append(
                {
                    "name": name,
                    "description": fn.get("description", "") or "",
                    "parameters": fn.get("parameters", {"type": "object"}) or {"type": "object"},
                }
            )
        if not decls:
            return None
        return [{"functionDeclarations": decls}]

    def _openai_messages_to_gemini(self, messages: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
        system_parts: List[str] = []
        contents: List[Dict[str, Any]] = []

        for m in messages or []:
            role = (m.get("role") or "").strip().lower()
            content = m.get("content")
            if content is None:
                content = ""
            if not isinstance(content, str):
                content = json.dumps(content, default=str)

            if role == "system":
                if content.strip():
                    system_parts.append(content.strip())
                continue

            if role == "assistant":
                g_role = "model"
            elif role == "user":
                g_role = "user"
            elif role == "tool":
                # Gemini supports function responses, but our runtime uses OpenAI-style tool
                # messages. Treat as user-visible observation.
                tool_name = m.get("name")
                prefix = f"TOOL_RESULT({tool_name}): " if tool_name else "TOOL_RESULT: "
                content = prefix + content
                g_role = "user"
            else:
                # Fallback: treat unknown roles as user content.
                g_role = "user"

            contents.append({"role": g_role, "parts": [{"text": content}]})

        return ("\n\n".join(system_parts).strip(), contents)

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

        payload: Dict[str, Any] = {
            "contents": contents,
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        if gemini_tools:
            payload["tools"] = gemini_tools

        # Map some common generation options from config/extra.
        extra = getattr(self.config, "extra", {}) or {}
        generation_config: Dict[str, Any] = {}
        if "temperature" in extra:
            try:
                generation_config["temperature"] = float(extra.get("temperature"))
            except (TypeError, ValueError):
                # If temperature cannot be parsed as float, skip it
                pass
        if "max_output_tokens" in extra:
            try:
                generation_config["maxOutputTokens"] = int(extra.get("max_output_tokens"))
            except (TypeError, ValueError):
                # If max_output_tokens cannot be parsed as int, skip it
                pass
        if generation_config:
            payload["generationConfig"] = generation_config

        url = f"{endpoint}/v1beta/models/{model}:generateContent"
        params = {"key": api_key}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    raise RuntimeError(f"Gemini HTTP {resp.status}: {text[:500]}")
                data = json.loads(text) if text else {}

        candidates = data.get("candidates") or []
        if not candidates:
            return {"role": "assistant", "content": "", "tool_calls": None}

        content_obj = (candidates[0] or {}).get("content") or {}
        parts = content_obj.get("parts") or []

        out_text_parts: List[str] = []
        tool_calls: List[Dict[str, Any]] = []

        for p in parts:
            if not isinstance(p, dict):
                continue
            if "text" in p and isinstance(p.get("text"), str):
                out_text_parts.append(p.get("text") or "")
            fc = p.get("functionCall")
            if isinstance(fc, dict) and fc.get("name"):
                tool_calls.append(
                    {
                        "id": f"gemini-fn-{len(tool_calls)+1}",
                        "type": "function",
                        "function": {
                            "name": fc.get("name"),
                            "arguments": json.dumps(fc.get("args") or {}, ensure_ascii=False),
                        },
                    }
                )

        content_out = "".join(out_text_parts).strip()
        res = {"role": "assistant", "content": content_out}
        if tool_calls:
            res["tool_calls"] = tool_calls
        return res
