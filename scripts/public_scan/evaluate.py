"""Public scan evaluation (protocol: results/public_scan/protocol.md).

    python -m scripts.public_scan.evaluate read dev_real dev_device    # OCR once per photo, cached
    python -m scripts.public_scan.evaluate tune                        # configs A, B, C on the dev sets
    python -m scripts.public_scan.evaluate final fresh_real            # frozen config, whole pipeline, once
    python -m scripts.public_scan.evaluate final fresh                 # the 50 CV4b device packs, once
"""
from __future__ import annotations

import json
import math
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

OUT = Path("results/public_scan")
CONFIG_FILE = Path("src/api/public_scan_config.json")
DEV_SETS = ("dev_real", "dev_device")
PHOTOS = OUT / "photos_v2.json"


def load_set(name: str) -> list[dict[str, Any]]:
    """Photos of one set: id, path, expected product name (None when it is not in the corpus), kind."""
    if name == "dev_device":
        data = json.loads(Path("src/gen/cv4_dataset.json").read_text(encoding="utf-8"))
        return [{"id": r["filename"], "path": f"data/cv4_photos/candidates/{r['filename']}", "expected": None,
                 "kind": "device", "condition": "photo"} for r in data["records"] if r["split"] == "dev"]
    if name == "fresh":
        data = json.loads(Path("src/gen/cv4b_fresh.json").read_text(encoding="utf-8"))
        return [{"id": r["filename"], "path": f"data/cv4b_photos/candidates/{r['filename']}", "expected": None,
                 "kind": "device", "condition": "photo"} for r in data["records"]]
    if name in ("dev_real", "fresh_real"):
        photos = json.loads(PHOTOS.read_text(encoding="utf-8"))["photos"]
        return [{"id": p["id"], "path": p["file"], "expected": p["expected"], "kind": p["role"],
                 "condition": p["condition"], "product": p["product_name"]} for p in photos if p["set"] == name]
    raise SystemExit(f"unknown set {name}")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% interval of a proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (round(centre - half, 3), round(centre + half, 3))


def category(result: dict[str, Any], expected: str | None, catalog: Any) -> str:
    """correct, wrong, review, not_identified or timeout for one identification."""
    outcome = result["outcome"]
    if outcome == "no_reference_match":
        return "timeout" if result.get("reason") == "timeout" else "not_identified"
    names = [catalog.products[pid].name for pid, _ in result["best"]["found"]["candidates"]]
    if outcome == "matched":
        return "correct" if expected is not None and names[0] == expected else "wrong"
    return "review"


def gate(path: str) -> dict[str, Any]:
    """The photo-quality gate verdict, as the job would apply it."""
    from src.api.quality import assess_photo

    report = assess_photo(Path(path))
    return {"ok": report.ok, "reasons": list(report.reasons)}


def cmd_read(names: list[str]) -> None:
    """OCR every photo once (child process, CV4b budget) and cache lines, completeness, seconds and the gate."""
    from src.api import public_scan

    for name in names:
        target = OUT / f"lines_{name}.jsonl"
        done = {json.loads(row)["id"] for row in target.read_text(encoding="utf-8").splitlines()} if target.exists() else set()
        with target.open("a", encoding="utf-8") as handle:
            for item in load_set(name):
                if item["id"] in done:
                    continue
                started = time.monotonic()
                reading = public_scan.read_lines(Path(item["path"]))
                row = {**item, "gate": gate(item["path"]), "lines": reading["lines"], "complete": reading["complete"],
                       "killed": reading["killed"], "ocr_seconds": round(time.monotonic() - started, 2)}
                handle.write(json.dumps(row) + "\n")
                handle.flush()
                print(name, item["id"], len(reading["lines"]), row["ocr_seconds"], flush=True)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Counts, Wilson intervals and latency of scored rows (each row has category, gate, seconds, expected)."""
    n = len(rows)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["category"]] = counts.get(r["category"], 0) + 1
    in_corpus = [r for r in rows if r["expected"] is not None]
    not_in = [r for r in rows if r["expected"] is None]
    pipeline: dict[str, int] = {}
    for r in rows:
        key = "retake" if not r["gate"]["ok"] else r["category"]
        pipeline[key] = pipeline.get(key, 0) + 1
    seconds = sorted(r["seconds"] for r in rows)
    out: dict[str, Any] = {
        "photos": n, "ignoring_gate": counts, "pipeline_view": pipeline,
        "wrong_total": counts.get("wrong", 0), "wrong_interval": wilson(counts.get("wrong", 0), n),
        "not_in_corpus_photos": len(not_in),
        "wrong_on_not_in_corpus": sum(r["category"] == "wrong" for r in not_in),
        "review_on_not_in_corpus": sum(r["category"] == "review" for r in not_in),
    }
    if in_corpus:
        k = sum(r["category"] == "correct" for r in in_corpus)
        out["in_corpus_photos"] = len(in_corpus)
        out["correct"] = k
        out["correct_interval"] = wilson(k, len(in_corpus))
        out["correct_in_pipeline_view"] = sum(
            r["category"] == "correct" and r["gate"]["ok"] for r in in_corpus)
        out["review_expected_in_top3"] = sum(r.get("expected_in_review") is True for r in in_corpus)
    out["by_condition"] = by_condition(rows)
    if seconds:
        out["seconds"] = {"median": round(statistics.median(seconds), 1),
                          "p90": round(seconds[min(len(seconds) - 1, math.ceil(0.9 * len(seconds)) - 1)], 1),
                          "max": round(seconds[-1], 1), "over_60": sum(s >= 60 for s in seconds)}
    return out


def by_condition(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Counts and Wilson intervals per group (positive, decoy, device) and condition, ignoring the quality gate."""
    out: dict[str, Any] = {}
    for row in rows:
        key = f"{row['kind']}/{row['condition']}"
        out.setdefault(key, []).append(row)
    summary = {}
    for key, group in sorted(out.items()):
        n = len(group)
        counts: dict[str, int] = {}
        for r in group:
            counts[r["category"]] = counts.get(r["category"], 0) + 1
        entry: dict[str, Any] = {"n": n, **counts,
                                 "wrong_interval": wilson(counts.get("wrong", 0), n),
                                 "retake": sum(not r["gate"]["ok"] for r in group)}
        if key.startswith("positive"):
            entry["correct_interval"] = wilson(counts.get("correct", 0), n)
        summary[key] = entry
    return summary


def cmd_tune() -> None:
    """Score the candidate configurations on the cached dev OCR lines. Dev sets only."""
    from src.api import medicine, public_scan

    candidates = json.loads((OUT / "candidate_configs.json").read_text(encoding="utf-8"))
    service = medicine.MedicineService()
    public_scan.memoise_queries(service.matcher)
    catalog = service.catalog
    vocab = public_scan.vocabulary([p.name for p in catalog.products.values()]
                                   + [a for p in catalog.products.values() for a in p.aliases])
    cached = [json.loads(row) for name in DEV_SETS
              for row in (OUT / f"lines_{name}.jsonl").read_text(encoding="utf-8").splitlines()]
    report: dict[str, Any] = {}
    for key, values in candidates.items():
        config = public_scan.ScanConfig(**values)
        rows = []
        for row in cached:
            started = time.monotonic()
            result = public_scan.identify(row["lines"], service.matcher.match, vocab, config, start=time.monotonic(),
                                          cut_short=not row["complete"])
            cat = category(result, row["expected"], catalog)
            names = ([catalog.products[pid].name for pid, _ in result["best"]["found"]["candidates"]]
                     if result["best"] else [])
            rows.append({"id": row["id"], "kind": row["kind"], "expected": row["expected"], "category": cat,
                         "gate": row["gate"], "seconds": row["ocr_seconds"] + time.monotonic() - started,
                         "expected_in_review": (row["expected"] in names) if cat == "review" else None, "condition": row["condition"],
                         "matched_text": result["best"]["text"] if result["best"] else "", "names": names})
        report[key] = {"config": values, "positives": summarize([r for r in rows if r["kind"] == "positive"]),
                       "decoys": summarize([r for r in rows if r["kind"] == "decoy"]),
                       "device": summarize([r for r in rows if r["kind"] == "device"]), "rows": rows}
        print(key, json.dumps({k: v for k, v in report[key].items() if k != "rows"}), flush=True)
    (OUT / "dev_configs.json").write_text(json.dumps(report, indent=1), encoding="utf-8")


def cmd_final(name: str) -> None:
    """The frozen configuration, whole pipeline per photo, written once (an existing output is never replaced)."""
    from src.api import medicine, public_scan

    committed = subprocess.run(["git", "log", "-1", "--format=%H", "--", str(CONFIG_FILE)], capture_output=True,
                               text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", str(CONFIG_FILE)], capture_output=True,
                           text=True).stdout.strip()
    if not committed or dirty:
        raise SystemExit("the frozen config must be committed before a final run")
    target, summary_path = OUT / f"final_{name}.jsonl", OUT / f"final_{name}_summary.json"
    if target.exists():
        raise SystemExit(f"{target} exists: a final run is scored once")
    config = public_scan.load_config()
    service = medicine.MedicineService()
    service.matcher.match("warm up")  # the model load is a one-time server cost (run_demo does the same)
    rows = []
    with target.open("x", encoding="utf-8") as handle:
        for item in load_set(name):
            report = gate(item["path"])
            outcome = public_scan.scan_photo(Path(item["path"]), service, config)
            body = outcome.body
            result = {"outcome": body["outcome"], "reason": body.get("reason"),
                      "best": {"found": {"candidates": [(c["product_id"], c["match_confidence"])
                                                        for c in body["candidates"]]}} if body["candidates"] else None}
            cat = category(result, item["expected"], service.catalog)
            names = [c["product_name"] for c in body["candidates"]]
            row = {**item, "gate": report, "category": cat, "seconds": round(outcome.seconds, 1),
                   "outcome": body["outcome"], "reason": body.get("reason"), "matched_text": body["matched_text"],
                   "names": names, "score": body.get("score"), "tried": outcome.extra["tried"],
                   "killed": outcome.extra["killed"], "read_lines": len(body["read_lines"]),
                   "expected_in_review": (item["expected"] in names) if cat == "review" else None}
            rows.append(row)
            handle.write(json.dumps(row) + "\n")
            handle.flush()
            print(item["id"], cat, row["seconds"], flush=True)
    summary = {"set": name, "config": config.__dict__, "config_commit": committed, **summarize(rows)}
    summary_path.write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "read":
        cmd_read(sys.argv[2:])
    elif command == "tune":
        cmd_tune()
    elif command == "final":
        cmd_final(sys.argv[2])
    else:
        raise SystemExit(__doc__)
