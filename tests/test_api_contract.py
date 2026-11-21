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
from tests.upload_helpers import jpeg_bytes, passing_gate, png_bytes, rejecting_gate

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
    run.client.app.state.quality_gate = passing_gate

    # upload, scan, extraction (Step 24a)
    form = {"source": "upload", "product_id": PRODUCT_ID}
    sent = c("uploadScan", 202, "POST", "/scans", files={"file": ("a.png", png_bytes(), "image/png")}, data=form)
    scan_url = sent.json()["result_url"]
    scan = c("getScan", 200, "GET", scan_url).json()
    assert scan["state"] == "done"
    c("getScan", 401, "GET", scan_url, user=None)
    c("getScan", 404, "GET", "/scans/scn_00000000")
    ext_url = f"/label-versions/{scan['version_id']}/extraction"
    c("getExtraction", 200, "GET", ext_url)
    c("getExtraction", 401, "GET", ext_url, user=None)
    c("getExtraction", 404, "GET", "/label-versions/lbv_00000000/extraction")
    c("confirmExtraction", 200, "POST", ext_url + "/confirm", json={"fields": {"lot": "LOT: A1"}})
    c("confirmExtraction", 401, "POST", ext_url + "/confirm", user=None, json={"fields": {}})
    c("confirmExtraction", 403, "POST", ext_url + "/confirm", user=REVIEWER, json={"fields": {}})
    c("confirmExtraction", 404, "POST", "/label-versions/lbv_00000000/extraction/confirm", json={"fields": {}})
    c("confirmExtraction", 422, "POST", ext_url + "/confirm", json={"fields": {"nonsense": "x"}})
    c("uploadScan", 401, "POST", "/scans", user=None, files={"file": ("a.png", png_bytes(), "image/png")}, data=form)
    c("uploadScan", 403, "POST", "/scans", user=REVIEWER, data=form,
      files={"file": ("a.png", png_bytes(), "image/png")})
    c("uploadScan", 404, "POST", "/scans", files={"file": ("a.png", png_bytes(), "image/png")},
      data={"source": "upload", "product_id": "prd_missing"})
    c("uploadScan", 422, "POST", "/scans", files={"file": ("a.png", b"not an image", "image/png")}, data=form)
    run.client.app.state.quality_gate = rejecting_gate  # a failed scan (retake_photo) must conform to Scan and Job too
    failed = c("uploadScan", 202, "POST", "/scans", files={"file": ("b.jpg", jpeg_bytes(), "image/jpeg")}, data=form)
    assert c("getScan", 200, "GET", failed.json()["result_url"]).json()["error"]["error"] == "retake_photo"
    assert c("getJob", 200, "GET", f"/jobs/{failed.json()['job_id']}").json()["error"]["error"] == "retake_photo"
    run.client.app.state.quality_gate = passing_gate

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
    c("publishVersion", 201, "POST", f"/label-versions/{L3}/publish", user=REVIEWER)  # Step 25b
    c("publishVersion", 200, "POST", f"/label-versions/{L3}/publish", user=REVIEWER)
    c("publishVersion", 401, "POST", f"/label-versions/{L3}/publish", user=None)
    c("publishVersion", 403, "POST", f"/label-versions/{L3}/publish", user=EDITOR)
    c("publishVersion", 404, "POST", "/label-versions/lbv_missing/publish", user=REVIEWER)
    c("getChange", 200, "GET", f"/changes/{CHANGE_ID}")  # status published
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
    c("publishVersion", 409, "POST", f"/label-versions/{own.version_id}/publish", user=REVIEWER)  # change_closed
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

    # ask (Step 23c): fake provider, fixed retrieval
    from src.rag.provider import NullProvider
    from src.rag.service import RagService
    from tests.rag_api_helpers import stub_service

    run.client.app.state.rag = stub_service()
    pub = {"question": "where does the expiration date go", "product_id": "prd_demo"}
    c("askPublic", 200, "POST", "/public/ask", user=None, json=pub)
    c("askPublic", 200, "POST", "/public/ask", user=None, json={**pub, "question": "how much should I take for my cold"})  # noqa: E501
    c("askPublic", 422, "POST", "/public/ask", user=None, json={"question": "x"})
    c("askProfessional", 200, "POST", "/ask", user=None, json={"question": "date format on a device label"})
    c("askProfessional", 200, "POST", "/ask", user=None, json={"question": "should I take two of these"})
    c("askProfessional", 422, "POST", "/ask", user=None, json={"question": " "})
    # public medicine mode (Step 25a): stub matching over the real data/medicine catalog
    from tests.medicine_helpers import stub_medicine

    run.client.app.state.medicine = stub_medicine()
    c("matchMedicine", 200, "POST", "/public/match", user=None, json={"product_name": "Childrens Ibuprofen"})
    c("matchMedicine", 200, "POST", "/public/match", user=None, json={"product_name": "Zzyzx Gummies"})
    c("matchMedicine", 422, "POST", "/public/match", user=None, json={"product_name": " "})
    run.client.app.state.medicine = stub_medicine(broken=True)
    c("matchMedicine", 503, "POST", "/public/match", user=None, json={"product_name": "Childrens Ibuprofen"})
    run.client.app.state.medicine = stub_medicine()
    # public photo scan (CR-27): stub reader, real matcher thresholds over the stub ranker
    from src.api import public_scans
    from tests.test_public_scan import FIRST, reader

    run.client.app.state.public_reader = reader([FIRST])
    shot = {"file": ("pack.png", png_bytes(), "image/png")}
    sent = c("publicScan", 202, "POST", "/public/scans", user=None, files=shot)
    c("getPublicScan", 200, "GET", sent.json()["result_url"], user=None)
    c("getPublicScan", 404, "GET", "/public/scans/pscn_00000000", user=None)
    c("publicScan", 422, "POST", "/public/scans", user=None, files={"file": ("a.png", b"junk", "image/png")})
    run.client.app.state.quality_gate = rejecting_gate
    failed = c("publicScan", 202, "POST", "/public/scans", user=None, files=shot)
    c("getPublicScan", 409, "GET", failed.json()["result_url"], user=None)
    run.client.app.state.quality_gate = passing_gate
    taken = [public_scans.SLOTS.acquire(blocking=False) for _ in range(public_scans.MAX_RUNNING)]
    try:
        c("publicScan", 429, "POST", "/public/scans", user=None, files=shot)
    finally:
        for ok in taken:
            if ok:
                public_scans.release()
    # optional AI answer (Step 24c): a fake provider whose reply fails verification, so the job falls back
    from src.rag.provider import FakeProvider

    run.client.app.state.ai_provider = FakeProvider("not json")
    started = c("askPublic", 202, "POST", "/public/ask?mode=ai", user=None, json=pub)
    c("getJob", 200, "GET", f"/jobs/{started.json()['job_id']}", user=None)
    c("askProfessional", 202, "POST", "/ask?mode=ai", user=None, json={"question": "date format on a device label"})
    c("askPublic", 422, "POST", "/public/ask?mode=bogus", user=None, json=pub)
    monkeypatch.setattr("src.ir.step18_config.load_system", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    run.client.app.state.rag = RagService(provider=NullProvider())
    c("askPublic", 503, "POST", "/public/ask", user=None, json=pub)
    c("askProfessional", 503, "POST", "/ask", user=None, json={"question": "date format"})

    # generate, artwork, exports, download (Step 24b): a fake renderer, so no CV libraries are needed
    from sqlalchemy import select

    from src.api.models import Artifact
    from tests.artwork_helpers import FakeEngine

    engine = FakeEngine()
    run.client.app.state.artwork_engine = engine
    gen = {"name": "Gen Pump", "udi_di": "00000000000000", "manufacturer": "M", "manufacturer_address": "A",
           "model": "G1", "extra": {"lot": "L1", "expiry": "2030-06-30", "serial": "S1"}}
    gen_slots = [
        {"id": "name", "type": "text", "field": "product_name", "bbox_mm": [5, 12, 60, 6], "size_pt": 12},
        {"id": "barcode", "type": "barcode", "field": "udi", "symbology": "GS1_DataMatrix",
         "bbox_mm": [70, 20, 25, 25]},
    ]

    def gen_family(slots: list[dict]) -> tuple[str, str]:
        pid = c("registerProduct", 201, "POST", "/products", json=gen).json()["product"]["product_id"]
        c("registerTemplate", 201, "POST", f"/products/{pid}/templates",
          json={"size_mm": {"w": 100, "h": 60}, "background": None, "slots": slots})
        with sf() as session:
            return pid, add_label_version(session, EDITOR, pid, "uploads/" + "a" * 64 + ".png").label_id

    def gen_change(pid: str, confirm: bool) -> str:
        made = c("assessChange", 201, "POST", "/changes", json={"product_id": pid, "edits": [
            {"field": "name", "new_value": "Gen Pump 2"}]})
        if confirm:
            decisions = [{"impact_id": i["impact_id"], "user_decision": "confirmed"} for i in made.json()["affected"]]
            c("confirmChange", 200, "POST", f"/changes/{made.json()['change']['change_id']}/confirm",
              json={"parse_confirmed": True, "decisions": decisions})
        return made.json()["change"]["change_id"]

    gen_pid, gen_label = gen_family(gen_slots)
    gen_body = {"label_id": gen_label, "test_data": True}
    ready = gen_change(gen_pid, confirm=True)
    unconfirmed = gen_change(gen_pid, confirm=False)
    started = c("generateArtwork", 202, "POST", f"/changes/{ready}/generate", json=gen_body)
    artwork_url = c("getJob", 200, "GET", f"/jobs/{started.json()['job_id']}").json()["result_url"]
    art = c("getArtwork", 200, "GET", artwork_url).json()
    c("getArtwork", 401, "GET", artwork_url, user=None)
    c("getArtwork", 404, "GET", "/artworks/art_00000000")
    c("generateArtwork", 401, "POST", f"/changes/{ready}/generate", user=None, json=gen_body)
    c("generateArtwork", 403, "POST", f"/changes/{ready}/generate", user=REVIEWER, json=gen_body)
    c("generateArtwork", 404, "POST", "/changes/chg_missing/generate", json=gen_body)
    c("generateArtwork", 409, "POST", f"/changes/{unconfirmed}/generate", json=gen_body)  # change_not_confirmed
    needs = c("generateArtwork", 409, "POST", f"/changes/{ready}/generate", json={"label_id": gen_label})
    assert needs.json()["error"] == "needs_input"  # placeholder identifier without test_data: NeedsInput shape
    bad_pid, bad_label = gen_family([{**gen_slots[0], "bbox_mm": [5, 2, 60, 6]}, gen_slots[1]])
    c("generateArtwork", 422, "POST", f"/changes/{gen_change(bad_pid, True)}/generate", json={"label_id": bad_label})
    engine.unavailable = True
    c("generateArtwork", 503, "POST", f"/changes/{ready}/generate", json=gen_body)
    engine.unavailable = False
    exports_url = f"/label-versions/{art['version_id']}/exports"
    package = c("getExports", 200, "GET", exports_url).json()
    c("getExports", 401, "GET", exports_url, user=None)
    c("getExports", 404, "GET", "/label-versions/lbv_00000000/exports")
    pdf = run.client.get(package["pdf"]["url"], headers=h(EDITOR))  # a file, not JSON: checked by hand
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf" and pdf.headers["X-Draft-Mark"]
    run.seen["downloadArtifact"].add(200)
    c("downloadArtifact", 401, "GET", package["pdf"]["url"], user=None)
    c("downloadArtifact", 404, "GET", "/artifacts/" + "0" * 64)
    c("downloadArtifact", 422, "GET", "/artifacts/not-a-hash")
    with sf() as session:
        qr_sha = session.scalars(select(Artifact).where(Artifact.role == "qr_png")).first().sha256
    c("downloadArtifact", 409, "GET", f"/artifacts/{qr_sha}")  # not published yet

    # print verification (Step 25b): a fake CV engine, a draft is refused, an approved version is verified
    from tests.test_api_printverify import FakePrintEngine

    run.client.app.state.print_engine = FakePrintEngine()
    run.client.app.state.quality_gate = passing_gate
    pv_url = f"/label-versions/{art['version_id']}/print-verifications"
    photo = {"photo": ("p.png", png_bytes(), "image/png")}
    c("verifyPrint", 409, "POST", pv_url, files=photo, data={"condition": "phone_photo"})  # not_approved
    with sf() as session:
        sha = art["artifact_sha256"]
        pv_check = add_check_result(session, "self_check", [], version_id=art["version_id"], artifact_sha256=sha)
    c("reviewArtwork", 201, "POST", f"/label-versions/{art['version_id']}/reviews", user=REVIEWER,
      json={"decision": "approve", "artifact_sha256": sha, "check_id": pv_check.check_id})
    started = c("verifyPrint", 202, "POST", pv_url, files=photo, data={"condition": "phone_photo"})
    verification_url = c("getJob", 200, "GET", f"/jobs/{started.json()['job_id']}").json()["result_url"]
    c("getPrintVerification", 200, "GET", verification_url)
    c("getPrintVerification", 401, "GET", verification_url, user=None)
    c("getPrintVerification", 404, "GET", "/print-verifications/pv_00000000")
    c("listPrintVerifications", 200, "GET", pv_url)
    c("listPrintVerifications", 401, "GET", pv_url, user=None)
    c("listPrintVerifications", 404, "GET", "/label-versions/lbv_00000000/print-verifications")
    c("verifyPrint", 401, "POST", pv_url, user=None, files=photo, data={"condition": "phone_photo"})
    c("verifyPrint", 404, "POST", "/label-versions/lbv_00000000/print-verifications", files=photo,
      data={"condition": "phone_photo"})
    c("verifyPrint", 422, "POST", pv_url, files=photo, data={"condition": "sepia"})

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
        assert codes & {200, 201, 202}, operation_id
        assert find_operation(operation_id)["tags"], operation_id
