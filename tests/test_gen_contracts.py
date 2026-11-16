"""Contract-facing renderer and approval checks with synthetic fixtures only."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

for dependency in ("cv2", "PIL", "zxingcpp", "reportlab", "pypdf"):
    pytest.importorskip(dependency)

from PIL import Image, ImageDraw  # noqa: E402
from pypdf import PdfReader  # noqa: E402
from reportlab.graphics.shapes import Drawing, Group, Rect  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402

from src.common.schemas import LabelExtraction, ProductRecord  # noqa: E402
from src.cv import extract, verify  # noqa: E402
from src.gen.render import _draw_symbol, _svg_with_layers, render_label  # noqa: E402
from src.gen.symbols import draw_symbol  # noqa: E402

NS = {"s": "http://www.w3.org/2000/svg"}


@pytest.mark.parametrize(
    "name,text", [("sterile", "STERILE"), ("sterile_eo", "STERILE EO"), ("sterile_r", "STERILE R")]
)
def test_sterile_artwork_in_raster_and_vectors(name: str, text: str) -> None:
    """Each supported sterile method produces bounded synthetic artwork in both outputs."""
    image = Image.new("L", (180, 100), 255)
    draw_symbol(ImageDraw.Draw(image), name, (10, 10, 160, 80))
    ink = image.point(lambda value: 255 - value).getbbox()
    assert ink is not None and ink[0] >= 10 and ink[1] >= 10 and ink[2] <= 170 and ink[3] <= 90
    group = Group()
    _draw_symbol(group, name, (0, 0, 160, 80))
    assert any(getattr(item, "text", None) == text for item in group.contents)


def test_named_svg_layers_preserve_slot_metadata() -> None:
    """ReportLab groups get stable contract IDs with millimetre root dimensions."""
    template = {
        "template_id": "fixture",
        "version": 2,
        "size_mm": {"w": 100, "h": 60},
        "slots": [{"id": "barcode", "field": "udi", "type": "barcode", "bbox_mm": [10, 12, 20, 20]}],
    }
    drawing = Drawing(100 * mm, 60 * mm)
    layers = [Group() for _ in range(4)]
    for layer in layers:
        drawing.add(layer)
    slot = Group()
    slot.add(Rect(10 * mm, 12 * mm, mm, mm))
    layers[1].add(slot)
    root = ET.fromstring(_svg_with_layers(drawing, template, {"10": "LOT001"}))
    assert root.attrib["viewBox"] == "0 0 100 60"
    assert root.attrib["width"] == "100mm" and root.attrib["height"] == "60mm"
    for name in ("background", "slots", "watermark", "review"):
        assert root.find(f".//s:g[@id='layer-{name}']", NS) is not None
    barcode = root.find(".//s:g[@id='slot-barcode']", NS)
    assert barcode is not None and barcode.attrib["data-payload"] == "(10)LOT001"
    assert barcode.attrib["data-bbox-mm"] == "10 12 20 20"
    with pytest.raises(RuntimeError, match="four label layers"):
        _svg_with_layers(Drawing(100, 60), template, {})


@pytest.mark.skipif(shutil.which("pdftoppm") is None, reason="Poppler is required for legacy-renderer previews")
def test_legacy_renderer_sterile_slot_and_version_binding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The original renderer accepts sterile artwork and names every slot without claiming OCR success."""
    template = json.loads(Path("src/gen/templates/test_device.json").read_text())
    template["slots"] = [slot for slot in template["slots"] if slot["type"] != "symbol"] + [
        {
            "id": "sterile",
            "type": "symbol",
            "field": "sterilization",
            "symbol_name": "sterile_eo",
            "bbox_mm": [70, 48, 25, 8],
        },
    ]
    record = ProductRecord(
        product_id="fixture-device",
        name="TEST DEVICE",
        model="TEST-M001",
        manufacturer="Example Manufacturer",
        manufacturer_address="123 Example Road",
        udi_di="00000000000000",
        extra={"lot": "LOT001", "expiry": "2028-12-31", "serial": "SN001"},
    )
    monkeypatch.setattr(extract, "extract_label", lambda _: LabelExtraction(label_id="fixture"))
    result = render_label(
        template,
        record,
        tmp_path / "draft",
        actor="fixture-author",
        reason="contract test",
        test_data=True,
        version_id="fixture-version-1",
    )
    manifest = json.loads(Path(result.manifest).read_text())
    assert manifest["version_id"] == "fixture-version-1" and manifest["created_by"] == "fixture-author"
    assert manifest["symbols"] == ["sterile_eo"]
    assert manifest["self_check"]["status"] == "NEEDS_HUMAN_REVIEW"
    assert "STERILE EO" in PdfReader(result.pdf).pages[0].extract_text()
    assert "DRAFT, not for production" in PdfReader(result.pdf).pages[0].extract_text()
    assert "DRAFT, not for production" in Path(result.svg).read_text()
    root = ET.parse(result.svg).getroot()
    for slot in template["slots"]:
        group = root.find(f".//s:g[@id='slot-{slot['id']}']", NS)
        assert group is not None and group.attrib["data-field"] == slot["field"]
    with pytest.raises(ValueError, match="new version_id"):
        render_label(
            template,
            record.model_copy(update={"version": 2}),
            tmp_path / "bad",
            actor="fixture-author",
            reason="test",
            test_data=True,
            previous_manifest=manifest,
            version_id="fixture-version-1",
        )


def test_print_verifier_refuses_bad_checks_before_extraction(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The legacy print verifier must validate the passed check before attempting OCR."""
    source = tmp_path / "manifest.json"
    source.write_text(
        json.dumps(
            {
                "version_id": "v1",
                "created_by": "author",
                "artifacts": {},
                "artifact_sha256": {},
                "fields": {},
                "barcode_ais": {},
                "symbols": [],
            }
        )
    )
    fingerprint = hashlib.sha256(source.read_bytes()).hexdigest()
    review = {
        "decision": "approve",
        "reviewer": "reviewer",
        "reviewer_role": "reviewer",
        "version_id": "v1",
        "reference_sha256": fingerprint,
        "check_id": "check-1",
    }
    check = {"check_id": "check-1", "version_id": "v1", "reference_sha256": fingerprint, "passed": True}
    calls = []
    monkeypatch.setattr(
        verify, "extract_label", lambda _: calls.append("extract") or LabelExtraction(label_id="fixture")
    )
    for bad in (
        None,
        {**check, "passed": False},
        {**check, "check_id": "old"},
        {**check, "version_id": "old"},
        {**check, "reference_sha256": "wrong"},
    ):
        with pytest.raises(PermissionError):
            verify.verify_print(
                tmp_path / "photo.png",
                source,
                approval_record=review,
                check_record=bad,
                authorized_reviewers=frozenset({"reviewer"}),
            )
        assert calls == []
    verify.verify_print(
        tmp_path / "photo.png",
        source,
        approval_record=review,
        check_record=check,
        authorized_reviewers=frozenset({"reviewer"}),
    )
    assert calls == ["extract"]
