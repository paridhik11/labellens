"""Step 20c: every operation that is not real serves its mock JSON with X-Mock: true."""

from __future__ import annotations

import json
import re

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.mock_server import MOCK_DIR, NOT_MOCKED, load_index, load_spec, mock_operations, pick_entry
from src.api.routes import REAL_OPERATIONS
from src.api.seed import PRODUCT_ID

SPEC = load_spec()
MOCKED = mock_operations(SPEC)
HEADERS = {"X-User-Id": "usr_demo_editor"}


@pytest.fixture(scope="module")
def client():
    """One app with a seeded in-memory database for the whole module."""
    with TestClient(create_app("sqlite://", seed=True)) as c:
        yield c


def concrete(path: str) -> str:
    """Fill every {param} of a path template with a dummy value."""
    return re.sub(r"\{[^}]+\}", "x", path)


def test_mock_and_real_operations_partition_the_spec() -> None:
    all_ops = {op["operationId"] for item in SPEC["paths"].values() for op in item.values()}
    mocked = {operation_id for operation_id, _, _ in MOCKED}
    assert mocked | NOT_MOCKED == all_ops
    assert not mocked & NOT_MOCKED
    assert REAL_OPERATIONS <= all_ops
    assert len(mocked) == len(all_ops) - len(NOT_MOCKED)


def test_every_mocked_operation_has_a_mock_file() -> None:
    have = {e["operationId"] for e in load_index()}
    assert {operation_id for operation_id, _, _ in MOCKED} <= have
    for entry in load_index():
        assert (MOCK_DIR / entry["file"]).is_file()


@pytest.mark.parametrize(("operation_id", "method", "path"), MOCKED, ids=[m[0] for m in MOCKED])
def test_every_non_real_operation_returns_x_mock(client, operation_id, method, path) -> None:
    response = client.request(method, concrete(path))
    entries = [e for e in load_index() if e["operationId"] == operation_id]
    expected = pick_entry(entries, None)
    assert response.headers.get("X-Mock") == "true", operation_id
    assert response.status_code == expected["status"], operation_id
    assert response.json() == json.loads((MOCK_DIR / expected["file"]).read_text(encoding="utf-8"))


def test_real_operations_never_carry_x_mock(client) -> None:
    calls = [
        ("GET", "/health"),
        ("GET", "/me"),
        ("GET", "/products"),
        ("GET", f"/products/{PRODUCT_ID}"),
        ("GET", f"/products/{PRODUCT_ID}/versions"),
        ("GET", f"/products/{PRODUCT_ID}/history"),
        ("GET", "/templates/tpl_exampledevice_carton"),
        ("GET", "/labels/lbl_exampledevice_carton/versions"),
        ("GET", "/label-versions/lbv_exampledevice_carton_l3"),
        ("GET", "/label-versions/lbv_exampledevice_carton_l3/reviews"),
        ("GET", "/changes/chg_0002"),
        ("POST", "/products"),
        ("POST", f"/products/{PRODUCT_ID}/templates"),
        ("POST", "/changes"),
        ("POST", "/label-versions/lbv_exampledevice_carton_l3/reviews"),
        ("POST", "/label-versions/lbv_exampledevice_carton_l3/inspect"),
        ("POST", "/label-versions/lbv_exampledevice_carton_l3/recheck"),
        ("GET", "/jobs/job_deadbeef"),
        ("GET", "/check-results/chk_0001"),
        ("POST", "/search"),
        ("POST", "/scans"),
        ("GET", "/scans/scn_00000000"),
        ("GET", "/label-versions/lbv_00000000/extraction"),
        ("POST", "/label-versions/lbv_00000000/extraction/confirm"),
        ("POST", "/public/ask"),
        ("POST", "/ask"),
        ("POST", "/public/match"),
        ("POST", "/public/scans"),
        ("POST", "/public/live/search"),
        ("POST", "/public/live/fetch"),
        ("GET", "/public/live/products/live_0000000000000000_v1"),
        ("GET", "/public/scans/pscn_00000000"),
        ("GET", "/label-versions/lbv_exampledevice_carton_l3/print-verifications"),
        ("GET", "/print-verifications/pv_00000000"),
        ("POST", "/label-versions/lbv_exampledevice_carton_l3/print-verifications"),
        ("POST", "/label-versions/lbv_exampledevice_carton_l3/publish"),
        ("POST", "/changes/chg_0002/generate"),
        ("GET", "/artworks/art_00000000"),
        ("GET", "/label-versions/lbv_exampledevice_carton_l3/exports"),
        ("GET", "/artifacts/" + "0" * 64),
    ]
    for method, path in calls:
        response = client.request(method, path, headers=HEADERS, json={} if method == "POST" else None)
        assert "X-Mock" not in response.headers, (method, path)
    # confirmChange and listAffectedLabels are real too, but a change with no stored assessment (like the seed's)
    # keeps the mock for them. That fallback is tested in tests/test_api_changes.py.
    assert len(calls) + 2 >= len(REAL_OPERATIONS)


def test_every_spec_path_and_method_is_routed(client) -> None:
    """Mock routes are plain routes. Real routes show up in FastAPI's own schema, with the contract's operationId."""
    mock_routed = {(m, r.path) for r in client.app.routes for m in getattr(r, "methods", None) or ()}
    real_schema = client.app.openapi()["paths"]
    for path, item in SPEC["paths"].items():
        for method, op in item.items():
            if op["operationId"] in NOT_MOCKED:
                assert real_schema[path][method]["operationId"] == op["operationId"], (method, path)
            else:
                assert (method.upper(), path) in mock_routed, (method, path)


def test_mock_state_picks_another_mock_of_the_same_operation(client) -> None:
    default = client.get("/label-versions/x/extraction", headers=HEADERS)
    review = client.get("/label-versions/x/extraction?mock_state=needs_review", headers=HEADERS)
    assert (default.status_code, review.status_code) == (200, 200) and default.json() != review.json()
    assert review.headers["X-Mock"] == "true"
    empty = client.get("/public/scans/x?mock_state=empty")
    assert empty.json()["candidates"] == [] and empty.headers["X-Mock"] == "true"
    by_file = client.get("/public/scans/x?mock_state=failed")
    assert by_file.headers["X-Mock"] == "true" and by_file.json() != empty.json()
    fallback = client.get("/label-versions/x/extraction?mock_state=nonsense", headers=HEADERS)
    assert fallback.json() == default.json()


def test_no_operation_is_mocked_any_more() -> None:
    """With publicScan real (CR-27) every operation has a real route. The mock files still back unknown-id fallbacks."""
    assert MOCKED == []
