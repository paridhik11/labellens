"""Phase 7: effect of the lot/expiry format check on mismatch flags, from ``eval_v2`` records.

    python scripts/symbols/phase7_report.py results/cv_records_p7/dev42.json results/cv_records_p7/neg42.json ...

Each record holds the flags of the current checker (``flags``) and of the confidence-only checker (``flags_confidence_only``),
both computed from the same OCR, so the comparison is paired. Main-set records count false ``barcode_mismatch`` alarms on
labels whose printed lot and expiry agree with the barcode. Negative-set records (``generate_negatives``) count, for
``wrong_barcode`` labels, how many were flagged as ``barcode_mismatch`` (the right answer) or as ``needs_human_review``,
and false alarms on every other case. Wilson 95% intervals.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.cv.eval_v2 import CONDITION_ORDER  # noqa: E402
from src.cv.symbol_eval import rate  # noqa: E402

KINDS = (("confidence only", "flags_confidence_only"), ("with format check", "flags"))


def has(flags: list[dict], kind: str) -> bool:
    """True when any flag has this kind."""
    return any(flag["kind"] == kind for flag in flags)


def main() -> int:
    """Print the two tables."""
    records = []
    for name in sys.argv[1:]:
        records += json.loads(Path(name).read_text(encoding="utf-8"))["records"]
    main_cells: dict[tuple, dict] = defaultdict(lambda: defaultdict(int))
    neg_cells: dict[tuple, dict] = defaultdict(lambda: defaultdict(int))
    for record in records:
        if "error" in record:
            continue
        truth = record["truth"]
        for mode in ("template", "blind"):
            result = record[mode]
            decoded = len(result["barcodes"]) == 1 and bool(result["barcodes"][0])
            if "case" not in truth:  # main set
                cell = main_cells[(truth["condition"], mode)]
                cell["images"] += 1
                if not decoded:
                    continue
                cell["checkable"] += 1
                for label, key in KINDS:
                    cell[f"{label}|mismatch"] += has(result[key], "barcode_mismatch")
                    cell[f"{label}|review"] += has(result[key], "needs_human_review")
            else:
                group = "wrong_barcode" if truth["case"] == "wrong_barcode" else "other cases"
                cell = neg_cells[(group, mode)]
                cell["images"] += 1
                if not decoded:
                    continue
                cell["checkable"] += 1
                for label, key in KINDS:
                    cell[f"{label}|mismatch"] += has(result[key], "barcode_mismatch")
                    cell[f"{label}|review"] += has(result[key], "needs_human_review")
                    cell[f"{label}|either"] += has(result[key], "barcode_mismatch") or has(result[key], "needs_human_review")
    print("### Labels whose print agrees with the barcode: false `barcode_mismatch` alarms (lower is better)\n")
    print("| condition | mode | decoded labels | confidence only: false mismatch | with format check: false mismatch | with format check: needs_human_review |")
    print("| --- | --- | ---: | --- | --- | --- |")
    for (condition, mode), c in sorted(main_cells.items(), key=lambda kv: (CONDITION_ORDER.index(kv[0][0]), kv[0][1])):
        n = c["checkable"]
        print(f"| {condition} | {mode} | {n} | {rate(c['confidence only|mismatch'], n)} | "
              f"{rate(c['with format check|mismatch'], n)} | {rate(c['with format check|review'], n)} |")
    print("\n### Negative sets (moderate and hard): wrong_barcode must stay flagged, other cases must stay quiet\n")
    print("| group | mode | decoded labels | confidence only: `barcode_mismatch` | with format check: `barcode_mismatch` | with format check: mismatch or review |")
    print("| --- | --- | ---: | --- | --- | --- |")
    for (group, mode), c in sorted(neg_cells.items()):
        n = c["checkable"]
        print(f"| {group} | {mode} | {n} | {rate(c['confidence only|mismatch'], n)} | "
              f"{rate(c['with format check|mismatch'], n)} | {rate(c['with format check|either'], n)} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
