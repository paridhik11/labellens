"""Step 21c: inspectLabel, recheckArtwork, getJob, getCheckResult and searchEvidence are real."""

from __future__ import annotations

import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from src.api.db import _add_missing_columns
from src.api.extractor import ExtractorUnavailable
from src.api.main import create_app
from src.api.models import Extraction, Job
from src.api.seed import L3_SHA256
from src.checker.retrieval import module_chunks
from tests.checker_api_helpers import L2, L3, REVIEWER, h, install


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """A seeded app with a stub extractor, returning (client, stub)."""
    with TestClient(create_app("sqlite://", seed=True)) as client:
        yield client, install(client, tmp_path, monkeypatch)


def job_result(client, response):
    """Follow a 202: the job must be done, then fetch its result_url."""
    job = client.get(f"/jobs/{response.json()['job_id']}").json()
    assert job["state"] == "done", job
    return client.get(job["result_url"], headers=h()).json()


def test_first_inspect_is_a_job_second_is_immediate(env) -> None:
    client, stub = env
    first = client.post(f"/label-versions/{L2}/inspect", headers=h())
    assert first.status_code == 202 and first.json()["kind"] == "inspect"
    result = job_result(client, first)
    assert result["kind"] == "inspection" and result["version_id"] == L2 and stub.calls == 1
    second = client.post(f"/label-versions/{L2}/inspect", headers=h())
    assert second.status_code == 200 and stub.calls == 1  # the stored extraction is reused
    assert second.json()["check_id"] != result["check_id"]  # a new check row, nothing overwritten


def test_clean_label_passes_with_coverage_and_no_info_findings(env) -> None:
    client, _ = env
    result = job_result(client, client.post(f"/label-versions/{L2}/inspect", headers=h()))
    assert result["passed"] and result["critical_count"] == 0
    assert all(f["severity"] != "info" for f in result["findings"])
    ids = [c["rule_id"] for c in result["coverage"]]
    assert len(ids) == len(set(ids)) >= 16
    assert result["needs_human_count"] == sum(c["outcome"] == "needs_human" for c in result["coverage"]) > 0
    assert result["retrieval_config"]["method"] == "bm25"


def test_injected_error_gives_a_critical_finding_with_a_real_citation(env) -> None:
    client, stub = env
    stub.fields["expiry"] = "EXP: 31/03/2028"
    result = job_result(client, client.post(f"/label-versions/{L2}/inspect", headers=h()))
    assert not result["passed"] and result["critical_count"] == 1
    finding = next(f for f in result["findings"] if f["rule_id"] == "D-FMT")
    cite = finding["citations"][0]
    chunk = module_chunks("device")[cite["chunk_id"]]
    assert cite["section"] == "801.18" and cite["quote"] in chunk.text
    assert finding["evidence_chunk_ids"] == [cite["chunk_id"]] and "rank" not in cite
    assert next(c for c in result["coverage"] if c["rule_id"] == "D-FMT")["outcome"] == "fail"


def test_extraction_is_stored_append_only(env) -> None:
    client, _ = env
    job_result(client, client.post(f"/label-versions/{L2}/inspect", headers=h()))
    with client.app.state.session_factory() as session:
        row = session.query(Extraction).one()
        assert row.version_id == L2 and row.mode == "stub" and row.payload["label_id"] == "lbl_exampledevice_carton"
        with pytest.raises(Exception, match="append-only"):
            session.execute(text("UPDATE extractions SET mode = 'x'"))
        session.rollback()
        with pytest.raises(Exception, match="append-only"):
            session.execute(text("DELETE FROM jobs"))


def test_recheck_needs_generated_artwork_and_copies_the_hash(env) -> None:
    client, _ = env
    refused = client.post(f"/label-versions/{L2}/recheck", headers=h())
    assert (refused.status_code, refused.json()["error"]) == (409, "not_generated")
    first = client.post(f"/label-versions/{L3}/recheck", headers=h())
    assert first.status_code == 202 and first.json()["kind"] == "recheck"
    check = job_result(client, first)
    assert check["kind"] == "self_check" and check["artifact_sha256"] == L3_SHA256 and check["passed"]
    assert client.post(f"/label-versions/{L3}/recheck", headers=h()).status_code == 200


def test_a_passed_recheck_clears_the_approval_rules_of_step_20(env) -> None:
    client, _ = env
    check = job_result(client, client.post(f"/label-versions/{L3}/recheck", headers=h()))
    body = {"decision": "approve", "artifact_sha256": L3_SHA256, "check_id": check["check_id"], "comment": "ok"}
    approved = client.post(f"/label-versions/{L3}/reviews", headers=h(REVIEWER), json=body)
    assert approved.status_code == 201


def test_a_failed_recheck_blocks_the_approval(env) -> None:
    client, stub = env
    stub.fields["product_name"] = "WrongName"
    check = job_result(client, client.post(f"/label-versions/{L3}/recheck", headers=h()))
    assert not check["passed"]
    body = {"decision": "approve", "artifact_sha256": L3_SHA256, "check_id": check["check_id"], "comment": "ok"}
    refused = client.post(f"/label-versions/{L3}/reviews", headers=h(REVIEWER), json=body)
    assert (refused.status_code, refused.json()["error"]) == (409, "check_not_passed")


def test_failed_jobs_report_why(env) -> None:
    client, stub = env
    stub.error = ExtractorUnavailable("CV libraries are not installed")
    job = client.get(f"/jobs/{client.post(f'/label-versions/{L2}/inspect', headers=h()).json()['job_id']}").json()
    assert job["state"] == "failed" and job["error"]["error"] == "extractor_unavailable"
    stub.error = RuntimeError("boom")
    job = client.get(f"/jobs/{client.post(f'/label-versions/{L2}/inspect', headers=h()).json()['job_id']}").json()
    assert job["state"] == "failed" and job["error"]["error"] == "check_failed" and "boom" in job["error"]["message"]


def test_missing_image_fails_the_job_with_artwork_not_found(env, tmp_path) -> None:
    client, _ = env
    (tmp_path / "files" / f"{L2}.png").unlink()
    job = client.get(f"/jobs/{client.post(f'/label-versions/{L2}/inspect', headers=h()).json()['job_id']}").json()
    assert job["state"] == "failed" and job["error"]["error"] == "artwork_not_found"


def test_job_states_are_appended_not_overwritten(env) -> None:
    client, _ = env
    job_id = client.post(f"/label-versions/{L2}/inspect", headers=h()).json()["job_id"]
    with client.app.state.session_factory() as session:
        states = [r.state for r in session.query(Job).filter(Job.job_id == job_id).order_by(Job.seq)]
    assert states == ["queued", "processing", "processing", "done"]


def test_retrieval_override_and_refused_options(env) -> None:
    client, _ = env
    body = {"retrieval": {"method": "tfidf"}}
    result = job_result(client, client.post(f"/label-versions/{L2}/inspect", headers=h(), json=body))
    assert result["retrieval_config"]["method"] == "tfidf"
    refused = client.post(f"/label-versions/{L2}/inspect", headers=h(), json={"retrieval": {"rerank": True}})
    assert refused.status_code == 422 and refused.json()["error"] == "validation_error"


def test_inspect_errors(env) -> None:
    client, _ = env
    assert client.post("/label-versions/lbv_missing/inspect", headers=h()).status_code == 404
    assert client.post(f"/label-versions/{L2}/inspect").status_code == 401
    assert client.get("/check-results/chk_missing", headers=h()).status_code == 404
    assert client.get("/jobs/job_deadbeef").status_code == 404


def test_unknown_mock_style_job_ids_still_get_the_mock(env) -> None:
    client, _ = env
    response = client.get("/jobs/job_scan_0001")
    assert response.status_code == 200 and response.headers["X-Mock"] == "true"


def test_search_device_and_medicine_never_mix(env) -> None:
    client, _ = env
    for module in ("device", "medicine"):
        response = client.post("/search", json={"query": "expiration date format", "module": module, "k": 5,
                                                "retrieval": {"method": "bm25"}})
        body = response.json()
        assert response.status_code == 200 and len(body["hits"]) == 5 == len(body["citations"])
        corpus = module_chunks(module)
        assert all(hit["doc_id"] in corpus for hit in body["hits"])
        for cite in body["citations"]:
            assert cite["quote"] in corpus[cite["chunk_id"]].text
        assert body["retrieval"]["method"] == "bm25" and [h_["rank"] for h_ in body["hits"]] == [1, 2, 3, 4, 5]


def test_search_section_level_and_errors(env) -> None:
    client, _ = env
    body = {"query": "unique device identifier", "module": "device", "k": 5, "section_level": True,
            "retrieval": {"method": "bm25"}}
    sections = [c["section"] for c in client.post("/search", json=body).json()["citations"]]
    assert len(sections) == len(set(sections)) == 5
    assert client.post("/search", json={"query": "x"}).status_code == 422
    assert client.post("/search", json={"query": "x", "module": "both"}).status_code == 422
    bad = client.post("/search", json={"query": "x", "module": "device", "retrieval": {"expansion": True}})
    assert bad.status_code == 422


@pytest.mark.slow
def test_search_default_is_plain_hybrid_rrf(tmp_path, monkeypatch) -> None:
    with TestClient(create_app("sqlite://", seed=False)) as client:
        body = client.post("/search", json={"query": "expiration date format", "module": "device", "k": 3}).json()
        assert body["retrieval"]["method"] == "hybrid_rrf" and body["hits"][0]["doc_id"] == "fda_21cfr801_s801.18"


def test_api_imports_without_the_cv_libraries() -> None:
    code = (
        "import sys, src.api.main, src.api.checks, src.api.extractor; "
        "assert not {'cv2', 'zxingcpp', 'rapidocr_onnxruntime'} & set(sys.modules), 'a CV library was imported'"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_missing_columns_are_added_to_an_older_database(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE check_results (seq INTEGER PRIMARY KEY, check_id TEXT)")
    _add_missing_columns(engine)
    with engine.begin() as conn:
        names = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(check_results)")}
    assert {"needs_human_count", "coverage", "retrieval_config"} <= names
    _add_missing_columns(engine)  # idempotent
