"""Physical rendering, content integrity and approval tests for Task 2."""

from __future__ import annotations

import hashlib
import json
import shutil
import socket
import subprocess
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

np = pytest.importorskip("numpy")
zxingcpp = pytest.importorskip("zxingcpp")
pytest.importorskip("reportlab")
pytest.importorskip("pypdf")
from PIL import Image  # noqa: E402
from pypdf import PdfReader  # noqa: E402

from src.common.schemas import ProductRecord  # noqa: E402
from src.export.label_model import (  # noqa: E402
    ApprovalRecord,
    Element,
    Label,
    ModuleSizeWarning,
    PassedCheck,
    reference_sha256,
    validate_label,
)
from src.export.pdf import render_pdf  # noqa: E402
from src.export.qr import make_qr  # noqa: E402
from src.export.svg import SVG_NS, render_svg  # noqa: E402
from src.export.template import barcode_element, from_product, from_template  # noqa: E402

AIS = {"01": "00000000000000", "17": "281231", "10": "LOT001", "21": "SN001"}


@pytest.fixture
def sample() -> Label:
    """Create a test-only label with every internal content type."""
    buffer = BytesIO()
    Image.new("RGB", (80, 40), "black").save(buffer, format="PNG")
    return Label(
        100,
        60,
        (
            Element("name", "text", (5, 12, 55, 7), text="TEST DEVICE & <DRAFT>", size_pt=10),
            Element("patch", "image", (5, 25, 20, 10), png=buffer.getvalue()),
            Element("sterile", "symbol", (35, 25, 20, 10), symbol_name="sterile_eo"),
            barcode_element("udi", (65, 20, 30, 30), AIS, module_mm=0.5, test_data=True),
        ),
        "version-1",
        "parth",
        "Task 2 export verification",
        test_data=True,
        review_boxes=((5, 12, 55, 7),),
    )


def rasterize(pdf: Path, output: Path) -> np.ndarray:
    """Use independent Poppler rendering at 600 dpi, without resizing the result."""
    executable = shutil.which("pdftoppm")
    if executable is None:
        pytest.skip("600 dpi validation requires Poppler pdftoppm")
    subprocess.run(
        [executable, "-singlefile", "-png", "-r", "600", str(pdf), str(output)], check=True, capture_output=True
    )
    with Image.open(output.with_suffix(".png")) as image:
        return np.asarray(image.convert("RGB"))


def test_pdf_physical_size_text_and_600dpi_positions(sample: Label, tmp_path: Path) -> None:
    """Measure page size and black image bounds, then decode the printed barcode."""
    pdf = render_pdf(sample, tmp_path / "label.pdf")
    page = PdfReader(pdf).pages[0]
    assert float(page.mediabox.width) == pytest.approx(100 * 72 / 25.4, abs=1e-4)
    assert float(page.mediabox.height) == pytest.approx(60 * 72 / 25.4, abs=1e-4)
    text = page.extract_text()
    assert "TEST DEVICE & <DRAFT>" in text
    assert "TEST DATA | DRAFT" in text
    pixels = rasterize(pdf, tmp_path / "label")
    scale = 600 / 25.4
    assert abs(pixels.shape[1] - 100 * scale) <= 1
    assert abs(pixels.shape[0] - 60 * scale) <= 1
    # Independent full-ink image bounds must match its physical description.
    region = pixels[round(23 * scale) : round(37 * scale), round(3 * scale) : round(27 * scale)]
    rows, columns = np.where(np.min(region, axis=2) < 128)
    observed = (
        columns.min() + round(3 * scale),
        rows.min() + round(23 * scale),
        columns.max() + round(3 * scale) + 1,
        rows.max() + round(23 * scale) + 1,
    )
    expected = tuple(v * scale for v in (5, 25, 25, 35))
    assert np.max(np.abs(np.array(observed) - expected)) <= 1.5
    decoded = zxingcpp.read_barcodes(pixels)
    assert len(decoded) == 1
    assert decoded[0].text == sample.elements[-1].payload
    # Actual rectangle widths in the PDF are checked separately from decode.
    audit = json.loads(pdf.with_suffix(".pdf.json").read_text())
    assert audit["artifact_sha256"] == hashlib.sha256(pdf.read_bytes()).hexdigest()
    assert audit["status"] == "DRAFT" and audit["change_log"] and audit["self_check"]["passed"]


@pytest.mark.parametrize("size", [(50.5, 30.25), (100, 60), (150, 75)])
def test_nonstandard_pdf_sizes(size: tuple[float, float], tmp_path: Path) -> None:
    """Page size follows the description instead of a default printer page."""
    label = Label(
        *size, (Element("text", "text", (2, 10, 40, 8), text="Size test"),), "v1", "parth", "physical size test"
    )
    page = PdfReader(render_pdf(label, tmp_path / "size.pdf")).pages[0]
    assert float(page.mediabox.width) == pytest.approx(size[0] * 72 / 25.4, abs=1e-4)
    assert float(page.mediabox.height) == pytest.approx(size[1] * 72 / 25.4, abs=1e-4)


def test_svg_layers_fields_coordinates_and_vector_bars(sample: Label, tmp_path: Path) -> None:
    """SVG keeps named layers, escaped editable text and exact square modules."""
    root = ET.parse(render_svg(sample, tmp_path / "label.svg")).getroot()
    ns = {"s": SVG_NS}
    assert root.attrib["width"] == "100mm" and root.attrib["viewBox"] == "0 0 100 60"
    groups = {node.attrib["id"]: node for node in root.findall(".//s:g", ns)}
    assert {"layer-background", "layer-slots", "layer-watermark", "layer-review"} <= groups.keys()
    for element in sample.elements:
        assert element.field in groups
        group = groups[f"slot-{element.field}"]
        assert tuple(map(float, group.attrib["data-bbox-mm"].split())) == element.bbox_mm
    assert groups["slot-udi"].attrib["data-payload"] == sample.elements[-1].payload
    rects = groups["udi"].findall("s:rect", ns)
    assert rects and not groups["udi"].findall("s:image", ns)
    assert all(float(rect.attrib["height"]) == 0.5 for rect in rects)
    assert all(
        float(rect.attrib["width"]) / 0.5 == pytest.approx(round(float(rect.attrib["width"]) / 0.5)) for rect in rects
    )
    assert groups["name"].find("s:text", ns).text == "TEST DEVICE & <DRAFT>"
    assert groups["layer-review"].find("s:rect", ns) is not None
    assert len(groups) == len(root.findall(".//s:g", ns))


def test_review_highlights_never_change_print(sample: Label, tmp_path: Path) -> None:
    """The PDF bytes are unchanged when only review highlights are supplied."""
    first = render_pdf(sample, tmp_path / "with.pdf").read_bytes()
    second = render_pdf(replace(sample, review_boxes=()), tmp_path / "without.pdf").read_bytes()
    assert first == second


@pytest.mark.parametrize(
    "symbology,box,module",
    [
        ("GS1_DataMatrix", (5, 12, 35, 35), 0.5),
        ("GS1-128", (5, 12, 135, 30), 0.3),
    ],
)
def test_both_gs1_formats_survive_pdf_rasterization(
    symbology: str,
    box: tuple[float, float, float, float],
    module: float,
    tmp_path: Path,
) -> None:
    """Vector GS1 formats remain decodable after independent 600 dpi rendering."""
    element = barcode_element("udi", box, AIS, symbology=symbology, module_mm=module, test_data=True)
    label = Label(150, 60, (element,), "v1", "parth", "GS1 print test", test_data=True)
    pdf = render_pdf(label, tmp_path / "barcode.pdf")
    pixels = rasterize(pdf, tmp_path / "barcode")
    decoded = zxingcpp.read_barcodes(pixels)
    assert len(decoded) == 1 and decoded[0].text == element.payload
    # Check the actual PDF bar heights and widths, in points, before rasterization.
    operations = PdfReader(pdf).pages[0].get_contents().operations
    rectangles = [args for args, operator in operations if operator == b"re"]
    assert rectangles
    for _, _, width, height in rectangles:
        assert float(height) == pytest.approx(module * 72 / 25.4, abs=1e-5)
        ratio = float(width) / (module * 72 / 25.4)
        assert ratio == pytest.approx(round(ratio), abs=1e-4)


@pytest.mark.parametrize(
    "payload",
    [
        "https://example.org/verify/version-1",
        '{"version_id":"v2","url":"https://example.org/v2"}',
        "Version 3: café",
        "x" * 200,
    ],
)
def test_qr_png_and_svg_payload(payload: str) -> None:
    """Verification text survives QR PNG encoding exactly, including Unicode."""
    qr = make_qr(payload)
    with Image.open(BytesIO(qr.png)) as image:
        decoded = zxingcpp.read_barcodes(np.asarray(image))
    assert len(decoded) == 1 and decoded[0].text == payload
    assert ET.fromstring(qr.svg).tag == f"{{{SVG_NS}}}svg"


def test_qr_invalid_input_and_failed_decode(monkeypatch: pytest.MonkeyPatch) -> None:
    """No empty or undecodable QR is returned as successful artwork."""
    with pytest.raises(ValueError):
        make_qr("")
    with pytest.raises(ValueError):
        make_qr("payload", scale=0)
    monkeypatch.setattr(zxingcpp, "read_barcodes", lambda _: [])
    with pytest.raises(RuntimeError):
        make_qr("payload")


def test_approval_requires_matching_check_and_independent_reviewer(sample: Label, tmp_path: Path) -> None:
    """Review binding is checked; prototype warnings are never production authorization."""
    fingerprint = reference_sha256(sample)
    approval = ApprovalRecord("pari", sample.version_id, fingerprint, "check-1", reviewer_role="reviewer")
    check = PassedCheck("check-1", sample.version_id, fingerprint, True)
    pdf = render_pdf(
        sample, tmp_path / "approved.pdf", approval=approval, check=check, authorized_reviewers=frozenset({"pari"})
    )
    text = PdfReader(pdf).pages[0].extract_text()
    assert "TEST DATA\n" in text and "TEST DATA | DRAFT" not in text
    assert json.loads(pdf.with_suffix(".pdf.json").read_text())["check_id"] == "check-1"
    invalid = [
        (replace(approval, check_id=""), check, sample, frozenset({"pari"})),
        (replace(approval, reviewer_role="editor"), check, sample, frozenset({"pari"})),
        (approval, replace(check, passed=False), sample, frozenset({"pari"})),
        (approval, replace(check, version_id="wrong"), sample, frozenset({"pari"})),
        (approval, replace(check, reference_sha256="wrong"), sample, frozenset({"pari"})),
        (approval, check, replace(sample, reason="changed"), frozenset({"pari"})),
        (approval, check, sample, frozenset()),
        (replace(approval, reviewer="parth"), check, sample, frozenset({"parth"})),
    ]
    for index, (record, result, label, reviewers) in enumerate(invalid):
        with pytest.raises(PermissionError):
            render_svg(
                label, tmp_path / f"invalid-{index}.svg", approval=record, check=result, authorized_reviewers=reviewers
            )
        assert not (tmp_path / f"invalid-{index}.svg").exists()


@pytest.mark.parametrize(
    "bad",
    [
        Element("x", "text", (0, 1, 20, 8), text="heading collision"),
        Element("x", "text", (95, 15, 20, 8), text="clipped"),
        Element("x", "text", (2, 15, 5, 3), text="long unbreakable text"),
        Element("x", "symbol", (2, 15, 10, 10), symbol_name="unknown"),
        Element("x", "text", (2, 15, 20, 8), text="", size_pt=3),
    ],
)
def test_invalid_layout_does_not_write_files(bad: Element, tmp_path: Path) -> None:
    """Critical layout errors stop both writers before any artwork is saved."""
    label = Label(100, 60, (bad,), "v1", "parth", "negative layout test")
    for writer in (render_pdf, render_svg):
        with pytest.raises(ValueError):
            writer(label, tmp_path / writer.__name__)
        assert not (tmp_path / writer.__name__).exists()


def test_exact_modules_warn_or_refuse_without_stretching(sample: Label, tmp_path: Path) -> None:
    """Too-small modules warn, and modules that cannot fit are never shrunk."""
    barcode = sample.elements[-1]
    small = replace(sample, elements=(replace(barcode, module_mm=0.2),))
    with pytest.warns(ModuleSizeWarning):
        render_pdf(small, tmp_path / "small.pdf", min_module_mm=0.25)
    with pytest.raises(ValueError, match="cannot fit"):
        validate_label(replace(sample, elements=(replace(barcode, module_mm=10),)))


@pytest.mark.parametrize("size_mm", [(100, 60), (106.25, 64.5)])
def test_template_adapter_and_product_schema(tmp_path: Path, size_mm: tuple[float, float]) -> None:
    """The existing template exports against the locked ProductRecord schema."""
    template = json.loads(Path("src/gen/templates/test_device.json").read_text())
    template["size_mm"] = {"w": size_mm[0], "h": size_mm[1]}
    record = ProductRecord(
        product_id="test-device",
        name="Test Device",
        model="REF001",
        manufacturer="Test Labs",
        manufacturer_address="Test address",
        udi_di="00000000000000",
        extra={"expiry": "2028-12-31", "lot": "LOT001"},
    )
    label = from_product(template, record, version_id="v1", actor="parth", reason="adapter test", test_data=True)
    assert {e.slot_id for e in label.elements} == {slot["id"] for slot in template["slots"]}
    assert "(21)" not in next(e.payload for e in label.elements if e.kind == "barcode")
    pdf = render_pdf(label, tmp_path / "template.pdf")
    page = PdfReader(pdf).pages[0]
    assert abs(float(page.mediabox.width) * 25.4 / 72 - template["size_mm"]["w"]) <= 0.1
    assert abs(float(page.mediabox.height) * 25.4 / 72 - template["size_mm"]["h"]) <= 0.1
    svg = render_svg(label, tmp_path / "template.svg")
    root = ET.parse(svg).getroot()
    slots = root.find(f"{{{SVG_NS}}}g[@id='layer-slots']")
    assert slots is not None
    expected_ids = {f"slot-{slot['id']}" for slot in template["slots"]}
    assert {node.attrib["id"] for node in slots} == expected_ids
    assert len(slots) == len(template["slots"])
    for slot in template["slots"]:
        group = slots.find(f"{{{SVG_NS}}}g[@id='slot-{slot['id']}']")
        assert group is not None and group.attrib["data-field"] == slot["field"]
    with pytest.raises(ValueError, match="background"):
        from_template(
            {**template, "background": "existing.svg"},
            {},
            AIS,
            version_id="v1",
            actor="parth",
            reason="negative test",
            test_data=True,
        )


def test_overlap_duplicate_ids_and_immutable_outputs(sample: Label, tmp_path: Path) -> None:
    """Overlapping or duplicate fields fail, and saved versions cannot be overwritten."""
    with pytest.raises(ValueError, match="overlap"):
        validate_label(
            replace(sample, elements=(sample.elements[0], replace(sample.elements[1], bbox_mm=(5, 12, 20, 10))))
        )
    with pytest.raises(ValueError, match="unique"):
        validate_label(replace(sample, elements=(sample.elements[0], sample.elements[0])))
    pdf = render_pdf(sample, tmp_path / "immutable.pdf")
    before = pdf.read_bytes()
    with pytest.raises(FileExistsError):
        render_pdf(sample, pdf)
    assert pdf.read_bytes() == before


@pytest.mark.parametrize("name", ["manufacturer", "expiry", "sterile", "sterile_eo", "sterile_r"])
def test_supported_symbols_render_as_vectors(name: str, tmp_path: Path) -> None:
    """All four simplified symbols are exported as vector shapes or editable text."""
    label = Label(
        50,
        30,
        (Element("symbol", "symbol", (5, 12, 15, 12), symbol_name=name),),
        "v1",
        "parth",
        "symbol test",
        test_data=True,
    )
    root = ET.parse(render_svg(label, tmp_path / f"{name}.svg")).getroot()
    assert root.findall(f".//{{{SVG_NS}}}g[@id='symbol']/*")
    assert not root.findall(f".//{{{SVG_NS}}}image")
    render_pdf(label, tmp_path / f"{name}.pdf")


def test_reserved_svg_ids_and_tampered_matrix_are_rejected(sample: Label) -> None:
    """Reserved layers and barcode content cannot be overwritten by field data."""
    with pytest.raises(ValueError, match="unique"):
        validate_label(replace(sample, elements=(replace(sample.elements[0], field="layer-slots"),)))
    barcode = sample.elements[-1]
    with pytest.raises(ValueError, match="decode"):
        validate_label(replace(sample, elements=(replace(barcode, payload="wrong data"),)))
    with pytest.raises(ValueError, match="binary"):
        validate_label(replace(sample, elements=(replace(barcode, matrix=("xyz",)),)))


def test_svg_approval_retains_test_mark_and_audit(sample: Label, tmp_path: Path) -> None:
    """Approved test data remains visibly marked and records its passed check ID."""
    fingerprint = reference_sha256(sample)
    root_path = render_svg(
        sample,
        tmp_path / "approved.svg",
        approval=ApprovalRecord("pari", sample.version_id, fingerprint, "check-1", reviewer_role="reviewer"),
        check=PassedCheck("check-1", sample.version_id, fingerprint, True),
        authorized_reviewers=frozenset({"pari"}),
    )
    root = ET.parse(root_path).getroot()
    headings = root.findall(f"{{{SVG_NS}}}g[@id='layer-watermark']/{{{SVG_NS}}}text")
    assert {heading.text for heading in headings} == {"TEST DATA", "DRAFT, not for production"}
    audit = json.loads(root_path.with_suffix(".svg.json").read_text())
    assert audit["check_id"] == "check-1" and audit["reference_sha256"] == fingerprint
    assert audit["artifact_sha256"] == hashlib.sha256(root_path.read_bytes()).hexdigest()


def test_barcode_rectangles_have_correct_physical_origin(sample: Label, tmp_path: Path) -> None:
    """The printed module matrix is centred in its specified physical slot."""
    pdf = render_pdf(replace(sample, elements=(sample.elements[-1],)), tmp_path / "origin.pdf")
    bars = [args for args, op in PdfReader(pdf).pages[0].get_contents().operations if op == b"re"]
    barcode = sample.elements[-1]
    x, y, w, h = barcode.bbox_mm
    matrix = np.array([[int(bit) for bit in row] for row in barcode.matrix])
    rows, cols = np.where(matrix == 1)
    module = barcode.module_mm
    left = x + (w - matrix.shape[1] * module) / 2
    top = y + (h - matrix.shape[0] * module) / 2
    # ReportLab's y origin is at the bottom; the internal description is top-left.
    observed_left = min(float(args[0]) for args in bars) * 25.4 / 72
    observed_top = sample.height_mm - max(float(args[1] + args[3]) for args in bars) * 25.4 / 72
    assert observed_left == pytest.approx(left + cols.min() * module, abs=1e-4)
    assert observed_top == pytest.approx(top + rows.min() * module, abs=1e-4)


def test_reused_test_barcode_cannot_lose_test_watermark(sample: Label, tmp_path: Path) -> None:
    """Direct matrix reuse must not bypass the all-zero GTIN test-data rule."""
    from src.common.schemas import IdentifierRequired

    with pytest.raises(IdentifierRequired):
        render_pdf(replace(sample, test_data=False), tmp_path / "unmarked.pdf")
    assert not (tmp_path / "unmarked.pdf").exists()


def test_product_extra_cannot_override_core_fields() -> None:
    """Auxiliary fields cannot replace canonical product identity in exported text."""
    template = json.loads(Path("src/gen/templates/test_device.json").read_text())
    record = ProductRecord(
        product_id="test-device",
        name="Canonical Device",
        model="REF001",
        manufacturer="Canonical Labs",
        manufacturer_address="Test address",
        udi_di="00000000000000",
        extra={
            "expiry": "2028-12-31",
            "lot": "LOT001",
            "name": "Wrong name",
            "product_name": "Wrong alias",
            "manufacturer": "Wrong manufacturer",
        },
    )
    label = from_product(template, record, version_id="v1", actor="parth", reason="identity check", test_data=True)
    fields = {element.field: element.text for element in label.elements if element.kind == "text"}
    assert fields["product_name"] == record.name
    assert fields["manufacturer"] == record.manufacturer


def test_repeated_product_field_keeps_distinct_slot_groups(tmp_path: Path) -> None:
    """The same product field can be printed in multiple independently editable slots."""
    template = {
        "template_id": "repeat-name",
        "version": 1,
        "background": None,
        "size_mm": {"w": 100, "h": 60},
        "slots": [
            {"id": "top-name", "field": "name", "type": "text", "bbox_mm": [5, 12, 60, 7], "size_pt": 10},
            {"id": "bottom-name", "field": "name", "type": "text", "bbox_mm": [5, 25, 60, 7], "size_pt": 10},
        ],
    }
    label = from_template(template, {"name": "Test Device"}, {}, version_id="v1", actor="parth", reason="repeat test")
    root = ET.parse(render_svg(label, tmp_path / "repeat.svg")).getroot()
    ids = [node.attrib["id"] for node in root.iter() if "id" in node.attrib]
    assert len(ids) == len(set(ids))
    for slot_id in ("top-name", "bottom-name"):
        group = root.find(f".//{{{SVG_NS}}}g[@id='slot-{slot_id}']")
        assert group is not None and group.attrib["data-field"] == "name"
        assert any(node.text == "Test Device" for node in group.iter(f"{{{SVG_NS}}}text"))
    page = PdfReader(render_pdf(label, tmp_path / "repeat.pdf")).pages[0]
    assert page.extract_text().count("Test Device") == 2


def test_published_url_qr_generation_never_connects_to_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """The published-page URL is encoded literally without visiting the address."""

    def reject_connection(*args: object, **kwargs: object) -> None:
        """Fail if any network connection is attempted by QR generation."""
        raise AssertionError("QR generation must not use the network")

    monkeypatch.setattr(socket, "create_connection", reject_connection)
    monkeypatch.setattr(socket.socket, "connect", reject_connection)
    payload = "https://example.org/published/test-device/version-2"
    qr = make_qr(payload)
    with Image.open(BytesIO(qr.png)) as image:
        decoded = zxingcpp.read_barcodes(np.asarray(image))
    assert len(decoded) == 1 and decoded[0].text == payload


def test_nonproduction_mark_and_approved_prototypes(sample: Label, tmp_path: Path) -> None:
    """Test identifiers and synthetic pictograms keep their warning even after test approval."""
    from src.export.label_model import watermark_lines

    mark = 'DRAFT, not for production'
    assert mark in watermark_lines(sample, False)
    assert mark in watermark_lines(sample, True)
    symbol_only = replace(sample, test_data=False,
                          elements=(Element('symbol', 'symbol', (5, 12, 10, 10), symbol_name='manufacturer'),))
    assert watermark_lines(symbol_only, True) == (mark,)
    placeholder_only = replace(sample, test_data=False,
                               elements=tuple(e for e in sample.elements if e.kind == 'barcode'))
    assert watermark_lines(placeholder_only, True) == (mark,)
    text_only = replace(symbol_only, elements=(Element('name', 'text', (5, 12, 20, 10), text='Demo'),))
    assert watermark_lines(text_only, True) == ()
    fingerprint = reference_sha256(sample)
    approval = ApprovalRecord('test_reviewer', sample.version_id, fingerprint, 'test-mark', reviewer_role='reviewer')
    check = PassedCheck('test-mark', sample.version_id, fingerprint, True)
    kwargs = {'approval': approval, 'check': check, 'authorized_reviewers': frozenset({'test_reviewer'})}
    pdf = render_pdf(sample, tmp_path / 'prototype.pdf', **kwargs)
    svg = render_svg(sample, tmp_path / 'prototype.svg', **kwargs)
    assert mark in PdfReader(pdf).pages[0].extract_text()
    assert mark in ''.join(ET.fromstring(svg.read_text()).itertext())
    assert mark in json.loads(pdf.with_suffix('.pdf.json').read_text())['visible_markings']
