"""Step 24b: one end-to-end run through the real API with the real renderer, no network.

upload a fixture scan, extract, check, create a change, assess, confirm, generate, re-check, approve, export.
Skipped when the renderer libraries (zxing-cpp, reportlab) or pypdfium2 (reads the PDF back as an image) are missing,
so CI without them stays green. The extractor is a stub that reads what the product record says, so no OCR runs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("zxingcpp")
pytest.importorskip("reportlab")
pypdfium2 = pytest.importorskip("pypdfium2")

from fastapi.testclient import TestClient  # noqa: E402

from src.api.main import create_app  # noqa: E402
from src.api.seed import CHANGE_ID, LABEL_ID  # noqa: E402
from src.checker.settings import CheckerSettings, RetrievalSettings  # noqa: E402
from src.checker.synthetic import extraction_from_truth  # noqa: E402
from src.common.schemas import LabelExtraction  # noqa: E402
from tests.upload_helpers import passing_gate, png_bytes  # noqa: E402

EDITOR, REVIEWER = "usr_demo_editor", "usr_demo_reviewer"
TEMPLATE = json.loads((Path(__file__).parents[1] / "src" / "gen" / "templates" / "test_device.json").read_text())
RECORD = {
    "name": "Test Pump", "model": "TP-1", "manufacturer": "Demo Labs", "manufacturer_address": "12 Demo Road",
    "udi_di": "00000000000000", "sterilization": "EO", "storage": "Store dry",
    "extra": {"lot": "LOT1", "expiry": "2030-06-30", "serial": "SN1"},
}
MARK = "DRAFT, not for production"


def h(user: str = EDITOR) -> dict[str, str]:
    """Headers naming the calling user."""
    return {"X-User-Id": user}


class RecordReader:
    """Replaces the CV extractor: returns an extraction that matches the product's CURRENT record (no OCR)."""

    def __init__(self, client: TestClient, product_id: str) -> None:
        self.client, self.product_id = client, product_id
        self.calls: list[Path] = []

    def __call__(self, path: Path) -> tuple[LabelExtraction, str]:
        self.calls.append(path)
        record = self.client.get(f"/products/{self.product_id}", headers=h()).json()["record"]
        extra = record["extra"]
        fields = {
            "product_name": record["name"], "manufacturer": record["manufacturer"],
            "manufacturer_address": record["manufacturer_address"], "model": f"REF: {record['model']}",
            "lot": f"LOT: {extra['lot']}", "expiry": f"EXP: {extra['expiry']}",
        }
        yymmdd = extra["expiry"][2:4] + extra["expiry"][5:7] + extra["expiry"][8:10]
        ais = {"01": record["udi_di"], "17": yymmdd, "10": extra["lot"], "21": extra["serial"]}
        return extraction_from_truth(path.stem, fields, ais), "stub"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("LABELLENS_FILES_DIR", str(tmp_path))
    with TestClient(create_app("sqlite://", seed=True)) as c:
        c.app.state.checker_settings = CheckerSettings(retrieval=RetrievalSettings(method="bm25"))
        c.app.state.quality_gate = passing_gate
        yield c


def job_result(client: TestClient, response: Any) -> str:
    """Follow a 202 job to its result_url (the job must have finished in `done`)."""
    assert response.status_code == 202, response.text
    job = client.get(f"/jobs/{response.json()['job_id']}", headers=h()).json()
    assert job["state"] == "done", job
    return job["result_url"]


def test_scan_to_export_through_the_real_api(client: TestClient, tmp_path: Path) -> None:
    product = client.post("/products", headers=h(), json={**RECORD, "intended_market": ["US"]}).json()
    pid = product["product"]["product_id"]
    client.app.state.extractor = RecordReader(client, pid)
    assert client.post(f"/products/{pid}/templates", headers=h(), json={
        "size_mm": TEMPLATE["size_mm"], "background": None, "slots": TEMPLATE["slots"]}).status_code == 201

    # upload a fixture scan: the job extracts it and creates version 1 of a label family
    sent = client.post("/scans", headers=h(), files={"file": ("scan.png", png_bytes(), "image/png")},
                       data={"source": "upload", "product_id": pid})
    scan = client.get(job_result(client, sent), headers=h()).json()
    assert scan["state"] == "done"
    label_id, v1 = scan["label_id"], scan["version_id"]
    assert client.get(f"/label-versions/{v1}/extraction", headers=h()).json()["fields"]["lot"] == "LOT: LOT1"

    # check the uploaded label
    inspected = client.post(f"/label-versions/{v1}/inspect", headers=h())
    assert inspected.status_code == 200 and inspected.json()["kind"] == "inspection"

    # create, assess and confirm a lot change (an encoded value, so the barcode must be regenerated)
    made = client.post("/changes", headers=h(), json={"product_id": pid, "edits": [
        {"field": "lot", "new_value": "LOT2"}]})
    assert made.status_code == 201 and made.json()["parser"] == "rules"
    change_id = made.json()["change"]["change_id"]
    blocked = client.post(f"/changes/{change_id}/generate", headers=h(), json={"label_id": label_id, "test_data": True})
    assert blocked.status_code == 409 and blocked.json()["task"]["task_id"] == "task_confirm_lot"  # not confirmed yet
    decisions = [{"impact_id": i["impact_id"], "user_decision": "confirmed"} for i in made.json()["affected"]]
    assert client.post(f"/changes/{change_id}/confirm", headers=h(),
                       json={"parse_confirmed": True, "decisions": decisions}).status_code == 200

    # generate: the placeholder identifier is refused without test_data, accepted with it
    refused = client.post(f"/changes/{change_id}/generate", headers=h(), json={"label_id": label_id})
    assert refused.status_code == 409 and refused.json()["barcode_decision"]["required_identifier"] == "udi_di"
    started = client.post(f"/changes/{change_id}/generate", headers=h(), json={"label_id": label_id, "test_data": True})
    art = client.get(job_result(client, started), headers=h()).json()
    assert art["barcode_decision"]["decision"] == "REGENERATE" and art["draft_watermark"] is True
    assert art["barcode_decision"]["new_payload"].endswith("(10)LOT2(21)SN1")
    v2 = art["version_id"]
    assert v2 != v1 and client.get(f"/label-versions/{v1}", headers=h()).json()["kind"] == "uploaded"

    # the stored PDF is the physical size, carries the visible mark, and matches the recorded hash
    pdf_path = tmp_path / "artifacts" / f"{art['artifact_sha256']}.pdf"
    data = pdf_path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == art["artifact_sha256"]
    document = pypdfium2.PdfDocument(data)
    width_pt, height_pt = document[0].get_size()
    assert (round(width_pt * 25.4 / 72, 1), round(height_pt * 25.4 / 72, 1)) == (100.0, 60.0)
    text = document[0].get_textpage().get_text_range()
    assert MARK in text and "TEST DATA" in text and "LOT2" in text
    document.close()

    # re-check: the PDF is read back as an image (the stub reads the new record), then approve with that check
    rechecked = client.post(f"/label-versions/{v2}/recheck", headers=h())
    check = client.get(job_result(client, rechecked), headers=h()).json()
    assert check["kind"] == "self_check" and check["artifact_sha256"] == art["artifact_sha256"]
    assert check["passed"] is True, check["findings"]
    approve = {"decision": "approve", "artifact_sha256": art["artifact_sha256"], "check_id": check["check_id"]}
    assert client.post(f"/label-versions/{v2}/reviews", headers=h(EDITOR), json=approve).status_code == 403
    approved = client.post(f"/label-versions/{v2}/reviews", headers=h(REVIEWER), json=approve)
    assert approved.status_code == 201, approved.text
    now = client.get(f"/label-versions/{v2}", headers=h()).json()
    assert now["status"] == "reviewed" and now["draft_watermark"] is True  # the stored files still carry the mark

    # export and download
    exports = client.get(f"/label-versions/{v2}/exports", headers=h()).json()
    assert exports["status"] == "reviewed" and exports["draft_watermark"] is True
    downloaded = client.get(exports["pdf"]["url"], headers=h())
    assert downloaded.content == data and downloaded.headers["X-Draft-Mark"].startswith(MARK)
    svg = client.get(exports["svg"]["url"], headers=h()).text
    assert 'id="layer-watermark"' in svg and 'id="slot-barcode"' in svg and MARK in svg
    assert client.get(exports["report"]["url"], headers=h()).json()["artifact_sha256"] == art["artifact_sha256"]

    # a new version voids the approval
    again = client.post(f"/changes/{change_id}/generate", headers=h(), json={"label_id": label_id, "test_data": True})
    v3 = client.get(job_result(client, again), headers=h()).json()["version_id"]
    assert v3 not in (v1, v2) and client.get(f"/changes/{change_id}", headers=h()).json()["status"] == "draft"
    assert client.post(f"/label-versions/{v2}/reviews", headers=h(REVIEWER), json=approve).json()["error"] == (
        "version_superseded")
    assert client.get(f"/label-versions/{v3}", headers=h()).json()["status"] == "draft"


def test_a_text_change_reuses_the_barcode_bytes(client: TestClient, tmp_path: Path) -> None:
    pid = client.post("/products", headers=h(), json=RECORD).json()["product"]["product_id"]
    client.post(f"/products/{pid}/templates", headers=h(), json={
        "size_mm": TEMPLATE["size_mm"], "background": None, "slots": TEMPLATE["slots"]})
    with client.app.state.session_factory() as session:
        from src.api.store import add_label_version

        family = add_label_version(session, EDITOR, pid, "uploads/" + "a" * 64 + ".png").label_id
    made = client.post("/changes", headers=h(), json={"product_id": pid, "edits": [
        {"field": "name", "new_value": "Test Pump Mk2"}]})
    change_id = made.json()["change"]["change_id"]
    decisions = [{"impact_id": i["impact_id"], "user_decision": "confirmed"} for i in made.json()["affected"]]
    client.post(f"/changes/{change_id}/confirm", headers=h(), json={"parse_confirmed": True, "decisions": decisions})
    started = client.post(f"/changes/{change_id}/generate", headers=h(), json={"label_id": family, "test_data": True})
    art = client.get(job_result(client, started), headers=h()).json()
    assert art["barcode_decision"]["decision"] == "KEEP"
    assert art["barcode_decision"]["old_payload"] == art["barcode_decision"]["new_payload"]
    svg = client.get(art["svg_url"], headers=h()).text
    assert "Test Pump Mk2" in svg


def test_the_demo_seed_template_is_refused_because_of_its_background(client: TestClient) -> None:
    """The seeded template has a background image, which the renderer cannot take (contract gap D-5)."""
    body = {"label_id": LABEL_ID, "test_data": True}
    response = client.post(f"/changes/{CHANGE_ID}/generate", headers=h(), json=body)
    assert response.status_code == 422 and response.json()["error"] == "template_background_unsupported", response.text
