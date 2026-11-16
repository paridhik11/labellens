# Task 2: physical-size export

This package exports an immutable label description as a physical-size PDF and
an editable SVG. It adapts the current blank-background template contract and
uses Task 1's GS1 encoder. It does not call OCR, edit CV code, approve a label,
or publish anything.

## Files and interfaces

| File | Interface |
|---|---|
| `label_model.py` | `Element`, `Label`, `ApprovalRecord`, `PassedCheck`, layout checks and reference hashing |
| `template.py` | `from_template`, `from_product`, `barcode_element` |
| `pdf.py` | `render_pdf(label, path, min_module_mm=0.25, ...)` |
| `svg.py` | `render_svg(label, path, min_module_mm=0.25, ...)` |
| `qr.py` | `make_qr(payload)` returns `.png` bytes, `.svg` text and `.payload` |

All coordinates are millimetres from the top left. PDF coordinates are converted
with `points = mm * 72 / 25.4`, with the y axis reversed. SVG uses millimetre
width/height and a matching viewBox. Supported element types are text, embedded
PNG image, binary barcode matrix and simplified vector symbol.

Text remains text in both formats. Standard PDF fonts, printable ASCII and
explicit line limits are supported. Long text is wrapped by measured font width;
overflow is refused. SVG viewers need the chosen font installed to reproduce
its typography. A PNG image fills its explicitly specified box. Background is
`null` only, as agreed for this template family.

A barcode's `module_mm` is its exact square module width, including its quiet
zone grid. It is centred in its box and never stretched or shrunk to fit. A
caller-selected minimum produces `ModuleSizeWarning` when crossed. A barcode
that cannot fit at the requested width is refused. The default 0.25 mm threshold
is a project setting, not a universal GS1 printing requirement.

The adapter preserves template slot IDs and creates the named SVG groups
`layer-background`, `layer-slots`, `slot-{id}`, `layer-watermark` and
`layer-review`. Each field also has its own group named after the field, as in
the original Task 2 brief. IDs must be unique; ambiguous collisions are refused.
Barcode slots contain vector rectangles and `data-payload`.
Review highlights appear in SVG only and never affect the PDF.
A product field can appear in multiple slots with different slot IDs. Each
occurrence keeps its own `slot-{id}` group; the alias using the field name is
emitted only once, preventing duplicate SVG IDs.

The 9 mm DRAFT band follows the current renderer and Paridhi's handoff, which
supersedes the older contract's 6 mm draft default. Symbol names are
`manufacturer`, `expiry`, `sterile`, `sterile_eo`, and `sterile_r`. These are simplified
synthetic test drawings, not licensed or certified ISO artwork.

## Usage

Run from the repository root, using the CV environment and dependencies already
recorded in `requirements-cv.txt`. No dependency was added for Task 2.

```python
import json
from pathlib import Path
from src.common.schemas import ProductRecord
from src.export.template import from_product
from src.export.pdf import render_pdf
from src.export.svg import render_svg
from src.export.qr import make_qr

template = json.loads(Path("src/gen/templates/test_device.json").read_text())
record = ProductRecord(
    product_id="test-device",
    name="Test Device",
    model="REF001",
    manufacturer="Test Labs",
    manufacturer_address="Test address",
    udi_di="00000000000000",  # Explicit existing test placeholder only.
    extra={"expiry": "2028-12-31", "lot": "LOT001", "serial": "SN001"},
)
label = from_product(template, record, version_id="test-v1", actor="parth", reason="Task 2 test export", test_data=True)
render_pdf(label, Path("output/test-v1/label.pdf"))
render_svg(label, Path("output/test-v1/label.svg"))
qr = make_qr("https://example.org/verify/test-v1")  # Example URL, no hosted service.
Path("output/test-v1/qr.png").write_bytes(qr.png)
Path("output/test-v1/qr.svg").write_text(qr.svg)
```

Rendered files cannot overwrite an existing version. Each writer also produces
an audit sidecar (`label.pdf.json`, `label.svg.json`) containing the content hash,
reference hash, version, change log and a scoped self-check. That check covers
layout, text measurements and the source barcode decode. It does not claim OCR,
regulatory checking, symbol recognition or a physical printer test.

The template and field mapping are export inputs, not a change-request engine.
Call Task 1's decision policy before a revision, and keep the existing barcode
matrix when its decision is KEEP. `barcode_element` builds a new matrix only
when the caller is generating a new barcode. Direct `Element` input supports
an existing matrix without regenerating it.

## Approval and check_id

Draft output is the default and always carries DRAFT. TEST DATA remains visible
even on an approved test export. This package accepts approval records from the
application; it never creates one. To remove DRAFT, supply all of:

- `ApprovalRecord` with reviewer, reviewer_role (`reviewer` or `admin`), version_id, reference_sha256 and nonempty check_id.
- A `PassedCheck` with the same check_id, version_id and reference_sha256, and passed=True.
- The trusted application's authorized reviewer set. The creator cannot approve their own label.

The reference hash is `reference_sha256(label)`: SHA-256 of the canonical export
snapshot, including image bytes, fields, geometry, version and change reason.
Any content edit invalidates the approval. The sidecar separately records the
actual PDF or SVG bytes' artifact hash. These are local export records, not
changes to `src/common/schemas.py`. The eventual server adapter must map its
stored Review/CheckResult and generated-artwork manifest onto this local
snapshot; the exporter does not treat a client-supplied reviewer set as login.
This local gate is not publication.

## Libraries and Windows evidence

ReportLab is already installed and produces PDF vectors and real text without
Ghostscript or Cairo. zxing-cpp is already installed and produces PNG/SVG QR
codes plus GS1 matrices, which are decoded again before use. Pillow embeds PNG
images. Tests use the existing pypdf installation and Poppler's `pdftoppm` for
independent 600 dpi rendering; Poppler is not required just to export files.

Windows Python 3.12 packages for ReportLab 5.1.0 and zxing-cpp 3.1.1 were
successfully downloaded using pip with `--only-binary=:all:` and
`--platform win_amd64`. ReportLab's wheel is platform independent; zxing-cpp's
wheel is Windows x86-64. An actual Windows runtime/install test was not run on
this Mac. Installation inside a user-created venv does not need a system-wide
package installation.

Sources:

- PDF drawing API: https://docs.reportlab.com/reportlab/userguide/ch2_graphics/
- QR/image/SVG writing: https://github.com/zxing-cpp/zxing-cpp/blob/master/wrappers/python/README.md
- GS1 rules and citations: `src/gen/GS1_REVIEW.md`
- Layout/groups: `docs/contracts/TEMPLATE_SPEC.md`, with the handoff's 9 mm band and background-null limit.

## Reproduce the checks

```sh
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider tests/test_export.py tests/test_gs1.py
/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check --no-cache src/export tests/test_export.py
```

The export tests check nonstandard page sizes, extractable PDF text, XML escaping
and named groups, PNG embedding, all five supported symbols, immutable outputs, blocked
overflow/overlap/clipping, module warnings, exact barcode dimensions and origins,
both GS1 formats decoded from independent 600 dpi renders, QR payloads, valid
approval and rejected stale, failed, missing or unauthorized approvals.

Executed on 2026-11-15 in the CV Conda environment:

```text
........................................................................ [ 83%]
..............                                                           [100%]
86 passed in 50.14s
```

This is 30 export tests plus 56 GS1 tests. It includes synthetic software output
checks, not an accuracy result on real labels or printed phone photographs.
The 600 dpi position check uses a 1.5-pixel tolerance (about 0.064 mm); PDF page
dimensions are checked to 0.0001 point. Both printed GS1 test formats decoded.
A sample with the new sterile symbol and a verification QR was rendered and
visually inspected at `/tmp/labellens-task2-sample/`. Temporary examples are not
committed; the usage example above recreates a draft from the existing fixture.

## Task 5 approval and renderer alignment

`src/export/approval.py` holds the shared local records and approval gate. Existing
imports from `label_model` remain available. `reviewer_role` is required, and
authorization still comes from the trusted application, not the uploaded role.
The canonical hash field stays `reference_sha256`, as clarified by Paridhi.
`approval_from_records` also maps API `user_id`/`artifact_sha256` to the local
names and refuses conflicting aliases or a check with critical findings.

`verify_print` now needs `check_record` as well as `approval_record`. The passed
check must have the same check ID, version and exact manifest hash as the review.
Missing or old records without that evidence fail before OCR. The original
generator now writes `version_id` and `created_by`, supports all five symbol
names and emits named SVG layers/slots too. It accepts an explicit version ID;
otherwise its local ID is derived from product ID and record version.

The print verifier hashes the original generated manifest bytes. The standalone
exporter continues to hash its canonical Label snapshot. These references are
different representations and must not be interchanged without an explicit
application mapping and a new check for the chosen reference. No approval is
automatically issued. Real symbol detection accuracy has not been established.
