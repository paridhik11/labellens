"""Immutable export descriptions in millimetres, measured from the top left."""

from __future__ import annotations

import base64
import hashlib
import json
import math
import re
import warnings
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from typing import Literal

import numpy as np
import zxingcpp
from PIL import Image
from reportlab.pdfbase.pdfmetrics import getAscentDescent, standardFonts, stringWidth

from src.common.schemas import IdentifierRequired
from src.gen.gs1 import parse_gs1

MM_TO_PT = 72 / 25.4
DRAFT_BAND_MM = 9.0


@dataclass(frozen=True)
class Element:
    """One named field with a physical bounding box and explicit content.

    Matrix rows contain 0 for white and 1 for black, including quiet zones.
    module_mm is an exact square-module size, never a request to stretch bars.
    Image content is embedded PNG bytes, so later file edits cannot change it.
    """

    field: str
    kind: Literal["text", "image", "barcode", "symbol"]
    bbox_mm: tuple[float, float, float, float]
    slot_id: str = ""
    text: str = ""
    font: str = "Helvetica"
    size_pt: float = 9
    align: str = "left"
    max_lines: int = 1
    symbol_name: str = ""
    png: bytes = b""
    matrix: tuple[str, ...] = ()
    module_mm: float = 0.3
    payload: str = ""
    symbology: str = ""


@dataclass(frozen=True)
class Label:
    """Internal label snapshot; every edit requires a new version_id.

    The canonical reference bytes include all content, identity and audit data.
    Their SHA-256 binds export approval to this exact immutable description.
    """

    width_mm: float
    height_mm: float
    elements: tuple[Element, ...]
    version_id: str
    created_by: str
    reason: str
    template_id: str = "internal"
    template_version: int = 1
    test_data: bool = False
    review_boxes: tuple[tuple[float, float, float, float], ...] = ()


@dataclass(frozen=True)
class ApprovalRecord:
    """An externally supplied reviewer decision, never created by export."""

    reviewer: str
    version_id: str
    reference_sha256: str
    check_id: str
    decision: str = "approve"


@dataclass(frozen=True)
class PassedCheck:
    """Externally supplied check result for the same version and reference."""

    check_id: str
    version_id: str
    reference_sha256: str
    passed: bool


@dataclass(frozen=True)
class Primitive:
    """A measured rectangle, line, text baseline or PNG shared by both writers."""

    kind: str
    x: float
    y: float
    w: float = 0
    h: float = 0
    text: str = ""
    font: str = "Helvetica"
    size_pt: float = 9
    png: bytes = b""


class ModuleSizeWarning(UserWarning):
    """The requested barcode X-dimension is below a caller-selected minimum."""


def reference_sha256(label: Label) -> str:
    """Hash the canonical snapshot, including image bytes and exact module sizes."""
    content = json.dumps(
        asdict(label),
        sort_keys=True,
        separators=(",", ":"),
        default=lambda value: base64.b64encode(value).decode("ascii"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def validate_approval(
    label: Label,
    approval: ApprovalRecord | None,
    check: PassedCheck | None,
    authorized_reviewers: frozenset[str],
) -> bool:
    """Allow watermark removal only for a matching authorized approval and check.

    Caller supplies reviewer authorization and check provenance from trusted
    application storage. This local exporter is not an authentication service.
    """
    if approval is None:
        return False
    fingerprint = reference_sha256(label)
    if (
        approval.decision != "approve"
        or not approval.check_id
        or approval.reviewer not in authorized_reviewers
        or approval.reviewer == label.created_by
        or approval.version_id != label.version_id
        or approval.reference_sha256 != fingerprint
        or check is None
        or check.passed is not True
        or check.check_id != approval.check_id
        or check.version_id != label.version_id
        or check.reference_sha256 != fingerprint
    ):
        raise PermissionError("Approval needs an authorized independent reviewer and matching passed check_id")
    return True


def text_lines(element: Element) -> list[str]:
    """Wrap at word boundaries using the same font metrics used in the PDF."""
    width = element.bbox_mm[2] * MM_TO_PT
    lines: list[str] = []
    for paragraph in element.text.split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}" if current else word
            if current and stringWidth(candidate, element.font, element.size_pt) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return lines


def validate_label(label: Label, min_module_mm: float = 0.25) -> None:
    """Reject clipping, overlap, invalid content and overflow before writing.

    The 9 mm draft band and default minimum X-dimension are project defaults,
    not regulatory limits. A small module emits the explicitly requested warning.
    """
    if not all(math.isfinite(v) and v > 0 for v in (label.width_mm, label.height_mm, min_module_mm)):
        raise ValueError("Dimensions and minimum module size must be finite and positive")
    if not label.elements or not all((label.version_id, label.created_by, label.reason, label.template_id)):
        raise ValueError("Elements, version, creator, reason and template identity are required")
    if isinstance(label.template_version, bool) or label.template_version < 1:
        raise ValueError("Template version must be a positive integer")
    if label.height_mm <= DRAFT_BAND_MM or label.width_mm < 35:
        raise ValueError("Label must have room for the mandatory DRAFT heading")
    ids: set[str] = {"layer-background", "layer-slots", "layer-watermark", "layer-review"}
    field_ids = [element.field for element in label.elements]
    slot_ids = [f"slot-{element.slot_id or element.field}" for element in label.elements]
    all_ids = list(ids) + list(dict.fromkeys(field_ids)) + slot_ids
    if len(all_ids) != len(set(all_ids)) or any(
        not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", field) for field in field_ids
    ):
        raise ValueError("Field and layer IDs must be unique valid SVG names")
    ids = set()
    for element in label.elements:
        identity = element.slot_id or element.field
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", identity) or identity in ids or not element.field:
            raise ValueError("Slot IDs must be unique SVG names and field names must be nonempty")
        ids.add(identity)
        x, y, w, h = element.bbox_mm
        if not all(math.isfinite(v) for v in (x, y, w, h)) or min(w, h) <= 0:
            raise ValueError(f"Invalid physical bounds: {identity}")
        if x < 0 or y < DRAFT_BAND_MM or x + w > label.width_mm or y + h > label.height_mm:
            raise ValueError(f"clipping or watermark_overlap: {identity}")
        if element.kind == "text":
            if element.font not in standardFonts or not math.isfinite(element.size_pt) or element.size_pt < 6:
                raise ValueError("Use a standard PDF font and size at least 6 pt")
            if not element.text.strip() or any(ord(c) > 126 or (ord(c) < 32 and c != "\n") for c in element.text):
                raise ValueError("Text must contain printable ASCII with optional newlines")
            if element.align not in {"left", "center", "right"}:
                raise ValueError("Unsupported text alignment")
            lines = text_lines(element)
            ascent, descent = getAscentDescent(element.font, element.size_pt)
            required_height = (ascent - descent + (len(lines) - 1) * element.size_pt * 1.2) / MM_TO_PT
            if (
                len(lines) > element.max_lines
                or required_height > h
                or any(stringWidth(line, element.font, element.size_pt) > w * MM_TO_PT for line in lines)
            ):
                raise ValueError(f"text_overflow: {identity}")
        elif element.kind == "image":
            with Image.open(BytesIO(element.png)) as image:
                if image.format != "PNG":
                    raise ValueError("Only embedded PNG images are supported")
                image.verify()
        elif element.kind == "barcode":
            if not element.matrix or len({len(row) for row in element.matrix}) != 1:
                raise ValueError("Barcode matrix must be a nonempty rectangle")
            if not element.matrix[0] or any(set(row) - {"0", "1"} for row in element.matrix):
                raise ValueError("Barcode matrix requires binary rows")
            if not math.isfinite(element.module_mm) or element.module_mm <= 0:
                raise ValueError("Barcode module size must be finite and positive")
            if (
                len(element.matrix[0]) * element.module_mm > w + 1e-9
                or len(element.matrix) * element.module_mm > h + 1e-9
            ):
                raise ValueError("Barcode cannot fit at the exact requested module size")
            if element.module_mm < min_module_mm:
                warnings.warn(
                    f"{identity}: module {element.module_mm:g} mm below {min_module_mm:g} mm",
                    ModuleSizeWarning,
                    stacklevel=2,
                )
            pixels = np.array([[0 if bit == "1" else 255 for bit in row] for row in element.matrix], dtype=np.uint8)
            decoded = zxingcpp.read_barcodes(np.repeat(np.repeat(pixels, 4, axis=0), 4, axis=1))
            if len(decoded) != 1 or decoded[0].text != element.payload or str(decoded[0].format) != element.symbology:
                raise ValueError("Barcode matrix does not decode to the supplied payload and symbology")
            if decoded[0].content_type == zxingcpp.ContentType.GS1:
                values = parse_gs1(decoded[0].bytes.decode("latin-1"))
                if values.get("01") == "00000000000000" and not label.test_data:
                    raise IdentifierRequired("Test-only GTIN requires a visibly marked test label")
            border = [pixels[:, 0], pixels[:, -1]]
            if element.symbology != "Code 128":
                border.extend([pixels[0], pixels[-1]])
            if any(np.any(edge != 255) for edge in border):
                raise ValueError("Barcode quiet zone is missing")
        elif element.kind == "symbol":
            if element.symbol_name not in {"manufacturer", "expiry", "sterile", "sterile_eo"} or min(w, h) < 5:
                raise ValueError("Unsupported symbol or symbol below 5 mm project minimum")
        else:
            raise ValueError(f"Unsupported element kind: {element.kind}")
    for index, element in enumerate(label.elements):
        x, y, w, h = element.bbox_mm
        for other in label.elements[index + 1 :]:
            ox, oy, ow, oh = other.bbox_mm
            if min(x + w, ox + ow) > max(x, ox) and min(y + h, oy + oh) > max(y, oy):
                raise ValueError(f"overlap: {element.field}, {other.field}")


def primitives(element: Element) -> list[Primitive]:
    """Map validated elements into vector/text/image operations without scaling bars."""
    x, y, w, h = element.bbox_mm
    if element.kind == "image":
        return [Primitive("image", x, y, w, h, png=element.png)]
    if element.kind == "text":
        ascent, _ = getAscentDescent(element.font, element.size_pt)
        result = []
        for index, line in enumerate(text_lines(element)):
            remaining = w - stringWidth(line, element.font, element.size_pt) / MM_TO_PT
            offset = {"left": 0, "center": remaining / 2, "right": remaining}[element.align]
            baseline = y + (ascent + index * element.size_pt * 1.2) / MM_TO_PT
            result.append(
                Primitive("text", x + offset, baseline, text=line, font=element.font, size_pt=element.size_pt)
            )
        return result
    if element.kind == "barcode":
        module = element.module_mm
        left = x + (w - len(element.matrix[0]) * module) / 2
        top = y + (h - len(element.matrix) * module) / 2
        result = []
        for row, bits in enumerate(element.matrix):
            for run in re.finditer("1+", bits):
                result.append(
                    Primitive(
                        "rect", left + run.start() * module, top + row * module, len(run.group()) * module, module
                    )
                )
        return result
    # Simplified synthetic symbol artwork, not licensed or certified ISO artwork.
    if element.symbol_name.startswith("sterile"):
        label = "STERILE EO" if element.symbol_name == "sterile_eo" else "STERILE"
        size = min(8, w * MM_TO_PT / stringWidth(label, "Helvetica", 1) * 0.8)
        return [
            Primitive("outline", x + 0.05 * w, y + 0.15 * h, 0.9 * w, 0.7 * h),
            Primitive("text", x + 0.1 * w, y + 0.55 * h, text=label, size_pt=size),
        ]
    if element.symbol_name == "manufacturer":
        points = [
            (0.1, 0.9),
            (0.1, 0.45),
            (0.35, 0.3),
            (0.35, 0.45),
            (0.6, 0.3),
            (0.6, 0.55),
            (0.75, 0.55),
            (0.75, 0.1),
            (0.9, 0.1),
            (0.9, 0.9),
            (0.1, 0.9),
        ]
    else:
        points = [(0.15, 0.1), (0.85, 0.1), (0.15, 0.9), (0.85, 0.9), (0.15, 0.1)]
    return [
        Primitive("line", x + a * w, y + b * h, (c - a) * w, (d - b) * h)
        for (a, b), (c, d) in zip(points, points[1:], strict=False)
    ]


def write_artifact(path: Path, content: bytes, label: Label, approved: bool, check_id: str = "") -> Path:
    """Save immutable artwork and its change log, hash and scoped self-check record."""
    path = Path(path)
    audit_path = path.with_suffix(path.suffix + ".json")
    if path.exists() or audit_path.exists():
        raise FileExistsError("Export files are immutable; choose a new version/output path")
    audit = {
        "version_id": label.version_id,
        "reference_sha256": reference_sha256(label),
        "artifact_sha256": hashlib.sha256(content).hexdigest(),
        "status": "APPROVED" if approved else "DRAFT",
        "test_data": label.test_data,
        "check_id": check_id,
        "change_log": [
            {
                "actor": label.created_by,
                "reason": label.reason,
                "action": "export",
                "fields": [element.field for element in label.elements],
            }
        ],
        "self_check": {
            "passed": True,
            "scope": "layout, text metrics and source barcode decode; no OCR or compliance check",
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as output:
        output.write(content)
    try:
        with audit_path.open("x", encoding="utf-8") as output:
            output.write(json.dumps(audit, indent=2) + "\n")
    except Exception:
        path.unlink()
        raise
    return path
