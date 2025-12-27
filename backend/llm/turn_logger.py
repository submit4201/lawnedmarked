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

    def log_turn(self, ctx: TurnContext):
        """Log the turn step to a markdown file."""
        self._log_turn_context(ctx)

    @staticmethod
    def create_context(agent_id: str, step_idx: int, content: str, 
                       tool_calls: list = None, tool_results: list = None, 
                       command_extraction: Any = None) -> TurnContext:
        """Factory method to create TurnContext with defaults."""
        return TurnContext(
            agent_id=agent_id, 
            step_idx=step_idx, 
            content=content, 
            tool_calls=tool_calls or [], 
            tool_results=tool_results or [], 
            command_extraction=command_extraction
        )

    def _log_turn_context(self, ctx: TurnContext):
        filepath = self._get_log_filepath(ctx.agent_id)
        
        with open(filepath, "a", encoding="utf-8") as f:
            self._write_header_if_first_step(f, ctx)
            self._write_step_content(f, ctx)
            self._write_structured_sections(f, ctx)
            self._write_footer(f, ctx)

    def _get_log_filepath(self, agent_id: str) -> Path:
        """Get the log file path for this agent."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"{date_str}_{agent_id}.md"

    def _write_header_if_first_step(self, f, ctx: TurnContext):
        """Write turn header for first step."""
        if ctx.step_idx == 0:
            f.write(f"\n---\n# Turn Log: {ctx.agent_id} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    def _write_step_content(self, f, ctx: TurnContext):
        """Write step header and raw response."""
        f.write(f"---\n## Step {ctx.step_idx + 1}\n\n")
        f.write("### Raw Response\n\n")
        f.write(f"```\n{ctx.content}\n```\n\n")

    def _write_structured_sections(self, f, ctx: TurnContext):
        """Write parsed sections, tool calls, and command extraction."""
        found_sections = self._log_response_sections(f, ctx.content)
        found_sections = self._try_log_tool_calls(f, ctx.tool_calls) or found_sections
        found_sections = self._try_log_command(f, ctx.command_extraction) or found_sections
        self._log_fallback_content(f, ctx.content, found_sections)

    def _try_log_tool_calls(self, f, tool_calls: list) -> bool:
        """Log tool calls if present. Returns True if logged."""
        if not tool_calls:
            return False
        self._log_tool_calls(f, tool_calls)
        return True

    def _try_log_command(self, f, extraction) -> bool:
        """Log command extraction if present. Returns True if logged."""
        if not extraction or not getattr(extraction, 'command_name', None):
            return False
        self._log_command_extraction(f, extraction)
        return True

    def _log_fallback_content(self, f, content: str, found_sections: bool):
        """Log raw content as fallback if no sections found."""
        content_stripped = content.strip()
        if found_sections or not content_stripped:
            return
        if content_stripped == "Executing tool calls...":
            return
        f.write(f"### Raw Response\n{content_stripped}\n\n")

    def _write_footer(self, f, ctx: TurnContext):
        """Write tool results and separator."""
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
