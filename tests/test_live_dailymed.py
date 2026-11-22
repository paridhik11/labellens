"""Live DailyMed lookup (CR-28): search, fetch, cache, citations, API flow. Recorded fixtures, no network."""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from src.api import live_jobs
from src.api.live_dailymed import (
    CATEGORIES,
    LIVE_LABEL,
    LiveFetchError,
    LiveUnavailable,
    default_http,
    parse_label,
    parse_title,
    product_id_for,
    read_spl_zip,
    unverified_sources,
)
from src.api.main import create_app
from tests.live_helpers import LABEL, XML, FakeHttp, live_service, zip_of


def test_categories_equal_the_curated_build() -> None:
    from scripts.real.build_medicine_corpus import CATEGORIES as CURATED

    assert CATEGORIES == CURATED


def test_parse_title_parts() -> None:
    parts = parse_title("ALLERGY RELIEF (CETIRIZINE HCL) TABLET, FILM COATED [PIONEER LIFE SCIENCES, LLC]")
    assert parts == {"product_name": "ALLERGY RELIEF", "generic_name": "CETIRIZINE HCL",
                     "dosage_form": "tablet, film coated", "labeler": "PIONEER LIFE SCIENCES, LLC"}
    plain = parse_title("CETIRIZINE HYDROCHLORIDE SOLUTION [PADAGIS]")
    assert plain["product_name"] == "CETIRIZINE HYDROCHLORIDE SOLUTION" and plain["labeler"] == "PADAGIS"


def test_search_lists_candidates_without_ranking_or_picking(tmp_path) -> None:
    http = FakeHttp()
    result = live_service(tmp_path, http).search("cetirizine")
    assert result["outcome"] == "candidates" and 1 <= len(result["candidates"]) <= 10
    assert len({c["setid"] for c in result["candidates"]}) == len(result["candidates"])
    assert all("selected" not in c and "score" not in c for c in result["candidates"])
    assert len(http.calls) == 2 and all("doctype=" in u for u in http.calls)


def test_search_no_candidates_and_unavailable(tmp_path) -> None:
    none = live_service(tmp_path, FakeHttp(empty=True)).search("zzzz")
    assert none["outcome"] == "no_candidates" and none["candidates"] == [] and none["message"]
    off = live_service(tmp_path, FakeHttp(error=LiveUnavailable("offline", "DailyMed cannot be reached."))).search("x1")
    assert off["outcome"] == "unavailable" and off["reason"] == "offline" and "curated" in off["message"]


def test_default_http_refuses_other_hosts() -> None:
    with pytest.raises(LiveUnavailable):
        default_http("https://example.com/x", 1, 10)


def test_parse_label_checks_identity() -> None:
    label = parse_label(XML, LABEL["setid"], LABEL["version"], "2026-01-02")
    assert label.chunks and label.product_id == product_id_for(LABEL["setid"], LABEL["version"])
    assert all(c.chunk_id.startswith(f"dailymed_{LABEL['setid']}_v{LABEL['version']}_") for c in label.chunks)
    with pytest.raises(LiveFetchError) as wrong_id:
        parse_label(XML, "00000000-0000-0000-0000-000000000000", LABEL["version"], "2026-01-02")
    assert wrong_id.value.code == "id_mismatch"
    with pytest.raises(LiveFetchError) as wrong_version:
        parse_label(XML, LABEL["setid"], LABEL["version"] + 1, "2026-01-02")
    assert wrong_version.value.code == "id_mismatch"
    device = XML.replace(b'code="34390-5"', b'code="55439-4"', 1).replace(b'code="34391-3"', b'code="55439-4"', 1)
    with pytest.raises(LiveFetchError) as not_human:
        parse_label(device, LABEL["setid"], LABEL["version"], "2026-01-02")
    assert not_human.value.code == "not_a_human_label"


def test_bad_archive_is_refused() -> None:
    with pytest.raises(LiveFetchError):
        read_spl_zip(b"not a zip")


def test_fetch_caches_and_second_fetch_uses_the_cache(tmp_path) -> None:
    http = FakeHttp()
    service = live_service(tmp_path, http)
    label = service.fetch(LABEL["setid"], LABEL["version"])
    downloads = [u for u in http.calls if "getFile" in u]
    assert len(downloads) == 1 and service.knows(label.product_id)
    again = service.fetch(LABEL["setid"], LABEL["version"])
    assert again.fetched == label.fetched and len([u for u in http.calls if "getFile" in u]) == 1


def test_fetch_rejects_bad_ids_and_unknown_cache_ids(tmp_path) -> None:
    service = live_service(tmp_path)
    with pytest.raises(LiveFetchError):
        service.fetch("../../etc/passwd", 1)
    assert not service.knows("live_../x") and not service.knows(None)
    with pytest.raises(LiveFetchError):
        service.load("live_0000000000000000_v1")


def test_answer_has_live_label_and_verified_citations(tmp_path) -> None:
    service = live_service(tmp_path)
    label = service.fetch(LABEL["setid"], LABEL["version"])
    from src.rag.provider import NullProvider
    from src.rag.settings import RagSettings

    result, loaded = service.ask("What are the warnings?", label.product_id, NullProvider(),
                                 RagSettings(rerank_display=False))
    body = service.wire(result, loaded)
    assert body["live"]["label"] == LIVE_LABEL and body["live"]["setid"] == LABEL["setid"]
    assert LIVE_LABEL in body.get("based_on", LIVE_LABEL)
    assert body["sources"] and not unverified_sources(body["sources"], loaded)
    assert all(s["source_type"] == "label_section" for s in body["sources"])


def test_unverifiable_citation_becomes_an_abstention(tmp_path) -> None:
    service = live_service(tmp_path)
    label = service.fetch(LABEL["setid"], LABEL["version"])
    from src.rag.provider import NullProvider
    from src.rag.settings import RagSettings

    result, loaded = service.ask("What are the warnings?", label.product_id, NullProvider(),
                                 RagSettings(rerank_display=False))
    result.sources[0]["quote"] = "words that are not in the label at all"
    body = service.wire(result, loaded)
    assert body["abstained"] is True and "sources" not in body
    assert unverified_sources([{"chunk_id": "other_chunk", "quote": "x"}], loaded)


def _client(tmp_path, http=None):
    client = TestClient(create_app("sqlite://", seed=False))
    return client


def test_api_flow_search_fetch_ask(tmp_path) -> None:
    with TestClient(create_app("sqlite://", seed=False)) as client:
        client.app.state.live = live_service(tmp_path)
        found = client.post("/public/live/search", json={"product_name": "cetirizine"}).json()
        assert found["outcome"] == "candidates"
        pick = {"setid": LABEL["setid"], "version": LABEL["version"]}
        started = client.post("/public/live/fetch", json=pick)
        assert started.status_code == 202 and started.json()["kind"] == "live_fetch"
        job = {}
        for _ in range(100):
            job = client.get(f"/jobs/{started.json()['job_id']}").json()
            if job["state"] in ("done", "failed"):
                break
            time.sleep(0.05)
        assert job["state"] == "done", job
        page = client.get(job["result_url"]).json()
        assert page["outcome"] == "live_selected" and page["live"]["label"] == LIVE_LABEL
        assert "match_confidence" not in page["candidates"][0]
        pid = page["candidates"][0]["product_id"]
        answer = client.post("/public/ask", json={"question": "What are the warnings?", "product_id": pid}).json()
        assert answer["live"]["setid"] == LABEL["setid"] and LIVE_LABEL in answer.get("based_on", LIVE_LABEL)
        assert client.get("/public/live/products/live_0000000000000000_v9").status_code == 404
        assert client.post("/public/live/search", json={"product_name": "x"}).status_code == 422


def test_api_fetch_failure_has_a_reason(tmp_path) -> None:
    with TestClient(create_app("sqlite://", seed=False)) as client:
        other = XML.replace(LABEL["setid"].encode(), b"00000000-0000-0000-0000-000000000000")
        client.app.state.live = live_service(tmp_path, FakeHttp(xml=other))
        started = client.post("/public/live/fetch", json={"setid": LABEL["setid"], "version": LABEL["version"]})
        for _ in range(100):
            job = client.get(f"/jobs/{started.json()['job_id']}").json()
            if job["state"] in ("done", "failed"):
                break
            time.sleep(0.05)
        assert job["state"] == "failed" and job["error"]["details"]["reason"] == "id_mismatch"


def test_busy_and_disabled(tmp_path) -> None:
    with TestClient(create_app("sqlite://", seed=False)) as client:
        client.app.state.live = live_service(tmp_path)
        pick = {"setid": LABEL["setid"], "version": LABEL["version"]}
        for _ in range(live_jobs.MAX_RUNNING):
            live_jobs.try_acquire()
        try:
            assert client.post("/public/live/fetch", json=pick).status_code == 429
        finally:
            for _ in range(live_jobs.MAX_RUNNING):
                live_jobs.release()
        client.app.state.live.enabled = False
        assert client.post("/public/live/fetch", json=pick).status_code == 503
        assert client.post("/public/live/search", json={"product_name": "cetirizine"}).json()["reason"] == "disabled"


def test_zip_helper_roundtrip() -> None:
    assert read_spl_zip(zip_of(XML)) == XML
