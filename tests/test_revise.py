"""Task 6 revision policy, source binding and real draft export integration."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock
from xml.etree import ElementTree as ET

import pytest

for dependency in ("numpy", "zxingcpp", "PIL", "reportlab"):
    pytest.importorskip(dependency)

import numpy as np  # noqa: E402
import zxingcpp  # noqa: E402

from src.common.schemas import ChangeRequest, IdentifierRequired, ProductRecord  # noqa: E402
from src.export import template as adapter  # noqa: E402
from src.export.label_model import Label, reference_sha256  # noqa: E402
from src.gen.gs1 import BarcodeAction, parse_gs1  # noqa: E402
from src.gen.revise import barcode_values, record_fields, revise_template  # noqa: E402

AIS = {"01": "00000000000000", "17": "281231", "10": "LOT001", "21": "SN001"}


@pytest.fixture
def source() -> tuple[dict, ProductRecord, Label]:
    """Supply an existing test-only draft with independently specified GS1 values."""
    template = json.loads(Path("src/gen/templates/test_device.json").read_text())
    record = ProductRecord(product_id="device-fixture", version=3, name="TEST DEVICE", model="M1",
                           manufacturer="Example Labs", manufacturer_address="101 Example Road",
                           udi_di="00000000000000", sterilization="EO",
                           extra={"lot": "LOT001", "expiry": "2028-12-31", "serial": "SN001"})
    fields = {"product_name": "TEST DEVICE", "model": "M1", "manufacturer": "Example Labs",
              "manufacturer_address": "101 Example Road", "lot": "LOT001", "expiry": "2028-12-31"}
    label = adapter.from_template(template, fields, AIS, version_id="original-v3", actor="creator",
                                  reason="existing test fixture", test_data=True)
    return template, record, label


def test_record_binding_and_iso_expiry(source: tuple[dict, ProductRecord, Label]) -> None:
    """Core name wins over extra, and no absent identifier is supplied by the mapper."""
    _, record, _ = source
    record.extra.update(name="malicious", product_name="malicious")
    assert record_fields(record)["name"] == record_fields(record)["product_name"] == "TEST DEVICE"
    assert barcode_values(record) == AIS
    record.udi_di = ""
    assert barcode_values(record)["01"] == ""
    record.extra["expiry"] = "20281231"
    with pytest.raises(ValueError, match="ISO date"):
        barcode_values(record)


def test_keep_reuses_exact_matrix_without_encoder(
    source: tuple[dict, ProductRecord, Label], monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A text revision increments versions, preserves the source and never redraws a barcode."""
    template, record, label = source
    before = deepcopy(template), record.model_dump(), reference_sha256(label)
    encoder = Mock(side_effect=AssertionError("KEEP must not encode another barcode"))
    monkeypatch.setattr(adapter, "barcode_element", encoder)
    result = revise_template(template, record, ChangeRequest(change_id="c1", product_id=record.product_id,
                             field="manufacturer_address", old_value="101 Example Road", new_value="88 Demo Rd"),
                             previous_label=label, version_id="draft-v4", actor="parth", reason="Address update")
    assert result.barcode_decision.action == BarcodeAction.KEEP and result.status == "DRAFT"
    assert result.require_label() is result.label
    assert result.template["version"] == 2 and result.record.version == 4
    assert result.fields["manufacturer_address"] == "88 Demo Rd"
    old_barcode = next(e for e in label.elements if e.kind == "barcode")
    assert next(e for e in result.label.elements if e.kind == "barcode") is old_barcode
    assert not encoder.called
    assert result.template["slots"] == template["slots"]
    assert result.change_log[0]["actor"] == "parth" and result.change_log[0]["barcode_action"] == "KEEP"
    assert result.self_check["status"] == "NEEDS_HUMAN_REVIEW"
    assert reference_sha256(result.label) != reference_sha256(label)
    assert (template, record.model_dump(), reference_sha256(label)) == before


@pytest.mark.parametrize(("field", "old", "new", "flag", "ai", "encoded"), [
    ("lot", "LOT001", "LOT002", "confirmed_lot_change", "10", "LOT002"),
    ("expiry", "2028-12-31", "2029-01-01", "confirmed_expiry_change", "17", "290101"),
    ("serial", "SN001", "SN002", "confirmed_serial_change", "21", "SN002"),
    ("udi_di", "00000000000000", "09506000134352", "confirmed_gtin_change", "01", "09506000134352"),
])
def test_unconfirmed_blocks_and_confirmed_regenerates(
    source: tuple[dict, ProductRecord, Label], field: str, old: str, new: str, flag: str, ai: str, encoded: str,
) -> None:
    """Each encoded field needs its own confirmation and the replacement barcode decodes exactly."""
    template, record, label = source
    change = ChangeRequest(change_id="encoded", product_id=record.product_id, field=field, old_value=old, new_value=new)
    blocked = revise_template(template, record, change, previous_label=label, version_id="new-v4",
                              actor="parth", reason="encoded change")
    assert blocked.barcode_decision.action == BarcodeAction.NEEDS_INPUT
    assert blocked.label is None and blocked.status == "NEEDS_INPUT"
    assert blocked.self_check["status"] == "NEEDS_INPUT"
    with pytest.raises(ValueError):
        blocked.require_label()
    result = revise_template(template, record, change, previous_label=label, version_id="new-v4",
                             actor="parth", reason="encoded change", confirmed={flag: True})
    assert result.barcode_decision.action == BarcodeAction.REGENERATE
    barcode = next(e for e in result.label.elements if e.kind == "barcode")
    pixels = np.array([[0 if bit == "1" else 255 for bit in row] for row in barcode.matrix], dtype=np.uint8)
    decoded = zxingcpp.read_barcodes(np.repeat(np.repeat(pixels, 4, axis=0), 4, axis=1))
    assert len(decoded) == 1
    assert parse_gs1(decoded[0].bytes.decode("ascii")) == {**AIS, ai: encoded}
    assert record.extra["lot"] == "LOT001" and record.udi_di == "00000000000000"


def test_new_model_requires_caller_supplied_identifier(source: tuple[dict, ProductRecord, Label]) -> None:
    """A flagged identifier-changing revision cannot silently inherit the old identifier."""
    template, record, label = source
    change = ChangeRequest(change_id="model", product_id=record.product_id, field="model",
                           old_value="M1", new_value="M2")
    result = revise_template(template, record, change, previous_label=label, version_id="new-v4", actor="parth",
                             reason="New model", requires_new_identifier=True)
    assert result.required_identifier == "udi_di" and result.record.udi_di == "" and result.label is None
    with pytest.raises(IdentifierRequired):
        result.require_label()
    supplied = revise_template(template, record, change, previous_label=label, version_id="new-v4", actor="parth",
                               reason="New model", requires_new_identifier=True,
                               allocated_identifier="09506000134352", confirmed={"confirmed_gtin_change": True})
    assert supplied.barcode_decision.action == BarcodeAction.REGENERATE
    assert supplied.record.udi_di == "09506000134352" and supplied.required_identifier is None
    assert supplied.change_log[1]["field"] == "udi_di"


def test_name_alias_and_extra_field_change(source: tuple[dict, ProductRecord, Label]) -> None:
    """The product_name alias edits the core name, while extra.lot uses the encoded-field policy."""
    template, record, label = source
    change = ChangeRequest(change_id="name", product_id=record.product_id, field="product_name",
                           old_value="TEST DEVICE", new_value="NEW DEVICE", status="published")
    result = revise_template(template, record, change, previous_label=label, version_id="v4",
                             actor="parth", reason="Rename")
    assert result.record.name == result.fields["product_name"] == "NEW DEVICE"
    assert result.status == "DRAFT"  # A change's published status does not approve new artwork.
    change = change.model_copy(update={"field": "extra.lot", "old_value": "LOT001", "new_value": "LOT003"})
    blocked = revise_template(template, record, change, previous_label=label, version_id="v4",
                              actor="parth", reason="Lot update")
    assert blocked.label is None


def test_sterilization_updates_symbol_and_keeps_barcode(source: tuple[dict, ProductRecord, Label]) -> None:
    """EO to gamma changes the symbol without changing positions or encoded payload."""
    template, record, _ = source
    template["slots"] = [slot for slot in template["slots"] if slot["type"] != "symbol"] + [
        {"id": "sterile", "type": "symbol", "field": "sterilization", "symbol_name": "sterile_eo",
         "bbox_mm": [70, 48, 25, 8]},
    ]
    label = adapter.from_template(template, record_fields(record), AIS, version_id="v3", actor="creator",
                                  reason="Source", test_data=True)
    change = ChangeRequest(change_id="sterile", product_id=record.product_id, field="sterilization",
                           old_value="EO", new_value="gamma")
    result = revise_template(template, record, change, previous_label=label, version_id="v4",
                             actor="parth", reason="Method")
    assert result.barcode_decision.action == BarcodeAction.KEEP
    assert result.template["slots"][-1]["symbol_name"] == "sterile_r"
    assert result.template["slots"][-1]["bbox_mm"] == [70, 48, 25, 8]
    assert template["slots"][-1]["symbol_name"] == "sterile_eo" and record.sterilization == "EO"
    with pytest.raises(ValueError, match="supported sterilization"):
        revise_template(template, record, change.model_copy(update={"new_value": "unknown"}),
                        previous_label=label, version_id="v4", actor="parth", reason="Method")


@pytest.mark.parametrize(("field", "old", "new"), [
    ("name", "stale name", "NEW DEVICE"), ("name", "TEST DEVICE", "TEST DEVICE"),
    ("extra.name", "TEST DEVICE", "Injected"), ("version", "", "99"),
    ("unknown", "", "new"), ("storage", "", "Cold"), ("name", "TEST DEVICE", "X" * 300),
    ("manufacturer_symbol", "", "expiry"), ("udi", "", "override"),
])
def test_invalid_or_unrepresented_changes_do_not_modify_source(
    source: tuple[dict, ProductRecord, Label], field: str, old: str, new: str,
) -> None:
    """Stale edits, metadata injection, ignored fields and overflowing text fail safely."""
    template, record, label = source
    before = deepcopy(template), record.model_dump()
    change = ChangeRequest(change_id="bad", product_id=record.product_id, field=field, old_value=old, new_value=new)
    with pytest.raises(ValueError):
        revise_template(template, record, change, previous_label=label, version_id="v4", actor="parth", reason="Test")
    assert (template, record.model_dump()) == before


@pytest.mark.parametrize(("field", "old", "new"), [
    ("expiry", "2028-12-31", "not-a-date"), ("lot", "LOT001", "bad space"),
    ("serial", "SN001", ""), ("udi_di", "00000000000000", ""),
])
def test_invalid_encoded_proposals_have_no_artwork(
    source: tuple[dict, ProductRecord, Label], field: str, old: str, new: str,
) -> None:
    """Missing identifiers, invalid dates/lots and serial removal remain blocked proposals."""
    template, record, label = source
    change = ChangeRequest(change_id="bad", product_id=record.product_id, field=field, old_value=old, new_value=new)
    result = revise_template(template, record, change, previous_label=label, version_id="v4",
                             actor="parth", reason="Test")
    assert result.label is None and result.barcode_decision.action == BarcodeAction.NEEDS_INPUT


def test_snapshot_binding_and_reuse_guard(source: tuple[dict, ProductRecord, Label]) -> None:
    """A mismatched source record or tampered reused barcode cannot become a new draft."""
    template, record, label = source
    change = ChangeRequest(change_id="name", product_id=record.product_id, field="name",
                           old_value="TEST DEVICE", new_value="NEW DEVICE")
    with pytest.raises(ValueError, match="Source snapshot"):
        revise_template(template, record, change, previous_label=replace(label, template_version=9),
                        version_id="v4", actor="parth", reason="Test")
    barcode = next(e for e in label.elements if e.kind == "barcode")
    for altered in (replace(barcode, payload="wrong"), replace(barcode, matrix=("0",))):
        with pytest.raises(ValueError):
            adapter.from_template(template, record_fields(record), AIS, version_id="v4", actor="parth",
                                  reason="Test", test_data=True, reuse_barcode=altered)


def test_revision_exports_new_text_as_draft(source: tuple[dict, ProductRecord, Label], tmp_path: Path) -> None:
    """The returned snapshot produces actual PDF/SVG drafts with new text and named groups."""
    pypdf = pytest.importorskip("pypdf")
    from src.export.pdf import render_pdf
    from src.export.svg import render_svg

    template, record, label = source
    change = ChangeRequest(change_id="address", product_id=record.product_id, field="manufacturer_address",
                           old_value="101 Example Road", new_value="88 Demo Rd")
    result = revise_template(template, record, change, previous_label=label, version_id="v4",
                             actor="parth", reason="New address")
    pdf = render_pdf(result.label, tmp_path / "draft.pdf")
    svg = render_svg(result.label, tmp_path / "draft.svg")
    text = pypdf.PdfReader(pdf).pages[0].extract_text()
    assert "88 Demo Rd" in text and "101 Example Road" not in text and "DRAFT" in text
    root = ET.parse(svg).getroot()
    assert root.attrib["data-template-version"] == "2"
    assert root.find(".//{http://www.w3.org/2000/svg}g[@id='slot-address']") is not None


def test_new_identifier_flag_rejects_the_old_identifier(source: tuple[dict, ProductRecord, Label]) -> None:
    """An explicit new-identifier requirement cannot be fulfilled by entering the old value."""
    template, record, label = source
    change = ChangeRequest(change_id="model", product_id=record.product_id, field="model",
                           old_value="M1", new_value="M2")
    result = revise_template(template, record, change, previous_label=label, version_id="v4", actor="parth",
                             reason="New identifier needed", requires_new_identifier=True,
                             allocated_identifier=record.udi_di)
    assert result.required_identifier == "udi_di" and result.status == "NEEDS_INPUT"


@pytest.mark.parametrize("options", [
    {"actor": ""}, {"reason": " "}, {"version_id": "original-v3"}, {"requires_new_identifier": "yes"},
    {"allocated_identifier": "09506000134352"},
])
def test_required_metadata_and_identifier_options(
    source: tuple[dict, ProductRecord, Label], options: dict,
) -> None:
    """Malformed audit metadata and ambiguous identifier options fail before proposing a draft."""
    template, record, label = source
    change = ChangeRequest(change_id="name", product_id=record.product_id, field="name",
                           old_value="TEST DEVICE", new_value="NEW DEVICE")
    arguments = {"version_id": "v4", "actor": "parth", "reason": "Test", **options}
    with pytest.raises(ValueError):
        revise_template(template, record, change, previous_label=label, **arguments)


@pytest.mark.parametrize("mutation", [{"product_id": "other"}, {"change_id": ""}])
def test_change_identity_is_required(
    source: tuple[dict, ProductRecord, Label], mutation: dict[str, str],
) -> None:
    """Audit IDs and product identity cannot be omitted or borrowed from another product."""
    template, record, label = source
    change = ChangeRequest(change_id="name", product_id=record.product_id, field="name",
                           old_value="TEST DEVICE", new_value="NEW DEVICE").model_copy(update=mutation)
    with pytest.raises(ValueError):
        revise_template(template, record, change, previous_label=label, version_id="v4", actor="parth", reason="Test")


@pytest.mark.parametrize("symbology", ["GS1_DataMatrix", "GS1-128"])
def test_both_formats_reuse_and_export_confirmed_changes(
    source: tuple[dict, ProductRecord, Label], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, symbology: str,
) -> None:
    """Independent PDF rasterization decodes the revised lot in both supported formats."""
    import shutil
    import subprocess

    executable = shutil.which("pdftoppm")
    if executable is None:
        pytest.skip("Poppler is needed for independent PDF decode")
    from PIL import Image

    from src.export.pdf import render_pdf

    template, record, _ = source
    if symbology == "GS1-128":
        template["size_mm"] = {"w": 160, "h": 100}
        slot = next(slot for slot in template["slots"] if slot["type"] == "barcode")
        slot.update(symbology=symbology, bbox_mm=[5, 65, 150, 25])
    label = adapter.from_template(template, record_fields(record), AIS, version_id="source", actor="creator",
                                  reason="Format fixture", test_data=True)
    change = ChangeRequest(change_id="address", product_id=record.product_id, field="manufacturer_address",
                           old_value="101 Example Road", new_value="88 Demo Rd")
    with monkeypatch.context() as context:
        context.setattr(adapter, "barcode_element", Mock(side_effect=AssertionError("KEEP encoded again")))
        kept = revise_template(template, record, change, previous_label=label, version_id="v4", actor="parth",
                               reason="Address")
    assert kept.barcode_decision.action == BarcodeAction.KEEP
    change = change.model_copy(update={"field": "lot", "old_value": "LOT001", "new_value": "LOT002"})
    result = revise_template(template, record, change, previous_label=label, version_id="v4", actor="parth",
                             reason="New lot", confirmed={"confirmed_lot_change": True})
    pdf = render_pdf(result.label, tmp_path / "new_lot.pdf")
    subprocess.run([executable, "-singlefile", "-png", "-r", "600", str(pdf), str(tmp_path / "print")],
                   check=True, capture_output=True)
    with Image.open(tmp_path / "print.png") as image:
        decoded = zxingcpp.read_barcodes(np.asarray(image.convert("RGB")))
    assert len(decoded) == 1 and parse_gs1(decoded[0].bytes.decode("ascii")) == {**AIS, "10": "LOT002"}


def test_reuse_rejects_plain_text_that_looks_like_gs1(source: tuple[dict, ProductRecord, Label]) -> None:
    """A text DataMatrix with parenthesized AIs cannot be reused as a GS1 symbol."""
    template, record, label = source
    original = next(e for e in label.elements if e.kind == "barcode")
    code = zxingcpp.create_barcode(original.payload, zxingcpp.BarcodeFormat.DataMatrix, gs1=False)
    pixels = np.asarray(code.to_image(scale=1, add_hrt=False, add_quiet_zones=True))
    read = zxingcpp.read_barcodes(np.repeat(np.repeat(pixels, 4, axis=0), 4, axis=1))[0]
    assert read.text == original.payload and read.content_type != zxingcpp.ContentType.GS1
    matrix = tuple("".join("1" if pixel == 0 else "0" for pixel in row) for row in pixels)
    altered = replace(original, matrix=matrix,
                      module_mm=min(original.bbox_mm[2] / pixels.shape[1], original.bbox_mm[3] / pixels.shape[0]))
    with pytest.raises(ValueError, match="GS1"):
        adapter.from_template(template, record_fields(record), AIS, version_id="v4", actor="parth",
                              reason="Reject plain text", test_data=True, reuse_barcode=altered)
