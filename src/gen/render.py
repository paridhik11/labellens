"""Deterministic draft SVG/PDF rendering for the supported test-device template."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass, replace
from datetime import date
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from xml.etree import ElementTree as ET

import numpy as np
import zxingcpp
from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
from reportlab.lib.colors import black, white
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import getRegisteredFontNames, standardFonts, stringWidth
from reportlab.pdfgen.canvas import Canvas

from src.common.schemas import Flag, IdentifierRequired, ProductRecord
from src.cv.barcode import parse_gs1


@dataclass
class RenderResult:
    """Local draft artifacts and their audit/self-check state; never publication approval."""

    svg: str
    pdf: str
    preview: str
    manifest: str
    barcode_action: str
    change_log: list[dict[str, Any]]
    self_check: dict[str, Any]
    status: str = "DRAFT"


class LayoutError(ValueError):
    """A proposed layout has critical flags and cannot produce artwork safely."""

    def __init__(self, flags: list[Flag]) -> None:
        """Retain structured layout findings for the caller's review UI."""
        self.flags = flags
        super().__init__("; ".join(flag.message for flag in flags))


def wrap_text(text: str, font: str, size: float, width: float) -> list[str]:
    """Wrap explicit lines at word boundaries using actual PDF font measurements."""
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split(" "):
            candidate = f"{current} {word}" if current else word
            if current and stringWidth(candidate, font, size) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return lines


def check_layout(template: dict[str, Any], fields: dict[str, str], matrix: np.ndarray) -> list[Flag]:
    """Return layout flags using lab minimums, not regulatory compliance claims."""
    flags = []

    def flag(kind: str, message: str) -> None:
        """Append a uniquely identified critical layout finding."""
        flags.append(Flag(flag_id=f"layout_{len(flags) + 1}", kind=kind, severity="critical", message=message))

    size = template["size_mm"]
    if not np.isfinite([size["w"], size["h"]]).all() or min(size.values()) <= 0:
        flag("invalid_size", "Physical dimensions must be finite and positive")
    if template.get("background"):
        flag("unsupported_background", "This renderer requires the supported blank-background template")
    boxes = []
    for slot in template["slots"]:
        x, y, w, h = slot["bbox_mm"]
        name = slot["id"]
        if not np.isfinite([x, y, w, h]).all() or min(w, h) <= 0:
            flag("invalid_box", f"Invalid slot bounds: {name}")
            continue
        if x < 0 or y < 0 or x + w > size["w"] or y + h > size["h"]:
            flag("clipping", f"Slot outside label: {name}")
        boxes.append((name, x, y, w, h))
        if slot["type"] == "text":
            text = fields.get(slot["field"], "")
            font, point_size = slot.get("font", "Helvetica"), slot["size_pt"]
            if not text.strip():
                flag("required_field", f"Required field empty: {slot['field']}")
            if any(ord(character) > 126 or (ord(character) < 32 and character != "\n") for character in text):
                flag("unsupported_characters", f"Only printable ASCII text is supported: {name}")
            if font not in {*standardFonts, *getRegisteredFontNames()}:
                flag("unavailable_font", f"Unavailable font: {font}")
                continue
            if not np.isfinite(point_size) or point_size < 6:
                flag("font_size", f"Font below lab minimum of 6 pt: {name}")
                continue
            lines = wrap_text(text, font, point_size, w * mm)
            if len(lines) > slot.get("max_lines", 1) or len(lines) * point_size * 1.2 > h * mm:
                flag("text_overflow", f"Too many lines or excessive text height: {name}")
            if any(stringWidth(line, font, point_size) > w * mm for line in lines):
                flag("text_overflow", f"Text exceeds slot width: {name}")
        elif slot["type"] == "symbol":
            if slot.get("symbol_name") not in {"manufacturer", "expiry"} or min(w, h) < 5:
                flag("symbol_size_or_type", f"Unsupported symbol or below lab minimum of 5 mm: {name}")
        elif slot["type"] == "barcode":
            module_mm = min(w / matrix.shape[1], h / matrix.shape[0])
            if module_mm < 0.25:
                flag("barcode_size", f"Barcode modules below lab minimum of 0.25 mm: {name}")
            edges = (
                (matrix[:, 0], matrix[:, -1])
                if slot.get("symbology") == "GS1-128"
                else (matrix[0], matrix[-1], matrix[:, 0], matrix[:, -1])
            )
            if not all(np.all(edge == 255) for edge in edges):
                flag("barcode_quiet_zone", f"Barcode lacks a white quiet border: {name}")
        else:
            flag("unsupported_slot", f"Unsupported slot type: {slot['type']}")
    for index, (name, x, y, w, h) in enumerate(boxes):
        if y < 9:
            flag("watermark_overlap", f"Slot overlaps the reserved DRAFT heading: {name}")
        for other, ox, oy, ow, oh in boxes[index + 1 :]:
            if min(x + w, ox + ow) > max(x, ox) and min(y + h, oy + oh) > max(y, oy):
                flag("overlap", f"Overlapping slots: {name}, {other}")
    return flags


def record_content(record: ProductRecord, test_data: bool) -> tuple[dict[str, str], dict[str, str]]:
    """Use only supplied identifiers and derive matching printed and GS1 values."""
    if not record.udi_di or (record.udi_di == "00000000000000" and not test_data):
        raise IdentifierRequired(
            "Enter an allocated identifier, or explicitly use the existing test placeholder in test mode"
        )
    parse_gs1("01" + record.udi_di)
    if any(not isinstance(record.extra.get(key), str) or not record.extra[key] for key in ("expiry", "lot", "serial")):
        raise ValueError("Record requires nonempty expiry, lot and serial values")
    expiry = date.fromisoformat(record.extra["expiry"])
    if not 2000 <= expiry.year <= 2099:
        raise ValueError("Expiry must be in the supported 2000-2099 range")
    ais = {
        "01": record.udi_di,
        "17": expiry.strftime("%y%m%d"),
        "10": record.extra["lot"],
        "21": record.extra["serial"],
    }
    parse_gs1(f"01{ais['01']}17{ais['17']}10{ais['10']}\x1d21{ais['21']}")
    fields = {
        "product_name": record.name,
        "manufacturer": record.manufacturer,
        "manufacturer_address": record.manufacturer_address,
        "model": f"REF: {record.model}",
        "lot": f"LOT: {ais['10']}",
        "expiry": f"EXP: {expiry.isoformat()}",
    }
    return fields, ais


def _draw_symbol(drawing: Drawing, name: str, box: tuple[float, float, float, float]) -> None:
    """Draw the existing simplified pictograms as editable vector lines."""
    x, y, w, h = box
    stroke = min(w, h) * 0.05
    if name == "manufacturer":
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
        drawing.add(
            PolyLine(
                [coordinate for u, v in points for coordinate in (x + u * w, y + (1 - v) * h)],
                strokeColor=black,
                strokeWidth=stroke,
            )
        )
        for u in (0.25, 0.45, 0.65):
            drawing.add(Rect(x + u * w, y + 0.12 * h, 0.08 * w, 0.2 * h, fillColor=black, strokeColor=None))
    else:
        for points in [(0.15, 0.1, 0.85, 0.1), (0.15, 0.9, 0.85, 0.9), (0.15, 0.1, 0.85, 0.9), (0.85, 0.1, 0.15, 0.9)]:
            u, v, a, b = points
            drawing.add(
                Line(x + u * w, y + (1 - v) * h, x + a * w, y + (1 - b) * h, strokeColor=black, strokeWidth=stroke)
            )


def _render_package(
    template_spec: dict[str, Any],
    record: ProductRecord,
    output_dir: Path,
    *,
    actor: str,
    reason: str,
    test_data: bool = False,
    previous_manifest: dict[str, Any] | None = None,
    confirmed_encoded_change: bool = False,
) -> RenderResult:
    """Write an immutable DRAFT SVG, physical-size PDF, preview and audited manifest.

    Supports the current template family and explicit GS1 DataMatrix/GS1-128
    setup. A previous unchanged barcode reuses its exact module matrix. Changed
    encoded data requires confirmation. This API cannot approve or publish.
    """
    if not actor.strip() or not reason.strip() or not record.product_id or record.version < 1:
        raise ValueError("Actor, reason, product ID and a positive record version are required")
    fields, ais = record_content(record, test_data)
    slots = [slot for slot in template_spec["slots"] if slot["type"] == "barcode"]
    if len(slots) != 1:
        raise ValueError("Exactly one barcode slot is supported")
    symbology = slots[0]["symbology"]
    if symbology not in {"GS1_DataMatrix", "GS1-128"}:
        raise ValueError("Unsupported GS1 symbology")
    format_ = zxingcpp.BarcodeFormat.DataMatrix if symbology == "GS1_DataMatrix" else zxingcpp.BarcodeFormat.Code128
    reused = False
    if previous_manifest is not None:
        if (
            record.product_id != previous_manifest["product_id"]
            or record.version <= previous_manifest["record_version"]
        ):
            raise ValueError("A revision requires the same product and a greater version")
        if (template_spec["template_id"], template_spec["version"]) != (
            previous_manifest["template_id"],
            previous_manifest["template_version"],
        ):
            raise ValueError("Template migration is outside this renderer's current scope")
        reused = ais == previous_manifest["barcode_ais"] and symbology == previous_manifest["symbology"]
        if not reused and not confirmed_encoded_change:
            raise ValueError("Encoded barcode changes require explicit confirmation")
    if reused:
        rows = previous_manifest["barcode_matrix"]
        if not rows or len({len(row) for row in rows}) != 1 or any(set(row) - {"0", "1"} for row in rows):
            raise ValueError("Invalid previous barcode matrix")
        matrix = np.array([[0 if bit == "1" else 255 for bit in row] for row in rows], dtype=np.uint8)
    else:
        payload = "".join(f"[{key}]{value}" for key, value in ais.items())
        format_ = zxingcpp.BarcodeFormat.DataMatrix if symbology == "GS1_DataMatrix" else zxingcpp.BarcodeFormat.Code128
        code = zxingcpp.create_barcode(payload, format_, gs1=True, force_square=symbology == "GS1_DataMatrix")
        matrix = np.asarray(zxingcpp.write_barcode_to_image(code, scale=1, add_quiet_zones=True))
    decoded = zxingcpp.read_barcodes(np.repeat(np.repeat(matrix, 4, axis=0), 4, axis=1))
    if (len(decoded) != 1 or decoded[0].content_type != zxingcpp.ContentType.GS1
            or decoded[0].format != format_ or parse_gs1(decoded[0].bytes.decode("latin-1")) != ais):
        raise ValueError("Barcode matrix does not decode to the supplied values")
    flags = check_layout(template_spec, fields, matrix)
    if flags:
        raise LayoutError(flags)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError("Draft output directory is not empty; revisions must be immutable")
    executable = shutil.which("pdftoppm")
    if executable is None:
        raise RuntimeError("Poppler pdftoppm is required for the PDF preview and self-check")
    output_dir.mkdir(parents=True, exist_ok=True)
    width, height = template_spec["size_mm"]["w"] * mm, template_spec["size_mm"]["h"] * mm
    drawing = Drawing(width, height)
    drawing.add(
        Rect(
            0.2 * mm,
            0.2 * mm,
            width - 0.4 * mm,
            height - 0.4 * mm,
            fillColor=white,
            strokeColor=black,
            strokeWidth=0.25 * mm,
        )
    )
    drawing.add(
        String(
            5 * mm,
            height - 3 * mm - 10,
            "TEST DATA | DRAFT" if test_data else "DRAFT",
            fontName="Helvetica",
            fontSize=10,
            fillColor=black,
        )
    )
    for slot in template_spec["slots"]:
        x, top, w, h = [value * mm for value in slot["bbox_mm"]]
        y = height - top - h
        if slot["type"] == "text":
            font, point_size = slot.get("font", "Helvetica"), slot["size_pt"]
            for index, line in enumerate(wrap_text(fields[slot["field"]], font, point_size, w)):
                drawing.add(
                    String(
                        x,
                        height - top - point_size - index * point_size * 1.2,
                        line,
                        fontName=font,
                        fontSize=point_size,
                        fillColor=black,
                    )
                )
        elif slot["type"] == "symbol":
            _draw_symbol(drawing, slot["symbol_name"], (x, y, w, h))
        else:
            module = min(w / matrix.shape[1], h / matrix.shape[0])
            bx, by = x + (w - matrix.shape[1] * module) / 2, y + (h - matrix.shape[0] * module) / 2
            for row, values in enumerate(matrix):
                for column in np.flatnonzero(values == 0):
                    drawing.add(
                        Rect(
                            bx + column * module,
                            by + (matrix.shape[0] - 1 - row) * module,
                            module,
                            module,
                            fillColor=black,
                            strokeColor=None,
                        )
                    )
    svg_path, pdf_path = output_dir / "label.svg", output_dir / "label.pdf"
    root = ET.fromstring(renderSVG.drawToString(drawing))
    root.set("width", f"{template_spec['size_mm']['w']}mm")
    root.set("height", f"{template_spec['size_mm']['h']}mm")
    svg_path.write_text(ET.tostring(root, encoding="unicode"), encoding="utf-8")
    buffer = BytesIO()
    canvas = Canvas(buffer, pagesize=(width, height), invariant=1)
    renderPDF.draw(drawing, canvas, 0, 0)
    canvas.showPage()
    canvas.save()
    pdf_path.write_bytes(buffer.getvalue())
    subprocess.run(
        [executable, "-singlefile", "-png", "-r", "300", str(pdf_path), str(output_dir / "label")],
        check=True,
        capture_output=True,
    )
    preview = output_dir / "label.png"
    previous_fields = previous_manifest["fields"] if previous_manifest else {}
    changes = [
        {"field": field, "before": previous_fields.get(field), "after": value, "actor": actor, "reason": reason}
        for field, value in fields.items()
        if previous_fields.get(field) != value
    ]
    changes.append({"action": "barcode_reused" if reused else "barcode_generated", "actor": actor, "reason": reason})
    manifest = {
        "status": "DRAFT",
        "test_data": test_data,
        "product_id": record.product_id,
        "record_version": record.version,
        "template_id": template_spec["template_id"],
        "template_version": template_spec["version"],
        "size_mm": template_spec["size_mm"],
        "fields": fields,
        "barcode_ais": ais,
        "symbology": symbology,
        "barcode_matrix": ["".join("1" if pixel == 0 else "0" for pixel in row) for row in matrix],
        "symbols": [slot["symbol_name"] for slot in template_spec["slots"] if slot["type"] == "symbol"],
        "barcode_action": "reused" if reused else "generated",
        "change_log": changes,
        "layout_flags": [],
        "artifacts": {"svg": "label.svg", "pdf": "label.pdf", "preview": "label.png"},
        "artifact_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in (("svg", svg_path), ("pdf", pdf_path), ("preview", preview))
        },
    }
    from src.cv.extract import extract_label
    from src.cv.verify import compare_extraction

    extraction = extract_label(preview)
    check = compare_extraction(extraction, manifest)
    manifest["self_check"] = {
        "status": check.status,
        "issues": check.issues,
        "warnings": check.warnings,
        "scope": "OCR, barcode, symbols and template layout; no retrieval-rule checker",
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return RenderResult(
        str(svg_path),
        str(pdf_path),
        str(preview),
        str(manifest_path),
        manifest["barcode_action"],
        changes,
        manifest["self_check"],
    )


def render_label(
    template_spec: dict[str, Any], record: ProductRecord, output_dir: Path, *, actor: str, reason: str,
    test_data: bool = False, previous_manifest: dict[str, Any] | None = None,
    confirmed_encoded_change: bool = False,
) -> RenderResult:
    """Create an immutable draft package atomically, with no partial final artifacts.

    Layout failures retain structured flags. Identifiers are supplied by the
    caller. Changed encoded values require confirmation; unchanged barcode
    matrices are reused. Rendering never creates an approval or publishes.
    """
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError("Draft output directory is not empty; revisions must be immutable")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="labellens_draft_", dir=output_dir.parent) as temporary:
        result = _render_package(
            template_spec, record, Path(temporary) / "package", actor=actor, reason=reason,
            test_data=test_data, previous_manifest=previous_manifest,
            confirmed_encoded_change=confirmed_encoded_change,
        )
        os.rename(Path(temporary) / "package", output_dir)
    return replace(result, svg=str(output_dir / "label.svg"), pdf=str(output_dir / "label.pdf"),
                   preview=str(output_dir / "label.png"), manifest=str(output_dir / "manifest.json"))
