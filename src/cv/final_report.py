"""Phase 3 report: final configuration against the starting point on the same images.

Inputs are ``eval_v2`` record files (final code) and the generated datasets
(the starting-point code is run on them from its git commit). Run from the
repo root, for example:

    python -m src.cv.final_report \\
        --main data/synthetic/fresh100 data/synthetic/fresh101 data/synthetic/fresh102 \\
        --neg data/synthetic/freshneg100 data/synthetic/freshneg101 data/synthetic/freshneg102 \\
        --records-dir results/cv_records --output results/cv_final_eval.md
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from src.cv.baseline_ref import OLD_REF, START_REF, run_ref
from src.cv.eval_v2 import (
    CONDITION_ORDER,
    FIELDS,
    _percent,
    _quad_box,
    box_iou,
    edit_distance,
    merge_counts,
    render_main,
    render_negatives,
    summarise,
)


def _records_path(records_dir: Path, dataset: Path) -> Path:
    """Return the eval_v2 record file that belongs to a dataset folder."""
    return records_dir / f"{dataset.name}.json"


def baseline_main(datasets: list[Path], workers: int) -> dict[str, dict[str, Any]]:
    """Score the starting-point extractor (commit START_REF) per condition, all seeds together."""
    table: dict[str, dict[str, Any]] = {}
    for dataset in datasets:
        records = run_ref(START_REF, dataset, full=True, workers=workers)
        for image, record in records.items():
            truth = json.loads((dataset / image).with_suffix(".json").read_text(encoding="utf-8"))
            counts = table.setdefault(truth["condition"], {
                "images": 0, "gs1_exact": 0, "symbols_expected": 0, "symbols_matched": 0,
                "symbol_false_positives": 0, "corners_10px": 0, "errors": 0,
                "cer": {field: [0, 0] for field in FIELDS},
            })
            counts["images"] += 1
            extraction = record.get("extraction")
            if extraction is None:
                counts["errors"] += 1
                extraction = {"fields": {}, "barcodes": [], "symbols": []}
            parsed = [item["parsed"] for item in extraction["barcodes"]]
            counts["gs1_exact"] += int(len(parsed) == 1 and parsed[0] == truth["barcode_ais"])
            if record["corners"] is not None:
                distance = np.linalg.norm(np.asarray(record["corners"]) - np.asarray(truth["label_quad_px"]), axis=1)
                counts["corners_10px"] += int(distance.max() <= 10)
            present = {item["name"]: _quad_box(item["quad_px"]) for item in truth["symbols"]}
            counts["symbols_expected"] += len(present)
            for symbol in extraction["symbols"]:
                if symbol["name"] in present and box_iou(tuple(symbol["bbox"]), present[symbol["name"]]) >= 0.5:
                    counts["symbols_matched"] += 1
                else:
                    counts["symbol_false_positives"] += 1
            for field in FIELDS:
                reference = truth["fields"][field]
                counts["cer"][field][0] += edit_distance(reference, extraction["fields"].get(field, ""))
                counts["cer"][field][1] += len(reference)
    return table


def baseline_negatives(datasets: list[Path], workers: int) -> dict[str, dict[str, int]]:
    """Count starting-point symbol false positives on the negative and variation cases."""
    table: dict[str, dict[str, int]] = {}
    for dataset in datasets:
        records = run_ref(START_REF, dataset, full=True, workers=workers)
        for image, record in records.items():
            truth = json.loads((dataset / image).with_suffix(".json").read_text(encoding="utf-8"))
            counts = table.setdefault(f"{truth['case']}|{truth['condition']}", {
                "images": 0, "present_total": 0, "present_matched": 0, "absent_total": 0, "absent_reported": 0,
            })
            counts["images"] += 1
            present = {item["name"]: _quad_box(item["quad_px"]) for item in truth["present_symbols"]}
            absent = [name for name in truth["expected_symbols"] if name not in present]
            counts["present_total"] += len(present)
            counts["absent_total"] += len(absent)
            for symbol in (record.get("extraction") or {"symbols": []})["symbols"]:
                if symbol["name"] in absent:
                    counts["absent_reported"] += 1
                elif symbol["name"] in present and box_iou(tuple(symbol["bbox"]), present[symbol["name"]]) >= 0.5:
                    counts["present_matched"] += 1
    return table


def hard_comparison(datasets: list[Path], records_dir: Path, workers: int) -> list[str]:
    """Exact GS1 on original vs reduced hard for old, starting, and final decoders."""
    rows = {name: {"hard_original": [0, 0], "hard": [0, 0]} for name in ("old", "start", "template", "blind")}
    for dataset in datasets:
        final = {r["image"]: r for r in json.loads(_records_path(records_dir, dataset).read_text())["records"]}
        for name, ref in (("old", OLD_REF), ("start", START_REF)):
            for image, record in run_ref(ref, dataset, conditions=("hard", "hard_original"), workers=workers).items():
                truth = json.loads((dataset / image).with_suffix(".json").read_text(encoding="utf-8"))
                parsed = record["barcode_parsed"]
                cell = rows[name][truth["condition"]]
                cell[0] += int(len(parsed) == 1 and parsed[0] == truth["barcode_ais"])
                cell[1] += 1
        for record in final.values():
            condition = record["truth"]["condition"]
            if condition not in ("hard", "hard_original"):
                continue
            for mode in ("template", "blind"):
                parsed = record.get(mode, {}).get("barcodes", [])
                cell = rows[mode][condition]
                cell[0] += int(len(parsed) == 1 and parsed[0] == record["truth"]["barcode_ais"])
                cell[1] += 1
    labels = {
        "old": f"Old decoder (`{OLD_REF}`): photo, then rectified label",
        "start": f"Starting point (`{START_REF}`): plus thresholded template slot",
        "template": "Final, template-assisted",
        "blind": "Final, blind (no slot position)",
    }
    lines = [
        "| Decoder | Original hard (blur to 1.8, noise 8) | Reduced hard (blur to 1.6, noise 6) |",
        "| --- | --- | --- |",
    ]
    for name, label in labels.items():
        lines.append(f"| {label} | {_percent(*rows[name]['hard_original'])} | {_percent(*rows[name]['hard'])} |")
    return lines


def render(main: list[Path], neg: list[Path], records_dir: Path, workers: int) -> str:
    """Assemble the Phase 3 report from records and starting-point runs."""
    seeds = [json.loads((d / "manifest.json").read_text(encoding="utf-8"))["seed"] for d in main]
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    runs = [json.loads(_records_path(records_dir, d).read_text(encoding="utf-8")) for d in main]
    title = "Seeds " + ", ".join(str(seed) for seed in seeds)
    per_seed = json.loads((main[0] / "manifest.json").read_text(encoding="utf-8"))["labels_per_condition"]
    final_main = merge_counts([summarise(run) for run in runs])
    base = baseline_main(main, workers)
    lines = [
        "# CV final evaluation on fresh seeds",
        "",
        f"Seeds {', '.join(str(s) for s in seeds)} were generated once, after the code was frozen at commit"
        f" `{commit}`. No code was changed after these images were generated.",
        f"{per_seed} labels per condition and seed, so {per_seed * len(main)} images per condition below. All data"
        " is synthetic, from one template family, with test identifiers.",
        "",
        "## Starting point on the same images",
        "",
        f"Extractor at `{START_REF}` (the parth-cv branch as received), run from that commit.",
        "",
        "| Condition | Images | Exact GS1 | Symbols IoU>=0.5 | Symbol false positives | Corners within 10 px | "
        + " | ".join(f"CER {field}" for field in FIELDS) + " | CER all |",
        "| --- | ---: | --- | --- | ---: | --- | " + " | ".join("---:" for _ in FIELDS) + " | ---: |",
    ]
    for condition in CONDITION_ORDER:
        if condition not in base:
            continue
        c = base[condition]
        cer = [f"{100 * e / n:.2f}%" for e, n in (c["cer"][f] for f in FIELDS)]
        edits = sum(c["cer"][f][0] for f in FIELDS)
        chars = sum(c["cer"][f][1] for f in FIELDS)
        lines.append(
            f"| {condition} | {c['images']} | {_percent(c['gs1_exact'], c['images'])} |"
            f" {_percent(c['symbols_matched'], c['symbols_expected'])} | {c['symbol_false_positives']} |"
            f" {_percent(c['corners_10px'], c['images'])} | " + " | ".join(cer)
            + f" | {100 * edits / chars:.2f}% ({edits}/{chars}) |"
        )
    lines += ["", "## Final configuration", "", *render_main(final_main, title)]
    lines += ["## Original hard against reduced hard", "", *hard_comparison(main, records_dir, workers), ""]
    if neg:
        neg_runs = [json.loads(_records_path(records_dir, d).read_text(encoding="utf-8")) for d in neg]
        neg_table = merge_counts([summarise(run) for run in neg_runs])
        lines += ["## Negative and variation cases", "", *render_negatives(neg_table, title)]
        base_neg = baseline_negatives(neg, workers)
        lines += [
            f"### Starting point (`{START_REF}`) on the same negative and variation cases",
            "",
            "| Case | Condition | Images | Present symbols matched | Absent symbols reported |",
            "| --- | --- | ---: | --- | --- |",
        ]
        for key in sorted(base_neg):
            case, condition = key.split("|")
            c = base_neg[key]
            lines.append(
                f"| {case} | {condition} | {c['images']} | {_percent(c['present_matched'], c['present_total'])} |"
                f" {_percent(c['absent_reported'], c['absent_total'])} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    """Write the Phase 3 report."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--main", type=Path, nargs="+", required=True)
    parser.add_argument("--neg", type=Path, nargs="*", default=[])
    parser.add_argument("--records-dir", type=Path, default=Path("results/cv_records"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args(argv)
    args.output.write_text(render(args.main, args.neg, args.records_dir, args.workers), encoding="utf-8", newline="\n")
    print(f"Report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
