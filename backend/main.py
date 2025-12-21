"""Main application runner.

This module launches the FastAPI server (no reload) to preserve simulation
integrity during production runs.
"""

import uvicorn

try:
    from backend.server import app
except Exception:  # noqa: BLE001
    from server import app


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
