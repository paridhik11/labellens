"""Whole-label evaluation of symbol detectors, without OCR or barcode decoding.

The pipeline in ``src.cv.extract`` finds the label boundary, straightens the
photo and only then searches for symbols. This module repeats exactly those
first steps (boundary, fallback boundary, rectification, or the whole photo
when no boundary is found), caches the straightened label, and then runs any
detector on it. Detections are projected back to original-photo coordinates
and scored against the ground truth with IoU >= 0.5, as ``src.cv.eval_v2``
does. Nothing here reads a ground-truth file while detecting.

Truth formats understood:

* main sets (``generate_dataset``): ``symbols`` with ``name`` and ``quad_px``;
  both symbols are present, none absent.
* negative and styled sets (``generate_negatives``, ``generate_styled``):
  ``present_symbols``, ``expected_symbols`` and ``distractor_symbols``. An
  expected symbol that is not present is absent; reporting it is a false positive.

Run ``python -m src.cv.symbol_eval --help`` for the command line.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from src.common.schemas import SymbolDetection
from src.cv.intervals import wilson_interval

Detector = Callable[[np.ndarray], list[SymbolDetection]]
CONDITIONS = ("clean", "moderate", "hard", "very_hard")


@dataclass
class Item:
    """One evaluation image: straightened label, the way back to the photo, and its truth."""

    key: str
    corrected: np.ndarray
    inverse: np.ndarray | None
    size: tuple[int, int]
    present: dict[str, tuple[float, float, float, float]]
    absent: list[str]
    meta: dict[str, str]


def box_iou(first: tuple[float, ...], second: tuple[float, ...]) -> float:
    """Intersection over union of two x, y, width, height boxes."""
    x1, y1, w1, h1 = first
    x2, y2, w2, h2 = second
    inter = max(0.0, min(x1 + w1, x2 + w2) - max(x1, x2)) * max(0.0, min(y1 + h1, y2 + h2) - max(y1, y2))
    union = w1 * h1 + w2 * h2 - inter
    return float(inter / union) if union > 0 else 0.0


def quad_box(quad: list[list[float]]) -> tuple[float, float, float, float]:
    """Enclose four corners in an axis-aligned x, y, width, height box."""
    points = np.asarray(quad, dtype=float)
    left, top = points.min(axis=0)
    right, bottom = points.max(axis=0)
    return float(left), float(top), float(right - left), float(bottom - top)


def straighten(image: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
    """Return the label as the extractor would see it, and the matrix back to the photo (or None)."""
    from src.cv.preprocess import find_label_corners, find_label_corners_fallback, rectify_label

    corners = find_label_corners(image)
    if corners is None:
        corners = find_label_corners_fallback(image)
    if corners is None:
        return image, None
    corrected, forward = rectify_label(image, corners)
    return corrected, np.linalg.inv(forward)


def glyph_quad(entry: dict[str, Any]) -> list[list[float]]:
    """Return the quad of the glyph's own ink inside a styled symbol's square slot.

    A styled pictogram does not fill its square box (an hourglass is narrower than it is tall), so overlap is
    measured against the glyph's tight ink box, mapped through the same photo transform as the slot (the corners
    of the slot are interpolated bilinearly). Entries whose style is not in the style library keep their quad.
    """
    from functools import lru_cache

    from src.gen.symbol_styles import STYLES, render_mask

    @lru_cache(maxsize=None)
    def fractions(name: str, style_id: str) -> tuple[float, float, float, float] | None:
        style = next((s for s in STYLES if s.id == style_id), None)
        if style is None:
            return None
        ink = np.asarray(render_mask(name, style, 256, 256)) < 128
        ys, xs = np.nonzero(ink)
        return xs.min() / 256, ys.min() / 256, (xs.max() + 1) / 256, (ys.max() + 1) / 256

    box = fractions(entry["name"], entry.get("style", ""))
    if box is None:
        return entry["quad_px"]
    tl, tr, br, bl = (np.asarray(p, dtype=float) for p in entry["quad_px"])

    def at(u: float, v: float) -> list[float]:
        top, bottom = tl + (tr - tl) * u, bl + (br - bl) * u
        return (top + (bottom - top) * v).tolist()

    x0, y0, x1, y1 = box
    return [at(x0, y0), at(x1, y0), at(x1, y1), at(x0, y1)]


def normalise_truth(truth: dict[str, Any]) -> tuple[dict[str, tuple[float, ...]], list[str], dict[str, str]]:
    """Return (present boxes by name, absent names, metadata) from either truth format."""
    if "present_symbols" in truth:
        present = {item["name"]: quad_box(glyph_quad(item)) for item in truth["present_symbols"]}
        absent = [name for name in truth["expected_symbols"] if name not in present]
        styles = sorted({item.get("style", "") for item in truth["present_symbols"]})
        meta = {
            "case": truth.get("case", ""),
            "condition": truth.get("condition", ""),
            "style": styles[0] if styles else "none",
        }
        meta["split"] = truth.get("split", "")
        return present, absent, meta
    present = {item["name"]: quad_box(item["quad_px"]) for item in truth["symbols"]}
    return present, [], {"case": "main", "condition": truth["condition"], "style": "outline", "split": "orig"}


def _prepare_one(job: tuple[str, str, str, bool]) -> str:
    """Straighten one image and cache it as an npz file (worker for the process pool)."""
    root, relative, cache_dir, straighten_it = job
    target = Path(cache_dir) / (relative.replace("/", "__") + ".npz")
    if target.exists():
        return relative
    with Image.open(Path(root) / relative) as photo:
        image = np.asarray(photo.convert("RGB"))
    corrected, inverse = straighten(image) if straighten_it else (image, None)
    target.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        target, corrected=corrected, inverse=np.zeros((3, 3)) if inverse is None else inverse,
        has_inverse=inverse is not None, size=np.array([image.shape[1], image.shape[0]]),
    )
    return relative


def load_dataset(root: Path, *, workers: int = 4) -> list[Item]:
    """Load (and cache the straightened form of) every image in a generated dataset."""
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    cache_dir = root / "_corrected"
    # Real photos (``"straighten": false`` in the manifest) are used as they are: no label boundary is assumed.
    flag = bool(manifest.get("straighten", True))
    jobs = [(str(root), entry["image"], str(cache_dir), flag) for entry in manifest["files"]]
    todo = [job for job in jobs if not (cache_dir / (job[1].replace("/", "__") + ".npz")).exists()]
    if todo:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            list(pool.map(_prepare_one, todo, chunksize=4))
    items = []
    for entry in manifest["files"]:
        data = np.load(cache_dir / (entry["image"].replace("/", "__") + ".npz"))
        truth = json.loads((root / entry["ground_truth"]).read_text(encoding="utf-8"))
        present, absent, meta = normalise_truth(truth)
        items.append(Item(
            key=entry["image"], corrected=data["corrected"],
            inverse=data["inverse"] if bool(data["has_inverse"]) else None,
            size=(int(data["size"][0]), int(data["size"][1])), present=present, absent=absent, meta=meta,
        ))
    return items


def run_detector(items: list[Item], detector: Detector) -> list[dict[str, Any]]:
    """Run a detector on every item and return one scored record per image."""
    return score_detections(items, [detector(item.corrected) for item in items])


def score_detections(items: list[Item], detections_per_item: list[list[SymbolDetection]]) -> list[dict[str, Any]]:
    """Score given detections (in straightened-label coordinates) against each item's truth."""
    from src.cv.extract import project_box

    records = []
    for item, detections in zip(items, detections_per_item, strict=True):
        projected = []
        for found in detections:
            box = found.bbox if item.inverse is None else project_box(found.bbox, item.inverse, item.size)
            projected.append((found.name, tuple(box), found.conf))
        matched = [
            name for name, box in item.present.items()
            if any(n == name and box_iou(b, box) >= 0.5 for n, b, _ in projected)
        ]
        false_positive = [n for n, _, _ in projected if n in item.absent]
        mislocated = [
            n for n, b, _ in projected
            if n in item.present and box_iou(b, item.present[n]) < 0.5
        ]
        records.append({
            "key": item.key, **item.meta, "expected": len(item.present), "matched": len(matched),
            "absent": len(item.absent), "false_positive": len(false_positive), "mislocated": len(mislocated),
            "detections": [{"name": n, "box": list(b), "conf": c} for n, b, c in projected],
        })
    return records


def tally(records: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[tuple[str, ...], dict[str, int]]:
    """Sum matched, expected, false-positive and absent counts per group of record fields."""
    table: dict[tuple[str, ...], dict[str, int]] = defaultdict(
        lambda: {"images": 0, "expected": 0, "matched": 0, "absent": 0, "false_positive": 0, "mislocated": 0}
    )
    for record in records:
        cell = table[tuple(record[key] for key in keys)]
        cell["images"] += 1
        for field in ("expected", "matched", "absent", "false_positive", "mislocated"):
            cell[field] += record[field]
    return dict(table)


def rate(successes: int, trials: int) -> str:
    """Format k/n with a Wilson 95% interval, or a dash when there are no trials."""
    if trials == 0:
        return "-"
    low, high = wilson_interval(successes, trials)
    return f"{successes}/{trials} ({100 * successes / trials:.1f}%; {100 * low:.1f} to {100 * high:.1f})"


def markdown_table(
    records: list[dict[str, Any]], keys: tuple[str, ...], *, order: dict[str, tuple[str, ...]] | None = None
) -> str:
    """Render recall and false-positive rates (Wilson 95% interval) per group as a markdown table."""
    table = tally(records, keys)

    def sort_key(group: tuple[str, ...]) -> tuple[int, ...]:
        out = []
        for key, value in zip(keys, group, strict=True):
            ranking = (order or {}).get(key, ())
            out.append(ranking.index(value) if value in ranking else len(ranking))
        return tuple(out) + (0,)

    lines = [
        "| " + " | ".join(keys) + " | images | recall | false positives |",
        "| " + " | ".join("---" for _ in keys) + " | ---: | --- | --- |",
    ]
    for group in sorted(table, key=lambda g: (sort_key(g), g)):
        cell = table[group]
        lines.append(
            "| " + " | ".join(group) + f" | {cell['images']} | {rate(cell['matched'], cell['expected'])}"
            f" | {rate(cell['false_positive'], cell['absent'])} |"
        )
    return "\n".join(lines)


def named_detector(name: str) -> Detector:
    """Return a detector by name (``v1_blind``, later ``v2``)."""
    if name == "v1_blind":
        from src.cv.symbols import detect_symbols_blind

        return detect_symbols_blind
    if name.startswith("v2"):
        from src.cv.symbols_v2 import get_detector

        return get_detector(name)
    raise ValueError(f"Unknown detector: {name}")


def main(argv: list[str] | None = None) -> int:
    """Evaluate one named detector on datasets and print or save a markdown table."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, nargs="+", required=True)
    parser.add_argument("--detector", default="v1_blind")
    parser.add_argument("--group", nargs="+", default=["case", "condition"])
    parser.add_argument("--records", type=Path, help="Write the scored records as JSON here")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args(argv)
    detector = named_detector(args.detector)
    records: list[dict[str, Any]] = []
    for root in args.dataset:
        items = load_dataset(root, workers=args.workers)
        for record in run_detector(items, detector):
            record["dataset"] = root.name
            records.append(record)
    if args.records:
        args.records.parent.mkdir(parents=True, exist_ok=True)
        args.records.write_text(json.dumps(records), encoding="utf-8")
    print(markdown_table(records, tuple(args.group), order={"condition": CONDITIONS}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
