"""Step 20d: every real response, success and error, validates against its schema in openapi.yaml.

One scripted run calls every real operation and every status the spec documents for it. Each response is
checked with `check`, which fails if the status is undocumented or the body breaks the schema. At the end the
run must have seen every documented status of every real operation.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.routes import REAL_OPERATIONS
from src.api.seed import CHANGE_ID, L3_SHA256, LABEL_ID, PRODUCT_ID, TEMPLATE_ID
from src.api.store import add_check_result, add_label_version
from tests.checker_api_helpers import install
from tests.openapi_helpers import conformance_errors, documented_statuses, find_operation

EDITOR, REVIEWER, ADMIN = "usr_demo_editor", "usr_demo_reviewer", "usr_demo_admin"
L3 = "lbv_exampledevice_carton_l3"
L2_ID = "lbv_exampledevice_carton_l2"
SLOT = {"id": "name", "type": "text", "field": "name", "bbox_mm": [5, 10, 50, 6], "size_pt": 10}
TEMPLATE_BODY = {"size_mm": {"w": 100, "h": 60}, "background": None, "slots": [SLOT]}
EDIT = [{"field": "storage", "new_value": "Store cool"}]


def h(user: str) -> dict[str, str]:
    """Headers naming the calling user."""
    return {"X-User-Id": user}


class Run:
    """A client plus the record of which (operationId, status) pairs were validated."""

    def __init__(self, client: TestClient) -> None:
        self.client = client
        self.seen: dict[str, set[int]] = defaultdict(set)

    def check(self, operation_id: str, status: int, method: str, path: str, user: str | None = EDITOR, **kw: Any):
        """Send a request, assert the status, and validate the body against the spec. Returns the response."""
        response = self.client.request(method, path, headers=h(user) if user else None, **kw)
        assert response.status_code == status, (operation_id, response.status_code, response.text)
        errors = conformance_errors(operation_id, status, response.json())
        assert not errors, (operation_id, status, errors)
        self.seen[operation_id].add(status)
        return response


@pytest.fixture()
def run():
    """A scripted run on a fresh seeded database."""
    with TestClient(create_app("sqlite://", seed=True)) as client:
        yield Run(client)


def test_every_real_response_conforms_to_openapi(run: Run, tmp_path, monkeypatch) -> None:
    sf = run.client.app.state.session_factory
    c = run.check
    install(run.client, tmp_path, monkeypatch)  # stub extractor and bm25 retrieval: no CV libraries needed

    # users
    c("getCurrentUser", 200, "GET", "/me")
    c("getCurrentUser", 401, "GET", "/me", user=None)

    # reads on the seed
    c("listProducts", 200, "GET", "/products")
    c("listProducts", 401, "GET", "/products", user=None)
    c("getProduct", 200, "GET", f"/products/{PRODUCT_ID}")
    c("getProduct", 404, "GET", "/products/prd_missing")
    c("getProduct", 401, "GET", f"/products/{PRODUCT_ID}", user=None)
    c("listProductVersions", 200, "GET", f"/products/{PRODUCT_ID}/versions")
    c("listProductVersions", 404, "GET", "/products/prd_missing/versions")
    c("listProductVersions", 401, "GET", f"/products/{PRODUCT_ID}/versions", user=None)
    c("getTemplate", 200, "GET", f"/templates/{TEMPLATE_ID}")
    c("getTemplate", 404, "GET", "/templates/tpl_missing")
    c("getTemplate", 401, "GET", f"/templates/{TEMPLATE_ID}", user=None)
    c("listLabelVersions", 200, "GET", f"/labels/{LABEL_ID}/versions")
    c("listLabelVersions", 404, "GET", "/labels/lbl_missing/versions")
    c("listLabelVersions", 401, "GET", f"/labels/{LABEL_ID}/versions", user=None)
    c("getLabelVersion", 200, "GET", f"/label-versions/{L3}")
    c("getLabelVersion", 404, "GET", "/label-versions/lbv_missing")
    c("getLabelVersion", 401, "GET", f"/label-versions/{L3}", user=None)
    c("getChange", 200, "GET", f"/changes/{CHANGE_ID}")
    c("getChange", 404, "GET", "/changes/chg_missing")
    c("getChange", 401, "GET", f"/changes/{CHANGE_ID}", user=None)
    c("listReviews", 200, "GET", f"/label-versions/{L3}/reviews")
    c("listReviews", 404, "GET", "/label-versions/lbv_missing/reviews")
    c("listReviews", 401, "GET", f"/label-versions/{L3}/reviews", user=None)

    # products and templates
    created = c("registerProduct", 201, "POST", "/products", json={"name": "Sample Pump", "intended_market": ["US"]})
    c("registerProduct", 422, "POST", "/products", json={"name": ""})
    c("registerProduct", 403, "POST", "/products", user=REVIEWER, json={"name": "Sample Pump"})
    c("registerProduct", 401, "POST", "/products", user=None, json={"name": "Sample Pump"})
    other = created.json()["product"]["product_id"]
    c("getProductHistory", 200, "GET", f"/products/{other}/history")
    c("getProductHistory", 404, "GET", "/products/prd_missing/history")
    c("getProductHistory", 401, "GET", f"/products/{other}/history", user=None)
    new_tpl = c("registerTemplate", 201, "POST", f"/products/{PRODUCT_ID}/templates", json=TEMPLATE_BODY)
    c(
        "registerTemplate",
        201,
        "POST",
        f"/products/{PRODUCT_ID}/templates",
        json={**TEMPLATE_BODY, "template_id": new_tpl.json()["template_id"]},
    )
    c(
        "registerTemplate",
        409,
        "POST",
        f"/products/{other}/templates",
        json={**TEMPLATE_BODY, "template_id": TEMPLATE_ID},
    )
    c("registerTemplate", 422, "POST", f"/products/{PRODUCT_ID}/templates", json={**TEMPLATE_BODY, "slots": []})
    c("registerTemplate", 404, "POST", "/products/prd_missing/templates", json=TEMPLATE_BODY)
    c("registerTemplate", 403, "POST", f"/products/{PRODUCT_ID}/templates", user=REVIEWER, json=TEMPLATE_BODY)
    c("registerTemplate", 401, "POST", f"/products/{PRODUCT_ID}/templates", user=None, json=TEMPLATE_BODY)

    # changes
    c("assessChange", 201, "POST", "/changes", json={"product_id": PRODUCT_ID, "edits": EDIT})
    c("assessChange", 201, "POST", "/changes", json={"product_id": PRODUCT_ID, "raw_text": "x", "edits": EDIT * 1})
    c("assessChange", 422, "POST", "/changes", json={"product_id": PRODUCT_ID, "raw_text": "Switch to gamma"})
    c("assessChange", 404, "POST", "/changes", json={"product_id": "prd_missing", "edits": EDIT})
    c("assessChange", 403, "POST", "/changes", user=REVIEWER, json={"product_id": PRODUCT_ID, "edits": EDIT})
    c("assessChange", 401, "POST", "/changes", user=None, json={"product_id": PRODUCT_ID, "edits": EDIT})

    # change assessment and confirmation (Step 22c)
    made = c("assessChange", 201, "POST", "/changes", json={"product_id": PRODUCT_ID, "edits": [
        {"field": "lot", "new_value": "LOT777"}]})
    made_id = made.json()["change"]["change_id"]
    items = made.json()["affected"]
    c("assessChange", 201, "POST", "/changes", json={"product_id": PRODUCT_ID, "raw_text": "Change the lot to LOT778"})
    c("assessChange", 201, "POST", "/changes", json={"product_id": PRODUCT_ID, "edits": [
        {"field": "colour", "new_value": "red"}]})  # parser not_implemented
    c("assessChange", 422, "POST", "/changes", json={"product_id": PRODUCT_ID, "edits": [
        {"field": "lot", "new_value": "A"}, {"field": "lot", "new_value": "B"}]})  # duplicate_field
    c("listAffectedLabels", 200, "GET", f"/changes/{made_id}/affected")
    seeded = c("listAffectedLabels", 200, "GET", f"/changes/{CHANGE_ID}/affected")  # the seed stores its assessment
    c("listAffectedLabels", 404, "GET", "/changes/chg_missing/affected")
    c("listAffectedLabels", 401, "GET", f"/changes/{made_id}/affected", user=None)
    decisions = [{"impact_id": i["impact_id"], "user_decision": "confirmed"} for i in items]
    confirm_body = {"parse_confirmed": True, "decisions": decisions}
    c("confirmChange", 200, "POST", f"/changes/{made_id}/confirm", json=confirm_body)
    seeded_body = {"parse_confirmed": True, "decisions": [
        {"impact_id": i["impact_id"], "user_decision": "confirmed"} for i in seeded.json()["items"]]}
    c("confirmChange", 200, "POST", f"/changes/{CHANGE_ID}/confirm", json=seeded_body)
    c("confirmChange", 401, "POST", f"/changes/{made_id}/confirm", user=None, json=confirm_body)
    c("confirmChange", 403, "POST", f"/changes/{made_id}/confirm", user=REVIEWER, json=confirm_body)
    c("confirmChange", 404, "POST", "/changes/chg_missing/confirm", json=confirm_body)
    c("confirmChange", 422, "POST", f"/changes/{made_id}/confirm", json={**confirm_body, "parse_confirmed": False})
    nothing = c("assessChange", 201, "POST", "/changes", json={"product_id": PRODUCT_ID, "edits": [
        {"field": "colour", "new_value": "blue"}]})
    c("confirmChange", 409, "POST", f"/changes/{nothing.json()['change']['change_id']}/confirm", json=confirm_body)

    # reviews: error shapes first, then a self-approval, a reject, and an approval that is later voided
    url = f"/label-versions/{L3}/reviews"
    approve = {"decision": "approve", "artifact_sha256": L3_SHA256, "check_id": "chk_0003"}
    c("reviewArtwork", 403, "POST", url, user=EDITOR, json=approve)
    c("reviewArtwork", 401, "POST", url, user=None, json=approve)
    c("reviewArtwork", 404, "POST", "/label-versions/lbv_missing/reviews", user=REVIEWER, json=approve)
    c("reviewArtwork", 422, "POST", url, user=REVIEWER, json={**approve, "check_id": None})
    c("reviewArtwork", 409, "POST", url, user=REVIEWER, json={**approve, "artifact_sha256": "0" * 64})
    c("reviewArtwork", 409, "POST", url, user=REVIEWER, json={**approve, "check_id": "chk_0001"})

    admin_change = c(
        "assessChange", 201, "POST", "/changes", user=ADMIN, json={"product_id": PRODUCT_ID, "edits": EDIT}
    )
    with sf() as session:
        own = add_label_version(
            session,
            EDITOR,
            PRODUCT_ID,
            "files/own.svg",
            kind="generated",
            artifact_sha256="a" * 64,
            change_id=admin_change.json()["change"]["change_id"],
        )
        own_check = add_check_result(session, "self_check", [], version_id=own.version_id, artifact_sha256="a" * 64)
    own_body = {"decision": "approve", "artifact_sha256": "a" * 64, "check_id": own_check.check_id}
    c("reviewArtwork", 403, "POST", f"/label-versions/{own.version_id}/reviews", user=ADMIN, json=own_body)

    c("reviewArtwork", 201, "POST", url, user=REVIEWER, json={**approve, "comment": "ok"})
    c("listReviews", 200, "GET", url)
    c("getChange", 200, "GET", f"/changes/{CHANGE_ID}")  # status reviewed
    with sf() as session:
        add_label_version(
            session,
            EDITOR,
            PRODUCT_ID,
            "files/l4.svg",
            kind="generated",
            label_id=LABEL_ID,
            artifact_sha256="b" * 64,
            change_id=CHANGE_ID,
        )
    c("reviewArtwork", 409, "POST", url, user=ADMIN, json=approve)  # version_superseded
    c("getChange", 200, "GET", f"/changes/{CHANGE_ID}")  # status draft again
    c("getLabelVersion", 200, "GET", f"/label-versions/{L3}")

    c(
        "reviewArtwork",
        201,
        "POST",
        f"/label-versions/{own.version_id}/reviews",
        user=REVIEWER,
        json={"decision": "reject", "artifact_sha256": "a" * 64, "comment": "No."},
    )
    c("reviewArtwork", 409, "POST", f"/label-versions/{own.version_id}/reviews", user=REVIEWER, json=own_body)  # closed
    c("getChange", 200, "GET", f"/changes/{admin_change.json()['change']['change_id']}")  # closed true
    c("getProductHistory", 200, "GET", f"/products/{PRODUCT_ID}/history")

    # checker (Step 21c): inspect, re-check, jobs, check results, search
    inspect = c("inspectLabel", 202, "POST", f"/label-versions/{L2_ID}/inspect")
    job = c("getJob", 200, "GET", f"/jobs/{inspect.json()['job_id']}", user=None)
    assert job.json()["state"] == "done"
    c("getCheckResult", 200, "GET", job.json()["result_url"])
    c("getCheckResult", 401, "GET", job.json()["result_url"], user=None)
    c("getCheckResult", 404, "GET", "/check-results/chk_missing")
    c("getJob", 404, "GET", "/jobs/job_deadbeef", user=None)
    c("inspectLabel", 200, "POST", f"/label-versions/{L2_ID}/inspect")
    c("inspectLabel", 401, "POST", f"/label-versions/{L2_ID}/inspect", user=None)
    c("inspectLabel", 404, "POST", "/label-versions/lbv_missing/inspect")
    c("inspectLabel", 422, "POST", f"/label-versions/{L2_ID}/inspect", json={"retrieval": {"rerank": True}})
    c("recheckArtwork", 409, "POST", f"/label-versions/{L2_ID}/recheck")
    c("recheckArtwork", 202, "POST", f"/label-versions/{L3}/recheck")
    c("recheckArtwork", 200, "POST", f"/label-versions/{L3}/recheck")
    c("recheckArtwork", 401, "POST", f"/label-versions/{L3}/recheck", user=None)
    c("recheckArtwork", 404, "POST", "/label-versions/lbv_missing/recheck")
    search = {"query": "expiration date format", "module": "device", "retrieval": {"method": "bm25"}}
    c("searchEvidence", 200, "POST", "/search", user=None, json=search)
    c("searchEvidence", 422, "POST", "/search", user=None, json={"query": "x"})

    # coverage: every documented status of every real operation was validated at least once
    real_in_spec = {op: documented_statuses(op) for op in REAL_OPERATIONS}
    missing = {op: sorted(codes - run.seen[op]) for op, codes in real_in_spec.items() if codes - run.seen[op]}
    assert not missing, missing


def test_validation_is_not_vacuous(run: Run) -> None:
    """A broken copy of a real response must fail the check, so a passing run means something."""
    body = run.client.get(f"/changes/{CHANGE_ID}", headers=h(EDITOR)).json()
    assert not conformance_errors("getChange", 200, body)
    assert conformance_errors("getChange", 200, {**body, "status": "approved"})
    assert conformance_errors("getChange", 200, {**body, "surprise": 1})
    assert conformance_errors("getChange", 200, {k: v for k, v in body.items() if k != "closed"})
    review = run.client.post(
        f"/label-versions/{L3}/reviews",
        headers=h(REVIEWER),
        json={"decision": "return", "artifact_sha256": L3_SHA256, "comment": "Fix."},
    ).json()
    assert not conformance_errors("reviewArtwork", 201, review)
    assert conformance_errors("reviewArtwork", 201, {**review, "resulting_status": "reviewed"})
    with pytest.raises(AssertionError, match="not documented"):
        conformance_errors("getCurrentUser", 418, {})


def test_every_real_operation_is_in_the_spec_with_a_success_response() -> None:
    for operation_id in REAL_OPERATIONS:
        codes = documented_statuses(operation_id)
        assert codes & {200, 201}, operation_id
        assert find_operation(operation_id)["tags"], operation_id
