"""Serve the API and the static UI on one port for UI checks (a lighter stand-in for scripts/run_demo.py).

    python -m scripts.public_scan.serve_ui [port]      # default 8010
"""
from __future__ import annotations

import sys
from pathlib import Path

import uvicorn
from fastapi.staticfiles import StaticFiles

from src.api.main import create_app

ROOT = Path(__file__).resolve().parents[2]


def build():
    """The API app with /ui (static) and /src/api/mock (the mock payloads the UI reads in mock mode)."""
    app = create_app()
    app.mount("/ui", StaticFiles(directory=ROOT / "ui", html=True), name="ui")
    app.mount("/src/api/mock", StaticFiles(directory=ROOT / "src" / "api" / "mock"), name="ui-mocks")
    return app


if __name__ == "__main__":
    uvicorn.run(build(), host="127.0.0.1", port=int(sys.argv[1]) if len(sys.argv) > 1 else 8010, log_level="warning")
