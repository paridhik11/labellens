"""Decode barcodes and parse the four GS1 AIs used by synthetic device labels."""

from __future__ import annotations

import argparse
import json
import string
from datetime import date
from pathlib import Path

import numpy as np
import zxingcpp
from PIL import Image

from src.common.schemas import BarcodeResult
from src.cv.preprocess import _validate_image, find_label_corners, rectify_label

GROUP_SEPARATOR = "\x1d"
VARIABLE_CHARACTERS = frozenset(string.ascii_letters + string.digits + "!\"%&'()*+,-./:;<=>?_")


def _validate_field(ai: str, value: str) -> None:
    """Validate supported field syntax without checking identifier allocation."""
    if ai in {"01", "17"}:
        length = 14 if ai == "01" else 6
        if len(value) != length or not value.isascii() or not value.isdigit():
            raise ValueError(f"AI {ai} requires exactly {length} ASCII digits")
        if ai == "01":
            weighted = sum(int(digit) * (3 if index % 2 else 1) for index, digit in enumerate(reversed(value)))
            if weighted % 10:
                raise ValueError("AI 01 has an invalid check digit")
        else:
            try:
                date(2000 + int(value[:2]), int(value[2:4]), int(value[4:]))
            except ValueError as error:
                raise ValueError("AI 17 requires a real YYMMDD date with a specific day") from error
    elif not 1 <= len(value) <= 20 or any(character not in VARIABLE_CHARACTERS for character in value):
        raise ValueError(f"AI {ai} requires 1 to 20 GS1 character-set-82 characters")


def parse_gs1(payload: str) -> dict[str, str]:
    """Parse raw GS1 element data for AIs 01, 17, 10 and 21 without guessing.

    The input is zxing-cpp's decoded bytes represented as a string, without
    human-readable AI parentheses or a scanner symbology prefix. Variable
    fields end at ASCII GS or the end of input. AIs may occur in any order.
    Return only complete results; unsupported, duplicate or malformed fields
    raise ValueError. AI associations and identifier allocation are not checked.
    """
    if not isinstance(payload, str) or not payload:
        raise ValueError("GS1 payload must be a nonempty string")
    fields = {}
    offset = 0
    while offset < len(payload):
        ai = payload[offset:offset + 2]
        if ai not in {"01", "17", "10", "21"}:
            raise ValueError(f"Unsupported AI or misplaced separator at offset {offset}")
        if ai in fields:
            raise ValueError(f"Duplicate AI {ai}")
        offset += 2
        if ai in {"01", "17"}:
            end = offset + (14 if ai == "01" else 6)
        else:
            separator = payload.find(GROUP_SEPARATOR, offset)
            end = len(payload) if separator == -1 else separator
        value = payload[offset:end]
        _validate_field(ai, value)
        fields[ai] = value
        offset = end
        if offset < len(payload) and payload[offset] == GROUP_SEPARATOR:
            offset += 1
    return fields


def decode_barcodes(image: np.ndarray) -> tuple[list[BarcodeResult], list[str]]:
    """Decode an RGB image into shared schema objects and explicit warnings.

    Raw bytes are preserved with a reversible Latin-1 string mapping. Parse
    only symbols marked GS1 by zxing-cpp. Boxes use x, y, width, height in the
    supplied image's coordinate space. Decode engine exceptions propagate.
    """
    _validate_image(image)
    decoded = zxingcpp.read_barcodes(image)
    if not decoded:
        return [], ["BARCODE_NOT_DECODED: no barcode could be decoded"]
    results = []
    warnings = []
    height, width = image.shape[:2]
    for item in decoded:
        raw = item.bytes.decode("latin-1")
        parsed = {}
        if item.content_type == zxingcpp.ContentType.GS1:
            try:
                parsed = parse_gs1(raw)
            except ValueError as error:
                warnings.append(f"GS1_PARSE_FAILED: {error}")
        else:
            warnings.append("NON_GS1_BARCODE: raw data retained without GS1 parsing")
        corners = [
            item.position.top_left, item.position.top_right,
            item.position.bottom_right, item.position.bottom_left,
        ]
        points = np.array([[point.x, point.y] for point in corners], dtype=float)
        left, top = points.min(axis=0)
        right, bottom = points.max(axis=0)
        bbox = None
        if np.isfinite(points).all() and 0 <= left < right <= width and 0 <= top < bottom <= height:
            bbox = (float(left), float(top), float(right - left), float(bottom - top))
        else:
            warnings.append("BARCODE_POSITION_INVALID: raw data retained without a bounding box")
        results.append(BarcodeResult(type=str(item.format), raw=raw, parsed=parsed, bbox=bbox))
    return results, warnings


def evaluate_dataset(dataset_dir: Path, rectify: bool = False) -> dict[str, dict[str, int]]:
    """Measure decode and exact four-AI matches per generated condition.

    The decoder receives only pixels. Ground truth is used only to compare
    results. Every image stays in its denominator, including decode failures.
    """
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    results = {
        condition: {
            "images": 0, "decoded_images": 0, "matching_ai_images": 0,
            "parse_warning_images": 0, "correction_failures": 0,
        }
        for condition in ("clean", "moderate", "hard")
    }
    for entry in manifest["files"]:
        truth = json.loads((dataset_dir / entry["ground_truth"]).read_text(encoding="utf-8"))
        counts = results[truth["condition"]]
        counts["images"] += 1
        with Image.open(dataset_dir / entry["image"]) as photo:
            image = np.asarray(photo.convert("RGB"))
        if rectify:
            corners = find_label_corners(image)
            if corners is None:
                counts["correction_failures"] += 1
                continue
            image, _ = rectify_label(image, corners)
        barcodes, warnings = decode_barcodes(image)
        counts["decoded_images"] += int(bool(barcodes))
        counts["matching_ai_images"] += int(len(barcodes) == 1 and barcodes[0].parsed == truth["barcode_ais"])
        counts["parse_warning_images"] += int(any(warning.startswith("GS1_PARSE_FAILED:") for warning in warnings))
    return results


def main(argv: list[str] | None = None) -> int:
    """Decode one image or print per-condition barcode measurements for a set."""
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--image", type=Path)
    inputs.add_argument("--dataset", type=Path)
    parser.add_argument("--rectify", action="store_true", help="Detect and straighten labels before decoding")
    args = parser.parse_args(argv)
    try:
        if args.dataset is not None:
            results = evaluate_dataset(args.dataset, rectify=args.rectify)
            print(f"Barcode evaluation: {'corrected images' if args.rectify else 'original images'}")
            for condition, counts in results.items():
                total = counts["images"]
                print(
                    f"{condition}: decoded={counts['decoded_images']}/{total}, "
                    f"all_ais_match={counts['matching_ai_images']}/{total}, "
                    f"parse_warning_images={counts['parse_warning_images']}, "
                    f"correction_failures={counts['correction_failures']}"
                )
            return 0
        with Image.open(args.image) as photo:
            image = np.asarray(photo.convert("RGB"))
        if args.rectify:
            corners = find_label_corners(image)
            if corners is None:
                parser.error("NEEDS_HUMAN_REVIEW: no suitable label boundary")
            image, _ = rectify_label(image, corners)
        barcodes, warnings = decode_barcodes(image)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    coordinate_space = "corrected_image" if args.rectify else "input_image"
    print(f"Coordinates: {coordinate_space}; size={image.shape[1]}x{image.shape[0]}")
    print(json.dumps({"barcodes": [item.model_dump() for item in barcodes], "warnings": warnings}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
