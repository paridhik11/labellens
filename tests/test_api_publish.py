"""Step 25b: publishVersion and the public page, on the demo seed (draft L3 of chg_0002 with a passed self-check)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.seed import L3_SHA256

V3 = "lbv_exampledevice_carton_l3"
EDITOR, REVIEWER = {"X-User-Id": "usr_demo_editor"}, {"X-User-Id": "usr_demo_reviewer"}
APPROVE = {"decision": "approve", "artifact_sha256": L3_SHA256, "check_id": "chk_0003"}


@pytest.fixture()
def client():
    with TestClient(create_app("sqlite://", seed=True)) as c:
        yield c


def test_an_unapproved_version_cannot_be_published(client) -> None:
    refused = client.post(f"/label-versions/{V3}/publish", headers=REVIEWER)
    assert refused.status_code == 409 and refused.json()["error"] == "not_approved"
    assert client.get(f"/versions/{V3}").status_code == 404  # no page before publication


def test_only_a_reviewer_or_admin_publishes(client) -> None:
    client.post(f"/label-versions/{V3}/reviews", headers=REVIEWER, json=APPROVE)
    assert client.post(f"/label-versions/{V3}/publish", headers=EDITOR).status_code == 403


def test_publish_after_approval_creates_a_pinned_page_and_is_repeatable(client) -> None:
    assert client.post(f"/label-versions/{V3}/reviews", headers=REVIEWER, json=APPROVE).status_code == 201
    first = client.post(f"/label-versions/{V3}/publish", headers=REVIEWER)
    assert first.status_code == 201 and "X-Mock" not in first.headers
    page = first.json()
    assert page["version_id"] == V3 and page["url"] == page["qr_payload"] and page["url"].endswith(f"/versions/{V3}")
    again = client.post(f"/label-versions/{V3}/publish", headers=REVIEWER)
    assert again.status_code == 200 and again.json()["page_id"] == page["page_id"]
    assert client.get(f"/label-versions/{V3}", headers=EDITOR).json()["status"] == "published"
    html = client.get(f"/versions/{V3}")
    assert html.status_code == 200 and V3 in html.text and L3_SHA256 in html.text
    assert "<script" not in html.text.lower()


def test_a_returned_version_is_not_publishable(client) -> None:
    client.post(f"/label-versions/{V3}/reviews", headers=REVIEWER, json=APPROVE)
    client.post(f"/label-versions/{V3}/reviews", headers=REVIEWER, json={
        "decision": "return", "artifact_sha256": L3_SHA256, "comment": "fix the lot"})
    assert client.post(f"/label-versions/{V3}/publish", headers=REVIEWER).json()["error"] == "not_approved"


def test_an_unpublished_pdf_is_not_served(client) -> None:
    assert client.get(f"/versions/{V3}/label.pdf").status_code == 404
