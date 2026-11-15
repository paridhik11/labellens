"""Adapter from the agreed template contract to the export description."""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping

import numpy as np
import zxingcpp

from src.common.schemas import ProductRecord
from src.export.label_model import Element, Label, validate_label
from src.gen.gs1 import GS1Symbology, build_element_string, build_hri, encode_gs1, validate_expiry


def barcode_element(
    field: str,
    bbox_mm: tuple[float, float, float, float],
    elements: Mapping[str, str],
    *,
    symbology: str = "GS1_DataMatrix",
    slot_id: str = "",
    module_mm: float | None = None,
    test_data: bool = False,
) -> Element:
    """Create a vector-ready GS1 matrix with quiet zones and exact module width."""
    encoded = encode_gs1(elements, GS1Symbology(symbology), test_data=test_data)
    # zxing-cpp uses parenthesized input. Escape data parentheses as in Task 1;
    # unlike the preview image, this matrix must not contain human-readable text.
    writer_text = "".join(
        f"({ai})" + value.replace("(", "\\(").replace(")", "\\)") for ai, value in encoded.elements.items()
    )
    fmt = zxingcpp.BarcodeFormat.DataMatrix if symbology == "GS1_DataMatrix" else zxingcpp.BarcodeFormat.Code128
    code = zxingcpp.create_barcode(writer_text, fmt, gs1=True)
    pixels = np.asarray(code.to_image(scale=1, add_hrt=False, add_quiet_zones=True))
    decoded = zxingcpp.read_barcodes(np.repeat(np.repeat(pixels, 4, axis=0), 4, axis=1))
    if len(decoded) != 1 or decoded[0].bytes != build_element_string(elements).encode("ascii"):
        raise RuntimeError("Export matrix differs from the GS1 elements")
    module = min(bbox_mm[2] / pixels.shape[1], bbox_mm[3] / pixels.shape[0]) if module_mm is None else module_mm
    matrix = tuple("".join("1" if value == 0 else "0" for value in row) for row in pixels)
    return Element(
        field,
        "barcode",
        bbox_mm,
        slot_id=slot_id,
        matrix=matrix,
        module_mm=module,
        payload=encoded.hri,
        symbology=str(fmt),
    )


def from_template(
    template: Mapping[str, Any],
    fields: Mapping[str, str],
    gs1_elements: Mapping[str, str],
    *,
    version_id: str,
    actor: str,
    reason: str,
    test_data: bool = False,
    barcode_module_mm: float | None = None,
    reuse_barcode: Element | None = None,
) -> Label:
    """Translate blank-background template slots, preserving IDs and millimetres."""
    if template.get("background") is not None:
        raise ValueError("Only background=null is supported; existing artwork must not be silently discarded")
    elements = []
    for slot in template["slots"]:
        kind, field = slot["type"], slot["field"]
        box = tuple(slot["bbox_mm"])
        if kind == "barcode":
            if reuse_barcode is not None:
                expected_format = {
                    "GS1_DataMatrix": str(zxingcpp.BarcodeFormat.DataMatrix),
                    "GS1-128": str(zxingcpp.BarcodeFormat.Code128),
                }.get(slot["symbology"])
                if (
                    reuse_barcode.kind != "barcode" or reuse_barcode.field != field
                    or reuse_barcode.slot_id != slot["id"] or reuse_barcode.bbox_mm != box
                    or reuse_barcode.payload != build_hri(gs1_elements)
                    or reuse_barcode.symbology != expected_format
                    or (barcode_module_mm is not None and barcode_module_mm != reuse_barcode.module_mm)
                ):
                    raise ValueError("Existing barcode does not match the requested slot, payload or format")
                element = reuse_barcode
            else:
                element = barcode_element(
                    field,
                    box,
                    gs1_elements,
                    symbology=slot["symbology"],
                    slot_id=slot["id"],
                    module_mm=barcode_module_mm,
                    test_data=test_data,
                )
        elif kind == "symbol":
            element = Element(field, kind, box, slot_id=slot["id"], symbol_name=slot["symbol_name"])
        elif kind == "text":
            value = fields.get(field, fields.get("name", "") if field == "product_name" else "")
            element = Element(
                field,
                kind,
                box,
                slot_id=slot["id"],
                text=value,
                font=slot.get("font", "Helvetica"),
                size_pt=slot["size_pt"],
                max_lines=slot.get("max_lines", 1),
                align=slot.get("align", "left"),
            )
            if element.size_pt < template.get("min_font_pt", 6):
                raise ValueError("Font size is below the template's minimum")
        else:
            raise ValueError(f"Unsupported template slot type: {kind}")
        if min(box[2:]) < slot.get("min_size_mm", 0):
            raise ValueError("Slot is below its configured minimum printed size")
        elements.append(element)
    label = Label(
        template["size_mm"]["w"],
        template["size_mm"]["h"],
        tuple(elements),
        version_id,
        actor,
        reason,
        template["template_id"],
        template["version"],
        test_data,
    )
    validate_label(label)
    return label


def from_product(
    template: Mapping[str, Any],
    record: ProductRecord,
    *,
    version_id: str,
    actor: str,
    reason: str,
    test_data: bool = False,
) -> Label:
    """Use the locked ProductRecord schema without supplying absent identifiers."""
    if template.get("product_id") not in {None, record.product_id}:
        raise ValueError("Template belongs to a different product")
    expiry = date.fromisoformat(record.extra["expiry"])
    if validate_expiry(expiry.strftime("%y%m%d")) != expiry:
        raise ValueError("Expiry is outside the GS1 century window")
    elements = {"01": record.udi_di, "17": expiry.strftime("%y%m%d"), "10": record.extra["lot"]}
    if record.extra.get("serial"):
        elements["21"] = record.extra["serial"]
    fields = {
        **record.extra,
        "name": record.name,
        "product_name": record.name,
        "manufacturer": record.manufacturer,
        "manufacturer_address": record.manufacturer_address,
        "model": record.model,
    }
    return from_template(
        template, fields, elements, version_id=version_id, actor=actor, reason=reason, test_data=test_data
    )
