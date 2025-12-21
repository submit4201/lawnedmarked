import os
import re
from datetime import datetime
from pathlib import Path

# Configuration
ROOT_DIR = Path(__file__).resolve().parent.parent
TODO_DIR = ROOT_DIR / ".todo"
DONE_DIR = TODO_DIR / ".done"

# Regex patterns for User Rule 4
# 4-E: comments with [ ] should be parsed
# 4-F: ! for important
# 4-G: ? for questions
# 4-H: * for notes
TODO_PATTERN = re.compile(r"\[\s*\]\s*(.*)")
IMPORTANT_PATTERN = re.compile(r"!\s+(.*)")
QUESTION_PATTERN = re.compile(r"\?\s+(.*)")
NOTE_PATTERN = re.compile(r"\*\s+(.*)")

# File extensions to scan
EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".md", ".html", ".css"}
SKIP_DIRS = {".git", ".venv", ".log", ".test", ".todo", "node_modules", "dist", "__pycache__"}

def scan_file(file_path: Path):
    found_items = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                
                # Check for comments (hash or slash-slash)
                comment_content = None
                if "#" in clean_line:
                    comment_content = clean_line.split("#", 1)[1].strip()
                elif "//" in clean_line:
                    comment_content = clean_line.split("//", 1)[1].strip()
                
                if comment_content:
                    # Check for patterns
                    if match := TODO_PATTERN.match(comment_content):
                        found_items.append(f"[TODO] {file_path.name}:{i} {match.group(1)}")
                    elif match := IMPORTANT_PATTERN.match(comment_content):
                        found_items.append(f"[IMPORTANT] {file_path.name}:{i} {match.group(1)}")
                    elif match := QUESTION_PATTERN.match(comment_content):
                        found_items.append(f"[QUESTION] {file_path.name}:{i} {match.group(1)}")
                    elif match := NOTE_PATTERN.match(comment_content):
                        found_items.append(f"[NOTE] {file_path.name}:{i} {match.group(1)}")

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return found_items

def main():
    print(f"Scanning {ROOT_DIR} for comments...")
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
        timestamp = datetime.now().strftime("%Y-%m-%d--%H%M%S")
        report_file = TODO_DIR / f"TODO-{timestamp}.txt"
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"Scanned on: {datetime.now()}\n")
            f.write("=" * 50 + "\n")
            for item in all_items:
                f.write(item + "\n")
        
        print(f"Found {len(all_items)} items. Report saved to {report_file}")
    else:
        print("No items found.")

if __name__ == "__main__":
    main()
