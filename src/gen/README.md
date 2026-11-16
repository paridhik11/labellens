# Synthetic test labels

Run from the repository root with the CV environment's Python:

```bash
python -m src.gen.generate_dataset --output-dir data/synthetic/task1 --seed 42
```

The default is 17 different base labels, each rendered as clean, moderate and
hard: 51 PNG images with 51 matching JSON files. Use `--labels-per-condition 2`
for a smaller run. Product, manufacturer, address, model, lot, expiry and serial
values vary. The three conditions for a base label share the same field values
and barcode payload. All images retain the template's TEST DATA and DRAFT text.

The existing all-zero AI 01 value is a test placeholder, not an allocated GTIN.
This command never allocates identifiers. The two pictograms are simplified
synthetic artwork, not certified ISO symbols.

## Output and reproducibility

Images and truth files live in separate `clean/`, `moderate/` and `hard/`
folders. For example, `hard/test_label_001_hard.png` has a matching
`hard/test_label_001_hard.json`. The root `manifest.json` records the dataset
seed, count, relative filenames and measured self-check totals per condition.
Temporary clean renders are removed after generation.

An empty output directory is accepted. An existing generated set can be
regenerated with the same seed and count. Different settings or unrelated files
require a new output directory. No files are deleted. Do not commit the full
generated dataset.

Repeated runs with the same seed and dependency versions produce the same file
bytes. Use `requirements-cv.txt` for the recorded versions. Each JSON records
the exact augmentation seed; the dataset seed is in the manifest. There are no
timestamps or absolute output paths in generated metadata.

## Coordinates in ground truth

All coordinates are pixels, with x increasing rightwards and y downwards.

- `source_image_size_px`: width and height of the original clean label.
- `image_size_px`: width and height of this output image.
- `source_slot_boxes_px_xywh`: original slot rectangles as x, y, width, height.
- `slot_quads_px`: each slot's four corners in the output image, ordered top
  left, top right, bottom right, bottom left according to the source rectangle.
- `symbols`: each symbol's original `source_bbox_px_xywh` and output `quad_px`.
- `homography`: the 3 by 3 matrix mapping source coordinates into output
  coordinates. Multiply a source point `[x, y, 1]` by this matrix, then divide
  the first two results by the third.
- `label_quad_px`: output positions of the clean label's pixel-centre corners,
  starting at `[0, 0]` and ending at `[0, height - 1]` in source coordinates.

Slot boxes describe template regions, not tight bounds around ink. Their source
corners use x plus width and y plus height, consistent with `transform_box`.
Preserve the four transformed corners when evaluating distorted images.
The `size_mm` and `dpi` values describe the source template; an augmented photo
canvas does not represent a new physical label size.

## Self-checks and limits

Every JSON has a change log and a self-check. The self-check measures whether
all recorded corners are finite and inside the output canvas, then tries the
barcode in the original image, after label rectification, and in the thresholded
template slot. It records the recovery path and decoded GS1 values, and reports
`NEEDS_HUMAN_REVIEW` if the geometry or exact barcode check fails. Failed photos
are retained, so difficult cases are not silently removed from later evaluation.

`PASS` applies only to geometry and recovered barcode checks. OCR and automated
symbol detection are explicitly `NOT_RUN`. The hard condition keeps its strong
rotation, perspective and lighting while using blur sigma 1.0 to 1.6 and noise
standard deviation 6. Photo effects do not include occlusion or glare. This is
synthetic test data, not approved artwork or evidence of regulatory compliance.

## Verification

```bash
python -m pytest -q src/gen
python -m ruff check src/gen
```

Tests cover matching image/JSON pairs, paired conditions, independent coordinate
calculations for all slots and symbols, clean-image preservation, reproducible
bytes, changed seeds, retained barcode failures, invalid arguments and CLI output.
Printed per-condition totals are measured for the generated set. OCR accuracy
and extraction metrics belong to later tasks and are not measured here.

## Deterministic draft rendering

`src.gen.render.render_label(template, record, output_dir, actor=..., reason=...)`
creates an immutable SVG, physical-size PDF, 300-DPI PNG preview and JSON
manifest for the supported test-device template. It requires ReportLab and
Poppler's `pdftoppm`; `pypdf` is used by the PDF tests. These dependencies are
recorded in `requirements-cv.txt`.

The renderer accepts only an identifier supplied in `ProductRecord`. The
existing all-zero identifier is accepted only with explicit `test_data=True`
and the output is marked `TEST DATA | DRAFT`. It validates the GS1 barcode
against the supplied values, checks slot bounds, text fit, fonts, overlaps,
symbol size and quiet zones, and refuses unsafe layout results. Every package
contains a change log, SHA-256 hashes and an OCR/barcode/symbol self-check.
Revisions write into a new empty directory. A matching encoded payload reuses
its exact barcode matrix; changing it requires `confirmed_encoded_change=True`.

The renderer does not create approval records or publish artwork. A separate
review system must bind an authorized review decision to the exact manifest
and artifact hashes. These checks are lab baselines, not compliance claims.

## Measured generation check

Two full runs with seed 42 and 17 labels per condition were generated using
`python -m src.gen.generate_dataset --output-dir <empty-output-directory> --seed 42`.
The 103 files in each run (51 PNGs, 51 truth JSONs and one manifest) were
byte-identical. The command printed these measured counts for both runs:

```text
Generated 51 image/JSON pairs (seed=42)
clean: images=17, barcode_matches=17/17, geometry_in_bounds=17/17
moderate: images=17, barcode_matches=17/17, geometry_in_bounds=17/17
hard: images=17, barcode_matches=15/17, geometry_in_bounds=17/17
Self-check scope: geometry and barcode only; OCR and symbol detection NOT_RUN
```

An independent seed-43 run measured 16/17 hard barcode matches, with 17/17 in
clean and moderate. The seed-42 hard rate is 88.24%; the seed-43 hard rate is
94.12%. These measurements use the same original-first, rectification and
template-slot recovery pipeline described in `src/cv/README.md`. Two seed-42
and one seed-43 hard images still require human barcode review. Failed images
remain in the datasets. These synthetic results do not estimate performance on
real photographs.

## Task 5 renderer and approval contract updates

The generator supports simplified `manufacturer`, `expiry`, `sterile`,
`sterile_eo` and `sterile_r` artwork. This is synthetic artwork, not licensed or
certified ISO artwork. The existing CV detector still has its original two
reference symbols; rendering a new symbol does not prove it can be detected.
Draft self-check findings must be reviewed, not silently treated as passes.

SVG output now has `layer-background`, `layer-slots`, `layer-watermark`,
`layer-review` and one `slot-{id}` group for every slot. Its root uses millimetre
units and a matching viewBox while preserving the PDF geometry.

Manifests include `created_by` and `version_id`. `render_label` accepts a supplied
version ID; its default local ID is the product ID plus record version. A new
revision cannot reuse its previous version ID. The generator creates no review
records or passed checks. `verify_print` requires an authorized independent
reviewer, reviewer role, `reference_sha256`, version and a matching passed
`check_id`. Old records missing these fields must be rechecked and reviewed.

## Task 6: structured label revisions

`src.gen.revise.revise_template` consumes the old contract template, its current
`ProductRecord`, one structured `ChangeRequest`, and the existing Task 2 export
`Label` snapshot. It returns a new template version, a copied record with the
new text and version, filled fields, a barcode decision, an audit change log,
and a renderable draft snapshot when input is complete. Contract templates use
field bindings rather than storing text inside slots, so the new record supplies
new text while layout, slot IDs, physical size and template ID remain unchanged.
The old template, record and snapshot are never modified.

Supply a fresh `version_id`, actor and reason. `old_value` must match the current
record, preventing a stale change from silently overwriting newer content. The
`product_name` alias maps to `name`; `extra.lot` maps to the lot field. Fields
without a text/symbol binding or encoded role are rejected instead of ignored.
A sterilization symbol bound to `sterilization` supports EO/sterile_eo and
R/gamma/sterile_r, plus generic sterile artwork. The source method and symbol must
agree. No change automatically carries an approval into the new draft.

- `KEEP`: exact existing barcode element, matrix and module size are reused;
  no encoder is called. Actual GS1 content type and raw bytes are checked,
  so plain symbols containing GS1-looking text are rejected. A text-only
  address change or EO-to-gamma change keeps the barcode.
- `REGENERATE`: every changed encoded field requires its matching explicit flag:
  confirmed_gtin_change, confirmed_expiry_change, confirmed_lot_change or
  confirmed_serial_change. The replacement is decoded and compared before return.
- `NEEDS_INPUT`: `result.label` is None and no artwork files are written. Missing
  identifiers are not invented. `result.require_label()` raises IdentifierRequired
  when an allocated identifier is missing and ValueError for other blocked inputs.

For a model change that requires a new allocated identifier, the caller must set
`requires_new_identifier=True` and supply `allocated_identifier` when available.
The engine does not guess identifier-allocation rules from model names. It
refuses to count the old identifier as a new one. Existing explicit test mode
is preserved; the all-zero placeholder cannot become production data.

Example, with an existing source template/record/snapshot:

```python
from src.common.schemas import ChangeRequest
from src.gen.revise import revise_template
from src.export.pdf import render_pdf
from src.export.svg import render_svg

change = ChangeRequest(
    change_id="address-change-1", product_id=record.product_id,
    field="manufacturer_address", old_value=record.manufacturer_address,
    new_value="88 Demo Rd",
)
revision = revise_template(
    template, record, change, previous_label=current_label,
    version_id="device-draft-v2", actor="parth", reason="Update the address",
)
label = revision.require_label()
render_pdf(label, output_dir / "label.pdf")
render_svg(label, output_dir / "label.svg")
# Persist revision.template, revision.record, revision.change_log and
# revision.self_check with the draft in application storage.
```

This returns a Task 2 export snapshot and uses its PDF/SVG writers. The older
`src.gen.render` manifest-based path retains its existing template-migration
restriction; do not mix its manifests with export snapshots or approval hashes.
Revision checks cover layout and barcode decoding. OCR and symbol detection are
NOT_RUN, and the result remains NEEDS_HUMAN_REVIEW. Publication, trusted storage
and approval/check issuance are outside this local revision engine.
