"""The 202 job behind fetchLiveLabel (CR-28): download, parse, cache and index one picked DailyMed label.

At most two labels are fetched at once (indexing uses a CPU for several seconds); another is answered with 429 `busy`.
A job always ends in `done` or `failed`. A failure carries an Error whose `details.reason` says why: offline, timeout,
api_error (DailyMed), not_a_human_label, id_mismatch, no_text, bad_archive (the label), or retrieval_unavailable
(the embedding models cannot be loaded). The curated products stay usable in every case.
"""
from __future__ import annotations

import threading
from typing import Any

from src.api import checks
from src.api.errors import ApiError
from src.api.live_dailymed import LiveFetchError, LiveUnavailable

MAX_RUNNING = 2
SLOTS = threading.BoundedSemaphore(MAX_RUNNING)


def try_acquire() -> None:
    """Take a running slot or answer 429 busy (the job gives it back when it ends)."""
    if not SLOTS.acquire(blocking=False):
        raise ApiError(429, "busy", f"{MAX_RUNNING} labels are being fetched already. Try again in a minute.")


def release() -> None:
    """Give a slot back (once per successful `try_acquire`)."""
    SLOTS.release()


def _error(code: str, message: str, reason: str) -> dict[str, Any]:
    return {"error": code, "message": message, "details": {"reason": reason}}


def run_fetch_job(app: Any, job_id: str, setid: str, version: int) -> None:
    """Background body of a 202 fetch; always ends the job."""
    try:
        with app.state.session_factory() as session:
            try:
                checks.advance_job(session, job_id, "processing", 0.1,
                                   "downloading and indexing the label from DailyMed (this can take a little while)")
                label = app.state.live.fetch(setid, version)
                checks.advance_job(session, job_id, "done", 1.0, "done",
                                   result_url=f"/public/live/products/{label.product_id}")
            except LiveUnavailable as error:
                message = f"{error.message} The curated medicines still work."
                failure = _error("live_fetch_failed", message, error.reason)
                checks.advance_job(session, job_id, "failed", 1.0, error=failure)
            except LiveFetchError as error:
                checks.advance_job(session, job_id, "failed", 1.0,
                                   error=_error("live_fetch_failed", error.message, error.code))
            except Exception as error:  # embedding models missing, disk full: say so, never leave the job open
                checks.advance_job(session, job_id, "failed", 1.0, error=_error(
                    "retrieval_unavailable", f"The label was fetched but could not be indexed: {type(error).__name__}.",
                    "retrieval_unavailable"))
    finally:
        release()
