"""Step 24a: real upload, scan state, extraction and confirmation, with a stub extractor and stub quality gate."""

from __future__ import annotations

import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from src.api import uploads
from src.api.main import create_app
from src.api.models import Extraction, ExtractionConfirmation, Scan
from tests.checker_api_helpers import EDITOR, REVIEWER, h, install
from tests.upload_helpers import PRODUCT, jpeg_bytes, passing_gate, pdf_bytes, png_bytes, rejecting_gate, upload


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """A seeded app with a stub extractor (counts calls), a passing gate and uploads going to tmp_path."""
    with TestClient(create_app("sqlite://", seed=True)) as client:
        stub = install(client, tmp_path, monkeypatch)
        client.app.state.quality_gate = passing_gate
        yield client, stub, tmp_path


def finish(client, response):
    """The scan row after the job ran (TestClient runs background tasks before it returns)."""
    assert response.status_code == 202, response.text
    scan_id = response.json()["result_url"].rsplit("/", 1)[1]
    return client.get(f"/scans/{scan_id}", headers=h()).json()


def test_happy_path_png_creates_version_and_extraction(env) -> None:
    client, stub, tmp = env
    data = png_bytes()
    response = upload(client, data, h(), name="../../evil name.png")  # the client filename must not matter
    job = response.json()
    assert response.status_code == 202 and job["kind"] == "scan" and job["state"] == "queued"
    scan = finish(client, response)
    assert scan["state"] == "done" and scan["product_id"] == PRODUCT and scan["source"] == "upload"
    sha = hashlib.sha256(data).hexdigest()
    assert scan["file"] == {"file_id": f"fil_{sha[:12]}", "mime": "image/png", "sha256": sha, "pages": 1}
    assert (tmp / "uploads" / f"{sha}.png").read_bytes() == data
    assert not list(tmp.rglob("*evil*"))
    assert client.get(f"/jobs/{job['job_id']}", headers=h()).json()["state"] == "done"
    version = client.get(f"/label-versions/{scan['version_id']}", headers=h()).json()
    assert version["kind"] == "uploaded" and version["label_id"] == scan["label_id"] and version["artwork_version"] == 1
    extraction = client.get(f"/label-versions/{scan['version_id']}/extraction", headers=h()).json()
    assert extraction["scan_id"] == scan["scan_id"] and extraction["confirmed"] is False
    assert extraction["unclear_fields"] == [] and stub.calls == 1


def test_jpeg_is_accepted_and_camera_source_recorded(env) -> None:
    client, _, tmp = env
    scan = finish(client, upload(client, jpeg_bytes(), h(), name="x.png", mime="image/png", source="camera"))
    assert scan["state"] == "done" and scan["file"]["mime"] == "image/jpeg" and scan["source"] == "camera"
    assert list((tmp / "uploads").glob("*.jpg"))


def test_pdf_is_accepted_by_signature(env, monkeypatch) -> None:
    client, stub, tmp = env
    seen = {}

    def fake_render(pdf_path, out_png):  # the real renderer needs pypdfium2, tested separately
        seen["pdf"] = pdf_path.name
        out_png.write_bytes(png_bytes())

    monkeypatch.setattr(uploads, "render_pdf_page", fake_render)
    gate_calls = []
    client.app.state.quality_gate = lambda p: gate_calls.append(p) or passing_gate(p)
    scan = finish(client, upload(client, pdf_bytes(), h(), name="label.png", mime="image/png"))
    assert scan["state"] == "done" and scan["file"]["mime"] == "application/pdf"
    assert seen["pdf"].endswith(".pdf") and stub.calls == 1 and not gate_calls  # a rendered page skips the photo gate
    version = client.get(f"/label-versions/{scan['version_id']}", headers=h()).json()
    assert version["artwork_file"].endswith(".pdf")


def test_pdf_renders_with_pypdfium2(env) -> None:
    pytest.importorskip("pypdfium2")
    client, stub, tmp = env
    scan = finish(client, upload(client, pdf_bytes(), h()))
    assert scan["state"] == "done" and scan["file"]["pages"] == 1 and stub.calls == 1
    assert list((tmp / "uploads").glob("*.page1.png"))


@pytest.mark.parametrize(
    "data", [b"GIF89a" + b"0" * 100, b"<svg xmlns='http://www.w3.org/2000/svg'/>", b"MZ\x90\x00", b"plain text"]
)
def test_bad_type_is_refused_whatever_the_name_or_mime(env, data) -> None:
    client, stub, tmp = env
    response = upload(client, data, h(), name="label.png", mime="image/png")
    assert response.status_code == 422 and response.json()["error"] == "unsupported_media_type"
    assert not (tmp / "uploads").exists() or not list((tmp / "uploads").iterdir())
    assert stub.calls == 0


def test_png_named_pdf_is_judged_by_content(env) -> None:
    client, _, _ = env
    scan = finish(client, upload(client, png_bytes(), h(), name="label.pdf", mime="application/pdf"))
    assert scan["file"]["mime"] == "image/png"


def test_empty_truncated_and_tiny_files_are_invalid(env) -> None:
    client, _, _ = env
    assert upload(client, b"", h()).json()["error"] == "invalid_file"
    assert upload(client, png_bytes()[:40], h()).json()["error"] == "invalid_file"
    assert upload(client, png_bytes()[:-20], h()).json()["error"] == "invalid_file"  # damaged stream
    tiny = upload(client, png_bytes(10, 10), h())
    assert tiny.status_code == 422 and tiny.json()["error"] == "invalid_file"


def test_oversize_file_is_refused(env, monkeypatch) -> None:
    client, stub, _ = env
    monkeypatch.setattr(uploads, "MAX_BYTES", 2000)
    big = png_bytes() + b"\x00" * 3000  # still a valid PNG prefix, over the (patched) cap
    response = upload(client, big, h())
    assert response.status_code == 422 and response.json()["error"] == "file_too_large" and stub.calls == 0


def test_declared_oversize_body_is_refused_before_parsing(env) -> None:
    client, _, _ = env
    headers = {**h(), "content-length": str(uploads.MAX_BYTES + 10**6),
               "content-type": "multipart/form-data; boundary=b"}
    response = client.post("/scans", content=b"x", headers=headers)
    assert response.status_code == 422 and response.json()["error"] == "file_too_large"


def test_pixel_limit_is_read_from_the_header(env, monkeypatch) -> None:
    client, stub, _ = env
    monkeypatch.setattr(uploads, "MAX_PIXELS", 5000)
    response = upload(client, png_bytes(120, 80), h())  # 9600 pixels
    assert response.status_code == 422 and response.json()["error"] == "image_too_large" and stub.calls == 0


def test_input_rules(env) -> None:
    client, _, _ = env
    assert upload(client, png_bytes(), h(), source="fax").status_code == 422
    assert upload(client, png_bytes(), h(), product_id=None).json()["error"] == "validation_error"
    assert upload(client, png_bytes(), h(), product_id="prd_missing").status_code == 404
    assert upload(client, png_bytes(), h(REVIEWER)).status_code == 403
    assert upload(client, png_bytes(), {}).status_code == 401
    assert client.post("/scans", data={"source": "upload", "product_id": PRODUCT}, headers=h()).status_code == 422


def test_quality_gate_rejects_with_retake_photo_and_no_version(env) -> None:
    client, stub, _ = env
    client.app.state.quality_gate = rejecting_gate
    response = upload(client, png_bytes(), h(), source="camera")
    scan = finish(client, response)
    assert scan["state"] == "failed" and "version_id" not in scan and stub.calls == 0
    assert scan["error"]["error"] == "retake_photo" and scan["error"]["details"]["reasons"] == ["glare"]
    job = client.get(f"/jobs/{response.json()['job_id']}", headers=h()).json()
    assert job["state"] == "failed" and job["error"] == scan["error"]
    with client.app.state.session_factory() as session:
        assert session.query(Extraction).count() == 0


def test_extractor_failure_ends_the_scan_in_failed(env) -> None:
    from src.api.extractor import ExtractorUnavailable

    client, stub, _ = env
    stub.error = ExtractorUnavailable("no cv")
    scan = finish(client, upload(client, png_bytes(), h()))
    assert scan["state"] == "failed" and scan["error"]["error"] == "extractor_unavailable"
    stub.error = RuntimeError("boom")
    assert finish(client, upload(client, png_bytes(100, 100), h()))["error"]["error"] == "scan_failed"


def test_unknown_scan_and_extraction_ids(env) -> None:
    client, _, _ = env
    assert client.get("/scans/scn_00000000", headers=h()).status_code == 404
    assert client.get("/scans/scn_00000000").status_code == 401
    assert client.get("/label-versions/lbv_00000000/extraction", headers=h()).status_code == 404
    assert client.get("/scans/scn_0001", headers=h()).headers.get("X-Mock") == "true"  # ids never issued: the mock


def test_confirm_appends_rows_and_keeps_the_original(env) -> None:
    client, _, _ = env
    scan = finish(client, upload(client, png_bytes(), h()))
    vid = scan["version_id"]
    first = client.get(f"/label-versions/{vid}/extraction", headers=h()).json()
    url = f"/label-versions/{vid}/extraction/confirm"
    response = client.post(url, json={"fields": {"lot": " LOT: FIXED1 "}}, headers=h())
    assert response.status_code == 200
    confirmed = response.json()
    assert confirmed["confirmed"] and confirmed["confirmed_by"] == EDITOR and confirmed["unclear_fields"] == []
    assert confirmed["fields"]["lot"] == "LOT: FIXED1" and confirmed["extraction_id"] != first["extraction_id"]
    assert confirmed["fields"]["expiry"] == first["fields"]["expiry"]  # untouched fields keep their value
    newest = client.get(f"/label-versions/{vid}/extraction", headers=h()).json()
    assert newest["extraction_id"] == confirmed["extraction_id"]
    with client.app.state.session_factory() as session:
        rows = session.query(Extraction).filter_by(version_id=vid).order_by(Extraction.seq).all()
        assert len(rows) == 2 and rows[0].payload["fields"]["lot"] != "LOT: FIXED1"  # original row unchanged
        assert session.query(ExtractionConfirmation).count() == 1
        assert session.query(Scan).filter_by(scan_id=scan["scan_id"]).count() >= 3  # queued, processing, done
    # the checker reads the newest extraction, so the correction is what inspect sees
    assert client.post(f"/label-versions/{vid}/inspect", headers=h()).json()["kind"] == "inspection"


def test_confirm_rules(env) -> None:
    client, _, _ = env
    vid = finish(client, upload(client, png_bytes(), h()))["version_id"]
    url = f"/label-versions/{vid}/extraction/confirm"
    assert client.post(url, json={"fields": {"nonsense": "x"}}, headers=h()).status_code == 422
    assert client.post(url, json={"fields": {"lot": "x" * 501}}, headers=h()).status_code == 422
    assert client.post(url, json={"fields": {"lot": "x"}}, headers=h(REVIEWER)).status_code == 403
    assert client.post(url, json={"fields": {"lot": "x"}}).status_code == 401
    assert client.post(url, json={}, headers=h()).status_code == 422
    missing = client.post("/label-versions/lbv_00000000/extraction/confirm", json={"fields": {}}, headers=h())
    assert missing.status_code == 404
    assert client.post(url, json={"fields": {}}, headers=h()).json()["confirmed"] is True  # confirm as extracted


def test_unclear_fields_follow_ocr_confidence(env) -> None:
    client, stub, _ = env

    def low_conf(path):
        extraction, mode = stub(path)
        blocks = [b.model_copy(update={"conf": 0.3 if b.text.startswith("LOT") else b.conf})
                  for b in extraction.ocr_blocks]
        return extraction.model_copy(update={"ocr_blocks": blocks}), mode

    client.app.state.extractor = low_conf
    vid = finish(client, upload(client, png_bytes(), h()))["version_id"]
    assert client.get(f"/label-versions/{vid}/extraction", headers=h()).json()["unclear_fields"] == ["lot"]


def test_stored_scan_rows_are_append_only(env) -> None:
    client, _, _ = env
    vid = finish(client, upload(client, png_bytes(), h()))["version_id"]
    client.post(f"/label-versions/{vid}/extraction/confirm", json={"fields": {}}, headers=h())  # one confirmation row
    with client.app.state.session_factory() as session:
        for sql in ("UPDATE scans SET state='queued'", "DELETE FROM scans", "DELETE FROM extraction_confirmations"):
            with pytest.raises(DBAPIError):
                session.execute(text(sql))
            session.rollback()


def test_resolve_stored_refuses_traversal(tmp_path) -> None:
    from src.api.errors import ApiError

    sha = "a" * 64
    assert uploads.resolve_stored(tmp_path, f"uploads/{sha}.png").parent == (tmp_path / "uploads").resolve()
    bad_paths = ("../x.png", f"uploads/../{sha}.png", f"uploads/{sha}.exe", "uploads/x.png", f"other/{sha}.png")
    for bad in bad_paths:
        with pytest.raises(ApiError):
            uploads.resolve_stored(tmp_path, bad)
