"""PNG and SVG QR codes for caller-supplied version and verification payloads."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import numpy as np
import zxingcpp
from PIL import Image


@dataclass(frozen=True)
class QRCode:
    """QR artwork bytes and the unchanged caller payload."""

    payload: str
    png: bytes
    svg: str


def make_qr(payload: str, *, scale: int = 5) -> QRCode:
    """Generate QR artwork, then decode-check its exact text before returning."""
    if not isinstance(payload, str) or not payload.strip():
        raise ValueError("QR payload must be a nonempty string")
    if isinstance(scale, bool) or not isinstance(scale, int) or scale < 1:
        raise ValueError("QR scale must be a positive integer")
    code = zxingcpp.create_barcode(payload, zxingcpp.BarcodeFormat.QRCode, ec_level="M")
    pixels = np.asarray(code.to_image(scale=scale, add_quiet_zones=True))
    decoded = zxingcpp.read_barcodes(pixels)
    if len(decoded) != 1 or decoded[0].format != zxingcpp.BarcodeFormat.QRCode or decoded[0].text != payload:
        raise RuntimeError("QR decode-back check failed")
    output = BytesIO()
    Image.fromarray(pixels).save(output, format="PNG")
    return QRCode(payload, output.getvalue(), code.to_svg(scale=scale, add_quiet_zones=True))
