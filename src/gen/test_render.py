"""Physical-size artifacts, identifier rules, barcode reuse and layout checks."""

import copy
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import pytest
from PIL import Image
from pypdf import PdfReader
from reportlab.lib.units import mm

from src.common.schemas import IdentifierRequired, ProductRecord
from src.gen.render import LayoutError, check_layout, record_content, render_label, wrap_text


@pytest.fixture
def record() -> ProductRecord:
    """Use the existing clearly synthetic identifier, never an invented allocated GTIN."""
    return ProductRecord(
        product_id="test_device",
        name="TEST DEVICE",
        model="TEST-M001",
        manufacturer="Example Manufacturer",
        manufacturer_address="123 Example Road",
        udi_di="00000000000000",
        extra={"lot": "TESTLOT001", "expiry": "2027-12-31", "serial": "TESTSER001"},
    )


@pytest.fixture
def template() -> dict:
    """Load the supported test-device template."""
    return json.loads((Path(__file__).parent / "templates/test_device.json").read_text())


def test_render_reuse_and_confirmed_change(tmp_path: Path, template: dict, record: ProductRecord) -> None:
    """Render real PDFs and preserve barcode pixels until confirmed encoded values change."""
    first = render_label(template, record, tmp_path / "first", actor="test_actor", reason="test", test_data=True)
    manifest = json.loads(Path(first.manifest).read_text())
    reader = PdfReader(first.pdf)
    assert len(reader.pages) == 1
    assert np.allclose(
        [float(reader.pages[0].mediabox.width), float(reader.pages[0].mediabox.height)], [100 * mm, 60 * mm]
    )
    assert "TEST DATA | DRAFT" in reader.pages[0].extract_text()
    assert "TEST DEVICE" in reader.pages[0].extract_text()
    assert ET.parse(first.svg).getroot().get("width") == "100mm"
    assert manifest["status"] == first.status == "DRAFT"
    assert manifest["change_log"] and manifest["self_check"]["status"] in {"MATCH", "MISMATCH", "NEEDS_HUMAN_REVIEW"}
    repeat = render_label(template, record, tmp_path / "repeat", actor="test_actor", reason="test", test_data=True)
    assert Path(first.pdf).read_bytes() == Path(repeat.pdf).read_bytes()
    assert Path(first.svg).read_bytes() == Path(repeat.svg).read_bytes()
    revised_record = record.model_copy(update={"name": "TEST SENSOR", "version": 2})
    revised = render_label(
        template,
        revised_record,
        tmp_path / "revised",
        actor="test_actor",
        reason="name revision",
        test_data=True,
        previous_manifest=manifest,
    )
    second = json.loads(Path(revised.manifest).read_text())
    assert second["barcode_action"] == "reused" and second["barcode_matrix"] == manifest["barcode_matrix"]
    with Image.open(first.preview) as a, Image.open(revised.preview) as b:
        assert a.crop((827, 230, 1130, 535)).tobytes() == b.crop((827, 230, 1130, 535)).tobytes()
    changed = record.model_copy(update={"version": 2, "extra": {**record.extra, "lot": "TESTLOT002"}})
    with pytest.raises(ValueError, match="confirmation"):
        render_label(
            template,
            changed,
            tmp_path / "unconfirmed",
            actor="test_actor",
            reason="test",
            test_data=True,
            previous_manifest=manifest,
        )
    third = render_label(
        template,
        changed,
        tmp_path / "changed",
        actor="test_actor",
        reason="confirmed test lot",
        test_data=True,
        previous_manifest=manifest,
        confirmed_encoded_change=True,
    )
    assert third.barcode_action == "generated"
    assert json.loads(Path(third.manifest).read_text())["barcode_ais"]["10"] == "TESTLOT002"
    with pytest.raises(FileExistsError):
        render_label(template, record, tmp_path / "first", actor="test_actor", reason="test", test_data=True)


def test_identifiers_and_required_values(record: ProductRecord) -> None:
    """Require supplied identifiers and explicit test mode for the existing placeholder."""
    for value in ("", "00000000000000"):
        with pytest.raises(IdentifierRequired):
            record_content(record.model_copy(update={"udi_di": value}), False)
    with pytest.raises(ValueError):
        record_content(record.model_copy(update={"udi_di": "00000000000001"}), True)
    with pytest.raises(ValueError):
        record_content(record.model_copy(update={"extra": {}}), True)
    assert record_content(record, True)[1]["01"] == "00000000000000"


@pytest.mark.parametrize("problem", ["overflow", "clip", "font", "small_symbol", "missing", "background", "overlap"])
def test_layout_flags(template: dict, record: ProductRecord, tmp_path: Path, problem: str) -> None:
    """Produce structured critical flags and no artwork for invalid proposed layouts."""
    template = copy.deepcopy(template)
    if problem == "overflow":
        record = record.model_copy(update={"name": "X" * 200})
    elif problem == "clip":
        template["slots"][0]["bbox_mm"][0] = 99
    elif problem == "font":
        template["slots"][0]["size_pt"] = 3
    elif problem == "small_symbol":
        template["slots"][-1]["bbox_mm"][2] = 2
    elif problem == "missing":
        record = record.model_copy(update={"manufacturer": ""})
    elif problem == "background":
        template["background"] = "unknown.svg"
    else:
        template["slots"][1]["bbox_mm"] = template["slots"][0]["bbox_mm"]
    with pytest.raises(LayoutError) as error:
        render_label(template, record, tmp_path / "invalid", actor="test_actor", reason="test", test_data=True)
    assert error.value.flags and all(flag.severity == "critical" for flag in error.value.flags)
    assert not (tmp_path / "invalid").exists()


def test_text_wrap_and_quiet_zone(template: dict, record: ProductRecord) -> None:
    """Measure actual font widths and flag a missing barcode quiet border."""
    assert wrap_text("one two three", "Helvetica", 10, 25) == ["one", "two", "three"]
    fields, _ = record_content(record, True)
    flags = check_layout(template, fields, np.zeros((20, 20), dtype=np.uint8))
    assert any(flag.kind == "barcode_quiet_zone" for flag in flags)
