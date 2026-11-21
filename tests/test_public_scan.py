"""Public photo scan (CR-27): candidate strings, the match decision, time cuts and the 202 job, with stubs.

No OCR and no embedding model: the reader returns prepared lines and the matcher is the word-overlap stub of
``tests/medicine_helpers.py`` (the real matcher's threshold logic is used, only its ranker is a stand-in).
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from src.api import public_scan, public_scans
from src.api.main import create_app
from src.api.medicine import MedicineCatalog
from tests.medicine_helpers import stub_medicine
from tests.openapi_helpers import conformance_errors
from tests.upload_helpers import jpeg_bytes, passing_gate, png_bytes, rejecting_gate

CATALOG = MedicineCatalog()
NAMES = [p.name for p in CATALOG.products.values()]
FIRST = NAMES[0]


def validate_response(operation_id: str, status: int, body: dict) -> None:
    """Fail with the schema errors when a real response does not match docs/contracts/openapi.yaml."""
    assert conformance_errors(operation_id, status, body) == []


def lines(*texts: str) -> list[dict]:
    """OCR lines as the worker prints them."""
    return [{"text": t, "confidence": 0.9, "box": [0, i * 20, 100, 18]} for i, t in enumerate(texts)]


def reader(texts: list[str], complete: bool = True):
    """A stub of the OCR child process."""
    return lambda _path: {"lines": lines(*texts), "complete": complete, "killed": False}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """A seeded app with a stub matcher and reader, a passing gate and uploads in tmp_path."""
    monkeypatch.setenv("LABELLENS_FILES_DIR", str(tmp_path))
    with TestClient(create_app("sqlite://", seed=True)) as client:
        client.app.state.medicine = stub_medicine()
        client.app.state.quality_gate = passing_gate
        client.app.state.public_reader = reader(["Store at room temperature", FIRST, "100 tablets"])
        yield client


def post(client, data: bytes | None = None, name: str = "pack.png"):
    """POST /public/scans without any header (the page is public)."""
    return client.post("/public/scans", files={"file": (name, data or png_bytes(), "image/png")})


def result_of(client, response):
    """The getPublicScan body after the job ran (the test client runs background tasks first)."""
    assert response.status_code == 202, response.text
    scan_id = response.json()["result_url"].rsplit("/", 1)[1]
    return scan_id, client.get(f"/public/scans/{scan_id}")


# ---------------------------------------------------------------- candidate strings


def test_candidates_are_lines_pairs_and_the_full_text_without_duplicates() -> None:
    vocab = public_scan.vocabulary(NAMES)
    config = public_scan.ScanConfig(max_candidates=50)
    found = public_scan.build_candidates(lines("Alpha tablets", "Beta syrup", "Rx only"), vocab, config)
    texts = [c.text for c in found]
    assert "Alpha tablets Beta syrup" in texts and "Alpha tablets Beta syrup Rx only" in texts
    assert "Beta syrup" in texts and len(texts) == len(set(t.lower() for t in texts))
    assert public_scan.build_candidates(lines("1234", "..."), vocab, config) == []  # too few letters


def test_candidates_are_limited_and_best_lexical_first_and_the_full_text_stays() -> None:
    vocab = public_scan.vocabulary(NAMES)
    config = public_scan.ScanConfig(max_candidates=3, pairs=False)
    noise = [f"zzqx{i} qqwv{i}" for i in range(10)]
    found = public_scan.build_candidates(lines(*noise, FIRST), vocab, config)
    assert len(found) == 3 and found[0].text == FIRST and found[-1].lines == tuple(range(11))


def test_pairs_and_full_text_can_be_switched_off() -> None:
    vocab = public_scan.vocabulary(NAMES)
    config = public_scan.ScanConfig(max_candidates=50, pairs=False, full_text=False)
    found = public_scan.build_candidates(lines("Alpha tablets", "Beta syrup"), vocab, config)
    assert [c.lines for c in found] == [(0,), (1,)]


def test_lexical_priority_tolerates_one_ocr_slip() -> None:
    vocab = {"ibuprofen", "tablets"}
    assert public_scan.lexical_priority("lbuprofen tablets", vocab) > public_scan.lexical_priority("lot 123", vocab)


# ---------------------------------------------------------------- the decision


def fake_match(scores: dict[str, float]):
    """A matcher stand-in: the score is looked up by the candidate text, outcome by the real thresholds."""
    def match(text: str) -> dict:
        score = scores.get(text, 0.3)
        outcome = "matched" if score >= 0.70 else "needs_review" if score >= 0.65 else "no_reference_match"
        return {"outcome": outcome, "score_name": "bge_large_cosine", "score": score, "threshold": 0.65,
                "candidates": [("med_x", score)] if outcome != "no_reference_match" else []}
    return match


def test_best_candidate_wins_and_remembers_its_lines() -> None:
    vocab = public_scan.vocabulary(NAMES)
    result = public_scan.identify(lines("Acme", FIRST, "tablets"), fake_match({FIRST: 0.8, "Acme": 0.5}), vocab,
                                  public_scan.ScanConfig(max_candidates=50), start=time.monotonic())
    assert result["outcome"] == "matched" and result["best"]["text"] == FIRST and result["best"]["lines"] == (1,)


def test_below_threshold_is_not_identified_with_reason_no_match() -> None:
    vocab = public_scan.vocabulary(NAMES)
    result = public_scan.identify(lines("Sterile catheter"), fake_match({}), vocab, public_scan.ScanConfig(),
                                  start=time.monotonic())
    assert result["outcome"] == "no_reference_match" and result["reason"] == "no_match"


def test_no_text_and_cut_reading_are_distinguished() -> None:
    vocab = public_scan.vocabulary(NAMES)
    none = public_scan.identify([], fake_match({}), vocab, public_scan.ScanConfig(), start=time.monotonic())
    assert none["reason"] == "no_text"
    cut = public_scan.identify(lines(FIRST), fake_match({FIRST: 0.9}), vocab, public_scan.ScanConfig(),
                               start=time.monotonic(), cut_short=True)
    assert cut["outcome"] == "no_reference_match" and cut["reason"] == "timeout" and cut["timed_out"]


def test_matching_that_runs_out_of_time_is_a_timeout_not_a_guess() -> None:
    vocab = public_scan.vocabulary(NAMES)
    result = public_scan.identify(lines(FIRST), fake_match({FIRST: 0.9}), vocab, public_scan.ScanConfig(),
                                  start=time.monotonic() - 100, hard_limit_s=1.0)
    assert result["outcome"] == "no_reference_match" and result["reason"] == "timeout"


def test_outcome_order_prefers_matched_over_a_higher_review_score() -> None:
    vocab = public_scan.vocabulary(NAMES)
    scores = {FIRST: 0.72, f"{FIRST} tablets": 0.74}
    plain = public_scan.identify(lines(FIRST, "tablets"), fake_match(scores), vocab,
                                 public_scan.ScanConfig(max_candidates=50), start=time.monotonic())
    assert plain["best"]["text"] == FIRST + " tablets"


# ---------------------------------------------------------------- the API


def test_public_scan_needs_no_login_and_identifies_a_known_name(client) -> None:
    response = post(client)
    job = response.json()
    assert job["kind"] == "public_scan" and job["state"] == "queued"
    assert client.get(f"/jobs/{job['job_id']}").json()["state"] == "done"
    scan_id, got = result_of(client, response)
    body = got.json()
    assert got.status_code == 200 and "X-Mock" not in got.headers
    assert body["outcome"] in ("matched", "needs_review") and body["candidates"]
    assert body["matched_text"] and any(row["used"] for row in body["read_lines"])
    assert [row["text"] for row in body["read_lines"]][1] == FIRST
    validate_response("publicScan", 202, job)
    validate_response("getPublicScan", 200, body)


def test_unknown_text_is_not_identified_and_shows_no_product(client) -> None:
    client.app.state.public_reader = reader(["Single use only", "Sterile", "Catheter 80 cm"])
    _, got = result_of(client, post(client))
    body = got.json()
    assert body["outcome"] == "no_reference_match" and body["candidates"] == [] and body["reason"] == "no_match"
    assert "summary" not in body and "sections" not in body and body["matched_text"] == ""
    validate_response("getPublicScan", 200, body)


def test_cut_reading_returns_timeout_even_when_a_name_was_seen(client) -> None:
    client.app.state.public_reader = reader([FIRST], complete=False)
    _, got = result_of(client, post(client))
    assert got.json()["outcome"] == "no_reference_match" and got.json()["reason"] == "timeout"


def test_killed_reader_returns_timeout(client) -> None:
    client.app.state.public_reader = lambda _p: {"lines": [], "complete": False, "killed": True}
    _, got = result_of(client, post(client))
    assert got.json()["reason"] == "timeout"


def test_blurry_photo_gets_retake_photo_and_no_result(client) -> None:
    client.app.state.quality_gate = rejecting_gate
    response = post(client)
    scan_id = response.json()["result_url"].rsplit("/", 1)[1]
    job = client.get(f"/jobs/{response.json()['job_id']}").json()
    assert job["state"] == "failed" and job["error"]["error"] == "retake_photo"
    assert job["error"]["details"]["reasons"] == ["glare"]
    got = client.get(f"/public/scans/{scan_id}")
    assert got.status_code == 409 and got.json()["error"] == "retake_photo"


def test_broken_models_end_the_job_failed_with_a_readable_error(client) -> None:
    client.app.state.medicine = stub_medicine(broken=True)
    response = post(client)
    job = client.get(f"/jobs/{response.json()['job_id']}").json()
    assert job["state"] == "failed" and job["error"]["error"] == "scan_failed"


def test_bad_files_are_refused_before_any_job(client) -> None:
    assert client.post("/public/scans", files={"file": ("a.png", b"not an image", "image/png")}).status_code == 422
    assert client.post("/public/scans", files={"file": ("a.png", b"", "image/png")}).status_code == 422


def test_unknown_and_unfinished_scans(client) -> None:
    assert client.get("/public/scans/pscn_00000000").status_code == 404
    assert client.get("/public/scans/x?mock_state=empty").headers["X-Mock"] == "true"  # a foreign id: the mock


def test_too_many_at_once_is_busy_and_the_slot_comes_back(client) -> None:
    taken = [public_scans.SLOTS.acquire(blocking=False) for _ in range(public_scans.MAX_RUNNING)]
    try:
        busy = post(client)
        assert busy.status_code == 429 and busy.json()["error"] == "busy"
    finally:
        for ok in taken:
            if ok:
                public_scans.release()
    assert post(client, jpeg_bytes()).status_code == 202
    assert post(client).status_code == 202  # finished jobs released their slot


def test_rows_are_append_only_and_the_photo_is_stored_by_hash(client, tmp_path) -> None:
    data = png_bytes()
    response = post(client, data, name="../../evil.png")
    scan_id, _ = result_of(client, response)
    stored = list((Path(tmp_path) / "uploads").glob("*.png"))
    assert len(stored) == 1 and "evil" not in stored[0].name
    with client.app.state.session_factory() as session:
        with pytest.raises(DBAPIError):
            session.execute(text("DELETE FROM public_scans"))
        session.rollback()
        rows = session.execute(text("SELECT state FROM public_scans WHERE scan_id = :s ORDER BY seq"),
                               {"s": scan_id}).scalars().all()
    assert rows[0] == "queued" and rows[-1] == "done" and "processing" in rows


def test_memoised_encoding_does_not_change_scores() -> None:
    class Model:
        def __init__(self) -> None:
            self.calls = 0

        def encode(self, sentences, *args, **kwargs):
            self.calls += 1
            return [len(sentences)]

    class Dense:
        _model = Model()

    class Matcher:
        _dense = Dense()

        def _load(self) -> None:
            return None

    matcher = Matcher()
    public_scan.memoise_queries(matcher)
    model = matcher._dense._model
    assert [model.encode("abc"), model.encode("abc")] == [[3], [3]] and model.calls == 1
    assert model.encode(["a", "b"]) == [2] and model.calls == 2  # batches (passages) are never cached
