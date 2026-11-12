"""Generate one clearly marked synthetic label and its ground truth."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import numpy as np
import zxingcpp
from PIL import Image, ImageDraw, ImageFont

from src.gen.symbols import draw_symbol

DPI = 300


def mm_to_px(value: float) -> int:
    """Convert millimetres to pixels at the configured resolution."""
    return round(value * DPI / 25.4)


def build_label(
    output_dir: Path,
    *,
    label_id: str = "test_label_001",
    field_values: dict[str, str] | None = None,
    barcode_ais: dict[str, str] | None = None,
) -> dict[str, str]:
    """Render a test label with optional overrides and verify its GS1 payload.

    Barcode overrides supply the printed lot and expiry unless those fields
    are explicitly provided, in which case they must match. AI 01 stays at
    the existing test placeholder; this generator cannot allocate identifiers.
    """
    if re.fullmatch(r"test_[A-Za-z0-9_-]+", label_id) is None:
        raise ValueError("label_id must start with test_ and contain only letters, digits, underscores or hyphens")
    template_path = Path(__file__).parent / "templates" / "test_device.json"
    template = json.loads(template_path.read_text(encoding="utf-8"))

    fields = {
        "product_name": "TEST DEVICE",
        "manufacturer": "Example Manufacturer",
        "manufacturer_address": "123 Example Road",
        "model": "REF: TEST-M001",
        "lot": "LOT: TESTLOT001",
        "expiry": "EXP: 2027-12-31",
    }
    ais = {
        "01": "00000000000000",
        "17": "271231",
        "10": "TESTLOT001",
        "21": "TESTSER001",
    }
    if barcode_ais is not None:
        if barcode_ais.keys() - ais.keys():
            raise ValueError("Unknown barcode AI")
        ais.update(barcode_ais)
    if ais["01"] != "00000000000000":
        raise ValueError("AI 01 must remain the existing test placeholder")
    if re.fullmatch(r"[0-9]{6}", ais["17"]) is None:
        raise ValueError("Expiry AI 17 must use YYMMDD")
    expiry = date.fromisoformat(f"20{ais['17'][:2]}-{ais['17'][2:4]}-{ais['17'][4:]}")
    for key in ("10", "21"):
        if not 1 <= len(ais[key]) <= 20 or not ais[key].isascii() or not ais[key].isalnum():
            raise ValueError(f"Test AI {key} must contain 1 to 20 ASCII letters or digits")
    fields.update(lot=f"LOT: {ais['10']}", expiry=f"EXP: {expiry.isoformat()}")
    if field_values is not None:
        if field_values.keys() - fields.keys():
            raise ValueError("Unknown label field")
        fields.update(field_values)
    if fields["lot"] != f"LOT: {ais['10']}" or fields["expiry"] != f"EXP: {expiry.isoformat()}":
        raise ValueError("Printed lot and expiry must match barcode AIs 10 and 17")
    payload = "".join(f"({key}){value}" for key, value in ais.items())
    size = template["size_mm"]
    image = Image.new(
        "RGB", (mm_to_px(size["w"]), mm_to_px(size["h"])), "white"
    )
    draw = ImageDraw.Draw(image)
    draw.rectangle(
        (1, 1, image.width - 2, image.height - 2), outline="black", width=3
    )
    heading_font = ImageFont.load_default(size=round(10 * DPI / 72))
    draw.text(
        (mm_to_px(5), mm_to_px(3)),
        "TEST DATA | DRAFT",
        font=heading_font,
        fill="black",
    )

    boxes = {}
    for slot in template["slots"]:
        x, y, width, height = map(mm_to_px, slot["bbox_mm"])
        boxes[slot["field"]] = [x, y, width, height]

        if slot["type"] == "text":
            font = ImageFont.load_default(
                size=round(slot["size_pt"] * DPI / 72)
            )
            text = fields[slot["field"]]
            bounds = draw.textbbox((0, 0), text, font=font, anchor="lt")
            if bounds[2] > width or bounds[3] > height:
                raise ValueError(f"Text does not fit: {slot['id']}")
            draw.text((x, y), text, font=font, fill="black", anchor="lt")

        elif slot["type"] == "symbol":
            draw_symbol(
                draw, slot["symbol_name"], (x, y, width, height)
            )

        elif slot["type"] == "barcode":
            barcode = zxingcpp.create_barcode(
                payload, zxingcpp.BarcodeFormat.DataMatrix, gs1=True
            )
            # Choose an integer module scale so barcode cells stay sharp.
            base = zxingcpp.write_barcode_to_image(
                barcode, scale=1, add_quiet_zones=True
            )
            matrix = np.asarray(base)
            scale = min(width // matrix.shape[1], height // matrix.shape[0])
            if scale < 1:
                raise ValueError("Barcode slot is too small")
            pixels = zxingcpp.write_barcode_to_image(
                barcode, scale=scale, add_quiet_zones=True
            )
            barcode_image = Image.fromarray(np.asarray(pixels)).convert("RGB")
            image.paste(
                barcode_image,
                (
                    x + (width - barcode_image.width) // 2,
                    y + (height - barcode_image.height) // 2,
                ),
            )

    decoded = zxingcpp.read_barcodes(np.asarray(image))
    if len(decoded) != 1:
        raise ValueError(f"Expected one barcode, decoded {len(decoded)}")
    result = decoded[0]
    if result.content_type != zxingcpp.ContentType.GS1:
        raise ValueError("Barcode was not recognized as GS1")
    if result.text != payload:
        raise ValueError("Decoded payload differs from intended payload")

    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"{label_id}.png"
    truth_path = output_dir / f"{label_id}.json"
    truth = {
        "label_id": label_id,
        "template_id": template["template_id"],
        "template_version": template["version"],
        "test_data": True,
        "status": "DRAFT",
        "condition": "clean",
        "dpi": DPI,
        "size_mm": size,
        "image_size_px": [image.width, image.height],
        "fields": fields,
        "barcode_payload": payload,
        "barcode_ais": ais,
        "slot_boxes_px_xywh": boxes,
        "symbols": [
            {
                "name": slot["symbol_name"],
                "bbox_px_xywh": boxes[slot["field"]],
                "synthetic_pictogram": True,
                "iso_ref": "",
            }
            for slot in template["slots"]
            if slot["type"] == "symbol"
        ],
        "limitations": ["Simplified test pictograms; augmentations not yet added"]
    }
    image.save(image_path, dpi=(DPI, DPI))
    truth_path.write_text(
        json.dumps(truth, indent=2) + "\n", encoding="utf-8"
    )
    return {"image": str(image_path), "ground_truth": str(truth_path)}


if __name__ == "__main__":
    paths = build_label(Path("data/synthetic/smoke"))
    print("PASS: barcode decoded as GS1 and payload matched")
    for name, path in paths.items():
        print(f"{name}: {path}")
