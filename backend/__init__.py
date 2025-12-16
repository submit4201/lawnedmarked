"""Backend package initializer.

This repository historically uses intra-backend absolute imports like
`from application_factory import ApplicationFactory`.

To make `import backend.server` work from the repo root (e.g. ASGI deployment),
we add the backend package directory to `sys.path`.
"""

from __future__ import annotations

import os
import sys

_pkg_dir = os.path.dirname(__file__)
if _pkg_dir and _pkg_dir not in sys.path:
	sys.path.insert(0, _pkg_dir)

try:
	from application_factory import ApplicationFactory
except Exception:  # noqa: BLE001
	from .application_factory import ApplicationFactory

__version__ = "0.1.0"
__all__ = ["ApplicationFactory"]
