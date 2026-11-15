"""Generate negative and variation test labels for symbol and barcode checks.

The main dataset only has labels where both pictograms are present, drawn by
the same code as the detector's references, and where the barcode agrees with
the print. This generator adds what is needed to measure false positives:

Negative cases (something is wrong and should be noticed):
- ``missing_manufacturer`` / ``missing_expiry``: one symbol slot is empty.
- ``wrong_symbol``: the expiry slot holds a different pictogram (caution).
- ``wrong_barcode``: the barcode encodes a lot (odd labels) or expiry date
  (even labels) that differs from the printed text.

Variation cases (both symbols present, but drawn differently):
- ``alt_style``: independent filled artwork from ``src.gen.alt_symbols``.
- ``small_symbols`` / ``large_symbols``: default artwork at 0.6 and 1.25 size.

Labels use the same text values and the same augmentation seeds as
``generate_dataset`` with the same seed, so each case is paired with a normal
label. All identifiers remain test placeholders.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np
from PIL import Image

from src.gen.augment import ALL_CONDITIONS, Condition, augment_label_detailed, transform_box
from src.gen.generate_dataset import CONDITIONS, _variant_values
from src.gen.smoke_label import DPI, build_label

EXPECTED_SYMBOLS = ("manufacturer", "expiry")
NEGATIVE_CASES = ("missing_manufacturer", "missing_expiry", "wrong_symbol", "wrong_barcode")
VARIATION_CASES = ("alt_style", "small_symbols", "large_symbols")
CASES = NEGATIVE_CASES + VARIATION_CASES


def _case_options(case: str, index: int, ais: dict[str, str]) -> dict[str, Any]:
    """Return the ``build_label`` options that realise one case for one label."""
    if case == "missing_manufacturer":
        return {"symbol_overrides": {"manufacturer": {"draw": None}}}
    if case == "missing_expiry":
        return {"symbol_overrides": {"expiry": {"draw": None}}}
    if case == "wrong_symbol":
        return {"symbol_overrides": {"expiry": {"draw": "caution", "style": "distractor"}}}
    if case == "alt_style":
        return {"symbol_overrides": {name: {"draw": name, "style": "alt"} for name in EXPECTED_SYMBOLS}}
    if case in ("small_symbols", "large_symbols"):
        scale = 0.6 if case == "small_symbols" else 1.25
        return {"symbol_overrides": {name: {"draw": name, "scale": scale} for name in EXPECTED_SYMBOLS}}
    if case == "wrong_barcode":
        changed = dict(ais)
        if index % 2:
            last = changed["10"][-1]
            changed["10"] = changed["10"][:-1] + str((int(last) + 1) % 10)
        else:
            day = date(2000 + int(ais["17"][:2]), int(ais["17"][2:4]), int(ais["17"][4:])) + timedelta(days=1)
            changed["17"] = day.strftime("%y%m%d")
        printed_expiry = date(2000 + int(ais["17"][:2]), int(ais["17"][2:4]), int(ais["17"][4:])).isoformat()
        return {
            "barcode_ais": changed,
            "print_fields": {"lot": f"LOT: {ais['10']}", "expiry": f"EXP: {printed_expiry}"},
            "allow_print_barcode_mismatch": True,
        }
    raise ValueError(f"Unknown case: {case}")


def generate_negatives(
    output_dir: Path,
    seed: int = 42,
    labels_per_case: int = 17,
    conditions: tuple[Condition, ...] = ("moderate", "hard"),
    cases: tuple[str, ...] = CASES,
) -> dict[str, Any]:
    """Render every case under every condition and return the saved manifest."""
    if set(conditions) - set(ALL_CONDITIONS) or set(cases) - set(CASES):
        raise ValueError("Unknown condition or case")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Output directory must be empty or absent")
    manifest: dict[str, Any] = {
        "generator": "src.gen.generate_negatives",
        "format_version": 1,
        "seed": seed,
        "labels_per_case": labels_per_case,
        "condition_names": list(conditions),
        "cases": list(cases),
        "files": [],
    }
    sequences = np.random.SeedSequence(seed).spawn(labels_per_case)
    with TemporaryDirectory(prefix="labellens_negative_") as temporary:
        for index, sequence in enumerate(sequences, start=1):
            rng = np.random.default_rng(sequence)
            fields, ais = _variant_values(index, rng)
            base_seeds = {condition: int(rng.integers(0, 2**32)) for condition in CONDITIONS}
            for case in cases:
                options = _case_options(case, index, ais)
                field_values = {**fields, **options.pop("print_fields", {})}
                barcode_ais = options.pop("barcode_ais", ais)
                label_id = f"test_label_{index:03d}_{case}"
                paths = build_label(
                    Path(temporary), label_id=label_id, field_values=field_values, barcode_ais=barcode_ais, **options
                )
                source_truth = json.loads(Path(paths["ground_truth"]).read_text(encoding="utf-8"))
                overrides = source_truth.get("symbol_overrides", {})
                with Image.open(paths["image"]) as source:
                    for condition in conditions:
                        aug_seed = base_seeds.get(condition, base_seeds["hard"])
                        photo, matrix, corners, _ = augment_label_detailed(source, condition, aug_seed)
                        present, distractors = [], []
                        for symbol in source_truth["symbols"]:
                            drawn = overrides.get(symbol["name"])
                            box = symbol["bbox_px_xywh"] if drawn is None else drawn["bbox_px_xywh"]
                            entry = {
                                "name": symbol["name"] if drawn is None else drawn["drawn_name"],
                                "style": "outline" if drawn is None else drawn["style"],
                                "scale": 1.0 if drawn is None else drawn["scale"],
                                "quad_px": transform_box(box, matrix),
                            }
                            if entry["name"] is None:
                                continue
                            (distractors if entry["style"] == "distractor" else present).append(entry)
                        truth = {
                            "label_id": f"{label_id}_{condition}",
                            "test_data": True,
                            "status": "DRAFT",
                            "case": case,
                            "negative": case in NEGATIVE_CASES,
                            "condition": condition,
                            "augmentation_seed": aug_seed,
                            "image_size_px": [photo.width, photo.height],
                            "fields": source_truth["fields"],
                            "barcode_ais": source_truth["barcode_ais"],
                            "print_matches_barcode": source_truth.get("print_matches_barcode", True),
                            "label_quad_px": corners,
                            "slot_quads_px": {
                                field: transform_box(box, matrix)
                                for field, box in source_truth["slot_boxes_px_xywh"].items()
                            },
                            "expected_symbols": list(EXPECTED_SYMBOLS),
                            "present_symbols": present,
                            "distractor_symbols": distractors,
                        }
                        folder = output_dir / case / condition
                        folder.mkdir(parents=True, exist_ok=True)
                        name = truth["label_id"]
                        photo.save(folder / f"{name}.png", dpi=(DPI, DPI))
                        (folder / f"{name}.json").write_text(json.dumps(truth, indent=2) + "\n", encoding="utf-8")
                        manifest["files"].append({
                            "image": f"{case}/{condition}/{name}.png",
                            "ground_truth": f"{case}/{condition}/{name}.json",
                        })
    manifest["total_images"] = len(manifest["files"])
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    """Generate the negative and variation set from command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--labels-per-case", type=int, default=17)
    parser.add_argument("--conditions", nargs="+", default=["moderate", "hard"], choices=list(ALL_CONDITIONS))
    args = parser.parse_args(argv)
    try:
        manifest = generate_negatives(args.output_dir, args.seed, args.labels_per_case, tuple(args.conditions))
    except ValueError as error:
        parser.error(str(error))
    print(f"Generated {manifest['total_images']} negative and variation images (seed={args.seed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
