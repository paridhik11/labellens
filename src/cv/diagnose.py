"""Phase 1 diagnosis of the CV baseline: writes results/cv_diagnosis.md from measured data.

Every table is computed here. The "before" code is run from its git commit
through ``src.cv.baseline_ref`` so the numbers do not move when ``src/cv``
changes later. Run from the repo root:

    python -m src.cv.diagnose --datasets data/synthetic/dev42 data/synthetic/dev43
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from src.common.schemas import LabelExtraction
from src.cv.baseline_ref import OLD_REF, START_REF, run_ref

FIELDS = ("product_name", "manufacturer", "manufacturer_address", "model", "lot", "expiry")
BASE_CONDITIONS = ("clean", "moderate", "hard")


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


def _truth(dataset: Path, image: str) -> dict[str, Any]:
    """Load the ground-truth sidecar of one manifest image path."""
    return json.loads((dataset / image).with_suffix(".json").read_text(encoding="utf-8"))


def _seed(dataset: Path) -> int:
    """Read the generator seed from a dataset manifest."""
    return int(json.loads((dataset / "manifest.json").read_text(encoding="utf-8"))["seed"])


def barcode_2x2(datasets: list[Path], workers: int) -> list[str]:
    """Count exact GS1 matches for the old and new decoder on both hard settings."""
    lines = [
        "## (a) Barcode: what the decoder gained and what the easier benchmark gained",
        "",
        "Commit `3c98598` did two things at once. It reduced the hard condition (blur sigma range 1.0 to 1.8",
        "became 1.0 to 1.6, noise sigma 8 became 6) and it added the barcode-slot recovery. The commit before it",
        f"is `{OLD_REF}`. The table separates the two effects. \"Old decoder\" is the barcode path of `{OLD_REF}`",
        "(whole photo, then the rectified label). \"New decoder\" is the path of "
        f"`{START_REF}` (the same, then an",
        "adaptively thresholded crop of the known template barcode slot). \"Original hard\" is the",
        "`hard_original` condition, \"reduced hard\" is `hard`. Both use the same augmentation seed per label, so",
        "geometry, background and lighting are identical and only blur and noise differ.",
        "An exact match needs exactly one decoded symbol whose four AIs equal the ground truth.",
        "",
        "| Seed | Decoder | Original hard (blur to 1.8, noise 8) | Reduced hard (blur to 1.6, noise 6) |",
        "| ---: | --- | --- | --- |",
    ]
    totals = {(ref, condition): [0, 0] for ref in (OLD_REF, START_REF) for condition in ("hard_original", "hard")}
    for dataset in datasets:
        for ref, name in ((OLD_REF, "old"), (START_REF, "new")):
            records = run_ref(ref, dataset, conditions=("hard", "hard_original"), workers=workers)
            cells = []
            for condition in ("hard_original", "hard"):
                matched = images = 0
                for image, record in records.items():
                    if image.split("/")[0] != condition:
                        continue
                    images += 1
                    parsed = record["barcode_parsed"]
                    matched += int(len(parsed) == 1 and parsed[0] == _truth(dataset, image)["barcode_ais"])
                totals[(ref, condition)][0] += matched
                totals[(ref, condition)][1] += images
                cells.append(f"{matched}/{images}")
            lines.append(f"| {_seed(dataset)} | {name} (`{ref}`) | {cells[0]} | {cells[1]} |")
    for ref, name in ((OLD_REF, "old"), (START_REF, "new")):
        cells = ["{}/{}".format(*totals[(ref, condition)]) for condition in ("hard_original", "hard")]
        lines.append(f"| all | {name} (`{ref}`) | {cells[0]} | {cells[1]} |")
    old_orig, old_red = totals[(OLD_REF, "hard_original")][0], totals[(OLD_REF, "hard")][0]
    new_orig, new_red = totals[(START_REF, "hard_original")][0], totals[(START_REF, "hard")][0]
    images = totals[(OLD_REF, "hard")][1]
    lines += [
        "",
        f"Reading, over {images} hard labels in total: on the original hard setting the new decoder moved exact",
        f"matches from {old_orig} to {new_orig} (+{new_orig - old_orig}). That part is a real decoder improvement,",
        "although it depends on knowing where the barcode slot is. Making the benchmark easier added",
        f"{new_red - new_orig} more for the new decoder ({new_orig} to {new_red}) and {old_red - old_orig} for the"
        " old one",
        f"({old_orig} to {old_red}). The published \"above 80 percent\" number therefore needs both changes."
        " Measured on the",
        f"setting that existed before the commit, the new decoder reaches {new_orig}/{images}"
        f" ({100 * new_orig / images:.1f}%).",
        "",
    ]
    return lines


def _field_tables(datasets: list[Path], workers: int) -> tuple[list[str], dict[str, int]]:
    """Build the CER table, five examples per field and condition, and an error taxonomy."""
    lines = [
        "### Baseline character error rate on both dev seeds",
        "",
        f"Extractor at `{START_REF}`, unchanged. Edits / reference characters over 17 labels per cell.",
        "",
        "| Seed | Condition | " + " | ".join(FIELDS) + " |",
        "| ---: | --- | " + " | ".join("---:" for _ in FIELDS) + " |",
    ]
    taxonomy = {"wrong_fields": 0, "space_only": 0, "zero_o_only": 0, "space_and_zero_o": 0, "other": 0, "fields": 0}
    examples: list[str] = []
    for dataset in datasets:
        records = run_ref(START_REF, dataset, full=True, workers=workers)
        for condition in BASE_CONDITIONS:
            edits = {field: 0 for field in FIELDS}
            characters = {field: 0 for field in FIELDS}
            shown = {field: 0 for field in FIELDS}
            for image, record in records.items():
                if image.split("/")[0] != condition:
                    continue
                truth = _truth(dataset, image)
                observed_fields = record.get("extraction", {}).get("fields", {})
                for field in FIELDS:
                    reference = truth["fields"][field]
                    observed = observed_fields.get(field, "")
                    distance = edit_distance(reference, observed)
                    edits[field] += distance
                    characters[field] += len(reference)
                    taxonomy["fields"] += 1
                    if distance:
                        taxonomy["wrong_fields"] += 1
                        no_space = reference.replace(" ", "") == observed.replace(" ", "")
                        zero_o = reference.replace("O", "0") == observed.replace("O", "0")
                        both = reference.replace(" ", "").replace("O", "0") == observed.replace(" ", "").replace(
                            "O", "0"
                        )
                        kind = (
                            "space_only" if no_space else "zero_o_only" if zero_o
                            else "space_and_zero_o" if both else "other"
                        )
                        taxonomy[kind] += 1
                    if dataset == datasets[0] and shown[field] < 5:
                        shown[field] += 1
                        mark = "" if not distance else f" ({distance} edits)"
                        examples.append(
                            f"| {condition} | {field} | {Path(image).name} | {json.dumps(reference)} |"
                            f" {json.dumps(observed)}{mark} |"
                        )
            cells = [f"{100 * edits[f] / characters[f]:.2f}% ({edits[f]}/{characters[f]})" for f in FIELDS]
            lines.append(f"| {_seed(dataset)} | {condition} | " + " | ".join(cells) + " |")
    lines += [
        "",
        f"### OCR text against ground truth, first five labels per field and condition (seed {_seed(datasets[0])})",
        "",
        "Quotes show whitespace exactly.",
        "",
        "| Condition | Field | Image | Ground truth | OCR text |",
        "| --- | --- | --- | --- | --- |",
        *examples,
        "",
    ]
    return lines, taxonomy


def _padded_crops(image: np.ndarray, boxes: list[np.ndarray], pad_ratio: float) -> list[np.ndarray]:
    """Cut each text quadrilateral out of the image with extra margin on every side.

    The margin is ``pad_ratio`` times the box height. Pixels outside the image
    repeat the nearest edge pixel.
    """
    import cv2

    crops = []
    for box in boxes:
        quad = np.asarray(box, dtype=np.float32)
        width = max(np.linalg.norm(quad[1] - quad[0]), np.linalg.norm(quad[2] - quad[3]))
        height = max(np.linalg.norm(quad[3] - quad[0]), np.linalg.norm(quad[2] - quad[1]))
        pad = pad_ratio * height
        out_w, out_h = int(round(width + 2 * pad)), int(round(height + 2 * pad))
        target = np.array(
            [[pad, pad], [pad + width, pad], [pad + width, pad + height], [pad, pad + height]], dtype=np.float32
        )
        matrix = cv2.getPerspectiveTransform(quad, target)
        crops.append(cv2.warpPerspective(image, matrix, (out_w, out_h), borderMode=cv2.BORDER_REPLICATE))
    return crops


def _ocr_variant_worker(job: tuple[str, str]) -> dict[str, Any]:
    """Run the baseline engine on one rectified label under several controlled changes."""
    import cv2
    from PIL import Image
    from rapidocr_onnxruntime import RapidOCR

    from src.cv.extract import TEMPLATE_PATH, map_fields
    from src.cv.ocr import ocr_blocks_from_results
    from src.cv.preprocess import find_label_corners, rectify_label

    image_path, truth_path = job
    truth = json.loads(Path(truth_path).read_text(encoding="utf-8"))
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    engine = RapidOCR(text_score=0.0, use_cls=False, intra_op_num_threads=1, inter_op_num_threads=1)
    with Image.open(image_path) as photo:
        image = np.asarray(photo.convert("RGB"))
    rectified, _ = rectify_label(image, find_label_corners(image))
    size = (rectified.shape[1], rectified.shape[0])
    noise = np.random.default_rng(0).normal(0, 4, rectified.shape)
    noisy = np.clip(rectified.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    def score(rows: list[list[Any]] | None) -> int:
        fields, _ = map_fields(ocr_blocks_from_results(rows, size), size, template)
        return sum(edit_distance(truth["fields"][field], fields.get(field, "")) for field in FIELDS)

    out = {"condition": truth["condition"], "characters": sum(len(truth["fields"][field]) for field in FIELDS)}
    out["as_is"] = score(engine(cv2.cvtColor(rectified, cv2.COLOR_RGB2BGR))[0])
    out["noise_4"] = score(engine(cv2.cvtColor(noisy, cv2.COLOR_RGB2BGR))[0])
    bgr = cv2.cvtColor(rectified, cv2.COLOR_RGB2BGR)
    boxes, _ = engine.text_det(bgr)
    boxes = [] if boxes is None else list(boxes)
    heights = [float(np.linalg.norm(np.asarray(box)[3] - np.asarray(box)[0])) for box in boxes]
    out["median_box_height"] = float(np.median(heights)) if heights else 0.0
    for name, ratio in (("pad_0", 0.0), ("pad_15", 0.15), ("pad_30", 0.30), ("pad_50", 0.50)):
        rows = []
        if boxes:
            recognised, _ = engine.text_rec(_padded_crops(bgr, boxes, ratio))
            rows = [
                [np.asarray(box).tolist(), text, confidence]
                for box, (text, confidence) in zip(boxes, recognised, strict=True)
            ]
        out[name] = score(rows)
    return out


def ocr_root_cause(dataset: Path, workers: int) -> list[str]:
    """Measure which controlled change removes the clean-image errors."""
    manifest = json.loads((dataset / "manifest.json").read_text(encoding="utf-8"))
    jobs = [
        (str(dataset / entry["image"]), str(dataset / entry["ground_truth"]))
        for entry in manifest["files"] if entry["image"].split("/")[0] in BASE_CONDITIONS
    ]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_ocr_variant_worker, jobs))
    names = ("as_is", "noise_4", "pad_0", "pad_15", "pad_30", "pad_50")
    lines = [
        "### Controlled experiment: what removes the clean-image errors",
        "",
        f"Seed {_seed(dataset)}, 17 labels per condition, same engine settings as the baseline. Each cell is total"
        " character",
        "edits over all six fields and 17 labels (lower is better). \"as is\" is the baseline. \"noise 4\" adds",
        "Gaussian noise with sigma 4 to the rectified label before OCR. \"pad N\" keeps the detector boxes but",
        "re-crops each one with a margin of N percent of the box height before recognition (pad 0 re-crops with",
        "no margin and is the control for the re-cropping itself).",
        "",
        "| Condition | Reference characters | Median detector box height (px) | "
        + " | ".join(name.replace("_", " ") for name in names) + " |",
        "| --- | ---: | ---: | " + " | ".join("---:" for _ in names) + " |",
    ]
    for condition in BASE_CONDITIONS:
        rows = [row for row in results if row["condition"] == condition]
        characters = sum(row["characters"] for row in rows)
        height = float(np.median([row["median_box_height"] for row in rows]))
        cells = [str(sum(row[name] for row in rows)) for name in names]
        lines.append(f"| {condition} | {characters} | {height:.1f} | " + " | ".join(cells) + " |")
    lines.append("")
    return lines


def schema_check(dataset: Path, workers: int) -> list[str]:
    """Check that the baseline extraction validates and fills every LabelExtraction field."""
    records = run_ref(START_REF, dataset, full=True, workers=workers)
    counts = {
        key: 0 for key in (
            "images", "validates", "label_id_is_stem", "six_fields", "prefixed_values", "one_barcode",
            "barcode_bbox", "barcode_centre_in_slot", "two_symbols", "iso_ref_filled", "blocks_in_bounds",
            "version_1", "errors",
        )
    }
    for image, record in records.items():
        if image.split("/")[0] not in BASE_CONDITIONS:
            continue
        counts["images"] += 1
        if "extraction" not in record:
            counts["errors"] += 1
            continue
        truth = _truth(dataset, image)
        extraction = LabelExtraction.model_validate(record["extraction"])
        counts["validates"] += 1
        counts["label_id_is_stem"] += int(extraction.label_id == Path(image).stem)
        counts["six_fields"] += int(set(extraction.fields) == set(FIELDS))
        counts["prefixed_values"] += int(
            extraction.fields.get("model", "").startswith("REF") and extraction.fields.get("lot", "").startswith("LOT")
        )
        counts["one_barcode"] += int(len(extraction.barcodes) == 1 and len(extraction.barcodes[0].parsed) == 4)
        if len(extraction.barcodes) == 1 and extraction.barcodes[0].bbox is not None:
            counts["barcode_bbox"] += 1
            x, y, w, h = extraction.barcodes[0].bbox
            quad = np.asarray(truth["slot_quads_px"]["udi"], dtype=float)
            inside = quad[:, 0].min() <= x + w / 2 <= quad[:, 0].max() and quad[:, 1].min() <= y + h / 2 <= quad[
                :, 1
            ].max()
            counts["barcode_centre_in_slot"] += int(inside)
        counts["two_symbols"] += int(sorted(s.name for s in extraction.symbols) == ["expiry", "manufacturer"])
        counts["iso_ref_filled"] += int(bool(extraction.symbols) and all(s.iso_ref for s in extraction.symbols))
        width, height = truth["image_size_px"]
        counts["blocks_in_bounds"] += int(
            bool(extraction.ocr_blocks) and all(
                b.bbox[0] >= 0 and b.bbox[1] >= 0 and b.bbox[0] + b.bbox[2] <= width + 1e-6
                and b.bbox[1] + b.bbox[3] <= height + 1e-6 and 0 <= b.conf <= 1
                for b in extraction.ocr_blocks
            )
        )
        counts["version_1"] += int(extraction.version == 1)
    n = counts["images"]
    rows = [
        ("Output validates as `schemas.LabelExtraction`", "validates"),
        ("`label_id` equals the image file stem", "label_id_is_stem"),
        ("`fields` has exactly the six template fields", "six_fields"),
        ("`fields[\"model\"]` and `fields[\"lot\"]` still carry the printed prefix (`REF`, `LOT`)", "prefixed_values"),
        ("`barcodes` has one result with all four AIs parsed", "one_barcode"),
        ("that barcode has a `bbox`", "barcode_bbox"),
        ("the bbox centre lies inside the true barcode slot (original-image pixels)", "barcode_centre_in_slot"),
        ("`symbols` has exactly manufacturer and expiry", "two_symbols"),
        ("every symbol has a non-empty `iso_ref`", "iso_ref_filled"),
        ("every `ocr_blocks` box is inside the photo and has `conf` in 0 to 1", "blocks_in_bounds"),
        ("`version` is 1 (the default, never set by the extractor)", "version_1"),
        ("`extract_label` raised an exception", "errors"),
    ]
    lines = [
        "## (d) Does `extract_label` return a correctly filled `LabelExtraction`?",
        "",
        f"Extractor at `{START_REF}`, seed {_seed(dataset)}, conditions clean, moderate and hard, {n} images.",
        "",
        "| Check | Images passing |",
        "| --- | --- |",
        *[f"| {text} | {counts[key]}/{n} |" for text, key in rows],
        "",
        "Findings:",
        "",
        "- The return type is right and every container field is populated. Boxes are in original-photo pixels.",
        "- `fields` values keep the printed prefix: `model` is `REF: TEST-M001`, `lot` is `LOT: ...`, `expiry` is",
        "  `EXP: 2028-11-01`. `ProductRecord.model` expects the bare model, so a consumer must strip the prefix.",
        "  This is a semantic gap, not a schema violation. Fix 6 adds a helper that strips it without touching",
        "  `schemas.py`.",
        "- `SymbolDetection.iso_ref` is always the empty string. That is deliberate (the pictograms are not",
        "  certified ISO artwork) but it means a checker cannot cite a symbol standard from this output.",
        "- `version` is always the schema default 1. The extractor has no notion of label versions.",
        "- `label_id` is the file stem, so two photos of the same label get different ids.",
        "- The hard-condition barcode misses (decode failures) leave `barcodes` empty; that is the correct way to",
        "  report a miss, and the warning `BARCODE_NOT_DECODED` is present in those cases.",
        "",
    ]
    return lines


TEMPLATE_AUDIT = """## (c) Template dependence audit

"Template" means `src/gen/templates/test_device.json`, the layout the synthetic labels are rendered from.
A step is template-dependent when it reads slot positions or reference artwork that an unknown label would
not provide.

| Step | Code | Uses the known template? | Would it work on an unknown label? |
| --- | --- | --- | --- |
| Label boundary detection | `preprocess.find_label_corners` | No. Otsu and Canny contours, largest convex quadrilateral covering at least 15% of the photo that does not touch the frame | Yes, if the label is a bright quadrilateral with a visible edge. A label that fills the frame, a round label or a strongly occluded edge returns None |
| Rectification | `preprocess.rectify_label` | No. Output size comes from the detected edge lengths | Yes |
| Text detection and recognition | `ocr.read_text` (RapidOCR) | No | Yes |
| Whole-photo and rectified barcode decode | `barcode.decode_barcodes` (zxing-cpp) | No | Yes |
| GS1 parsing | `barcode.parse_gs1` | No, but only AIs 01, 17, 10 and 21 are accepted | Any other AI raises `GS1_PARSE_FAILED` |
| Barcode-slot recovery | `barcode.decode_barcode_slot` | Yes. Crops `bbox_mm` of the barcode slot (70, 20, 25, 25 mm) scaled to the rectified label | No. On another layout the crop lands on the wrong place. 10 of the 15 hard matches on seed 42 came from this step (warning `BARCODE_DECODED_FROM_TEMPLATE_SLOT`) |
| Field mapping | `extract.map_fields` | Yes. A text block becomes `model` only because its centre falls in the `model` slot rectangle | No. There is no reading of the `REF`, `LOT` or `EXP` keys |
| Symbol detection | `symbols.detect_symbols` | Yes, twice. It searches only a window around each symbol slot, at 0.8 to 1.2 times the slot size, and the reference PNGs in `data/symbols/device` are drawn by `src.gen.symbols.draw_symbol`, the same function that draws the symbols on the labels | No. A symbol in another place is never searched. A real ISO 7000 pictogram has different artwork. Because the search window always contains the slot, the 34/34 score mostly shows that the label was rectified well |
| Symbol evaluation | `eval_extract` | Every test label contains both symbols | False positives and missing-symbol detection were never measured |
| Generator self-check | `generate_dataset._save_condition` | Yes, it calls the slot recovery | Same limit as the slot recovery |

Summary: on a label with a different layout only boundary detection, rectification, raw OCR blocks and the
two non-slot barcode attempts would still work. Field names, symbols and most hard-condition barcode decodes
depend on the single known template.
"""


def render(datasets: list[Path], workers: int) -> str:
    """Assemble the whole diagnosis report."""
    field_lines, taxonomy = _field_tables(datasets, workers)
    wrong = taxonomy["wrong_fields"]
    lines = [
        "# CV diagnosis (Phase 0 and Phase 1 of the cv-fixes work)",
        "",
        "Generated by `python -m src.cv.diagnose`. Dev seeds only: "
        + ", ".join(str(_seed(dataset)) for dataset in datasets)
        + ". 17 labels per condition and seed.",
        "All data is synthetic, from one template family. Identifiers are test placeholders.",
        "",
        "## Phase 0: reproduction of the published seed-42 numbers",
        "",
        "Environment: Windows, Python 3.12.10, the exact versions pinned in `requirements-cv.txt`.",
        "",
        "```bash",
        "python -m src.gen.generate_dataset --output-dir data/synthetic/seed42 --seed 42 --labels-per-condition 17",
        "python -m src.cv.eval_extract --dataset data/synthetic/seed42 --output results/cv_extract_repro.md",
        "```",
        "",
        "- Every count and percentage in `results/cv_extract.md` reproduced exactly (51 images): barcode",
        "  17/17, 17/17, 15/17; corners 17/17 in all conditions; symbols 34/34; all 18 CER cells; all warning counts.",
        "- Differences: only the provenance block. Platform line (Darwin arm64 there, Windows AMD64 here), the",
        "  source-file hashes (git checks the files out with CRLF line endings on Windows) and the dataset hash.",
        "  The three OCR model hashes are identical. I could not determine whether the dataset hash differs because",
        "  of PNG encoding or because of small pixel differences between the two CPUs; the metrics are identical.",
        "- `pytest -q src/gen src/cv`: 232 passed, 1 failed. The failure is",
        "  `test_render_reuse_and_confirmed_change`, which needs the Poppler `pdftoppm` program. It is not",
        "  installed on this machine; the published run (233 passed) had it.",
        "- `pylibdmtx` (a second DataMatrix decoder) could not be loaded on Windows with Python 3.12 (missing",
        "  `libdmtx-64.dll`), so it is not used anywhere.",
        "",
        *barcode_2x2(datasets, workers),
        "## (b) OCR: why clean is worse than hard",
        "",
        *field_lines,
        "### Error types",
        "",
        f"Over both seeds and the three conditions there are {taxonomy['fields']} field readings, {wrong} of them"
        " wrong.",
        "",
        "| Error type | Wrong fields |",
        "| --- | ---: |",
        f"| Only spaces dropped (`REF: TEST` read as `REF:TEST`) | {taxonomy['space_only']} |",
        f"| Only digit zero read as capital O (or the reverse) | {taxonomy['zero_o_only']} |",
        f"| Both of the above | {taxonomy['space_and_zero_o']} |",
        f"| Anything else | {taxonomy['other']} |",
        "",
        *ocr_root_cause(datasets[0], workers),
        "### Root cause",
        "",
        "- It is not a special character: the labels contain no trademark sign, and the errors are dropped spaces",
        "  and 0/O swaps (table above).",
        "- It is not a different preprocessing path. All three conditions go through the same",
        "  `find_label_corners`, `rectify_label` and `read_text` calls. Clean photos are also rectified (the",
        "  detector finds the printed border), and the rectified sizes are within a few percent of each other.",
        "- It is not resolution and not an evaluation bug. The reference strings are the rendered strings and the",
        "  metric counts every character.",
        "- It is not the text detector being tighter on clean images: the median detector box height is about",
        "  the same in every condition (table above).",
        "- The cause is the recogniser. PP-OCRv4 recognition receives each text line cropped almost exactly at",
        "  the ink, and on such tight crops it is at a tipping point for two decisions: whether a gap is a space,",
        "  and whether a round glyph is 0 or O. Pixel-perfect rendered text (flat white background, no noise)",
        "  falls on the wrong side. Evidence: adding sigma 4 noise to the same clean labels removes almost all",
        "  errors (column \"noise 4\"), and re-cropping the same detector boxes with a margin of 30 percent of the",
        "  box height removes them without touching the pixels (column \"pad 30\"), in every condition.",
        "- Why hard reaches 0%: the text is large (9 to 12 pt at 300 DPI, glyphs 30 to 45 px tall) and black on",
        "  white in one font. Blur sigma up to 1.6 px is small against stroke widths of 4 to 5 px, and the hard",
        "  noise (sigma 6) happens to act like the noise in the experiment above. So \"hard\" is hard for the",
        "  barcode but not for OCR, and the 0% is an artefact of the same sensitivity, not proof of robust OCR.",
        "- Consequence: the published CER numbers mostly measure this crop sensitivity. The fix is to pad the",
        "  crops before recognition (general, no template knowledge), not to add noise.",
        "",
        TEMPLATE_AUDIT,
        *schema_check(datasets[0], workers),
    ]
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    """Write the diagnosis report for the given dev datasets."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, default=Path("results/cv_diagnosis.md"))
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args(argv)
    args.output.write_text(render(args.datasets, args.workers), encoding="utf-8", newline="\n")
    print(f"Report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
