"""Evaluate the photo-quality gate on the development seeds 200 and 201 (Step 24a).

    python -m src.api.quality_eval --dir <folder with test_s200_*.png> [--dir ...] [--sweep]

Measures every image once, then applies the cut-offs (`judge` is pure). Reports, per photo condition and never
blended: how many images the gate rejects and why. For `very_hard` it also reports how many images whose blind
extraction found no barcode (the clearest sign of an unreadable photo in the dev sidecar files) the gate caught.
Only seeds 200 and 201 are accepted: the final seeds (300 to 302) must not be used to tune a cut-off.
Needs OpenCV (use the .venv-cv environment).
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

from src.api.quality import DEFAULT, Thresholds, judge, measure

DEV_SEEDS = {"200", "201"}
NAME = re.compile(r"^test_s(\d+)_\d+_.+?_(very_hard|clean|moderate|hard)\.png$")
CONDITIONS = ("clean", "moderate", "hard", "very_hard")


def _measure_file(path: str) -> dict[str, float]:
    import cv2

    return measure(cv2.imread(path, cv2.IMREAD_GRAYSCALE))


def collect(dirs: list[Path]) -> list[dict]:
    """Measured numbers, condition and 'no barcode in the blind extraction' flag for every dev image."""
    items = []
    for folder in dirs:
        for path in sorted(folder.glob("*.png")):
            match = NAME.match(path.name)
            if not match:
                continue
            if match.group(1) not in DEV_SEEDS:
                raise SystemExit(f"{path.name}: seed {match.group(1)} is not a development seed (200, 201 only).")
            sidecar = folder / "extractions" / (path.stem + ".json")
            no_barcode = None
            if sidecar.exists():
                no_barcode = not json.loads(sidecar.read_text(encoding="utf-8"))["blind"]["barcodes"]
            items.append({"path": str(path), "condition": match.group(2), "no_barcode": no_barcode})
    with ProcessPoolExecutor() as pool:
        for item, metrics in zip(items, pool.map(_measure_file, [i["path"] for i in items], chunksize=8), strict=True):
            item["metrics"] = metrics
    return items


def table(items: list[dict], thresholds: Thresholds) -> list[str]:
    """Markdown lines: per condition, n, rejected (with reasons) and, for very_hard, no-barcode images caught."""
    lines = ["| condition | n | rejected | blur | low_contrast | glare |", "|---|---|---|---|---|---|"]
    for condition in CONDITIONS:
        sel = [i for i in items if i["condition"] == condition]
        if not sel:
            continue
        reports = [judge(i["metrics"], thresholds) for i in sel]
        reasons = Counter(r for report in reports for r in report.reasons)
        rejected = sum(not report.ok for report in reports)
        counts = " | ".join(str(reasons[r]) for r in ("blur", "low_contrast", "glare"))
        lines.append(f"| {condition} | {len(sel)} | {rejected} | {counts} |")
    vh = [i for i in items if i["condition"] == "very_hard" and i["no_barcode"] is not None]
    if vh:
        missed = [i for i in vh if i["no_barcode"]]
        caught = sum(not judge(i["metrics"], thresholds).ok for i in missed)
        read_ok = [i for i in vh if not i["no_barcode"]]
        lost = sum(not judge(i["metrics"], thresholds).ok for i in read_ok)
        lines += ["", f"very_hard images with no barcode read (blind): {len(missed)}, gate caught {caught}.",
                  f"very_hard images whose barcode was read: {len(read_ok)}, gate rejected {lost} of them."]
    return lines


def main() -> None:
    """Print the table for the default cut-offs, and a sweep of the glare and sharpness cut-offs with --sweep."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", action="append", type=Path, required=True)
    parser.add_argument("--sweep", action="store_true")
    args = parser.parse_args()
    items = collect(args.dir)
    print(f"{len(items)} dev images (seeds 200, 201). Default cut-offs: {DEFAULT}\n")
    print("\n".join(table(items, DEFAULT)))
    if args.sweep:
        grid = (("glare_max_edge", (40.0, 50.0, 60.0, 70.0, 80.0)), ("min_sharpness", (150.0, 200.0, 250.0, 300.0)),
                ("min_contrast", (20.0, 40.0, 60.0, 80.0)))
        for name, values in grid:
            for value in values:
                print(f"\n### {name} = {value}\n")
                print("\n".join(table(items, replace(DEFAULT, **{name: value}))))


if __name__ == "__main__":
    main()
