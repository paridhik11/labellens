"""Step 20b: the real endpoints, role checks and review rules over HTTP."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.seed import CHANGE_ID, L3_SHA256, LABEL_ID, PRODUCT_ID, TEMPLATE_ID
from src.api.store import add_check_result, add_label_version

EDITOR, REVIEWER, ADMIN = "usr_demo_editor", "usr_demo_reviewer", "usr_demo_admin"
L2, L3 = "lbv_exampledevice_carton_l2", "lbv_exampledevice_carton_l3"
SLOT = {"id": "name", "type": "text", "field": "name", "bbox_mm": [5, 10, 50, 6], "size_pt": 10}
TEMPLATE_BODY = {"size_mm": {"w": 100, "h": 60}, "background": None, "slots": [SLOT]}


def h(user: str) -> dict[str, str]:
    """Headers naming the calling user."""
    return {"X-User-Id": user}


@pytest.fixture()
def client():
    """A client on a fresh in-memory database with the demo seed."""
    with TestClient(create_app("sqlite://", seed=True)) as c:
        yield c


def approve_body(**over):
    """Request body that approves the seeded draft L3."""
    return {"decision": "approve", "artifact_sha256": L3_SHA256, "check_id": "chk_0003", **over}


def error_code(response) -> str:
    """The `error` code of an error response."""
    return response.json()["error"]


# ---------------------------------------------------------------- users


def test_health_needs_no_header(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_me_and_unknown_user(client):
    assert client.get("/me", headers=h(EDITOR)).json() == {"user_id": EDITOR, "name": "Demo Editor", "role": "editor"}
    missing = client.get("/me")
    assert (missing.status_code, error_code(missing)) == (401, "unknown_user")
    unknown = client.get("/me", headers=h("usr_nobody"))
    assert (unknown.status_code, error_code(unknown)) == (401, "unknown_user")


def test_reads_need_a_known_user(client):
    for path in ("/products", f"/products/{PRODUCT_ID}", f"/label-versions/{L3}", f"/changes/{CHANGE_ID}"):
        assert client.get(path).status_code == 401, path


# ---------------------------------------------------------------- products and templates


def test_list_and_get_product(client):
    items = client.get("/products", headers=h(EDITOR)).json()["items"]
    assert len(items) == 1
    assert items[0]["label_count"] == 1 and items[0]["open_findings"] == 0
    detail = client.get(f"/products/{PRODUCT_ID}", headers=h(EDITOR)).json()
    assert detail["product"]["current_version"] == 2
    assert [t["template_id"] for t in detail["templates"]] == [TEMPLATE_ID]
    assert [(v["version_id"], v["artwork_version"]) for v in detail["labels"]] == [(L3, 3)]
    assert client.get("/products/prd_missing", headers=h(EDITOR)).status_code == 404


def test_register_product_creates_version_one_and_keeps_udi_as_given(client):
    body = {"name": "Sample Pump", "udi_di": "", "intended_market": ["US"]}
    created = client.post("/products", json=body, headers=h(EDITOR))
    assert created.status_code == 201
    data = created.json()
    assert data["record"]["version"] == 1 and data["record"]["udi_di"] == ""
    assert data["record"]["created_by"] == EDITOR and data["labels"] == [] and data["templates"] == []
    versions = client.get(f"/products/{data['product']['product_id']}/versions", headers=h(EDITOR)).json()
    assert [v["version"] for v in versions["versions"]] == [1]
    allocated = client.post("/products", json={"name": "Sample Valve", "udi_di": "00000000000000"}, headers=h(ADMIN))
    assert allocated.json()["record"]["udi_di"] == "00000000000000"


def test_register_product_rejects_bad_bodies(client):
    for body in ({}, {"name": ""}, {"name": "X", "status": "published"}):
        response = client.post("/products", json=body, headers=h(EDITOR))
        assert (response.status_code, error_code(response)) == (422, "validation_error"), body


def test_product_versions_are_listed_oldest_first(client):
    versions = client.get(f"/products/{PRODUCT_ID}/versions", headers=h(EDITOR)).json()["versions"]
    assert [v["version"] for v in versions] == [1, 2]
    assert client.get("/products/prd_missing/versions", headers=h(EDITOR)).status_code == 404


def test_register_template_new_and_next_version(client):
    first = client.post(f"/products/{PRODUCT_ID}/templates", json=TEMPLATE_BODY, headers=h(EDITOR))
    assert first.status_code == 201 and first.json()["version"] == 1
    new_id = first.json()["template_id"]
    second = client.post(
        f"/products/{PRODUCT_ID}/templates", json={**TEMPLATE_BODY, "template_id": new_id}, headers=h(ADMIN)
    )
    assert second.json()["version"] == 2
    seeded_next = client.post(
        f"/products/{PRODUCT_ID}/templates", json={**TEMPLATE_BODY, "template_id": TEMPLATE_ID}, headers=h(EDITOR)
    )
    assert seeded_next.json()["version"] == 2


def test_register_template_rules(client):
    other = client.post("/products", json={"name": "Sample Other"}, headers=h(EDITOR)).json()["product"]["product_id"]
    moved = client.post(
        f"/products/{other}/templates", json={**TEMPLATE_BODY, "template_id": TEMPLATE_ID}, headers=h(EDITOR)
    )
    assert (moved.status_code, error_code(moved)) == (409, "template_product_mismatch")
    missing = client.post("/products/prd_missing/templates", json=TEMPLATE_BODY, headers=h(EDITOR))
    assert missing.status_code == 404
    bad_symbol = {
        "id": "s",
        "type": "symbol",
        "field": "sterilization",
        "symbol_name": "sterile_eo",
        "bbox_mm": [1, 10, 5, 5],
    }
    no_size = {"id": "t", "type": "text", "field": "name", "bbox_mm": [1, 10, 5, 5]}
    for slots in ([bad_symbol], [no_size], [], [SLOT, SLOT]):
        response = client.post(
            f"/products/{PRODUCT_ID}/templates", json={**TEMPLATE_BODY, "slots": slots}, headers=h(EDITOR)
        )
        assert (response.status_code, error_code(response)) == (422, "validation_error"), slots


def test_get_template_latest_and_pinned_version(client):
    client.post(
        f"/products/{PRODUCT_ID}/templates", json={**TEMPLATE_BODY, "template_id": TEMPLATE_ID}, headers=h(EDITOR)
    )
    assert client.get(f"/templates/{TEMPLATE_ID}", headers=h(EDITOR)).json()["version"] == 2
    assert client.get(f"/templates/{TEMPLATE_ID}?version=1", headers=h(EDITOR)).json()["version"] == 1
    assert client.get(f"/templates/{TEMPLATE_ID}?version=9", headers=h(EDITOR)).status_code == 404
    assert client.get("/templates/tpl_missing", headers=h(EDITOR)).status_code == 404


def test_label_versions(client):
    listing = client.get(f"/labels/{LABEL_ID}/versions", headers=h(EDITOR)).json()
    assert [v["artwork_version"] for v in listing["versions"]] == [1, 2, 3]
    assert [v["status"] for v in listing["versions"]] == ["draft", "checked", "checked"]
    version = client.get(f"/label-versions/{L3}", headers=h(EDITOR)).json()
    assert version["draft_watermark"] is True and version["parent_version_id"] == L2
    assert client.get("/labels/lbl_missing/versions", headers=h(EDITOR)).status_code == 404
    assert client.get("/label-versions/lbv_missing", headers=h(EDITOR)).status_code == 404


# ---------------------------------------------------------------- changes


def test_create_change_says_nothing_was_checked(client):
    body = {"product_id": PRODUCT_ID, "edits": [{"field": "storage", "new_value": "Store cool"}]}
    response = client.post("/changes", json=body, headers=h(EDITOR))
    assert response.status_code == 201
    data = response.json()
    assert data["parser"] == "not_implemented" and data["affected"] == [] and data["citations"] == []
    assert data["checklist_complete"] is False
    assert data["needs_human_review"].startswith("NEEDS_HUMAN_REVIEW")
    change = data["change"]
    assert change["status"] == "draft" and change["closed"] is False and change["parse_state"] == "proposed"
    assert change["old_value"] == "Store dry, 5 to 25 C" and change["created_by"] == EDITOR
    fetched = client.get(f"/changes/{change['change_id']}", headers=h(EDITOR)).json()
    assert fetched == change


def test_create_change_with_several_edits_and_text(client):
    body = {
        "product_id": PRODUCT_ID,
        "raw_text": "Change storage and model",
        "edits": [
            {"field": "storage", "new_value": "A"},
            {"field": "model", "old_value": "ED-100", "new_value": "ED-200"},
        ],
    }
    change = client.post("/changes", json=body, headers=h(ADMIN)).json()["change"]
    assert change["field"] == "storage" and change["raw_text"] == "Change storage and model"
    assert change["edits"] == [{"field": "model", "old_value": "ED-100", "new_value": "ED-200"}]


def test_plain_text_change_is_not_parsed(client):
    response = client.post(
        "/changes", json={"product_id": PRODUCT_ID, "raw_text": "Switch to gamma"}, headers=h(EDITOR)
    )
    assert (response.status_code, error_code(response)) == (422, "parser_not_implemented")
    empty = client.post("/changes", json={"product_id": PRODUCT_ID}, headers=h(EDITOR))
    assert (empty.status_code, error_code(empty)) == (422, "validation_error")
    missing = client.post(
        "/changes", json={"product_id": "prd_missing", "edits": [{"field": "a", "new_value": "b"}]}, headers=h(EDITOR)
    )
    assert missing.status_code == 404


def test_get_change_derives_status(client):
    change = client.get(f"/changes/{CHANGE_ID}", headers=h(EDITOR)).json()
    assert change["status"] == "checked" and change["closed"] is False and "latest_review_id" not in change
    assert client.get("/changes/chg_missing", headers=h(EDITOR)).status_code == 404


# ---------------------------------------------------------------- roles: every forbidden case


@pytest.mark.parametrize(
    ("method", "path", "body", "user"),
    [
        ("post", "/products", {"name": "Sample Pump"}, REVIEWER),
        ("post", f"/products/{PRODUCT_ID}/templates", TEMPLATE_BODY, REVIEWER),
        ("post", "/changes", {"product_id": PRODUCT_ID, "edits": [{"field": "storage", "new_value": "x"}]}, REVIEWER),
        ("post", f"/label-versions/{L3}/reviews", approve_body(), EDITOR),
    ],
    ids=["reviewer-registers-product", "reviewer-registers-template", "reviewer-creates-change", "editor-reviews"],
)
def test_forbidden_roles_get_403_and_nothing_is_written(client, method, path, body, user):
    response = getattr(client, method)(path, json=body, headers=h(user))
    assert (response.status_code, error_code(response)) == (403, "role_forbidden")
    assert len(client.get("/products", headers=h(ADMIN)).json()["items"]) == 1
    assert client.get(f"/label-versions/{L3}/reviews", headers=h(ADMIN)).json()["items"] == []


def test_write_without_a_user_is_401(client):
    assert client.post("/products", json={"name": "Sample Pump"}).status_code == 401
    assert client.post(f"/label-versions/{L3}/reviews", json=approve_body()).status_code == 401


# ---------------------------------------------------------------- reviews over HTTP


def test_approve_over_http_and_status_follows(client):
    response = client.post(f"/label-versions/{L3}/reviews", json=approve_body(comment="ok"), headers=h(REVIEWER))
    assert response.status_code == 201
    review = response.json()
    assert review["resulting_status"] == "reviewed" and review["reviewer_role"] == "reviewer"
    assert review["check_id"] == "chk_0003" and review["change_id"] == CHANGE_ID
    change = client.get(f"/changes/{CHANGE_ID}", headers=h(EDITOR)).json()
    assert change["status"] == "reviewed" and change["latest_review_id"] == review["review_id"]
    version = client.get(f"/label-versions/{L3}", headers=h(EDITOR)).json()
    assert version["status"] == "reviewed" and version["draft_watermark"] is False
    listed = client.get(f"/label-versions/{L3}/reviews", headers=h(EDITOR)).json()
    assert [r["review_id"] for r in listed["items"]] == [review["review_id"]]
    assert client.get("/label-versions/lbv_missing/reviews", headers=h(EDITOR)).status_code == 404


def test_review_error_codes_over_http(client):
    url = f"/label-versions/{L3}/reviews"
    cases = [
        (approve_body(check_id=None), 422, "check_required"),
        (approve_body(artifact_sha256="0" * 64), 409, "hash_mismatch"),
        (approve_body(check_id="chk_0001"), 409, "check_not_passed"),
        ({"decision": "return", "artifact_sha256": L3_SHA256}, 422, "comment_required"),
        ({"decision": "reject", "artifact_sha256": L3_SHA256, "comment": " "}, 422, "comment_required"),
        ({"decision": "approve", "artifact_sha256": "xyz", "check_id": "chk_0003"}, 422, "validation_error"),
        ({"decision": "maybe", "artifact_sha256": L3_SHA256}, 422, "validation_error"),
    ]
    for body, status, code in cases:
        response = client.post(url, json=body, headers=h(REVIEWER))
        assert (response.status_code, error_code(response)) == (status, code), body
    assert (
        client.post("/label-versions/lbv_missing/reviews", json=approve_body(), headers=h(REVIEWER)).status_code == 404
    )


def test_submitter_cannot_approve_over_http(client):
    created = client.post(
        "/changes",
        json={"product_id": PRODUCT_ID, "edits": [{"field": "storage", "new_value": "Cool"}]},
        headers=h(ADMIN),
    ).json()["change"]
    with client.app.state.session_factory() as session:
        version = add_label_version(
            session,
            EDITOR,
            PRODUCT_ID,
            "files/x.svg",
            kind="generated",
            artifact_sha256="a" * 64,
            change_id=created["change_id"],
        )
        check = add_check_result(session, "self_check", [], version_id=version.version_id, artifact_sha256="a" * 64)
        version_id, check_id = version.version_id, check.check_id
    body = {"decision": "approve", "artifact_sha256": "a" * 64, "check_id": check_id}
    refused = client.post(f"/label-versions/{version_id}/reviews", json=body, headers=h(ADMIN))
    assert (refused.status_code, error_code(refused)) == (403, "self_approval_forbidden")
    returned = client.post(
        f"/label-versions/{version_id}/reviews",
        json={"decision": "return", "artifact_sha256": "a" * 64, "comment": "own return"},
        headers=h(ADMIN),
    )
    assert returned.status_code == 201
    assert client.post(f"/label-versions/{version_id}/reviews", json=body, headers=h(REVIEWER)).status_code == 201


def test_return_is_not_terminal_and_reject_is_terminal(client):
    url = f"/label-versions/{L3}/reviews"
    returned = client.post(
        url, json={"decision": "return", "artifact_sha256": L3_SHA256, "comment": "Fix symbol."}, headers=h(REVIEWER)
    )
    assert returned.status_code == 201 and returned.json()["resulting_status"] == "draft"
    change = client.get(f"/changes/{CHANGE_ID}", headers=h(EDITOR)).json()
    assert change["status"] == "draft" and change["closed"] is False
    assert change["latest_review_id"] == returned.json()["review_id"]
    rejected = client.post(
        url, json={"decision": "reject", "artifact_sha256": L3_SHA256, "comment": "Wrong."}, headers=h(REVIEWER)
    )
    assert rejected.status_code == 201
    assert client.get(f"/changes/{CHANGE_ID}", headers=h(EDITOR)).json()["closed"] is True
    again = client.post(url, json=approve_body(), headers=h(ADMIN))
    assert (again.status_code, error_code(again)) == (409, "change_closed")


def test_new_version_voids_the_approval_over_http(client):
    url = f"/label-versions/{L3}/reviews"
    assert client.post(url, json=approve_body(), headers=h(REVIEWER)).status_code == 201
    with client.app.state.session_factory() as session:
        l4 = add_label_version(
            session,
            EDITOR,
            PRODUCT_ID,
            "files/l4.svg",
            kind="generated",
            label_id=LABEL_ID,
            artifact_sha256="b" * 64,
            change_id=CHANGE_ID,
        )
        l4_id = l4.version_id
    change = client.get(f"/changes/{CHANGE_ID}", headers=h(EDITOR)).json()
    assert change["status"] == "draft" and "latest_review_id" not in change
    # the old version still shows as approved in its own record: read approval from the change instead
    assert client.get(f"/label-versions/{L3}", headers=h(EDITOR)).json()["status"] == "reviewed"
    stale = client.post(url, json=approve_body(), headers=h(ADMIN))
    assert (stale.status_code, error_code(stale)) == (409, "version_superseded")
    assert client.get(f"/label-versions/{l4_id}", headers=h(EDITOR)).json()["draft_watermark"] is True


def test_history_is_newest_first_and_covers_the_product(client):
    client.post(f"/label-versions/{L3}/reviews", json=approve_body(), headers=h(REVIEWER))
    history = client.get(f"/products/{PRODUCT_ID}/history", headers=h(EDITOR)).json()
    actions = [e["action"] for e in history["items"]]
    assert actions[0] == "review.approved"
    for expected in (
        "product.version_created",
        "template.version_created",
        "label.version_created",
        "change.created",
        "check.recorded",
    ):
        assert expected in actions, expected
    times = [e["at"] for e in history["items"]]
    assert times == sorted(times, reverse=True)
    assert client.get("/products/prd_missing/history", headers=h(EDITOR)).status_code == 404
