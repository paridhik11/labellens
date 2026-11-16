"""Evaluate blind extraction on real phone photos, once they exist.

Looks for photos in ``data/real_photos`` and for ``data/real_photos/transcriptions.csv``
(see the README in that folder). When either is missing it says so and exits
without producing numbers. Run from the repo root:

    python -m src.cv.eval_real
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

PHOTO_SUFFIXES = (".jpg", ".jpeg", ".png")
KEYED_FIELDS = ("model", "lot", "expiry", "serial")


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


def load_transcriptions(csv_path: Path) -> dict[str, dict[str, str]]:
    """Read reference transcriptions: one row per photo, ``filename`` plus one column per field.

    Empty cells mean "not transcribed" and are skipped. Values are used
    exactly as typed, apart from removing surrounding whitespace.
    """
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "filename" not in reader.fieldnames:
            raise ValueError("transcriptions.csv needs a 'filename' column")
        rows = {}
        for row in reader:
            name = (row.get("filename") or "").strip()
            if not name:
                continue
            if name in rows:
                raise ValueError(f"Duplicate filename in transcriptions: {name}")
            rows[name] = {
                key.strip(): value.strip() for key, value in row.items()
                if key and key != "filename" and value and value.strip()
            }
    return rows


def score(reference: dict[str, str], observed: dict[str, str]) -> dict[str, dict[str, int]]:
    """Compare transcribed fields with extracted fields, per field.

    For keyed fields (model, lot, expiry, serial) the printed key is removed
    from the extracted text first, so the transcription holds only the value.
    A field that was not extracted counts all its characters as errors.
    """
    from src.cv.fields import strip_key

    result = {}
    for field, expected in reference.items():
        text = observed.get(field, "")
        if field in KEYED_FIELDS and text:
            text = strip_key(text)
        result[field] = {
            "edits": edit_distance(expected, text),
            "characters": len(expected),
            "exact": int(text == expected),
            "present": int(field in observed),
        }
    return result


def evaluate(folder: Path) -> dict[str, object] | None:
    """Run blind extraction on every transcribed photo; None when there is nothing to evaluate."""
    csv_path = folder / "transcriptions.csv"
    photos = sorted(path for path in folder.glob("*") if path.suffix.lower() in PHOTO_SUFFIXES)
    if not photos or not csv_path.is_file():
        return None
    from src.cv.extract import extract_label

    transcriptions = load_transcriptions(csv_path)
    totals: dict[str, dict[str, int]] = {}
    rows = []
    for photo in photos:
        reference = transcriptions.get(photo.name)
        if reference is None or not reference:
            status = "no transcription row, skipped" if reference is None else "no readable reference fields, skipped"
            rows.append({"photo": photo.name, "status": status})
            continue
        try:
            extraction = extract_label(photo, mode="blind", postcorrect=True)
        except Exception as error:
            rows.append({"photo": photo.name, "status": f"extraction failed: {type(error).__name__}: {error}"})
            observed: dict[str, str] = {}
            barcodes = 0
        else:
            observed = extraction.fields
            barcodes = len(extraction.barcodes)
            rows.append({"photo": photo.name, "status": "ok", "fields": observed, "barcodes": barcodes})
        scores = score(reference, observed)
        rows[-1].update(reference=reference, scores=scores)
        for field, counts in scores.items():
            total = totals.setdefault(field, {"edits": 0, "characters": 0, "exact": 0, "present": 0, "photos": 0})
            for key, value in counts.items():
                total[key] += value
            total["photos"] += 1
    missing = sorted(set(transcriptions) - {photo.name for photo in photos})
    return {"photos": len(photos), "rows": rows, "totals": totals, "transcribed_but_missing": missing}



def report_cell(value: object) -> str:
    """Keep source and OCR text inside one Markdown table cell."""
    return str(value).replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def render_report(result: dict[str, object], reference_source: str) -> str:
    """Render exact per-photo field comparisons without treating blank references as correct."""
    from src.cv.fields import strip_key

    lines = ["# Real photo evaluation", "", f"Reference source: {report_cell(reference_source)}.",
             "Condition: photograph. Mode: blind, with post-correction.",
             "Human three-photo spot-check: NOT_RUN. Results against AI references are provisional.",
             "", f"Photos found: {result['photos']}.", "",
             "| Photo | Extraction status | Field | Reference | Observed | Exact match |",
             "|---|---|---|---|---|---|"]
    for row in result["rows"]:
        for field in ("product_name", "lot", "expiry"):
            expected = row.get("reference", {}).get(field)
            observed = row.get("fields", {}).get(field, "")
            if field in KEYED_FIELDS and observed:
                observed = strip_key(observed)
            exact = row.get("scores", {}).get(field, {}).get("exact")
            verdict = "not scored" if exact is None else ("yes" if exact else "no")
            cells = (row["photo"], row["status"], field, expected or "not transcribed", observed, verdict)
            lines.append("| " + " | ".join(report_cell(cell) for cell in cells) + " |")
    lines += ["", "| Field | Scored photos | Exact matches | Character errors |", "|---|---|---|---|"]
    for field, total in result["totals"].items():
        lines.append(f"| {report_cell(field)} | {total['photos']} | {total['exact']}/{total['photos']} | "
                     f"{total['edits']}/{total['characters']} |")
    lines += ["", "Blank, absent and unreadable reference fields are not scored. "
              "Extraction failures count as misses for every readable reference field."]
    if result["transcribed_but_missing"]:
        lines += ["", f"Transcribed but missing photos: {result['transcribed_but_missing']}"]
    return "\n".join(lines) + "\n"

def main(argv: list[str] | None = None) -> int:
    """Print per-field results on real photos, or explain what is missing."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--folder", type=Path, default=Path("data/real_photos"))
    parser.add_argument("--report", type=Path, help="Save per-photo field comparisons as Markdown")
    parser.add_argument("--reference-source", choices=("unspecified", "LLM-labelled"), default="unspecified")
    args = parser.parse_args(argv)
    result = evaluate(args.folder)
    if result is None:
        print(f"No real photos to evaluate: add photos and transcriptions.csv to {args.folder} (see its README.md).")
        return 0
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(render_report(result, args.reference_source), encoding="utf-8")
    print(f"Reference source: {args.reference_source}.")
    print(f"Real photos found: {result['photos']}. Mode: blind, with post-correction.")
    for row in result["rows"]:
        decoded = f", barcodes decoded: {row['barcodes']}" if "barcodes" in row else ""
        print(f"  {row['photo']}: {row['status']}{decoded}")
    print("Field | photos | exact matches | character error rate (edits / characters)")
    for field, total in result["totals"].items():
        rate = f"{100 * total['edits'] / total['characters']:.2f}%" if total["characters"] else "n/a"
        print(
            f"{field} | {total['photos']} | {total['exact']}/{total['photos']} | "
            f"{rate} ({total['edits']}/{total['characters']})"
        )
    if result["transcribed_but_missing"]:
        print(f"Transcribed but no photo found: {result['transcribed_but_missing']}")
    if args.report:
        print(f"Per-photo field comparisons saved to {args.report}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
