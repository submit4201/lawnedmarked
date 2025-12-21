import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Configuration
ROOT_DIR = Path(__file__).resolve().parent.parent
TODO_DIR = ROOT_DIR / ".todo"
DONE_DIR = TODO_DIR / ".done"

# Regex patterns for User Rule 4
PATTERNS = {
    "TODO": re.compile(r"\[\s*\]\s*(.*)"),
    "IMPORTANT": re.compile(r"!\s+(.*)"),
    "QUESTION": re.compile(r"\?\s+(.*)"),
    "NOTE": re.compile(r"\*\s+(.*)"),
}

# File extensions to scan
EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".md", ".html", ".css"}
SKIP_DIRS = {".git", ".venv", ".log", ".test", ".todo", "node_modules", "dist", "__pycache__"}


from typing import Tuple

def scan_file(file_path: Path) -> List[str]:
    """Scans a single file for known comment patterns."""
    found_items = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                item = _scan_line_for_todos(line, file_path.name, i)
                if item:
                    found_items.append(item)

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return found_items

def _scan_line_for_todos(line: str, filename: str, line_num: int) -> Optional[str]:
    """Analyze a single line for TODOs/Notes."""
    clean_line = line.strip()
    if not clean_line:
        return None
    
    comment_content = _extract_comment(clean_line)
    if not comment_content:
        return None
        
    matched = _match_pattern(comment_content)
    if matched:
        tag, msg = matched
        return f"[{tag}] {filename}:{line_num} {msg}"
    return None


def _extract_comment(line: str) -> Optional[str]:
    """Extracts comment content from a line of code."""
    if "#" in line:
        return line.split("#", 1)[1].strip()
    elif "//" in line:
        return line.split("//", 1)[1].strip()
    return None


def _match_pattern(content: str) -> Optional[Tuple[str, str]]:
    """Matches content against configured patterns."""
    for tag, pattern in PATTERNS.items():
        if match := pattern.match(content):
            return tag, match.group(1)
    return None


def main():
    print(f"Scanning {ROOT_DIR} for comments...")
    TODO_DIR.mkdir(exist_ok=True)
    
    all_items = []
    
    for root, dirs, files in os.walk(ROOT_DIR):
        # Modify dirs in-place to skip unwanted directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix in EXTENSIONS:
                results = scan_file(file_path)
                if results:
                    all_items.extend(results)

    if all_items:
        _write_report(all_items)
    else:
        print("No items found.")


def _write_report(items: List[str]):
    timestamp = datetime.now().strftime("%Y-%m-%d--%H%M%S")
    report_file = TODO_DIR / f"TODO-{timestamp}.txt"
    
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"Scanned on: {datetime.now()}\n")
            f.write("=" * 50 + "\n")
            for item in items:
                f.write(item + "\n")
        print(f"Found {len(items)} items. Report saved to {report_file}")
    except Exception as e:
        print(f"Failed to write report: {e}")


if __name__ == "__main__":
    main()
