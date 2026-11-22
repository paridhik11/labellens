"""Barcode reading for the NDC signal (zxing-cpp, the same library the device-label CV uses)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from src.ndc.codes import barcode_ndcs

MAX_SIDES = (2400, 1200)  # the photo is read at these long-side sizes (never enlarged), then the original


def read_payloads(path: Path) -> list[dict[str, Any]]:
    """Decode every barcode zxing-cpp finds (UPC-A, EAN-13, GS1 DataMatrix, Code 128, QR), fast and deterministic.

    Each item: ``{"payload", "format", "ndcs"}`` where ``ndcs`` are the 11-digit readings (empty for a barcode
    that is not an NDC barcode or whose check digit fails).
    """
    import zxingcpp

    formats = (zxingcpp.BarcodeFormat.UPCA | zxingcpp.BarcodeFormat.EAN13 | zxingcpp.BarcodeFormat.DataMatrix
               | zxingcpp.BarcodeFormat.Code128 | zxingcpp.BarcodeFormat.QRCode)
    with Image.open(path) as photo:
        gray = np.asarray(photo.convert("L"))
    found: dict[str, dict[str, Any]] = {}
    sizes = [None] + [s for s in MAX_SIDES if s < max(gray.shape)]
    for side in sizes:
        view = gray
        if side is not None:
            scale = side / max(gray.shape)
            view = np.asarray(Image.fromarray(gray).resize(
                (round(gray.shape[1] * scale), round(gray.shape[0] * scale)), Image.LANCZOS))
        for item in zxingcpp.read_barcodes(view, formats=formats, try_rotate=True, try_downscale=True):
            text = item.text
            if text and text not in found:
                found[text] = {"payload": text, "format": str(item.format).split(".")[-1],
                               "ndcs": barcode_ndcs(text)}
        if any(v["ndcs"] for v in found.values()):
            break
    return list(found.values())
