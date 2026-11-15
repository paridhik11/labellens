"""Editable SVG export in millimetres with the contract's named layers."""

from __future__ import annotations

import base64
from pathlib import Path
from xml.etree import ElementTree as ET

from src.export.label_model import (
    MM_TO_PT,
    ApprovalRecord,
    Label,
    PassedCheck,
    primitives,
    validate_approval,
    validate_label,
    write_artifact,
)

SVG_NS = "http://www.w3.org/2000/svg"


def render_svg(
    label: Label,
    path: Path,
    *,
    min_module_mm: float = 0.25,
    approval: ApprovalRecord | None = None,
    check: PassedCheck | None = None,
    authorized_reviewers: frozenset[str] = frozenset(),
) -> Path:
    """Write named editable fields and vector barcode rectangles, plus an audit."""
    validate_label(label, min_module_mm)
    approved = validate_approval(label, approval, check, authorized_reviewers)
    root = ET.Element(
        "svg",
        {
            "xmlns": SVG_NS,
            "width": f"{label.width_mm:g}mm",
            "height": f"{label.height_mm:g}mm",
            "viewBox": f"0 0 {label.width_mm:g} {label.height_mm:g}",
            "data-template-id": label.template_id,
            "data-template-version": str(label.template_version),
        },
    )
    ET.SubElement(root, "g", {"id": "layer-background"})
    slots = ET.SubElement(root, "g", {"id": "layer-slots"})
    fields_seen: set[str] = set()
    for element in label.elements:
        group = ET.SubElement(
            slots,
            "g",
            {
                "id": f"slot-{element.slot_id or element.field}",
                "data-slot-type": element.kind,
                "data-field": element.field,
                "data-bbox-mm": " ".join(f"{v:g}" for v in element.bbox_mm),
            },
        )
        if element.kind == "barcode":
            group.set("data-payload", element.payload)
            group.set("data-module-mm", f"{element.module_mm:g}")
        content = group if element.field in fields_seen else ET.SubElement(group, "g", {"id": element.field})
        fields_seen.add(element.field)
        for item in primitives(element):
            if item.kind in {"rect", "outline"}:
                ET.SubElement(
                    content,
                    "rect",
                    {
                        "x": str(item.x),
                        "y": str(item.y),
                        "width": str(item.w),
                        "height": str(item.h),
                        "fill": "black" if item.kind == "rect" else "none",
                        "stroke": "none" if item.kind == "rect" else "black",
                        "stroke-width": "0.2",
                    },
                )
            elif item.kind == "line":
                ET.SubElement(
                    content,
                    "line",
                    {
                        "x1": str(item.x),
                        "y1": str(item.y),
                        "x2": str(item.x + item.w),
                        "y2": str(item.y + item.h),
                        "stroke": "black",
                        "stroke-width": "0.3",
                    },
                )
            elif item.kind == "text":
                text = ET.SubElement(
                    content,
                    "text",
                    {
                        "x": str(item.x),
                        "y": str(item.y),
                        "font-family": item.font,
                        "font-size": str(item.size_pt / MM_TO_PT),
                    },
                )
                text.text = item.text
            else:
                ET.SubElement(
                    content,
                    "image",
                    {
                        "x": str(item.x),
                        "y": str(item.y),
                        "width": str(item.w),
                        "height": str(item.h),
                        "preserveAspectRatio": "none",
                        "href": "data:image/png;base64," + base64.b64encode(item.png).decode("ascii"),
                    },
                )
    watermark = ET.SubElement(root, "g", {"id": "layer-watermark"})
    if not approved or label.test_data:
        text = ET.SubElement(
            watermark, "text", {"x": "2", "y": "6", "font-family": "Helvetica", "font-size": str(9 / MM_TO_PT)}
        )
        text.text = (
            "TEST DATA | DRAFT" if label.test_data and not approved else "TEST DATA" if label.test_data else "DRAFT"
        )
    review = ET.SubElement(root, "g", {"id": "layer-review"})
    for x, y, w, h in label.review_boxes:
        ET.SubElement(
            review,
            "rect",
            {
                "x": str(x),
                "y": str(y),
                "width": str(w),
                "height": str(h),
                "fill": "none",
                "stroke": "red",
                "stroke-width": "0.2",
            },
        )
    return write_artifact(
        path,
        ET.tostring(root, encoding="utf-8", xml_declaration=True),
        label,
        approved,
        approval.check_id if approved else "",
    )
