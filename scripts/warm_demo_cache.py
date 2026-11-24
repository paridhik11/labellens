"""Prefetch the live DailyMed labels the demo uses, so no first fetch (30 s to 2 minutes) happens on stage.

    python scripts/warm_demo_cache.py --base http://127.0.0.1:8000     # against a running demo server
    python scripts/run_demo.py --warm                                  # the same, started by the demo script

For every name in DEMO_LIVE_NAMES (the live medicines of demo_photos and the rehearsal) it asks the server's own
DailyMed search and fetches the first FIRST_N labels in DailyMed's order, through the public API, so the server
caches the parsed label on disk and its retriever in memory. It picks nothing for a person: the demo still shows the
list and the person chooses; this only makes the likely choices fast. Needs internet access to DailyMed.
"""
from __future__ import annotations

import argparse
import sys
import time
from typing import Any

# Live medicines used by demo_photos (07 pregabalin, 08 Zetia), the synthetic LOPRESSOR pack and the rehearsal
# (metoprolol "how to store it", "side effects").
DEMO_LIVE_NAMES = ("pregabalin", "Zetia", "metoprolol", "Lopressor")
FIRST_N = 2
JOB_LIMIT_S = 600


def warm(base: str, names: tuple[str, ...] = DEMO_LIVE_NAMES, first_n: int = FIRST_N,
         session: Any = None, log: Any = print) -> list[dict[str, Any]]:
    """Fetch the first labels for each name through the API. Returns one row per label (name, setid, seconds, state)."""
    import requests

    http = session or requests.Session()
    rows: list[dict[str, Any]] = []
    for name in names:
        try:
            found = http.post(f"{base}/public/live/search", json={"product_name": name}, timeout=30).json()
        except Exception as error:  # server down, DailyMed offline
            log(f"warm: {name}: search failed ({error})")
            rows.append({"name": name, "state": "search_failed"})
            continue
        if found.get("outcome") != "candidates":
            log(f"warm: {name}: {found.get('outcome')} {found.get('message', '')}")
            rows.append({"name": name, "state": found.get("outcome", "unknown")})
            continue
        for cand in found["candidates"][:first_n]:
            started = time.time()
            row = {"name": name, "setid": cand["setid"], "version": cand["version"], "title": cand.get("title", "")}
            try:
                job = http.post(f"{base}/public/live/fetch", json={"setid": cand["setid"], "version": cand["version"]},
                                timeout=30).json()
                while job.get("state") not in ("done", "failed") and time.time() - started < JOB_LIMIT_S:
                    time.sleep(1.0)
                    job = http.get(f"{base}/jobs/{job['job_id']}", timeout=30).json()
                row["state"] = job.get("state", "unknown")
            except Exception as error:
                row["state"] = f"error: {error}"
            row["seconds"] = round(time.time() - started, 1)
            log(f"warm: {name}: {row['title'][:70]} -> {row['state']} in {row['seconds']} s")
            rows.append(row)
    return rows


def main() -> int:
    """Warm the demo cache against a running server."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--first-n", type=int, default=FIRST_N)
    args = ap.parse_args()
    rows = warm(args.base, first_n=args.first_n)
    failed = [r for r in rows if r.get("state") != "done"]
    print(f"warm: {len(rows) - len(failed)} of {len(rows)} labels ready")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
