"""Generate whole-label photos whose symbols come from the style library (``src.gen.symbol_styles``).

Cases written under ``<output>/<case>/<condition>/``:

* ``styled``: both pictograms present, drawn in one style, at a random size and place in the free
  lower-right part of the label (so a detector cannot rely on slot positions).
* ``empty``: neither pictogram present (an absent symbol that is reported is a false positive).
* ``distractor``: two wrong pictograms (not manufacturer, not expiry) drawn in the split's styles.

The truth files use the same keys as ``generate_negatives`` (``present_symbols``, ``expected_symbols``,
``distractor_symbols``), plus ``split``, so ``src.cv.symbol_eval`` reads them unchanged. Everything is
synthetic, from one label template, with test identifiers.

    python -m src.gen.generate_styled --output-dir data/synthetic/styled_heldout --seed 7 --split heldout
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np
from PIL import Image

from src.gen.augment import ALL_CONDITIONS, augment_label_detailed, transform_box
from src.gen.generate_dataset import CONDITIONS, _variant_values
from src.gen.smoke_label import DPI, build_label
from src.gen.symbol_styles import (
    HELDOUT_DISTRACTORS,
    SYMBOLS,
    TRAIN_DISTRACTORS,
    paste_symbol,
    styles_in,
)

DEFAULT_CONDITIONS = ("clean", "moderate", "hard", "very_hard")
REGION = (790, 545, 1150, 700)  # x0, y0, x1, y1 of the free area right of the text slots, below the barcode
TEMPLATE = Path(__file__).parent / "templates" / "test_device.json"


def anchored_boxes(
    rng: np.random.Generator, fields: dict[str, str], order: list[str]
) -> list[tuple[int, int, int, int]]:
    """Place each symbol just right of the printed text it belongs to, as on real labels.

    The manufacturer pictogram sits beside the manufacturer name line and the use-by pictogram beside the
    expiry line, 25 to 45 px after the last character, centred on the line.
    """
    from PIL import ImageFont

    from src.gen.smoke_label import mm_to_px

    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    slots = {slot["field"]: slot for slot in template["slots"] if slot["type"] == "text"}
    boxes = []
    for name in order:
        slot = slots[name]
        x, y, width, height = map(mm_to_px, slot["bbox_mm"])
        font = ImageFont.load_default(size=round(slot["size_pt"] * DPI / 72))
        end = x + int(font.getbbox(fields[name], anchor="lt")[2])
        size = int(rng.integers(56, 91))
        boxes.append((end + int(rng.integers(25, 46)), y + height // 2 - size // 2, size, size))
    return boxes


def place_boxes(rng: np.random.Generator, count: int = 2) -> list[tuple[int, int, int, int]]:
    """Choose ``count`` non-overlapping square boxes (56 to 124 px) inside the free region."""
    x0, y0, x1, y1 = REGION
    for _ in range(200):
        boxes = []
        for _ in range(count):
            size = int(rng.integers(56, 125))
            boxes.append((int(rng.integers(x0, x1 - size + 1)), int(rng.integers(y0, y1 - size + 1)), size, size))
        gaps = [
            max(a[0] - (b[0] + b[2]), b[0] - (a[0] + a[2]), a[1] - (b[1] + b[3]), b[1] - (a[1] + a[3]))
            for i, a in enumerate(boxes) for b in boxes[i + 1:]
        ]
        if all(gap >= 12 for gap in gaps):
            return boxes
    raise RuntimeError("could not place symbols without overlap")


def generate_styled(
    output_dir: Path,
    seed: int,
    split: str,
    *,
    labels_per_style: int = 6,
    negatives_per_case: int = 30,
    conditions: tuple[str, ...] = DEFAULT_CONDITIONS,
    layout: str = "random",
) -> dict[str, Any]:
    """Render the styled, empty and distractor cases for one style split and return the manifest."""
    if set(conditions) - set(ALL_CONDITIONS):
        raise ValueError("Unknown condition")
    if layout not in ("random", "anchored"):
        raise ValueError("layout must be random or anchored")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Output directory must be empty or absent")
    styles = styles_in(split)
    distractors = HELDOUT_DISTRACTORS if split == "heldout" else TRAIN_DISTRACTORS
    plan = [("styled", style) for style in styles for _ in range(labels_per_style)]
    plan += [(case, styles[i % len(styles)]) for case in ("empty", "distractor") for i in range(negatives_per_case)]
    manifest: dict[str, Any] = {
        "generator": "src.gen.generate_styled", "format_version": 1, "seed": seed, "split": split, "layout": layout,
        "styles": [style.id for style in styles], "condition_names": list(conditions), "files": [],
    }
    sequences = np.random.SeedSequence(seed).spawn(len(plan))
    blank = {name: {"draw": None} for name in SYMBOLS}
    with TemporaryDirectory(prefix="labellens_styled_") as temporary:
        for index, ((case, style), sequence) in enumerate(zip(plan, sequences, strict=True), start=1):
            rng = np.random.default_rng(sequence)
            fields, ais = _variant_values(index, rng)
            base_seeds = {condition: int(rng.integers(0, 2**32)) for condition in CONDITIONS}
            label_id = f"test_label_{index:03d}_{case}_{style.id}"
            paths = build_label(
                Path(temporary), label_id=label_id, field_values=fields, barcode_ais=ais, symbol_overrides=blank
            )
            boxes = place_boxes(rng) if layout == "random" else []
            order = list(SYMBOLS)
            rng.shuffle(order)
            if layout == "anchored":
                code = ais["17"]
                expiry_text = f"EXP: 20{code[:2]}-{code[2:4]}-{code[4:]}"
                printed = {"manufacturer": fields["manufacturer"], "expiry": expiry_text}
                boxes = anchored_boxes(rng, printed, order)
            ink = int(rng.integers(0, 70))
            drawn = []
            with Image.open(paths["image"]) as opened:
                source = opened.convert("RGB")
            if case == "styled":
                for name, box in zip(order, boxes, strict=True):
                    paste_symbol(source, name, style, box, ink_level=ink)
                    drawn.append({"name": name, "style": style.id, "box": box, "distractor": False})
            elif case == "distractor":
                chosen = rng.permutation(len(distractors))[:2]
                for pick, box in zip(chosen, boxes, strict=True):
                    paste_symbol(source, distractors[int(pick)], style, box, ink_level=ink)
                    drawn.append({"name": distractors[int(pick)], "style": style.id, "box": box, "distractor": True})
            for condition in conditions:
                aug_seed = base_seeds.get(condition, base_seeds["hard"])
                photo, matrix, corners, _ = augment_label_detailed(source, condition, aug_seed)
                present, wrong = [], []
                for item in drawn:
                    entry = {
                        "name": item["name"], "style": item["style"], "scale": 1.0,
                        "quad_px": transform_box(list(item["box"]), matrix),
                    }
                    (wrong if item["distractor"] else present).append(entry)
                truth = {
                    "label_id": f"{label_id}_{condition}", "test_data": True, "status": "DRAFT", "case": case,
                    "split": split, "style": style.id, "condition": condition, "augmentation_seed": aug_seed,
                    "image_size_px": [photo.width, photo.height], "fields": fields, "barcode_ais": ais,
                    "label_quad_px": corners, "expected_symbols": list(SYMBOLS), "present_symbols": present,
                    "distractor_symbols": wrong, "dpi": DPI, "layout": layout,
                }
                folder = output_dir / case / condition
                folder.mkdir(parents=True, exist_ok=True)
                name = truth["label_id"]
                photo.save(folder / f"{name}.png", dpi=(DPI, DPI))
                (folder / f"{name}.json").write_text(json.dumps(truth, indent=2) + "\n", encoding="utf-8")
                manifest["files"].append(
                    {"image": f"{case}/{condition}/{name}.png", "ground_truth": f"{case}/{condition}/{name}.json"}
                )
    manifest["total_images"] = len(manifest["files"])
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--split", choices=["train", "dev", "heldout"], required=True)
    parser.add_argument("--labels-per-style", type=int, default=6)
    parser.add_argument("--negatives-per-case", type=int, default=30)
    parser.add_argument("--layout", choices=["random", "anchored"], default="random")
    args = parser.parse_args(argv)
    manifest = generate_styled(
        args.output_dir, args.seed, args.split,
        labels_per_style=args.labels_per_style, negatives_per_case=args.negatives_per_case, layout=args.layout,
    )
    print(f"Generated {manifest['total_images']} images (split={args.split}, seed={args.seed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
