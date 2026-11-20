"""Step 25b: print verification with a fake CV engine (no CV libraries). The real engine has its own run (reports)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from src.api.extractor import ExtractorUnavailable
from src.api.models import PrintVerification
from src.api.store import add_check_result
from tests.openapi_helpers import conformance_errors
from tests.test_api_generate import EDITOR, REVIEWER, World, h, world  # noqa: F401  (world is a fixture)
from tests.upload_helpers import jpeg_bytes, passing_gate, pdf_bytes, png_bytes, rejecting_gate


class FakePrintEngine:
    """Returns a prepared engine result and remembers what it was asked to compare."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.status = "MATCH"
        self.error: Exception | None = None
        self.mismatch_field: str | None = None
        self.unsure_field: str | None = None

    def verify(self, photo: Path, expected: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(expected)
        if self.error:
            raise self.error
        fields = []
        for name, value in expected["fields"].items():
            status = "MATCH"
            observed: str | None = value
            if name == self.mismatch_field:
                status, observed = "MISMATCH", value + "X"
            if name == self.unsure_field:
                status, observed = "NEEDS_HUMAN_REVIEW", None
            fields.append({"field": name, "expected": value, "observed": observed, "status": status,
                           "confidence": None if observed is None else 0.93, "bbox": (1.0, 2.0, 30.0, 8.0)})
        raw = "".join(f"{ai}{v}" for ai, v in expected["barcode_ais"].items())
        barcode = {"type": "DataMatrix", "raw": raw, "parsed": dict(expected["barcode_ais"]), "bbox": None}
        return {"status": self.status, "fields": fields, "issues": [], "warnings": [], "barcode": barcode}


def approved_version(world: World, lot: str = "LOT9") -> str:  # noqa: F811
    """Generate a draft with the fake renderer and approve it (a passed read-back check, a reviewer)."""
    change = world.change([{"field": "lot", "new_value": lot}])
    world.last_change = change  # type: ignore[attr-defined]
    art = world.artwork(world.generate(change))
    version, sha = art["version_id"], art["artifact_sha256"]
    with world.client.app.state.session_factory() as session:
        check = add_check_result(session, "self_check", [], version_id=version, artifact_sha256=sha)
    done = world.client.post(f"/label-versions/{version}/reviews", headers=h(REVIEWER), json={
        "decision": "approve", "artifact_sha256": sha, "check_id": check.check_id})
    assert done.status_code == 201, done.text
    return version


def verify(world: World, version: str, data: bytes | None = None, condition: str = "phone_photo",  # noqa: F811
          user: str | None = EDITOR, name: str = "photo.png", mime: str = "image/png"):
    """POST verifyPrint."""
    return world.client.post(f"/label-versions/{version}/print-verifications", headers=h(user) if user else {},
                             files={"photo": (name, data or png_bytes(), mime)}, data={"condition": condition})


def result(world: World, response: Any) -> dict[str, Any]:  # noqa: F811
    """Follow a 202 job to its stored verification."""
    assert response.status_code == 202, response.text
    job = world.client.get(f"/jobs/{response.json()['job_id']}", headers=h()).json()
    assert job["kind"] == "print_verify"
    assert job["state"] == "done", job
    return world.client.get(job["result_url"], headers=h()).json()


@pytest.fixture()
def pv(world: World):  # noqa: F811
    engine = FakePrintEngine()
    world.client.app.state.print_engine = engine
    world.client.app.state.quality_gate = passing_gate
    return world, engine


def test_a_matching_print_is_stored_with_its_evidence(pv) -> None:
    world, engine = pv  # noqa: F811
    version = approved_version(world)
    body = result(world, verify(world, version))
    problems = conformance_errors("getPrintVerification", 200, body)
    assert not problems, problems
    assert body["outcome"] == "match" and body["mismatches"] == [] and body["version_id"] == version
    assert body["barcode"]["match"] is True and body["barcode"]["expected_payload"].endswith("(10)LOT9(21)SN1")
    assert {f["field"] for f in body["fields"]} == {"product_name", "manufacturer", "manufacturer_address", "model",
                                                    "lot", "expiry"}
    assert body["fields"][0]["confidence"] == 0.93 and body["quality"]["confidence"] == 0.93
    expected = engine.calls[0]
    assert expected["fields"]["lot"] == "LOT9" and expected["barcode_ais"]["10"] == "LOT9"
    listed = world.client.get(f"/label-versions/{version}/print-verifications", headers=h()).json()
    assert [i["verification_id"] for i in listed["items"]] == [body["verification_id"]]
    assert not conformance_errors("listPrintVerifications", 200, listed)


def test_a_wrong_field_is_a_mismatch_with_the_difference(pv) -> None:
    world, engine = pv  # noqa: F811
    engine.status, engine.mismatch_field = "MISMATCH", "lot"
    body = result(world, verify(world, approved_version(world), condition="clean_print_scan"))
    assert body["outcome"] == "mismatch" and body["condition"] == "clean_print_scan"
    assert body["mismatches"] == [
        {"field": "lot", "expected": "LOT9", "observed": "LOT9X", "bbox": [1.0, 2.0, 30.0, 8.0]}]
    assert not conformance_errors("getPrintVerification", 200, body)


def test_weak_evidence_is_rescan_needed_with_a_reason(pv) -> None:
    world, engine = pv  # noqa: F811
    engine.status, engine.unsure_field = "NEEDS_HUMAN_REVIEW", "expiry"
    body = result(world, verify(world, approved_version(world), data=jpeg_bytes(), mime="image/jpeg", name="p.jpg"))
    assert body["outcome"] == "rescan_needed" and "expiry" in body["rescan_reason"]
    assert body["quality"]["confidence"] == 0.0  # one field has no evidence at all


def test_a_photo_that_fails_the_quality_gate_is_rescan_needed_without_reading_it(pv) -> None:
    world, engine = pv  # noqa: F811
    world.client.app.state.quality_gate = rejecting_gate
    body = result(world, verify(world, approved_version(world), condition="glare"))
    assert body["outcome"] == "rescan_needed" and "glare" in body["rescan_reason"] and engine.calls == []
    assert body["quality"]["glare"] > 0 and "barcode" not in body


def test_missing_cv_libraries_end_the_job_failed(pv) -> None:
    world, engine = pv  # noqa: F811
    engine.error = ExtractorUnavailable("CV libraries are not installed (fake)")
    response = verify(world, approved_version(world))
    job = world.client.get(f"/jobs/{response.json()['job_id']}", headers=h()).json()
    assert job["state"] == "failed" and job["error"]["error"] == "extractor_unavailable"
    with world.client.app.state.session_factory() as session:
        assert session.query(PrintVerification).count() == 0  # nothing stored for a failed job


def test_only_an_approved_current_generated_version_can_be_verified(pv) -> None:
    world, engine = pv  # noqa: F811
    change = world.change([{"field": "lot", "new_value": "LOT7"}])
    art = world.artwork(world.generate(change))
    draft = art["version_id"]
    refused = verify(world, draft)
    assert refused.status_code == 409 and refused.json()["error"] == "not_approved"
    assert refused.json()["details"]["status"] == "draft"
    sha = art["artifact_sha256"]
    with world.client.app.state.session_factory() as session:
        check = add_check_result(session, "self_check", [], version_id=draft, artifact_sha256=sha)
    url = f"/label-versions/{draft}/reviews"
    world.client.post(url, headers=h(REVIEWER), json={"decision": "approve", "artifact_sha256": sha,
                                                      "check_id": check.check_id})
    world.client.post(url, headers=h(REVIEWER), json={"decision": "return", "artifact_sha256": sha, "comment": "again"})
    assert verify(world, draft).json()["error"] == "not_approved"  # a returned version is draft again
    world.client.post(url, headers=h(REVIEWER), json={"decision": "reject", "artifact_sha256": sha, "comment": "no"})
    assert verify(world, draft).json()["error"] == "rejected"
    assert engine.calls == []


def test_a_newer_version_voids_the_approval(pv) -> None:
    world, _ = pv  # noqa: F811
    first = approved_version(world, "LOT5")
    world.artwork(world.generate(world.last_change))  # type: ignore[attr-defined]
    assert verify(world, first).json()["error"] == "version_superseded"


def test_an_approved_version_without_generated_artwork_has_no_reference(pv) -> None:
    world, _ = pv  # noqa: F811
    seed = "lbv_exampledevice_carton_l3"  # approvable seed draft, but nothing was generated for it
    world.client.post(f"/label-versions/{seed}/reviews", headers=h(REVIEWER), json={
        "decision": "approve", "artifact_sha256": "23f81fcd260e85a1086f09eaf733427f7cbb09becdf887a081ee857dcad90b74",
        "check_id": "chk_0003"})
    assert verify(world, seed).json()["error"] == "no_reference"


def test_bad_requests(pv) -> None:
    world, _ = pv  # noqa: F811
    version = approved_version(world)
    assert verify(world, version, condition="sepia").status_code == 422
    pdf = verify(world, version, data=pdf_bytes(), name="p.pdf", mime="application/pdf")
    assert pdf.status_code == 422 and pdf.json()["error"] == "unsupported_media_type"
    assert verify(world, version, data=b"not an image").status_code == 422
    assert verify(world, version, user=None).status_code == 401
    assert verify(world, "lbv_00000000").status_code == 404
    assert world.client.get("/print-verifications/pv_00000000", headers=h()).status_code == 404
    assert world.client.get("/print-verifications/pv_0001", headers=h()).headers.get("X-Mock") == "true"  # mock id


def test_the_table_is_append_only(pv) -> None:
    world, _ = pv  # noqa: F811
    result(world, verify(world, approved_version(world)))
    with world.client.app.state.session_factory() as session:
        with pytest.raises(DBAPIError):
            session.execute(text("UPDATE print_verifications SET outcome = 'mismatch'"))


def test_the_photo_gate_is_not_applied_to_a_clean_scan(pv) -> None:
    world, engine = pv  # noqa: F811
    world.client.app.state.quality_gate = rejecting_gate  # would reject any camera photo
    body = result(world, verify(world, approved_version(world), condition="clean_print_scan"))
    assert body["outcome"] == "match" and len(engine.calls) == 1
