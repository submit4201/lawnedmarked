from __future__ import annotations
import re
from typing import Any, List
from pathlib import Path
from datetime import datetime

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
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_{agent_id}.md"
        filepath = self.log_dir / filename
        
        with open(filepath, "a", encoding="utf-8") as f:
            if step_idx == 0:
                f.write(f"\n---\n# Turn Log: {agent_id} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            fwrite = f.write
            fwrite(f"---\n## Step {step_idx + 1}\n\n")
            
            # Raw Response
            fwrite("### Raw Response\n\n")
            fwrite(f"```\n{content}\n```\n\n")

            # Sections
            patterns = [
                ("Thought", r"<\|-THOUGHT-\|>(.*?)(?=<\|-|$)"),
                ("Action Plan", r"<\|-ACTION PLAN-\|>(.*?)(?=<\|-|$)"),
                ("Checks", r"<\|-CHECKS-\|>(.*?)(?=<\|-|$)"),
                ("Command", r"<\|-COMMAND-\|>(.*?)(?=<\|-|$)"),
                ("Notes", r"<\|-NOTES-\|>(.*?)(?=<\|-|$)"),
            ]
            
            found_sections = False
            for title, pattern in patterns:
                match = re.search(pattern, content, re.S)
                if match:
                    text = match.group(1).strip()
                    if text:
                        f.write(f"### {title}\n{text}\n\n")
                        found_sections = True
            
            if tool_calls:
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
                found_sections = True

            if command_extraction and command_extraction.command_name:
                f.write(f"### Extracted Command (Text Fallback)\n")
                f.write(f"- **{command_extraction.command_name}**\n")
                f.write(f"  ```json\n{command_extraction.payload_json}\n  ```\n\n")
                found_sections = True

            if not found_sections and content.strip():
                if content.strip() != "Executing tool calls...":
                    f.write(f"### Raw Response\n{content.strip()}\n\n")
            
            if tool_results:
                f.write("### Tool Results\n")
                for res in tool_results:
                    name = res.get("name")
                    out = res.get("content")
                    if len(out) > 2000:
                        out = out[:2000] + "... (truncated)"
                    f.write(f"#### {name}\n{out}\n\n")

            f.write("---\n")
