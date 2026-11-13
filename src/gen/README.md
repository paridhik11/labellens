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
all recorded corners are finite and inside the output canvas, and whether
exactly one GS1 barcode decodes to the intended payload. It stores decoded
payloads and reports `NEEDS_HUMAN_REVIEW` if either check fails. Failed photos
are retained, so difficult cases are not silently removed from later evaluation.

`PASS` applies only to geometry and barcode checks. OCR and automated symbol
detection are explicitly `NOT_RUN`. This is synthetic test data, not approved
artwork or evidence of regulatory compliance. Photo effects currently include
rotation, perspective, blur, lighting, noise and a coloured background, without
occlusion or glare.

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
hard: images=17, barcode_matches=4/17, geometry_in_bounds=17/17
Self-check scope: geometry and barcode only; OCR and symbol detection NOT_RUN
```

These are generator self-check results with zxing-cpp, not extraction-pipeline
accuracy. All 13 hard images whose barcodes failed decoding remain in the set
with `NEEDS_HUMAN_REVIEW`. A hard sample was visually inspected for the DRAFT
and TEST DATA text, visible pictograms and unclipped label placement.
