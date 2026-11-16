"""Step 24b: generateArtwork, getArtwork, getExports and downloadArtifact, with a fake renderer (no CV libraries).

The real renderer is covered by tests/test_e2e_artwork.py, which is skipped when its libraries are missing.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from src.api.main import create_app
from src.api.models import Artifact, GeneratedArtwork, LabelTemplate, LabelVersion, ProductVersion, PublishedPage
from src.api.store import add_check_result, add_label_version
from src.checker.settings import CheckerSettings, RetrievalSettings
from tests.artwork_helpers import MARK, FakeEngine
from tests.openapi_helpers import conformance_errors

EDITOR, REVIEWER, ADMIN = "usr_demo_editor", "usr_demo_reviewer", "usr_demo_admin"
GOOD_GTIN = "09506000134352"  # a GS1 documentation example, valid check digit (used only as test input)
TEMPLATE = json.loads((Path(__file__).parents[1] / "src" / "gen" / "templates" / "test_device.json").read_text())
RECORD = {
    "name": "Test Pump", "model": "TP-1", "manufacturer": "Demo Labs", "manufacturer_address": "12 Demo Road",
    "udi_di": "00000000000000", "sterilization": "EO", "storage": "Store dry",
    "extra": {"lot": "LOT1", "expiry": "2030-06-30", "serial": "SN1"},
}


def h(user: str = EDITOR) -> dict[str, str]:
    """Headers naming the calling user."""
    return {"X-User-Id": user}


class World:
    """One app with a product, its template and an uploaded label family, and a fake renderer."""

    def __init__(self, client: TestClient, engine: FakeEngine, product_id: str, label_id: str) -> None:
        self.client, self.engine, self.product_id, self.label_id = client, engine, product_id, label_id

    def change(self, edits: list[dict[str, str]], confirm: bool = True) -> str:
        """Create a change and (optionally) confirm every item the assessment lists."""
        made = self.client.post("/changes", headers=h(), json={"product_id": self.product_id, "edits": edits})
        assert made.status_code == 201, made.text
        change_id = made.json()["change"]["change_id"]
        if confirm:
            decisions = [{"impact_id": i["impact_id"], "user_decision": "confirmed"} for i in made.json()["affected"]]
            done = self.client.post(f"/changes/{change_id}/confirm", headers=h(),
                                    json={"parse_confirmed": True, "decisions": decisions})
            assert done.status_code == 200, done.text
        return change_id

    def generate(self, change_id: str, test_data: bool = True, user: str = EDITOR):
        """POST generateArtwork for the world's label."""
        return self.client.post(f"/changes/{change_id}/generate", headers=h(user),
                                json={"label_id": self.label_id, "test_data": test_data})

    def artwork(self, response: Any) -> dict[str, Any]:
        """Follow a 202 job to its artwork."""
        assert response.status_code == 202, response.text
        job = self.client.get(f"/jobs/{response.json()['job_id']}", headers=h()).json()
        assert job["state"] == "done", job
        art = self.client.get(job["result_url"], headers=h())
        assert art.status_code == 200, art.text
        return art.json()

    def rows(self, model: type, **filters: Any) -> int:
        """Number of rows in one table (filter on this world's product or label to leave the demo seed out)."""
        with self.client.app.state.session_factory() as session:
            stmt = select(func.count()).select_from(model)
            for key, value in filters.items():
                stmt = stmt.where(getattr(model, key) == value)
            return session.scalar(stmt) or 0

    def versions(self) -> int:
        """Label versions of this world's family."""
        return self.rows(LabelVersion, label_id=self.label_id)

    def product_versions(self) -> int:
        """Product versions of this world's product."""
        return self.rows(ProductVersion, product_id=self.product_id)

    def first_version(self) -> str:
        """The uploaded version that started the family."""
        with self.client.app.state.session_factory() as session:
            return session.scalars(select(LabelVersion).where(LabelVersion.label_id == self.label_id).order_by(
                LabelVersion.artwork_version)).first().version_id


@pytest.fixture()
def world(tmp_path, monkeypatch) -> World:
    monkeypatch.setenv("LABELLENS_FILES_DIR", str(tmp_path))
    with TestClient(create_app("sqlite://", seed=True)) as client:
        engine = FakeEngine()
        client.app.state.artwork_engine = engine
        client.app.state.checker_settings = CheckerSettings(retrieval=RetrievalSettings(method="bm25"))
        product = client.post("/products", headers=h(), json={**RECORD, "intended_market": ["US"]}).json()
        pid = product["product"]["product_id"]
        slots = [{k: v for k, v in s.items()} for s in TEMPLATE["slots"]]
        made = client.post(f"/products/{pid}/templates", headers=h(),
                           json={"size_mm": TEMPLATE["size_mm"], "background": None, "slots": slots})
        assert made.status_code == 201, made.text
        with client.app.state.session_factory() as session:
            first = add_label_version(session, EDITOR, pid, "uploads/" + "a" * 64 + ".png")
        yield World(client, engine, pid, first.label_id)


def test_text_change_keeps_the_barcode_and_appends_a_draft(world: World) -> None:
    change = world.change([{"field": "name", "new_value": "Test Pump Mk2"}])
    versions_before = world.versions()
    art = world.artwork(world.generate(change))
    assert not conformance_errors("getArtwork", 200, art)
    assert art["barcode_decision"]["decision"] == "KEEP"
    assert art["draft_watermark"] is True and art["test_data"] is True
    with world.client.app.state.session_factory() as session:
        old = session.scalars(select(LabelVersion).where(LabelVersion.label_id == world.label_id).order_by(
            LabelVersion.artwork_version)).all()
        assert len(old) == 2 and world.versions() == versions_before + 1
        first, new = old
        assert first.kind == "uploaded" and first.artifact_sha256 is None  # the old version was not touched
        assert new.kind == "generated" and new.artwork_version == 2 and new.parent_version_id == first.version_id
        assert new.artifact_sha256 == art["artifact_sha256"] and new.change_id == change
        assert new.template_version == 2 and new.product_version == 2
        product = session.scalars(select(ProductVersion).where(
            ProductVersion.product_id == world.product_id, ProductVersion.version == 2)).one()
        assert product.name == "Test Pump Mk2" and product.source_change_id == change
        assert session.scalars(select(GeneratedArtwork)).one().self_check_id == art["self_check_id"]
    status = world.client.get(f"/label-versions/{new.version_id}", headers=h()).json()
    assert status["status"] == "draft"  # the layout check written at generation does not make it `checked`
    assert status["draft_watermark"] is True


def test_encoded_change_needs_confirmation_then_regenerates(world: World) -> None:
    change = world.change([{"field": "lot", "new_value": "LOT2"}], confirm=False)
    blocked = world.generate(change)
    assert blocked.status_code == 409 and blocked.json()["error"] == "needs_input"
    assert not conformance_errors("generateArtwork", 409, blocked.json())
    assert blocked.json()["barcode_decision"]["required_identifier"] == "confirm_lot"
    assert blocked.json()["task"]["task_id"] == "task_confirm_lot"
    assert world.rows(GeneratedArtwork) == 0 and world.product_versions() == 1 and world.engine.render_calls == 0
    confirmed = world.change([{"field": "lot", "new_value": "LOT3"}])
    art = world.artwork(world.generate(confirmed))
    assert art["barcode_decision"]["decision"] == "REGENERATE"
    assert world.engine.revise_calls[-1]["confirmed"] == {"confirmed_lot_change": True}
    assert art["change_log"][0]["field"] == "lot" and "BC-REGENERATE" in art["change_log"][0]["rules_fired"]


def test_model_change_never_invents_an_identifier(world: World) -> None:
    change = world.change([{"field": "model", "new_value": "TP-2"}])
    blocked = world.generate(change)
    assert blocked.status_code == 409 and blocked.json()["error"] == "needs_input"
    assert blocked.json()["barcode_decision"]["required_identifier"] == "udi_di"
    assert blocked.json()["task"]["task_id"] == "task_udi_di"
    assert world.rows(GeneratedArtwork) == 0 and world.engine.revise_calls == []
    paired = world.change([{"field": "model", "new_value": "TP-3"}, {"field": "udi_di", "new_value": GOOD_GTIN}])
    art = world.artwork(world.generate(paired))
    assert art["barcode_decision"]["decision"] == "REGENERATE"
    with world.client.app.state.session_factory() as session:
        newest = session.scalars(select(ProductVersion).where(ProductVersion.product_id == world.product_id).order_by(
            ProductVersion.version.desc())).first()
        assert newest.udi_di == GOOD_GTIN and newest.model == "TP-3"


def test_the_placeholder_identifier_needs_test_data(world: World) -> None:
    change = world.change([{"field": "name", "new_value": "Other"}])
    blocked = world.generate(change, test_data=False)
    assert blocked.status_code == 409 and blocked.json()["error"] == "needs_input"
    assert blocked.json()["barcode_decision"]["required_identifier"] == "udi_di"
    assert world.versions() == 1


def test_refusals_before_any_job(world: World) -> None:
    unconfirmed = world.change([{"field": "name", "new_value": "X"}], confirm=False)
    refused = world.generate(unconfirmed)
    assert refused.status_code == 409 and refused.json()["error"] == "change_not_confirmed"
    assert not conformance_errors("generateArtwork", 409, refused.json())
    two = world.change([{"field": "name", "new_value": "Y"}, {"field": "storage", "new_value": "Cold"}])
    assert world.generate(two).json()["error"] == "unsupported_edits"
    nothing = world.client.post("/changes", headers=h(), json={"product_id": world.product_id, "edits": [
        {"field": "colour", "new_value": "red"}]}).json()["change"]["change_id"]
    assert world.generate(nothing).json()["error"] == "nothing_assessed"
    ok = world.change([{"field": "name", "new_value": "Z"}])
    assert world.client.post(f"/changes/{ok}/generate", headers=h(REVIEWER),
                             json={"label_id": world.label_id}).status_code == 403
    assert world.client.post(f"/changes/{ok}/generate", json={"label_id": world.label_id}).status_code == 401
    assert world.client.post("/changes/chg_missing/generate", headers=h(),
                             json={"label_id": world.label_id}).status_code == 404
    missing = world.client.post(f"/changes/{ok}/generate", headers=h(), json={"label_id": "lbl_missing"})
    assert missing.status_code == 404
    seeded = world.client.post("/changes/chg_0002/generate", headers=h(),
                               json={"label_id": world.label_id, "test_data": True})
    assert seeded.status_code == 409 and seeded.json()["error"] == "label_product_mismatch"
    assert world.rows(GeneratedArtwork) == 0 and world.engine.render_calls == 0


def test_layout_failure_is_a_422_check_result(world: World) -> None:
    bad = [dict(s) for s in TEMPLATE["slots"]]
    bad[0]["bbox_mm"] = [5, 2, 60, 6]  # starts inside the 9 mm DRAFT band
    detail = world.client.get(f"/products/{world.product_id}", headers=h()).json()
    world.client.post(f"/products/{world.product_id}/templates", headers=h(), json={
        "template_id": detail["templates"][0]["template_id"],
        "size_mm": TEMPLATE["size_mm"], "background": None, "slots": bad})
    change = world.change([{"field": "name", "new_value": "Q"}])
    response = world.generate(change)
    assert response.status_code == 422, response.text
    body = response.json()
    assert body["kind"] == "layout" and body["passed"] is False and body["findings"][0]["severity"] == "critical"
    assert not conformance_errors("generateArtwork", 422, body)
    assert world.rows(GeneratedArtwork) == 0


def test_a_failed_render_leaves_no_rows(world: World) -> None:
    change = world.change([{"field": "name", "new_value": "R"}])
    world.engine.fail_render = RuntimeError("boom")
    response = world.generate(change)
    job = world.client.get(f"/jobs/{response.json()['job_id']}", headers=h()).json()
    assert job["state"] == "failed" and job["error"]["error"] == "generation_failed"
    assert not conformance_errors("getJob", 200, job)
    assert world.versions() == 1 and world.product_versions() == 1
    assert world.rows(GeneratedArtwork) == 0 and world.rows(Artifact) == 0
    with world.client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(LabelTemplate).where(
            LabelTemplate.product_id == world.product_id)) == 1


def test_files_are_stored_by_hash_and_downloads_are_verified(world: World, tmp_path: Path) -> None:
    art = world.artwork(world.generate(world.change([{"field": "name", "new_value": "S"}])))
    exports = world.client.get(f"/label-versions/{art['version_id']}/exports", headers=h())
    assert exports.status_code == 200 and not conformance_errors("getExports", 200, exports.json())
    body = exports.json()
    assert body["draft_watermark"] is True and "qr" not in body and body["status"] == "draft"
    folder = tmp_path / "artifacts"
    assert not [p for p in folder.iterdir() if p.name.startswith(".")]  # no temp files are left behind
    for role, ext in (("pdf", "pdf"), ("svg", "svg"), ("report", "json")):
        data = world.client.get(body[role]["url"], headers=h())
        sha = body[role].get("sha256") or body[role]["artifact_sha256"]
        assert data.status_code == 200
        assert hashlib.sha256(data.content).hexdigest() == sha
        assert (folder / f"{sha}.{ext}").is_file()
        assert data.headers["X-Draft-Mark"] == MARK and "attachment" in data.headers["Content-Disposition"]
        assert data.headers["X-Content-Type-Options"] == "nosniff"
    assert body["pdf"]["sha256"] == art["artifact_sha256"]
    report = json.loads(world.client.get(body["report"]["url"], headers=h()).content)
    assert report["artifact_sha256"] == art["artifact_sha256"] and report["qr"]["live"] is False
    assert report["visible_markings"] == [MARK] and report["status"] == "DRAFT"

    assert world.client.get(body["pdf"]["url"]).status_code == 401
    assert world.client.get("/artifacts/" + "0" * 64, headers=h()).status_code == 404
    assert world.client.get("/artifacts/not-a-hash", headers=h()).status_code == 422
    with world.client.app.state.session_factory() as session:
        qr = session.scalars(select(Artifact).where(Artifact.role == "qr_png")).one()
        assert world.client.get(f"/artifacts/{qr.sha256}", headers=h()).json()["error"] == "not_published"
    uploaded = world.client.get(f"/label-versions/{world.first_version()}/exports", headers=h())
    assert uploaded.json()["error"] == "no_artifacts"

    (folder / f"{body['pdf']['sha256']}.pdf").write_bytes(b"tampered")
    tampered = world.client.get(body["pdf"]["url"], headers=h())
    assert tampered.status_code == 500 and tampered.json()["error"] == "artifact_corrupt"
    (folder / f"{body['pdf']['sha256']}.pdf").unlink()
    assert world.client.get(body["pdf"]["url"], headers=h()).json()["error"] == "artifact_missing"


def test_qr_is_served_only_after_publication(world: World, tmp_path: Path) -> None:
    art = world.artwork(world.generate(world.change([{"field": "name", "new_value": "T"}])))
    with world.client.app.state.session_factory() as session:
        qr = session.scalars(select(Artifact).where(Artifact.role == "qr_svg")).one()
        review = world.client.post(f"/label-versions/{art['version_id']}/reviews", headers=h(REVIEWER), json={
            "decision": "return", "artifact_sha256": art["artifact_sha256"], "comment": "x"}).json()
        session.add(PublishedPage(page_id="pg_1", label_id=art["label_id"], version_id=art["version_id"],
                                  review_id=review["review_id"], url="https://example.org/p", qr_payload="https://example.org/p",
                                  published_at="2026-11-16T00:00:00Z"))
        session.commit()
    assert world.client.get(f"/artifacts/{qr.sha256}", headers=h()).status_code == 200
    exports = world.client.get(f"/label-versions/{art['version_id']}/exports", headers=h()).json()
    assert exports["qr"]["page_id"] == "pg_1"


def test_approval_is_bound_to_the_pdf_hash_a_read_back_check_and_a_confirmed_change(world: World) -> None:
    change = world.change([{"field": "lot", "new_value": "LOT9"}])
    first = world.artwork(world.generate(change))
    url = f"/label-versions/{first['version_id']}/reviews"
    sha = first["artifact_sha256"]
    with world.client.app.state.session_factory() as session:
        self_check = add_check_result(session, "self_check", [], version_id=first["version_id"], artifact_sha256=sha)
    approve = {"decision": "approve", "artifact_sha256": sha}
    # the layout check written at generation is not a read-back
    refused = world.client.post(url, headers=h(REVIEWER), json={**approve, "check_id": first["self_check_id"]})
    assert refused.status_code == 409 and refused.json()["error"] == "check_not_passed"
    wrong = world.client.post(url, headers=h(REVIEWER), json={**approve, "artifact_sha256": "0" * 64,
                                                             "check_id": self_check.check_id})
    assert wrong.json()["error"] == "hash_mismatch"
    approved = world.client.post(url, headers=h(REVIEWER), json={**approve, "check_id": self_check.check_id})
    assert approved.status_code == 201 and approved.json()["assessment_id"]
    now = world.client.get(f"/label-versions/{first['version_id']}", headers=h()).json()
    assert now["status"] == "reviewed" and now["draft_watermark"] is True  # the stored files still carry the mark
    exports = world.client.get(f"/label-versions/{first['version_id']}/exports", headers=h()).json()
    assert exports["draft_watermark"] is True

    # generating again appends a new version, reuses the product version, and voids the approval
    second = world.artwork(world.generate(change))
    assert second["version_id"] != first["version_id"] and second["artifact_sha256"] != sha
    assert world.product_versions() == 2 and world.versions() == 3
    assert world.client.get(f"/changes/{change}", headers=h()).json()["status"] == "draft"
    superseded = world.client.post(url, headers=h(REVIEWER), json={**approve, "check_id": self_check.check_id})
    assert superseded.json()["error"] == "version_superseded"
    assert world.client.get(f"/label-versions/{first['version_id']}", headers=h()).json()["status"] == "reviewed"
    with world.client.app.state.session_factory() as session:
        latest = session.scalars(select(LabelTemplate).where(LabelTemplate.product_id == world.product_id).order_by(
            LabelTemplate.version.desc())).first()
        assert latest.version == 3  # one template version per generation


def test_a_rejected_change_cannot_generate_again(world: World) -> None:
    change = world.change([{"field": "name", "new_value": "U"}])
    art = world.artwork(world.generate(change))
    rejected = world.client.post(f"/label-versions/{art['version_id']}/reviews", headers=h(REVIEWER), json={
        "decision": "reject", "artifact_sha256": art["artifact_sha256"], "comment": "No."})
    assert rejected.status_code == 201
    again = world.generate(change)
    assert again.status_code == 409 and again.json()["error"] == "change_closed"


def test_two_templates_and_a_label_without_one_is_refused(world: World) -> None:
    world.client.post(f"/products/{world.product_id}/templates", headers=h(), json={
        "size_mm": TEMPLATE["size_mm"], "background": None, "slots": TEMPLATE["slots"]})
    refused = world.generate(world.change([{"field": "name", "new_value": "V"}]))
    assert refused.status_code == 409 and refused.json()["error"] == "template_required"
    assert len(refused.json()["details"]["template_ids"]) == 2
