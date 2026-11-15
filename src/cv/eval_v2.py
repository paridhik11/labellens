"""Evaluate template-assisted and blind extraction on any set of conditions and on negative cases.

Step 1 runs the extractor on every image (in parallel) and stores one JSON
record per image. Step 2 turns records into counts. Reports are built from the
counts only, so every number can be traced to a record. Examples:

    python -m src.cv.eval_v2 run --dataset data/synthetic/dev42 --records results/cv_records/dev42.json
    python -m src.cv.eval_v2 run --dataset data/synthetic/neg42 --records results/cv_records/neg42.json
    python -m src.cv.eval_v2 summary --records results/cv_records/dev42.json results/cv_records/neg42.json
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

FIELDS = ("product_name", "manufacturer", "manufacturer_address", "model", "lot", "expiry")
MODES = ("template", "blind")
CONDITION_ORDER = ("clean", "moderate", "hard", "hard_original", "very_hard")


def edit_distance(reference: str, observed: str) -> int:
    """Count minimum character insertions, deletions and substitutions without normalization."""
    if len(reference) < len(observed):
        reference, observed = observed, reference
    previous = list(range(len(observed) + 1))
    for row, expected in enumerate(reference, start=1):
        current = [row]
        for column, actual in enumerate(observed, start=1):
            current.append(min(current[-1] + 1, previous[column] + 1, previous[column - 1] + (expected != actual)))
        previous = current
    return previous[-1]


def box_iou(first: tuple[float, ...], second: tuple[float, ...]) -> float:
    """Return intersection over union of two x, y, width, height boxes."""
    x1, y1, w1, h1 = first
    x2, y2, w2, h2 = second
    inter = max(0.0, min(x1 + w1, x2 + w2) - max(x1, x2)) * max(0.0, min(y1 + h1, y2 + h2) - max(y1, y2))
    union = w1 * h1 + w2 * h2 - inter
    return float(inter / union) if union > 0 else 0.0


def _quad_box(quad: list[list[float]]) -> tuple[float, float, float, float]:
    """Enclose four corners in an axis-aligned x, y, width, height box."""
    points = np.asarray(quad, dtype=float)
    left, top = points.min(axis=0)
    right, bottom = points.max(axis=0)
    return float(left), float(top), float(right - left), float(bottom - top)


def _run_one(job: tuple[str, str]) -> dict[str, Any]:
    """Extract one image in both modes and return a JSON-ready record. Never reads the truth file."""
    from src.cv.consistency import check_extraction
    from src.cv.extract import extract_label_modes

    image_path, relative = job
    record: dict[str, Any] = {"image": relative}
    started = time.time()
    try:
        outputs = extract_label_modes(image_path, modes=MODES, postcorrect=True)
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
        return record
    record["seconds"] = round(time.time() - started, 2)
    for mode, (extraction, details) in outputs.items():
        record[mode] = {
            "fields": extraction.fields,
            "raw_fields": details["raw_fields"],
            "barcodes": [item.parsed for item in extraction.barcodes],
            "barcode_method": details["barcode_method"],
            "symbols": [{"name": s.name, "bbox": list(s.bbox), "conf": s.conf} for s in extraction.symbols],
            "flags": [{"kind": flag.kind, "expected": flag.expected} for flag in check_extraction(extraction)],
            "flags_confidence_only": [
                {"kind": flag.kind, "expected": flag.expected}
                for flag in check_extraction(extraction, check_format=False)
            ],
            "warnings": sorted({warning.split(":", 1)[0] for warning in extraction.warnings}),
        }
    record["corners"] = outputs[MODES[0]][1]["corners"]
    record["corner_method"] = outputs[MODES[0]][1]["corner_method"]
    return record


def run_dataset(dataset_dir: Path, workers: int = 6) -> dict[str, Any]:
    """Run the extractor over a generated dataset and attach each image's ground truth."""
    dataset_dir = dataset_dir.resolve()
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    jobs = [(str(dataset_dir / entry["image"]), entry["image"]) for entry in manifest["files"]]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        records = list(pool.map(_run_one, jobs))
    for record, entry in zip(records, manifest["files"], strict=True):
        record["truth"] = json.loads((dataset_dir / entry["ground_truth"]).read_text(encoding="utf-8"))
    return {
        "generator": manifest["generator"],
        "seed": manifest["seed"],
        "dataset": dataset_dir.name,
        "records": records,
    }


def _new_counts() -> dict[str, Any]:
    """Create an empty counter block for one (condition, mode) cell."""
    return {
        "images": 0, "errors": 0, "gs1_exact": 0, "decoded": 0, "label_found": 0, "corners_10px": 0,
        "corners_fallback": 0, "symbols_expected": 0, "symbols_matched": 0, "symbol_false_positives": 0,
        "mismatch_false_alarms": 0, "mismatch_reviews": 0, "mismatch_checkable": 0,
        "raw": {field: [0, 0] for field in FIELDS}, "post": {field: [0, 0] for field in FIELDS},
        "barcode_methods": {},
    }


def _score_symbols(
    detected: list[dict[str, Any]], present: dict[str, tuple[float, ...]]
) -> tuple[int, int]:
    """Return (expected symbols matched at IoU 0.5, detections that match no present symbol)."""
    matched = 0
    false_positives = 0
    for symbol in detected:
        truth_box = present.get(symbol["name"])
        if truth_box is not None and box_iou(tuple(symbol["bbox"]), truth_box) >= 0.5:
            matched += 1
        else:
            false_positives += 1
    return matched, false_positives


def summarise_main(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Count results of a ``generate_dataset`` run per condition and mode."""
    table: dict[str, dict[str, Any]] = {}
    for record in run["records"]:
        truth = record["truth"]
        for mode in MODES:
            counts = table.setdefault(f"{truth['condition']}|{mode}", _new_counts())
            counts["images"] += 1
            if "error" in record:
                counts["errors"] += 1
                for field in FIELDS:
                    for kind in ("raw", "post"):
                        counts[kind][field][0] += len(truth["fields"][field])
                        counts[kind][field][1] += len(truth["fields"][field])
                counts["symbols_expected"] += len(truth["symbols"])
                continue
            result = record[mode]
            parsed = result["barcodes"]
            counts["decoded"] += int(bool(parsed))
            exact = len(parsed) == 1 and parsed[0] == truth["barcode_ais"]
            counts["gs1_exact"] += int(exact)
            method = result["barcode_method"] or "none"
            method = method.split("_wiener")[0].split("_unsharp")[0].split("_plain")[0]
            counts["barcode_methods"][method] = counts["barcode_methods"].get(method, 0) + 1
            corners = record["corners"]
            counts["label_found"] += int(corners is not None)
            if corners is not None:
                distances = np.linalg.norm(np.asarray(corners) - np.asarray(truth["label_quad_px"]), axis=1)
                counts["corners_10px"] += int(distances.max() <= 10)
                counts["corners_fallback"] += int(record["corner_method"] == "hull_fallback")
            present = {item["name"]: _quad_box(item["quad_px"]) for item in truth["symbols"]}
            matched, false_positives = _score_symbols(result["symbols"], present)
            counts["symbols_expected"] += len(present)
            counts["symbols_matched"] += matched
            counts["symbol_false_positives"] += false_positives
            for kind, key in (("raw", "raw_fields"), ("post", "fields")):
                for field in FIELDS:
                    reference = truth["fields"][field]
                    counts[kind][field][0] += edit_distance(reference, result[key].get(field, ""))
                    counts[kind][field][1] += len(reference)
            if len(parsed) == 1 and parsed[0]:
                counts["mismatch_checkable"] += 1
                counts["mismatch_false_alarms"] += int(
                    any(flag["kind"] == "barcode_mismatch" for flag in result["flags"])
                )
                counts["mismatch_reviews"] += int(
                    any(flag["kind"] == "needs_human_review" for flag in result["flags"])
                )
    return table


def summarise_negatives(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Count results of a ``generate_negatives`` run per case, condition and mode.

    For symbol cases: ``absent_total`` counts expected symbols that are not on
    the label, ``absent_reported`` how many of those the detector still
    reported (false positives), ``present_total`` and ``present_matched`` the
    symbols that are on the label. For ``wrong_barcode``: ``mismatch_flagged``
    counts labels where the print/barcode disagreement was noticed.
    """
    table: dict[str, dict[str, Any]] = {}
    for record in run["records"]:
        truth = record["truth"]
        for mode in MODES:
            counts = table.setdefault(
                f"{truth['case']}|{truth['condition']}|{mode}",
                {
                    "images": 0, "errors": 0, "absent_total": 0, "absent_reported": 0, "present_total": 0,
                    "present_matched": 0, "other_false_positives": 0, "missing_flagged": 0,
                    "mismatch_flagged": 0, "review_flagged": 0, "barcode_decoded": 0,
                },
            )
            counts["images"] += 1
            present = {item["name"]: _quad_box(item["quad_px"]) for item in truth["present_symbols"]}
            absent = [name for name in truth["expected_symbols"] if name not in present]
            counts["absent_total"] += len(absent)
            counts["present_total"] += len(present)
            if "error" in record:
                counts["errors"] += 1
                continue
            result = record[mode]
            for symbol in result["symbols"]:
                if symbol["name"] in absent:
                    counts["absent_reported"] += 1
                elif box_iou(tuple(symbol["bbox"]), present[symbol["name"]]) >= 0.5:
                    counts["present_matched"] += 1
                else:
                    counts["other_false_positives"] += 1
            flagged_missing = {flag["expected"] for flag in result["flags"] if flag["kind"] == "missing_symbol"}
            counts["missing_flagged"] += sum(name in flagged_missing for name in absent)
            counts["barcode_decoded"] += int(len(result["barcodes"]) == 1 and bool(result["barcodes"][0]))
            counts["mismatch_flagged"] += int(any(flag["kind"] == "barcode_mismatch" for flag in result["flags"]))
            counts["review_flagged"] += int(any(flag["kind"] == "needs_human_review" for flag in result["flags"]))
    return table


def summarise(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Dispatch to the right summary for the generator that made the dataset."""
    if run["generator"] == "src.gen.generate_negatives":
        return summarise_negatives(run)
    return summarise_main(run)


def merge_counts(tables: list[dict[str, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    """Add up count tables from several seeds, cell by cell."""
    merged: dict[str, dict[str, Any]] = {}

    def add(target: Any, source: Any) -> Any:
        if isinstance(source, dict):
            target = target if isinstance(target, dict) else {}
            for key, value in source.items():
                target[key] = add(target.get(key), value)
            return target
        if isinstance(source, list):
            return [a + b for a, b in zip(target or [0] * len(source), source, strict=True)]
        return (target or 0) + source

    for table in tables:
        for key, counts in table.items():
            merged[key] = add(merged.get(key), counts)
    return merged


def _percent(numerator: int, denominator: int) -> str:
    """Format a count with its rate, keeping a zero denominator visible."""
    return f"{numerator}/{denominator} ({100 * numerator / denominator:.1f}%)" if denominator else f"{numerator}/0"


def render_main(table: dict[str, dict[str, Any]], title: str) -> list[str]:
    """Render the per-condition tables of a main-dataset summary as Markdown lines."""
    conditions = [c for c in CONDITION_ORDER if any(key.startswith(f"{c}|") for key in table)]
    lines = [
        f"### {title}: barcode, symbols and label corners",
        "",
        "| Condition | Images | Exact GS1, blind | Exact GS1, template-assisted | Symbols IoU>=0.5, blind |"
        " Symbol false positives, blind | Symbols IoU>=0.5, template | Label found | Corners within 10 px |"
        " Found by fallback |",
        "| --- | ---: | --- | --- | --- | ---: | --- | --- | --- | ---: |",
    ]
    for condition in conditions:
        blind, template = table[f"{condition}|blind"], table[f"{condition}|template"]
        n = blind["images"]
        lines.append(
            f"| {condition} | {n} | {_percent(blind['gs1_exact'], n)} | {_percent(template['gs1_exact'], n)} |"
            f" {_percent(blind['symbols_matched'], blind['symbols_expected'])} | {blind['symbol_false_positives']} |"
            f" {_percent(template['symbols_matched'], template['symbols_expected'])} |"
            f" {_percent(blind['label_found'], n)} | {_percent(blind['corners_10px'], n)} |"
            f" {blind['corners_fallback']} |"
        )
    lines += [
        "",
        f"### {title}: print/barcode check on labels with one decoded barcode",
        "",
        "Every label here prints the same lot and expiry as its barcode, so every flag is a false alarm.",
        "",
        "| Condition | Mode | Labels checked | `barcode_mismatch` flags | `needs_human_review` flags |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for condition in conditions:
        for mode in MODES:
            c = table[f"{condition}|{mode}"]
            lines.append(
                f"| {condition} | {mode} | {c['mismatch_checkable']} | {c['mismatch_false_alarms']} |"
                f" {c.get('mismatch_reviews', 0)} |"
            )
    lines += [
        "",
        f"### {title}: OCR character error rate per field",
        "",
        "Edits / reference characters. \"raw\" is the OCR text as read, \"post\" is after format post-correction.",
        "",
        "| Condition | Mode | Text | " + " | ".join(FIELDS) + " | all fields |",
        "| --- | --- | --- | " + " | ".join("---:" for _ in FIELDS) + " | ---: |",
    ]
    for condition in conditions:
        for mode in MODES:
            for kind in ("raw", "post"):
                cells = table[f"{condition}|{mode}"][kind]
                texts = [f"{100 * e / c:.2f}% ({e}/{c})" if c else "n/a" for e, c in (cells[f] for f in FIELDS)]
                edits, chars = sum(cells[f][0] for f in FIELDS), sum(cells[f][1] for f in FIELDS)
                total = f"{100 * edits / chars:.2f}% ({edits}/{chars})" if chars else "n/a"
                lines.append(f"| {condition} | {mode} | {kind} | " + " | ".join(texts) + f" | {total} |")
    lines.append("")
    return lines


def render_negatives(table: dict[str, dict[str, Any]], title: str) -> list[str]:
    """Render the negative and variation summary as Markdown lines."""
    lines = [
        f"### {title}: negative and variation cases",
        "",
        "\"Absent symbols reported\" are false positives: the symbol is not on the label but was detected.",
        "\"Absence flagged\" counts absent symbols for which a `missing_symbol` flag was raised.",
        "",
        "| Case | Condition | Mode | Images | Present symbols matched | Absent symbols reported |"
        " Absence flagged | Other false positives | Barcode decoded | Print/barcode mismatch flagged |"
        " Needs-human review flagged |",
        "| --- | --- | --- | ---: | --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for key in sorted(table):
        case, condition, mode = key.split("|")
        c = table[key]
        lines.append(
            f"| {case} | {condition} | {mode} | {c['images']} | {_percent(c['present_matched'], c['present_total'])} |"
            f" {_percent(c['absent_reported'], c['absent_total'])} |"
            f" {_percent(c['missing_flagged'], c['absent_total'])} | {c['other_false_positives']} |"
            f" {_percent(c['barcode_decoded'], c['images'])} | {_percent(c['mismatch_flagged'], c['images'])} |"
            f" {_percent(c.get('review_flagged', 0), c['images'])} |"
        )
    lines.append("")
    return lines


def main(argv: list[str] | None = None) -> int:
    """Run the extractor over a dataset, or print the summary of saved records."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--dataset", type=Path, required=True)
    run.add_argument("--records", type=Path, required=True)
    run.add_argument("--workers", type=int, default=6)
    summary = commands.add_parser("summary")
    summary.add_argument("--records", type=Path, nargs="+", required=True)
    args = parser.parse_args(argv)
    if args.command == "run":
        result = run_dataset(args.dataset, args.workers)
        args.records.parent.mkdir(parents=True, exist_ok=True)
        args.records.write_text(json.dumps(result), encoding="utf-8")
        runs = [result]
    else:
        runs = [json.loads(path.read_text(encoding="utf-8")) for path in args.records]
    for is_negative, renderer in ((False, render_main), (True, render_negatives)):
        chosen = [r for r in runs if (r["generator"] == "src.gen.generate_negatives") == is_negative]
        if chosen:
            seeds = ", ".join(str(r["seed"]) for r in chosen)
            print("\n".join(renderer(merge_counts([summarise(r) for r in chosen]), f"Seeds {seeds}")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
