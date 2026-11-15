"""Whole-label photos that carry *real* pictogram artwork (fetched from Wikimedia Commons) instead of our own styles.

Reads ``scripts/symbols/real_symbol_sources.json`` (written by ``scripts/symbols/fetch_real_symbols.py``) and the
PNG renderings in ``data/real_symbols/``. Each label gets one real manufacturer drawing and one real use-by drawing,
placed beside their text (``anchored`` layout), printed in grey tones and pushed through the same photo conditions as
every other set. The truth box is the tight box of the visible artwork. The "style" field of a truth entry is
``<kind>:<file>``, where kind is ``iso`` (standard pictogram) or ``generic`` (a free icon of the same concept).

This is a test of real artwork on synthetic labels, not of real labels. Do not commit the PNGs (``data/`` is local).

    python -m src.gen.generate_real_artwork --output-dir data/synthetic/real_artwork --seed 31
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np
from PIL import Image

from src.gen.augment import augment_label_detailed, transform_box
from src.gen.generate_dataset import CONDITIONS, _variant_values
from src.gen.generate_styled import DEFAULT_CONDITIONS, anchored_boxes
from src.gen.smoke_label import DPI, build_label
from src.gen.symbol_styles import SYMBOLS

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "scripts" / "symbols" / "real_symbol_sources.json"
ART_DIR = ROOT / "data" / "real_symbols"


def load_artwork(path: Path) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Return the grey ink map (0 ink, 255 paper) of an artwork cropped to its visible extent, and the crop box."""
    with Image.open(path) as opened:
        rgba = opened.convert("RGBA")
    background = Image.new("RGBA", rgba.size, "white")
    background.alpha_composite(rgba)
    grey = np.asarray(background.convert("L"), dtype=np.uint8)
    ys, xs = np.nonzero(grey < 200)
    if len(xs) == 0:
        raise ValueError(f"{path.name} has no visible artwork")
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    return grey[box[1]:box[3], box[0]:box[2]], box


def paste_artwork(image: Image.Image, art: np.ndarray, slot: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Print artwork inside a square slot, scaled to fit and centred; return the tight box actually used."""
    x, y, width, height = slot
    scale = min(width / art.shape[1], height / art.shape[0])
    new_w, new_h = max(1, round(art.shape[1] * scale)), max(1, round(art.shape[0] * scale))
    small = np.asarray(Image.fromarray(art).resize((new_w, new_h), Image.Resampling.LANCZOS), dtype=np.float32)
    left, top = x + (width - new_w) // 2, y + (height - new_h) // 2
    region = np.asarray(image.crop((left, top, left + new_w, top + new_h)), dtype=np.float32)
    image.paste(Image.fromarray(np.clip(region * (small / 255.0)[..., None], 0, 255).astype(np.uint8)), (left, top))
    return left, top, new_w, new_h


def generate_real_artwork(
    output_dir: Path, seed: int, *, labels_per_artwork: int = 6, conditions: tuple[str, ...] = DEFAULT_CONDITIONS
) -> dict[str, Any]:
    """Render labels with real artwork; each artwork appears on ``labels_per_artwork`` labels."""
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Output directory must be empty or absent")
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    by_symbol = {name: [s for s in sources if s["symbol"] == name] for name in SYMBOLS}
    count = labels_per_artwork * max(len(v) for v in by_symbol.values())
    manifest: dict[str, Any] = {
        "generator": "src.gen.generate_real_artwork", "format_version": 1, "seed": seed, "split": "real",
        "layout": "anchored", "condition_names": list(conditions), "files": [],
        "artwork": [{k: s[k] for k in ("symbol", "kind", "title", "page_url", "license")} for s in sources],
    }
    sequences = np.random.SeedSequence(seed).spawn(count)
    blank = {name: {"draw": None} for name in SYMBOLS}
    with TemporaryDirectory(prefix="labellens_real_") as temporary:
        for index, sequence in enumerate(sequences):
            rng = np.random.default_rng(sequence)
            fields, ais = _variant_values(index + 1, rng)
            base_seeds = {condition: int(rng.integers(0, 2**32)) for condition in CONDITIONS}
            label_id = f"test_label_{index + 1:03d}_real"
            paths = build_label(
                Path(temporary), label_id=label_id, field_values=fields, barcode_ais=ais, symbol_overrides=blank
            )
            order = list(SYMBOLS)
            rng.shuffle(order)
            code = ais["17"]
            printed = {"manufacturer": fields["manufacturer"], "expiry": f"EXP: 20{code[:2]}-{code[2:4]}-{code[4:]}"}
            slots = anchored_boxes(rng, printed, order)
            with Image.open(paths["image"]) as opened:
                source = opened.convert("RGB")
            drawn = []
            for name, slot in zip(order, slots, strict=True):
                choices = by_symbol[name]
                chosen = choices[index % len(choices)]
                art, _ = load_artwork(ART_DIR / chosen["local_png"])
                box = paste_artwork(source, art, slot)
                drawn.append({"name": name, "style": f"{chosen['kind']}:{Path(chosen['local_png']).stem}", "box": box})
            for condition in conditions:
                aug_seed = base_seeds.get(condition, base_seeds["hard"])
                photo, matrix, corners, _ = augment_label_detailed(source, condition, aug_seed)
                present = [
                    {"name": d["name"], "style": d["style"], "scale": 1.0,
                     "quad_px": transform_box(list(d["box"]), matrix)}
                    for d in drawn
                ]
                truth = {
                    "label_id": f"{label_id}_{condition}", "test_data": True, "status": "DRAFT", "case": "real_artwork",
                    "split": "real", "style": drawn[0]["style"], "condition": condition, "augmentation_seed": aug_seed,
                    "image_size_px": [photo.width, photo.height], "fields": fields, "barcode_ais": ais,
                    "label_quad_px": corners, "expected_symbols": list(SYMBOLS), "present_symbols": present,
                    "distractor_symbols": [], "dpi": DPI, "layout": "anchored",
                }
                folder = output_dir / "real_artwork" / condition
                folder.mkdir(parents=True, exist_ok=True)
                name = truth["label_id"]
                photo.save(folder / f"{name}.png", dpi=(DPI, DPI))
                (folder / f"{name}.json").write_text(json.dumps(truth, indent=2) + "\n", encoding="utf-8")
                manifest["files"].append({
                    "image": f"real_artwork/{condition}/{name}.png",
                    "ground_truth": f"real_artwork/{condition}/{name}.json",
                })
    manifest["total_images"] = len(manifest["files"])
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--labels-per-artwork", type=int, default=6)
    args = parser.parse_args(argv)
    manifest = generate_real_artwork(args.output_dir, args.seed, labels_per_artwork=args.labels_per_artwork)
    print(f"Generated {manifest['total_images']} images with real artwork (seed={args.seed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
