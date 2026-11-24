"""scripts/warm_demo_cache.py: fetches the first labels per demo name through the API (fake session, no network)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import warm_demo_cache  # noqa: E402


class Reply:
    def __init__(self, body: dict) -> None:
        self.body = body

    def json(self) -> dict:
        return self.body


class FakeSession:
    """Answers search with three candidates, fetch with a job that is done on the first poll."""

    def __init__(self) -> None:
        self.fetched: list[str] = []

    def post(self, url: str, json: dict, timeout: float) -> Reply:
        if url.endswith("/public/live/search"):
            if json["product_name"] == "nothing":
                return Reply({"outcome": "no_candidates", "message": "none"})
            cands = [{"setid": f"s{i}", "version": 1, "title": f"{json['product_name']} {i}"} for i in range(3)]
            return Reply({"outcome": "candidates", "candidates": cands})
        self.fetched.append(json["setid"])
        return Reply({"job_id": "j1", "state": "queued"})

    def get(self, url: str, timeout: float) -> Reply:
        return Reply({"job_id": "j1", "state": "done"})


def test_warm_fetches_first_n_per_name_and_reports() -> None:
    session = FakeSession()
    lines: list[str] = []
    rows = warm_demo_cache.warm("http://x", names=("Zetia", "nothing"), first_n=2, session=session, log=lines.append)
    assert session.fetched == ["s0", "s1"]
    assert [r["state"] for r in rows] == ["done", "done", "no_candidates"]
    assert len(lines) == 3


def test_demo_names_cover_the_live_demo_photos() -> None:
    assert {"pregabalin", "Zetia", "metoprolol"} <= set(warm_demo_cache.DEMO_LIVE_NAMES)
