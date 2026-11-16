# Generation and medicine handoff for Pari

Updated 2026-11-16. App integration, authentication, review storage and publication
remain Pari's responsibility. No function below creates an approval or publishes.
Import renderers inside the generateArtwork worker, after CV dependencies are
available. `src.cv.extract` and `src.gen.medicine` themselves are importable without
CV libraries. Contract CR-2,3,4,5,9,10,11 are accepted by Pari.

## Recommended generation path: immutable export snapshots

All coordinates are millimetres from the top left. Read the authoritative
`docs/contracts/TEMPLATE_SPEC.md`; background must be null. Every slot has a
unique id, type, field and bbox_mm. Text slots also specify font, size_pt, align
and max_lines; symbols specify symbol_name; barcode slots specify symbology.
Only built-in synthetic pictograms are implemented; these are not certified.

```python
from src.export.template import from_product, from_template

from_product(template: Mapping[str, Any], record: ProductRecord, *,
             version_id: str, actor: str, reason: str,
             test_data: bool = False) -> Label

from_template(template: Mapping[str, Any], fields: Mapping[str, str],
              gs1_elements: Mapping[str, str], *, version_id: str,
              actor: str, reason: str, test_data: bool = False,
              barcode_module_mm: float | None = None,
              reuse_barcode: Element | None = None) -> Label
```

The input ProductRecord is the unchanged shared schema. Required binding values
include name, manufacturer, manufacturer_address and model, plus allocated
udi_di and extra.expiry (ISO YYYY-MM-DD), extra.lot and optional extra.serial.
Identifiers come from the caller. The existing all-zero placeholder requires
explicit test_data=True and is never a production identifier.

Label is a frozen dataclass containing width_mm, height_mm, elements (tuple of
Element), version_id, created_by, reason, template_id, template_version,
test_data and review_boxes. Element contains field, kind, bbox_mm, slot_id and
its text/font, symbol_name, PNG bytes or barcode matrix/module_mm/payload/
symbology. Do not treat this dataclass as the API data model. Pari maps it in
step 24b. Use reference_sha256(label) for the canonical snapshot fingerprint;
image bytes are base64-encoded by that canonical hasher. Hashing a different JSON
serialization will not produce the same reference.

## Structured changes and REGENERATE

```python
from src.gen.revise import revise_template

revise_template(template: Mapping[str, Any], record: ProductRecord,
                change: ChangeRequest, *, previous_label: Label,
                version_id: str, actor: str, reason: str,
                confirmed: Mapping[str, bool] | None = None,
                requires_new_identifier: bool = False,
                allocated_identifier: str | None = None) -> RevisionResult
```

ChangeRequest payload: change_id, product_id, field, old_value, new_value, status.
One field edit per call. The source record/template must match previous_label.
A fresh version_id, actor and reason are required. No in-place edits.

RevisionResult contains template (new version), record (new version), fields,
barcode_decision (action/reason), label or None, change_log,
required_identifier and self_check. status is DRAFT or NEEDS_INPUT.

- KEEP: exact prior barcode Element/matrix is reused, without encoding again.
- REGENERATE: changed encoded values must be confirmed. For a lot change pass
  confirmed={"confirmed_lot_change": True}. Other flags are
  confirmed_gtin_change, confirmed_expiry_change and confirmed_serial_change.
  The engine encodes the new GS1 matrix and decodes it to check exact payload.
  Export result.require_label(); never render the old Label as the revised one.
- NEEDS_INPUT: label is None and no artwork exists. require_label() raises
  IdentifierRequired for missing allocated identifiers, ValueError otherwise.
  Return a blocked response to the caller; do not silently fall back to KEEP.

The lower-level policy is
`decide_barcode(old_elements, new_values, confirmed=None, *, old_symbology=...,
new_symbology=...) -> BarcodeDecisionResult`. A policy result alone contains no
artwork. `barcode_element(field, bbox_mm, elements, *, symbology="GS1_DataMatrix", ...)` is the
lower-level encoder; normal application integration should use revise_template.

## Executable test-only example

```python
import json
from pathlib import Path
from src.common.schemas import ChangeRequest, ProductRecord
from src.export.template import from_product
from src.export.pdf import render_pdf
from src.export.svg import render_svg
from src.export.qr import make_qr
from src.gen.revise import revise_template

def example(output_dir: str | Path) -> dict[str, object]:
    """Render an explicitly test-only confirmed revision without approval."""
    output_dir = Path(output_dir)
    template = json.loads(Path('src/gen/templates/test_device.json').read_text())
    record = ProductRecord(
        product_id='handoff-test', name='TEST DEVICE', model='TEST-MODEL',
        manufacturer='Demo Labs', manufacturer_address='12 Demo Road',
        udi_di='00000000000000',
        extra={'lot': 'TESTLOT1', 'expiry': '2033-06-15', 'serial': 'TESTSERIAL'},
    )
    old = from_product(template, record, version_id='test-v1', actor='editor',
                       reason='test fixture', test_data=True)
    change = ChangeRequest(change_id='test-change', product_id=record.product_id,
                           field='lot', old_value='TESTLOT1', new_value='TESTLOT2')
    result = revise_template(
        template, record, change, previous_label=old, version_id='test-v2',
        actor='editor', reason='test lot revision',
        confirmed={'confirmed_lot_change': True},
    )
    label = result.require_label()
    pdf = render_pdf(label, output_dir/'label.pdf')
    svg = render_svg(label, output_dir/'label.svg')
    qr = make_qr('https://example.org/published/test-v2')
    (output_dir/'qr.png').write_bytes(qr.png)
    (output_dir/'qr.svg').write_text(qr.svg)
    return {'version_id': label.version_id, 'status': result.status,
            'barcode_decision': result.barcode_decision.action.value,
            'files': {'pdf': str(pdf), 'svg': str(svg), 'qr': str(output_dir/'qr.png')},
            'change_log': list(result.change_log), 'self_check': result.self_check}
```

The example deliberately uses only the already-established test placeholder and
example.org URL. It does not allocate identifiers, issue approval or host a page.
A regression test executes this exact example from this document.

## PDF, SVG and QR outputs

```python
render_pdf(label: Label, path: Path, *, min_module_mm: float = 0.25,
           approval: ApprovalRecord | None = None, check: PassedCheck | None = None,
           authorized_reviewers: frozenset[str] = frozenset()) -> Path
# render_svg has the same signature and returns Path.
make_qr(payload: str, *, scale: int = 5) -> QRCode
```

PDF has exact physical page size. SVG has layer-background, layer-slots,
slot-{id}, layer-watermark and layer-review groups. QRCode contains payload,
png bytes and svg text; no network request is made. QR is a supplementary URL,
not a GS1 identifier, label approval or an authentication mechanism.

Files are immutable: existing artifact or sidecar paths raise FileExistsError.
PDF/SVG sidecars include version_id, reference_sha256 (snapshot), artifact_sha256
(actual output bytes), status, test_data, check_id, visible_markings, change_log
and scoped self_check. Layout failures raise ValueError. Missing required product
values/identifiers are not generated. Supported GS1 types: GS1_DataMatrix and
GS1-128. Source barcode decode/layout checks are not OCR or compliance validation.

Every draft visibly carries `DRAFT, not for production`. Embedded raster artwork
also retains the mark because this format has no certification provenance. Placeholder identifiers
and built-in non-certified pictograms retain this mark even if a test snapshot
has valid reviewer evidence. A prototype approval never makes that artwork
production-ready. Approval requires trusted independent reviewer/role, exact
version/reference fingerprint and matching passed check_id. Do not fabricate
these records in generateArtwork or infer authorization from request JSON.

## Legacy manifest package path

```python
from src.gen.render import render_label
render_label(template_spec: dict[str, Any], record: ProductRecord,
             output_dir: Path, *, actor: str, reason: str, test_data: bool = False,
             previous_manifest: dict[str, Any] | None = None,
             confirmed_encoded_change: bool = False,
             version_id: str | None = None) -> RenderResult
```

RenderResult fields: svg, pdf, preview, manifest (paths), barcode_action
(`generated`/`reused`), change_log, self_check and status DRAFT. Output is atomic
and contains label.svg, label.pdf, label.png and manifest.json. This path requires
Poppler pdftoppm for preview/self-check and retains legacy template restrictions.
A confirmed changed payload sets confirmed_encoded_change=True. Prefer the newer
revision engine's per-field confirmations. Legacy manifest-byte hashes and
canonical export-snapshot hashes are different and must never be interchanged.

## Medicine corpus loader for retrieval

```python
from src.gen.medicine import load_medicine_corpus
chunks = load_medicine_corpus('data/medicine/corpus.jsonl')  # list[Chunk]
rows = [chunk.model_dump() for chunk in chunks]
```

No CV dependencies or index/model are loaded. The loader validates the entire
file before returning, rejecting duplicate IDs, mixed modules, wrong keys and
content-hash mismatches. Every row has exactly these existing Chunk fields:

```json
{"chunk_id": "source-defined stable id", "source": "DailyMed", "url": "source URL",
 "title": "product and section title", "section": "category/LOINC/index",
 "text": "verbatim source passage", "fetched": "YYYY-MM-DD",
 "hash": "first 16 hex characters of SHA-256(text UTF-8)", "module": "medicine"}
```

The committed corpus has 147 passages for ten pinned medicine products. Adjacent
products.json maps chunk IDs to product source URL, SPL version and effective_date
(the SPL document date). SOURCES.md records the pinned catalog and rights notes.
Re-fetch with `python -m scripts.real.build_medicine_corpus`; add --offline for
cached XML. Device data/results remain separate. Pari chooses/indexes these
passages in her retriever; this change does not edit src/ir.

## Real artwork and photo limitations

Pinned DailyMed re-fetch: `python scripts/real/fetch_dailymed.py` (or --offline).
The catalog in data/real/SOURCES.md recreates 20 device artworks and 44 LLM-labelled
symbol crops. No DailyMed image/PDF/archive is tracked; only two existing
synthetic symbol-reference PNGs remain. Ignore rules keep downloads local.
The grouped photo protocol is scripts/cv_experiments/photo_split_v2.json. Human
photo/crop review stays deferred; real-symbol accuracy is unmeasured. Photo
references are LLM-generated transcriptions. Previously exposed photos cannot
be presented as a new unseen holdout. See the current report for exact counts
and intervals; never substitute synthetic success for real-photo accuracy.
