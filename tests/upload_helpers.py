"""Shared helpers for the upload tests: tiny valid image files and stub quality gates (no OpenCV needed)."""

from __future__ import annotations

import io
from pathlib import Path

from src.api.quality import QualityReport

PRODUCT = "prd_exampledevice"


def png_bytes(width: int = 120, height: int = 80, colour: tuple[int, int, int] = (200, 200, 200)) -> bytes:
    """A valid PNG file."""
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (width, height), colour).save(buffer, format="PNG")
    return buffer.getvalue()


def jpeg_bytes(width: int = 120, height: int = 80) -> bytes:
    """A valid JPEG file."""
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (120, 120, 120)).save(buffer, format="JPEG")
    return buffer.getvalue()


def pdf_bytes() -> bytes:
    """A minimal one-page PDF (enough for the signature check and, with pypdfium2, for rendering)."""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 100] >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def passing_gate(_: Path) -> QualityReport:
    """A gate that accepts every photo."""
    metrics = {"sharpness": 999.0, "contrast": 90.0, "glare_blob": 0.0, "glare_edge": 255.0}
    return QualityReport(ok=True, reasons=(), metrics=metrics)


def rejecting_gate(_: Path) -> QualityReport:
    """A gate that rejects every photo for glare."""
    metrics = {"sharpness": 999.0, "contrast": 90.0, "glare_blob": 0.08, "glare_edge": 30.0}
    return QualityReport(ok=False, reasons=("glare",), metrics=metrics)


def upload(client, data: bytes, headers: dict[str, str], *, name: str = "label.png", mime: str = "image/png",
           source: str = "upload", product_id: str | None = PRODUCT):
    """POST /scans with a multipart body. The filename and mime given here are what a client claims."""
    form = {"source": source}
    if product_id is not None:
        form["product_id"] = product_id
    return client.post("/scans", files={"file": (name, data, mime)}, data=form, headers=headers)
