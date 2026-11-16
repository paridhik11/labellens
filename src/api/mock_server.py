"""Mock fallback (Step 20c): every operation of openapi.yaml that is not implemented for real serves its mock JSON.

Each mock response carries the header `X-Mock: true`, so the UI and the tests can tell mock from real.
When an operation has several mocks (for example `empty` and `success`), the default is picked by
DEFAULT_STATE_ORDER, and `?mock_state=<state or file name>` picks another one.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.routes import REAL_OPERATIONS

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs" / "contracts" / "openapi.yaml"
MOCK_DIR = Path(__file__).resolve().parent / "mock"
HTTP_METHODS = ("get", "post", "put", "patch", "delete")
DEFAULT_STATE_ORDER = ("success", "loading", "approved", "empty")
# Implemented outside the router (main.py) or real: never mocked.
NOT_MOCKED = REAL_OPERATIONS | {"getHealth"}


def load_spec() -> dict[str, Any]:
    """Read docs/contracts/openapi.yaml."""
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def load_index() -> list[dict[str, Any]]:
    """Read the list of mock files (src/api/mock/index.json)."""
    return json.loads((MOCK_DIR / "index.json").read_text(encoding="utf-8"))["mocks"]


def pick_entry(entries: list[dict[str, Any]], wanted: str | None) -> dict[str, Any]:
    """Choose one mock entry: the one named by `wanted` (state or file stem), else the default order."""
    if wanted:
        for entry in entries:
            if wanted in (entry["state"], Path(entry["file"]).stem):
                return entry
    for state in DEFAULT_STATE_ORDER:
        for entry in entries:
            if entry["state"] == state:
                return entry
    return entries[0]


def mock_operations(spec: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Return (operationId, method, path) for every operation that is served from a mock."""
    out = []
    for path, item in spec["paths"].items():
        for method in HTTP_METHODS:
            op = item.get(method)
            if op and op["operationId"] not in NOT_MOCKED:
                out.append((op["operationId"], method.upper(), path))
    return out


def register_mocks(app: FastAPI) -> None:
    """Add one route per mocked operation. Path params and request bodies are ignored."""
    by_operation: dict[str, list[dict[str, Any]]] = {}
    for entry in load_index():
        by_operation.setdefault(entry["operationId"], []).append(entry)

    for operation_id, method, path in mock_operations(load_spec()):
        entries = by_operation[operation_id]  # a missing mock is a bug, caught by tests
        app.add_api_route(
            path,
            _make_handler(entries),
            methods=[method],
            operation_id=f"mock_{operation_id}",
            tags=["mock"],
            include_in_schema=False,
        )


def mock_response(operation_id: str, request: Request) -> JSONResponse:
    """The mock response of one operation, for a real handler that has nothing real to return (fallback)."""
    entries = [e for e in load_index() if e["operationId"] == operation_id]
    entry = pick_entry(entries, request.query_params.get("mock_state"))
    body = json.loads((MOCK_DIR / entry["file"]).read_text(encoding="utf-8"))
    return JSONResponse(body, status_code=entry["status"], headers={"X-Mock": "true"})


def _make_handler(entries: list[dict[str, Any]]):  # noqa: ANN202
    """Build a route handler for one operation. Its only parameter is the request, so FastAPI reads no body."""

    def handler(request: Request) -> JSONResponse:
        entry = pick_entry(entries, request.query_params.get("mock_state"))
        body = json.loads((MOCK_DIR / entry["file"]).read_text(encoding="utf-8"))
        return JSONResponse(body, status_code=entry["status"], headers={"X-Mock": "true"})

    return handler
