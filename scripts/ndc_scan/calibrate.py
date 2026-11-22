"""Harness concurrency check (protocol amendment): 3 dev photos read alone, one after another, then all 3 at once.

The reader is the unchanged public scan reader. Per-photo wall time, line count and completeness are compared:
a concurrency is acceptable only when each photo gets what a single product request gets.

    python -m scripts.ndc_scan.calibrate 3
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.api import public_scan

DEV = Path("../labellens-publicscan/data/public_scan_real/photos/dev_real")


def pick() -> list[Path]:
    """The first moderate photo of three dev positive products (fixed order, dev only)."""
    out = []
    for prefix in ("a519e355", "4cd07a3c", "3881afaf"):
        out.append(sorted(DEV.glob(f"{prefix}__*__moderate.jpg"))[0])
    return out


def one(path: Path) -> dict:
    """Read one photo; wall seconds, lines, complete."""
    started = time.monotonic()
    reading = public_scan.read_lines(path, timeout_s=150)
    return {"photo": path.name, "seconds": round(time.monotonic() - started, 1), "lines": len(reading["lines"]),
            "complete": reading["complete"]}


def main(concurrency: int) -> None:
    photos = pick()
    alone = [one(p) for p in photos]
    with ThreadPoolExecutor(concurrency) as pool:
        together = list(pool.map(one, photos))
    report = {"concurrency": concurrency, "alone": alone, "together": together}
    out = Path(f"results/ndc_scan/calibration_c{concurrency}.json")
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]))
