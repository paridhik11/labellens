"""Generate paired synthetic test labels with reproducible photo conditions."""

from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np
from PIL import Image

from src.cv.barcode import decode_barcode_slot, decode_barcodes
from src.cv.preprocess import find_label_corners, rectify_label
from src.gen.augment import Condition, augment_label, transform_box
from src.gen.smoke_label import DPI, build_label

CONDITIONS: tuple[Condition, ...] = ("clean", "moderate", "hard")


def _variant_values(index: int, rng: np.random.Generator) -> tuple[dict[str, str], dict[str, str]]:
    """Choose bounded test text and matching GS1 values without allocating GTINs."""
    product = rng.choice(["DEVICE", "SENSOR", "KIT"])
    expiry = date(2027, 1, 1) + timedelta(days=int(rng.integers(0, 731)))
    fields = {
        "product_name": f"TEST {product} {index:03d}",
        "manufacturer": f"Example Labs {index:03d}",
        "manufacturer_address": f"{100 + index} Example Road",
        "model": f"REF: TEST-M{index:03d}",
    }
    ais = {
        "17": expiry.strftime("%y%m%d"),
        "10": f"TESTLOT{index:03d}{rng.integers(1000, 10000)}",
        "21": f"TESTSER{index:03d}{rng.integers(1000, 10000)}",
    }
    return fields, ais


def _save_condition(
    source: Image.Image,
    source_truth: dict[str, Any],
    output_dir: Path,
    condition: Condition,
    seed: int,
) -> dict[str, Any]:
    """Save a photo and its transformed ground truth with measured self-checks."""
    photo, matrix, label_corners = augment_label(source, condition, seed)
    slot_quads = {
        field: transform_box(box, matrix)
        for field, box in source_truth["slot_boxes_px_xywh"].items()
    }
    points = np.asarray([label_corners, *slot_quads.values()])
    geometry_ok = bool(
        np.isfinite(points).all()
        and (points[..., 0] >= 0).all()
        and (points[..., 0] < photo.width).all()
        and (points[..., 1] >= 0).all()
        and (points[..., 1] < photo.height).all()
    )
    rgb = np.asarray(photo.convert("RGB"))
    decoded, decode_warnings = decode_barcodes(rgb)
    recovery_method = "original_image"
    if not decoded:
        corners = find_label_corners(rgb)
        if corners is not None:
            corrected, _ = rectify_label(rgb, corners)
            decoded, decode_warnings = decode_barcodes(corrected)
            recovery_method = "rectified_image"
            if not decoded:
                decoded, decode_warnings = decode_barcode_slot(corrected)
                if decoded:
                    recovery_method = "thresholded_template_slot"
        else:
            recovery_method = "label_boundary_not_found"
    barcode_ok = len(decoded) == 1 and decoded[0].parsed == source_truth["barcode_ais"]
    label_id = f"{source_truth['label_id']}_{condition}"
    truth = {
        key: value for key, value in source_truth.items()
        if key not in {"slot_boxes_px_xywh", "symbols", "limitations"}
    }
    truth.update(
        label_id=label_id,
        base_label_id=source_truth["label_id"],
        condition=condition,
        augmentation_seed=seed,
        source_image_size_px=source_truth["image_size_px"],
        image_size_px=[photo.width, photo.height],
        homography=matrix.tolist(),
        label_quad_px=label_corners,
        source_slot_boxes_px_xywh=source_truth["slot_boxes_px_xywh"],
        slot_quads_px=slot_quads,
        symbols=[
            {
                "name": symbol["name"],
                "source_bbox_px_xywh": symbol["bbox_px_xywh"],
                "quad_px": transform_box(symbol["bbox_px_xywh"], matrix),
                "synthetic_pictogram": symbol["synthetic_pictogram"],
                "iso_ref": symbol["iso_ref"],
            }
            for symbol in source_truth["symbols"]
        ],
        change_log=[
            {"action": "render_test_template", "base_label_id": source_truth["label_id"]},
            {"action": "augment", "condition": condition, "seed": seed},
        ],
        self_check={
            "scope": "geometry_and_recovered_barcode_only",
            "status": "PASS" if geometry_ok and barcode_ok else "NEEDS_HUMAN_REVIEW",
            "geometry_in_bounds": geometry_ok,
            "barcode_matches": barcode_ok,
            "barcode_recovery_method": recovery_method,
            "barcode_warnings": decode_warnings,
            "decoded_barcodes": [
                {"type": item.type, "raw": item.raw, "parsed": item.parsed}
                for item in decoded
            ],
            "ocr": "NOT_RUN",
            "symbol_detection": "NOT_RUN",
        },
        limitations=[
            "Synthetic test data with the existing all-zero identifier placeholder; not an allocated GTIN",
            "Simplified pictograms, not certified ISO artwork",
            "Positions describe template slots, not tight text or barcode ink bounds",
            "OCR and automated symbol detection were not run",
            "Some distorted barcodes may still need human review; failed self-checks are retained",
        ],
    )
    condition_dir = output_dir / condition
    condition_dir.mkdir(parents=True, exist_ok=True)
    photo.save(condition_dir / f"{label_id}.png", dpi=(DPI, DPI))
    (condition_dir / f"{label_id}.json").write_text(json.dumps(truth, indent=2) + "\n", encoding="utf-8")
    return truth


def generate_dataset(output_dir: Path, seed: int = 42, labels_per_condition: int = 17) -> dict[str, Any]:
    """Generate three conditions per base label and return the saved manifest.

    An existing dataset may be regenerated with the same seed and count.
    Other nonempty output directories are rejected to avoid mixing datasets.
    """
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if isinstance(labels_per_condition, bool) or not isinstance(labels_per_condition, int):
        raise ValueError("labels_per_condition must be an integer from 1 to 999")
    if not 1 <= labels_per_condition <= 999:
        raise ValueError("labels_per_condition must be an integer from 1 to 999")
    config = {
        "generator": "src.gen.generate_dataset",
        "format_version": 1,
        "seed": seed,
        "labels_per_condition": labels_per_condition,
    }
    manifest_path = output_dir / "manifest.json"
    if output_dir.exists() and any(output_dir.iterdir()):
        if not manifest_path.is_file():
            raise ValueError("Nonempty output directory has no dataset manifest; use a new directory")
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        if any(previous.get(key) != value for key, value in config.items()):
            raise ValueError("Output dataset uses different settings; use a new directory")
        expected = {"manifest.json"} | {
            f"{condition}/test_label_{index:03d}_{condition}.{suffix}"
            for condition in CONDITIONS
            for index in range(1, labels_per_condition + 1)
            for suffix in ("png", "json")
        }
        actual = {path.relative_to(output_dir).as_posix() for path in output_dir.rglob("*") if path.is_file()}
        if actual - expected:
            raise ValueError("Output directory contains unrelated files; use a new directory")
    counts = {condition: {"images": 0, "barcode_passes": 0, "geometry_passes": 0} for condition in CONDITIONS}
    manifest = {**config, "total_images": labels_per_condition * len(CONDITIONS), "conditions": counts, "files": []}
    sequences = np.random.SeedSequence(seed).spawn(labels_per_condition)
    with TemporaryDirectory(prefix="labellens_source_") as temporary:
        for index, sequence in enumerate(sequences, start=1):
            rng = np.random.default_rng(sequence)
            fields, ais = _variant_values(index, rng)
            paths = build_label(
                Path(temporary), label_id=f"test_label_{index:03d}", field_values=fields, barcode_ais=ais
            )
            source_truth = json.loads(Path(paths["ground_truth"]).read_text(encoding="utf-8"))
            with Image.open(paths["image"]) as source:
                for condition in CONDITIONS:
                    augmentation_seed = int(rng.integers(0, 2**32))
                    truth = _save_condition(source, source_truth, output_dir, condition, augmentation_seed)
                    counts[condition]["images"] += 1
                    counts[condition]["barcode_passes"] += int(truth["self_check"]["barcode_matches"])
                    counts[condition]["geometry_passes"] += int(truth["self_check"]["geometry_in_bounds"])
                    manifest["files"].append({
                        "image": f"{condition}/{truth['label_id']}.png",
                        "ground_truth": f"{condition}/{truth['label_id']}.json",
                    })
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    """Generate a dataset from command-line arguments and print measured counts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/synthetic/task1"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--labels-per-condition", type=int, default=17)
    args = parser.parse_args(argv)
    try:
        manifest = generate_dataset(args.output_dir, args.seed, args.labels_per_condition)
    except ValueError as error:
        parser.error(str(error))
    print(f"Generated {manifest['total_images']} image/JSON pairs (seed={args.seed})")
    for condition, counts in manifest["conditions"].items():
        total = counts["images"]
        print(
            f"{condition}: images={total}, barcode_matches={counts['barcode_passes']}/{total}, "
            f"geometry_in_bounds={counts['geometry_passes']}/{total}"
        )
    print("Self-check scope: geometry and barcode only; OCR and symbol detection NOT_RUN")
    print(f"Manifest: {args.output_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
