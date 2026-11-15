"""Template matching for the two simplified test-device pictograms only."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from src.common.schemas import SymbolDetection
from src.cv.preprocess import _validate_image

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = ROOT / "data" / "symbols" / "device"
TEMPLATE_PATH = ROOT / "src" / "gen" / "templates" / "test_device.json"
NAMES = ("manufacturer", "expiry")


def build_templates(output_dir: Path = REFERENCE_DIR) -> dict[str, Path]:
    """Recreate deterministic reference PNGs from the existing synthetic drawing code."""
    from src.gen.smoke_label import mm_to_px
    from src.gen.symbols import draw_symbol

    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for slot in template["slots"]:
        if slot["type"] != "symbol":
            continue
        width, height = map(mm_to_px, slot["bbox_mm"][2:])
        image = Image.new("L", (width, height), 255)
        draw_symbol(ImageDraw.Draw(image), slot["symbol_name"], (0, 0, width, height))
        path = output_dir / f"test_{slot['symbol_name']}.png"
        image.save(path)
        paths[slot["symbol_name"]] = path
    return paths


def detect_symbols(
    image: np.ndarray,
    *,
    reference_dir: Path = REFERENCE_DIR,
    threshold: float = 0.75,
    scales: tuple[float, ...] = (0.8, 0.9, 1.0, 1.1, 1.2),
) -> list[SymbolDetection]:
    """Match reference shapes near known slots in an upright, corrected RGB label.

    Return at most one match per symbol. Boxes use this image's x, y, width,
    height coordinates. Confidence is normalized correlation, not probability.
    References are synthetic drawings and have no certified ISO attribution.
    """
    _validate_image(image)
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("threshold must be finite and between zero and one")
    if not scales or any(not np.isfinite(scale) or scale <= 0 for scale in scales):
        raise ValueError("scales must contain positive finite values")
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    height, width = image.shape[:2]
    gray = cv2.GaussianBlur(cv2.cvtColor(image, cv2.COLOR_RGB2GRAY), (3, 3), 0)
    detections = []
    for slot in template["slots"]:
        if slot["type"] != "symbol":
            continue
        name = slot["symbol_name"]
        with Image.open(reference_dir / f"test_{name}.png") as reference:
            reference_pixels = np.asarray(reference.convert("L"))
        if reference_pixels.std() < 1e-6:
            raise ValueError(f"Reference must contain nonconstant artwork: {name}")
        x, y, w, h = slot["bbox_mm"]
        sx, sy = (width - 1) / template["size_mm"]["w"], (height - 1) / template["size_mm"]["h"]
        padding = round(max(w * sx, h * sy) * 0.35)
        left, top = max(0, round(x * sx) - padding), max(0, round(y * sy) - padding)
        right, bottom = min(width, round((x + w) * sx) + padding), min(height, round((y + h) * sy) + padding)
        region = gray[top:bottom, left:right]
        if region.size == 0 or region.std() < 1e-6:
            continue
        best = None
        for scale in scales:
            tw, th = round(w * sx * scale), round(h * sy * scale)
            if min(tw, th) < 3 or tw > region.shape[1] or th > region.shape[0]:
                continue
            resized = cv2.resize(reference_pixels, (tw, th), interpolation=cv2.INTER_LINEAR)
            resized = cv2.GaussianBlur(resized, (3, 3), 0)
            scores = cv2.matchTemplate(region, resized, cv2.TM_CCOEFF_NORMED)
            scores = np.nan_to_num(scores, nan=-1, posinf=-1, neginf=-1)
            _, score, _, position = cv2.minMaxLoc(scores)
            score = float(np.clip(score, -1, 1))
            if score >= threshold and (best is None or score > best.conf):
                best = SymbolDetection(
                    name=name,
                    iso_ref="",
                    conf=score,
                    bbox=(float(left + position[0]), float(top + position[1]), float(tw), float(th)),
                )
        if best is not None:
            detections.append(best)
    return detections


def _reference_images(reference_dir: Path, name: str) -> list[np.ndarray]:
    """Load every reference drawing of a symbol: ``test_<name>.png`` and ``test_<name>_*.png``."""
    paths = sorted({*reference_dir.glob(f"test_{name}.png"), *reference_dir.glob(f"test_{name}_*.png")})
    images = []
    for path in paths:
        with Image.open(path) as reference:
            pixels = np.asarray(reference.convert("L"))
        if pixels.std() < 1e-6:
            raise ValueError(f"Reference must contain nonconstant artwork: {path.name}")
        images.append(pixels)
    return images


def detect_symbols_blind(
    image: np.ndarray,
    *,
    reference_dir: Path = REFERENCE_DIR,
    threshold: float = 0.7,
    relative_sizes: tuple[float, ...] = tuple(float(value) for value in np.geomspace(0.06, 0.26, 14)),
    work_short_side: int = 480,
) -> list[SymbolDetection]:
    """Search the whole upright label for each reference symbol at many sizes.

    Unlike ``detect_symbols`` this uses no slot positions and no template
    size. ``relative_sizes`` are symbol heights as a share of the label's
    short side, so a symbol may be anywhere and between roughly a quarter and
    twice the size used in the test template. Matching runs on a copy scaled
    to ``work_short_side`` pixels for speed. At most one detection per symbol
    name is returned, and when two names claim overlapping boxes only the
    better one is kept. Confidence is normalized correlation, not probability.
    The symbol still has to look like one of the reference drawings.
    """
    _validate_image(image)
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("threshold must be finite and between zero and one")
    if not relative_sizes or any(not np.isfinite(size) or size <= 0 for size in relative_sizes):
        raise ValueError("relative_sizes must contain positive finite values")
    height, width = image.shape[:2]
    factor = work_short_side / min(height, width)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    interpolation = cv2.INTER_AREA if factor < 1 else cv2.INTER_CUBIC
    small = cv2.resize(gray, None, fx=factor, fy=factor, interpolation=interpolation)
    small = cv2.GaussianBlur(small, (3, 3), 0)
    best: dict[str, SymbolDetection] = {}
    for name in NAMES:
        for reference in _reference_images(reference_dir, name):
            aspect = reference.shape[1] / reference.shape[0]
            for size in relative_sizes:
                th = round(size * min(small.shape))
                tw = round(th * aspect)
                if min(tw, th) < 8 or tw >= small.shape[1] or th >= small.shape[0]:
                    continue
                resized = cv2.resize(reference, (tw, th), interpolation=cv2.INTER_AREA)
                resized = cv2.GaussianBlur(resized, (3, 3), 0)
                scores = np.nan_to_num(
                    cv2.matchTemplate(small, resized, cv2.TM_CCOEFF_NORMED), nan=-1, posinf=-1, neginf=-1
                )
                _, score, _, position = cv2.minMaxLoc(scores)
                score = float(np.clip(score, -1, 1))
                if score >= threshold and (name not in best or score > best[name].conf):
                    best[name] = SymbolDetection(
                        name=name,
                        iso_ref="",
                        conf=score,
                        bbox=(position[0] / factor, position[1] / factor, tw / factor, th / factor),
                    )
    detections = sorted(best.values(), key=lambda item: -item.conf)
    kept: list[SymbolDetection] = []
    for candidate in detections:
        x1, y1, w1, h1 = candidate.bbox
        overlaps = False
        for other in kept:
            x2, y2, w2, h2 = other.bbox
            inter = max(0.0, min(x1 + w1, x2 + w2) - max(x1, x2)) * max(0.0, min(y1 + h1, y2 + h2) - max(y1, y2))
            if inter / (w1 * h1 + w2 * h2 - inter) > 0.3:
                overlaps = True
        if not overlaps:
            kept.append(candidate)
    return sorted(kept, key=lambda item: NAMES.index(item.name))
