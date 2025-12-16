from __future__ import annotations

"""Compatibility shim for the `llm.tools` package.

This repo moved all LLM tool implementations into the `llm/tools/` package.

Historically, `llm.tools` was a single module file (`tools.py`). Having both a
`tools.py` module and a `tools/` package causes import ambiguity.

We can't reliably remove this file in some environments, so we turn it into a
package-like module by setting `__path__` to point at the canonical `tools/`
directory. This keeps imports like `import llm.tools.registry` working.
"""

import os as _os

# Make this module behave like a package rooted at ./tools
__path__ = [_os.path.join(_os.path.dirname(__file__), "tools")]

# Re-export the canonical public surface
from .core import ToolExecutor, ToolSpec  # noqa: F401
from .end_of_turn import EndOfTurnTool  # noqa: F401
from .help import ToolHelpTool  # noqa: F401
from .registry import ToolRegistry  # noqa: F401

__all__ = [
    "ToolExecutor",
    "ToolSpec",
    "EndOfTurnTool",
    "ToolHelpTool",
    "ToolRegistry",
]
