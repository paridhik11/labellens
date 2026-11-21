"""Child process of the public photo scan: read every text line of one photo (OCR only), print JSON.

It runs in its own process so the parent can kill it at the time limit: native OCR calls cannot be interrupted
from inside. Usage: ``python -m src.api.public_scan_worker <image> <max_side> <budget_s> <search_side>``.
The last stdout line is a JSON object ``{"lines": [{"text", "confidence", "box"}], "complete": bool}``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

OCR_SHARE = 0.8  # the share of the budget that text reading may use (the same split as the CV4b extractor)


def read_all_lines(path: Path, max_side: int, budget_s: float, search_side: int | None) -> dict[str, Any]:
    """OCR the whole photo with the cv2 profile (RapidOCR plus Tesseract), shrunk to ``max_side`` pixels.

    No label detection and no field mapping: every line the readers find is returned in reading order.
    ``complete`` is False when the time budget stopped a reading step early.
    """
    import numpy as np
    from PIL import Image

    from src.cv.budget import Deadline
    from src.cv.photo_cv2 import read_cv2

    with Image.open(path) as photo:
        photo = photo.convert("RGB")
        if max(photo.size) > max_side:
            scale = max_side / max(photo.size)
            photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS)
        image = np.asarray(photo)
    deadline = Deadline(budget_s).stage(OCR_SHARE)
    reading = read_cv2(image, view="original", to_original=np.eye(3), second_engine=True, deadline=deadline,
                       search_side=search_side)
    blocks = sorted(reading.blocks, key=lambda b: (b.bbox[1], b.bbox[0]))
    lines = [{"text": b.text, "confidence": round(float(b.conf), 3), "box": [round(float(v), 1) for v in b.bbox]}
             for b in blocks if b.text.strip()]
    return {"lines": lines, "complete": bool(reading.complete)}


def main(argv: list[str]) -> int:
    """Read the arguments, run the reader and print one JSON line."""
    path, max_side, budget_s, search_side = Path(argv[1]), int(argv[2]), float(argv[3]), int(argv[4])
    out = read_all_lines(path, max_side, budget_s, search_side or None)
    sys.stdout.write("\n" + json.dumps(out) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
