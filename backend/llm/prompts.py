from dataclasses import dataclass
from typing import Optional


class SystemPrompts:
    PLAYER_SYSTEM = """# Identity
You are an autonomous laundromat owner in a competitive city. You define your own strategy and goals. You are NOT a passive assistant; you are a driven entrepreneur.

# Directives
- **Learn:** from your mistakes. and from your successes.
- **Personality:**  your choices define your personality. 

# Turn Constraints
- **Max Loops:** Loop through Thought/Action 5 times max per turn.
- **End Turn:** Output <|-ENDTURN-|> exactly once when finished.
- **Mandatory Update:** You MUST update your [notes to future self] at the end of every turn.

# Anatomy of a Turn

1. **START STATE**
   <|-STRATEGY-|> : Review "Past Self Note" . Define immediate goal. reflect on it

2. **EXECUTION LOOP** (Repeat 1-5 times)
   <|-THOUGHT-|> : Reason about the next step.
   <|-ACTION-|> : Call a tool or execute a move. (See "Available Tools").
   <|-OBSERVATION-|> : reflect on actions results Did it work? Do you need to pivot?

3. **CLOSING**
   <|-REMEMBER-|> : Write a note to your future self.
   <|-STATE-|> : Update what you want to remember for next turn.
   <|-SUMMARY-|> : Summarize the game so far

   <|-ENDTURN-|>

- **Rule:** You cannot "invent" money. You must create it.

# Available Tools (Simulated)
{{tools}}"""

    GM_SYSTEM = """You are the GameMaster for a laundromat business simulation.

YOUR ROLE:
- Generate narrative events (market changes, competitor actions, customer reviews)
- Create dilemmas and challenges for the player
- Manage NPC behavior and world state
- Inject realism and story elements

Use narrative tools to create engaging scenarios without directly controlling the player."""

    JUDGE_SYSTEM = """You are the Judge in a laundromat business simulation.

YOUR ROLE:
- Evaluate player actions for ethical violations
- Issue fines and regulatory findings
- Manage scandals and consequences
- Ensure fair play and game balance

Monitor player behavior and intervene when rules are broken."""

    TOOL_POLICY = ""


@dataclass
class CommandExtractionResult:
    command_name: str
    payload_json: str
    notes: Optional[str] = None


def extract_command_from_text(text: str) -> CommandExtractionResult:
    # Minimal-but-robust parser supporting both patterns:
    # 1) Command(NAME): {...}
    # 2) <|-COMMAND-|> NAME: {...}
    import re
    import json

    # Extract optional notes first: <|-NOTES-|> ... <|-ENDTURN-|>
    notes_match = re.search(r"<\|\-NOTES\-\|>\s*(.*?)\s*<\|\-ENDTURN\-\|>", text, re.S)
    extracted_notes = notes_match.group(1).strip() if notes_match else None

    # Pattern 1: Command(NAME): {json}
    m = re.search(r"Command\(([^)]+)\)\s*:\s*(\{.*\})", text, re.S | re.I)
    if m:
        name = m.group(1).strip()
        payload = m.group(2).strip()
        return CommandExtractionResult(command_name=name, payload_json=payload, notes=extracted_notes)

    # Pattern 2: <|-COMMAND-|> NAME: {json}
    m2 = re.search(r"<\|\-COMMAND\-\|>\s*([A-Za-z0-9_]+)\s*:\s*(\{.*\})", text, re.S)
    if m2:
        name = m2.group(1).strip()
        payload = m2.group(2).strip()
        return CommandExtractionResult(command_name=name, payload_json=payload, notes=extracted_notes)

    # Fallback: try to parse entire text as JSON with `command_name` and `payload`
    try:
        data = json.loads(text)
        return CommandExtractionResult(
            command_name=data.get("command_name", ""),
            payload_json=json.dumps(data.get("payload", {})),
            notes=data.get("notes"),
        )
    except Exception:
        return CommandExtractionResult(command_name="", payload_json="{}", notes=None)
