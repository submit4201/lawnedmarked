from __future__ import annotations
import re
from typing import Any, List
from pathlib import Path
from datetime import datetime

from dataclasses import dataclass, field

@dataclass
class TurnContext:
    agent_id: str
    step_idx: int
    content: str
    tool_calls: list = field(default_factory=list)
    tool_results: list = field(default_factory=list)
    command_extraction: Any = None

class TurnLogger:
    """Handles logging of LLM turns to markdown files."""

    def __init__(self, log_dir: Path | None = None):
        if log_dir is None:
            # Default to logs/turns relative to project root (assuming backend/llm/ location)
            self.log_dir = Path(__file__).resolve().parent.parent.parent / "logs" / "turns"
        else:
            self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_turn(self, agent_id: str, step_idx: int, content: str, tool_calls: list = None, tool_results: list = None, command_extraction: Any = None):
        """Log the turn step to a markdown file."""
        ctx = TurnContext(
            agent_id=agent_id, 
            step_idx=step_idx, 
            content=content, 
            tool_calls=tool_calls or [], 
            tool_results=tool_results or [], 
            command_extraction=command_extraction
        )
        self._log_turn_context(ctx)

    def _log_turn_context(self, ctx: TurnContext):
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_{ctx.agent_id}.md"
        filepath = self.log_dir / filename
        
        with open(filepath, "a", encoding="utf-8") as f:
            if ctx.step_idx == 0:
                f.write(f"\n---\n# Turn Log: {ctx.agent_id} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"---\n## Step {ctx.step_idx + 1}\n\n")
            f.write("### Raw Response\n\n")
            f.write(f"```\n{ctx.content}\n```\n\n")

            found_sections = self._log_response_sections(f, ctx.content)
            
            if ctx.tool_calls:
                self._log_tool_calls(f, ctx.tool_calls)
                found_sections = True

            if ctx.command_extraction and ctx.command_extraction.command_name:
                self._log_command_extraction(f, ctx.command_extraction)
                found_sections = True

            if not found_sections and ctx.content.strip():
                if ctx.content.strip() != "Executing tool calls...":
                    f.write(f"### Raw Response\n{ctx.content.strip()}\n\n")
            
            if ctx.tool_results:
                self._log_tool_results(f, ctx.tool_results)

            f.write("---\n")

    def _log_response_sections(self, f, content: str) -> bool:
        patterns = [
            ("Thought", r"<\|-THOUGHT-\|>(.*?)(?=<\|-|$)"),
            ("Action Plan", r"<\|-ACTION PLAN-\|>(.*?)(?=<\|-|$)"),
            ("Checks", r"<\|-CHECKS-\|>(.*?)(?=<\|-|$)"),
            ("Command", r"<\|-COMMAND-\|>(.*?)(?=<\|-|$)"),
            ("Notes", r"<\|-NOTES-\|>(.*?)(?=<\|-|$)"),
        ]
        
        found = False
        for title, pattern in patterns:
            match = re.search(pattern, content, re.S)
            if match:
                text = match.group(1).strip()
                if text:
                    f.write(f"### {title}\n{text}\n\n")
                    found = True
        return found

    def _log_tool_calls(self, f, tool_calls: list):
        f.write("### Tool Calls\n")
        for call in tool_calls:
            if isinstance(call, dict):
                name = call.get("function", {}).get("name")
                args = call.get("function", {}).get("arguments")
            else:
                name = getattr(getattr(call, "function", {}), "name", "unknown")
                args = getattr(getattr(call, "function", {}), "arguments", "{}")
            f.write(f"- **{name}**\n")
            f.write(f"  ```json\n{args}\n  ```\n")
        f.write("\n")

    def _log_command_extraction(self, f, extraction: Any):
        f.write(f"### Extracted Command (Text Fallback)\n")
        f.write(f"- **{extraction.command_name}**\n")
        f.write(f"  ```json\n{extraction.payload_json}\n  ```\n\n")

    def _log_tool_results(self, f, tool_results: list):
        f.write("### Tool Results\n")
        for res in tool_results:
            name = res.get("name")
            out = res.get("content")
            if len(out) > 2000:
                out = out[:2000] + "... (truncated)"
            f.write(f"#### {name}\n{out}\n\n")

    def log_console(self, step_idx: int, tool_calls: list):
        """Log tool calls to console (stdout)."""
        print(f"\n--- TOOL CALLS (Step {step_idx+1}) ---")
        for call in tool_calls:
            if isinstance(call, dict):
                fn = call.get("function") or {}
                t_name = fn.get("name")
                t_args = fn.get("arguments")
            else:
                t_name = getattr(getattr(call, "function", {}), "name", "unknown")
                t_args = getattr(getattr(call, "function", {}), "arguments", "{}")
            print(f"Tool: `{t_name}`")
            print(f"Args: ```json\n{t_args}\n```")
        print("-----------------------------------\n")
