# Label preprocessing

Preprocessing finds and straightens a single dominant label using OpenCV and
NumPy. OCR is available through the RapidOCR fallback described below. Barcode
decoding and GS1 parsing are also available. Field mapping and `LabelExtraction`
integration are available for this single synthetic template family, as
described below. Dataset-wide results are generated with the evaluation command
at the end of this file.

## Image interface

`find_label_corners(image)` accepts a NumPy uint8 RGB image. It looks for large
convex quadrilaterals in bright-region and edge masks and selects the largest
candidate covering at least 15% of the input image. A convex quadrilateral is
a four-sided outline with no inward-pointing corner. Candidates touching the
image frame are rejected. If there is no suitable boundary, it returns `None`.
There is no fallback that guesses the entire image is a label.

The returned array contains four x, y pixel coordinates in clockwise order:
top left, top right, bottom right, bottom left. `order_corners` starts with the
corner having minimum x plus y. This assumes an approximately upright label;
it cannot determine which way text reads or fix a label rotated upside down.

`rectify_label(image, corners)` orders and validates the corners, then returns
the corrected RGB image and a homography mapping input coordinates into the
corrected image. A homography is a 3 by 3 perspective transformation matrix.
The output width and height come from the longer of each pair of opposite
edges, plus one pixel. These are image dimensions, not a physical-size estimate.
The returned matrix can later map OCR or barcode positions back to the photo
using its inverse.

```python
import numpy as np
from PIL import Image

from src.cv.preprocess import find_label_corners, rectify_label

with Image.open("label.png") as photo:
    image = np.asarray(photo.convert("RGB"))
corners = find_label_corners(image)
if corners is None:
    print("NEEDS_HUMAN_REVIEW: no suitable label boundary")
else:
    corrected, image_to_corrected = rectify_label(image, corners)
```

## Reproducible verification

Run from the repository root with the CV environment's Python:

```bash
python -m pytest -q src/gen src/cv
python -m ruff check src/gen src/cv
python -m src.cv.preprocess --dataset data/synthetic/task1
```

Create that dataset first with the command in `src/gen/README.md`. The evaluator
reads its manifest and matching truth files. Detection itself receives only
image pixels; ground truth is used only to measure the returned corners.

The evaluator reports image counts, detected counts, the count for which all
four corners are within 10 pixels of ground truth, mean corner error and maximum
corner error, separately for clean, moderate and hard. The fixed 10-pixel
criterion is a position tolerance for this synthetic set, not a clinical or
regulatory threshold. Error averages include detected images only; missed
detections remain in the image-count denominator and are not assigned fake
errors. Corrected images are produced during evaluation, but OCR and barcode
accuracy after correction are not measured by this command.

Tests cover generated images in all three conditions, a known RGB crop,
perspective correction with coloured quadrants, corner ordering, invalid input,
blank images, missing detections and per-condition evaluation output.

## Limits

This is a boundary-based baseline for one dominant label against a reasonably
distinct background. A large unrelated rectangle can be mistaken for a label.
It does not authenticate labels, distinguish multiple products, recover missing
corners or handle severe occlusion. Small labels and labels touching the frame
are deliberately rejected. Highly uneven lighting, glare and curved packaging
may break the boundary. Measurements on synthetic images do not establish
performance on real photographs.

## Measured synthetic baseline

Measured on the seed-42 generator set with 17 images per condition. The command
`python -m src.cv.preprocess --dataset <generated-dataset-directory>` printed:

```text
Criterion: every detected corner within 10 pixels of ground truth; no OCR run
clean: detected=17/17, within_10px=17/17, mean_corner_error_px=6.403, max_corner_error_px=6.403
moderate: detected=17/17, within_10px=17/17, mean_corner_error_px=1.702, max_corner_error_px=2.607
hard: detected=17/17, within_10px=17/17, mean_corner_error_px=2.354, max_corner_error_px=7.523
```

This measures boundary location, not text recognition or barcode decoding.
The clean label's inset border produces a small crop and explains its nonzero
corner error. The hard examples test only the generator's current effects;
they do not include real glare, occlusion or curved packaging.

## OCR installation and fallback decision

The OCR wrapper uses `rapidocr-onnxruntime==1.4.4`, `onnxruntime==1.31.1` and
`pydantic==2.14.3`. Pydantic is needed by the existing `OcrBlock` schema. The
original NumPy 2.5.4 and opencv-python 5.0.0.93 pins remain unchanged.
Install from the repository root in the CV environment:

```bash
python -m pip install -r src/gen/requirements-cv.txt
python -m pip --no-cache-dir check
```

PaddleOCR was checked first with pip's dry-run resolver, without installing it.
PaddleOCR 3.7.0 with PaddlePaddle 3.3.1 could not resolve against the existing
pins. The actual resolver diagnosis included:

```text
paddlex 3.7.2 depends on numpy<2.4 and >=1.24
paddlex 3.7.1 depends on numpy<2.4 and >=1.24
paddlex 3.7.0 depends on numpy<2.4 and >=1.24
The user requested (constraint) numpy==2.5.4
```

The unconstrained PaddleOCR check selected version 3.4.1 and
opencv-contrib-python 4.10.0.84. Installing that beside the existing
opencv-python package would introduce a second provider of `cv2`. The
[OpenCV package instructions](https://pypi.org/project/opencv-python/) require
choosing only one OpenCV distribution. No Paddle packages were installed.

The modern `rapidocr` distribution also proposed a second OpenCV provider,
opencv-python-headless. The older `rapidocr-onnxruntime` distribution resolved
with the existing opencv-python package and was installed as the guide's
RapidOCR fallback. See the [versioned RapidOCR API documentation](https://rapidai.github.io/RapidOCRDocs/v1.4.4/install_usage/api/RapidOCR/).
This choice preserves the already-tested generator environment. It is not a
claim that PaddleOCR cannot run on Apple Silicon in a different environment.

## Reading text

```bash
python -m src.cv.ocr --image path/to/test_label.png --rectify
```

`--rectify` detects and straightens the label first. Without it, OCR runs on the
supplied image directly. No boundary is an explicit error when rectification
was requested. The command prints each actual `OcrBlock`, including text, box
and engine confidence. It does not read the matching ground-truth JSON.

For Python callers, `read_text(image)` accepts a uint8 RGB NumPy array and
returns `list[OcrBlock]`. The wrapper converts RGB to the BGR array expected by
this RapidOCR version. Models are cached in memory after the first call.
Inference uses CPU with one thread per operator and the line orientation
classifier disabled because this baseline assumes upright labels.

`OcrBlock.bbox` uses x, y, width, height in the image passed to `read_text`.
It is the smallest axis-aligned rectangle enclosing the OCR engine's four
corners, not a template slot. CLI boxes with `--rectify` are in corrected-image
coordinates; without it they are in input-image coordinates. They have not yet
been mapped back to the original photo. The shared schema is unchanged.

Text and confidence are preserved without ground-truth corrections. Empty
results become an empty list; malformed engine geometry or scores raise an
error. Empty text is omitted. Recognition filtering is set to zero to preserve
low-confidence text for later warning handling; text detection still uses its
bundled defaults. An inference failure propagates to the caller rather than
being presented as successful empty output.

The bundled detection and recognition models are PP-OCRv4 Chinese/English
models. They can return non-English false positives. Confidence is an engine
score, not a calibrated guarantee of correct text. The integrated extractor
described below adds template-based field mapping and warning generation.

## OCR smoke-check observations

One seed-42 image per condition was run through the real CLI with `--rectify`.
Each returned eight blocks. These are smoke checks, not accuracy measurements:

| Condition | Images checked | Intended product name | Actual recognized product name |
| --- | ---: | --- | --- |
| clean | 1 | TEST SENSOR 001 | TESTSENSORO01 |
| moderate | 1 | TEST SENSOR 001 | TEST SENSOR 001 |
| hard | 1 | TEST SENSOR 001 | TEST SENSOR O01 |

The barcode region produced a low-confidence spurious text block in all three
samples, including `2` in the clean sample with confidence
`0.23578742146492004`. These results are retained. No character-error rate or
field accuracy has been computed in this step.

Tests include real bundled-model inference on a generated clean label and
repeatability of its text, boxes and confidence. Unit tests separately verify
RGB conversion, raw result conversion, invalid inputs, empty results and errors.
Models are bundled in the wheel, so normal tests do not download model weights.

The inspected model files had these SHA-256 hashes. SHA-256 is a content
fingerprint that can identify a different model file:

```text
ch_PP-OCRv4_det_infer.onnx: d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9
ch_PP-OCRv4_rec_infer.onnx: 48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b
ch_ppocr_mobile_v2.0_cls_infer.onnx: e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c
```

The classifier file is bundled and loaded by the package but disabled during
inference. ONNX Runtime emitted a warning under the sandbox that its telemetry
device ID could not be persisted; inference completed successfully.

## Barcode decoding and GS1 parsing

```bash
python -m src.cv.barcode --image path/to/test_label.png
python -m src.cv.barcode --image path/to/test_label.png --rectify
python -m src.cv.barcode --dataset data/synthetic/task1
python -m src.cv.barcode --dataset data/synthetic/task1 --rectify
```

`decode_barcodes(image)` accepts uint8 RGB pixels and returns a pair:
`(list[BarcodeResult], list[str])`, containing shared schema objects and warning
messages. It preserves all decoded symbols. No decode gives an empty list and
`BARCODE_NOT_DECODED`. A non-GS1 symbol keeps raw data with empty parsed fields
and `NON_GS1_BARCODE`. Unsupported or malformed GS1 gives `GS1_PARSE_FAILED`,
preserving the raw data and leaving the entire parsed dictionary empty rather
than returning a misleading partial parse. Engine exceptions propagate.

`BarcodeResult.raw` preserves zxing-cpp's bytes with a reversible Latin-1 string
mapping. GS1 data here is ASCII, so its raw separator appears as `\u001d` in
JSON. For non-ASCII content, `raw.encode("latin-1")` recovers the decoded bytes;
the field is not necessarily a human-readable rendering of another encoding.
The decoder's display text with parenthesized AI names is not used for parsing.

`BarcodeResult.bbox` uses x, y, width, height around the decoder's four corner
positions. These are in the image supplied to the function. CLI `--rectify`
therefore returns corrected-image coordinates. Invalid positions give `None`
with `BARCODE_POSITION_INVALID`; the raw data is retained. Shared schemas are
unchanged.

`parse_gs1(payload)` accepts raw element data without a scanner symbology prefix
or human-readable AI parentheses. It implements this project subset:

| AI | Meaning | Accepted value |
| --- | --- | --- |
| 01 | GTIN | 14 ASCII digits with a valid check digit |
| 17 | Expiry | 6 ASCII digits, YYMMDD, with a valid specific calendar day |
| 10 | Lot | 1 to 20 GS1 character-set-82 characters |
| 21 | Serial | 1 to 20 GS1 character-set-82 characters |

Definitions and character sets were checked against the
[GS1 syntax dictionary](https://github.com/gs1/gs1-syntax-dictionary/blob/main/gs1-syntax-dictionary.txt)
and [its character-set reference](https://github.com/gs1/gs1-syntax-dictionary/blob/main/src/lint_cset82.c).
Character set 82 includes letters, digits and specified punctuation, excluding
space. The parser rejects duplicate or unsupported AIs, invalid lengths,
invalid characters, bad GTIN check digits and impossible dates. It accepts AIs
in different orders and subsets; mandatory AI associations are not checked.

Lot and serial end at ASCII GS (`\x1d`) or the end of input. A single separator
after a fixed-length field or final field is tolerated; leading or repeated
separators are rejected. Digits resembling AIs and literal parentheses inside
a variable value are preserved. For example, `10LOT(21)X` is one lot value,
not a lot followed by a serial. If a separator was lost, a short combined value
may still be syntactically valid as one field. The parser cannot recover that
missing information and does not invent the intended split.

For this healthcare baseline, AI 17 requires a specific day rather than `00`,
consistent with [GS1 Sweden's healthcare date notice](https://gs1.se/en/news/change-of-date-format-for-regulated-healthcare-products/).
Calendar validation uses years 2000 through 2099 and preserves the original
YYMMDD string; it does not decide a century for use outside that project range.
A valid checksum is not evidence that a GTIN was allocated, authentic or
approved. The generator's all-zero test placeholder is preserved as test data.
No identifiers are generated by the parser.

## Measured barcode baseline

The two dataset commands above were run on the same seed-42 set, with 17 images
in each condition. Original-image output:

```text
Barcode evaluation: original images
clean: decoded=17/17, all_ais_match=17/17, parse_warning_images=0, correction_failures=0
moderate: decoded=17/17, all_ais_match=17/17, parse_warning_images=0, correction_failures=0
hard: decoded=4/17, all_ais_match=4/17, parse_warning_images=0, correction_failures=0
```

Corrected-image output:

```text
Barcode evaluation: corrected images
clean: decoded=17/17, all_ais_match=17/17, parse_warning_images=0, correction_failures=0
moderate: decoded=17/17, all_ais_match=17/17, parse_warning_images=0, correction_failures=0
hard: decoded=3/17, all_ais_match=3/17, parse_warning_images=0, correction_failures=0
```

`decoded` counts images with any decoded symbol. `all_ais_match` requires
exactly one symbol whose parsed dictionary matches all expected AIs and values.
Both use every image in the denominator, not just successfully decoded images.
Ground truth is used only for comparison, never supplied to the decoder.
Parse-warning and failed-correction counts are reported separately.

Perspective correction did not improve the hard set's aggregate decode count.
Additional interpolation can degrade already-blurred barcode cells. These
commands intentionally measure original and corrected inputs separately;
automatic retries or merged decoding results are not implemented in this step.

## Integrated extraction

The single-family pipeline is available as:

```python
from src.cv.extract import extract_label

result = extract_label("path/to/test_label.png")
print(result.model_dump_json(indent=2))
```

Or run from the repository root:

```bash
python -m src.cv.extract --image path/to/test_label.png
python -m pytest -q src/gen src/cv
python -m ruff check src/gen src/cv
```

The function returns the existing `LabelExtraction` schema. Its label ID is
the input filename stem. It reads the image and fixed layout at
`src/gen/templates/test_device.json`, never the image's matching JSON or a
dataset manifest. The template identity is assumed, not recognized, and a
`TEMPLATE_ASSUMED` warning makes this explicit. Symbol detection is still a
later task: `symbols` stays empty with `SYMBOL_DETECTION_NOT_RUN`.

The pipeline detects the boundary and straightens the image for OCR. It scales
each OCR block's centre into the template's millimetre coordinates and checks
which text slot contains that point. One block in a slot becomes the field
value, preserving text, punctuation, whitespace and recognition errors exactly.
No blocks gives `FIELD_MISSING`. Multiple blocks in a slot, or a block matching
overlapping slots, gives `FIELD_AMBIGUOUS`; the affected field is omitted.
The six supported field names are `product_name`, `manufacturer`,
`manufacturer_address`, `model`, `lot` and `expiry`.

Header text, barcode noise and any other out-of-slot observations remain in
`ocr_blocks` without becoming product fields. OCR lot and expiry strings are
kept separate from the GS1 values in `barcodes[].parsed`. The pipeline does
not silently replace recognized text with barcode values or ground truth.
It does not yet compare printed values to barcode values or product records.

### Original-image coordinates

Every returned `ocr_blocks[].bbox` and `barcodes[].bbox` uses x, y, width, height
in the original image's pixel array. The input-image coordinate convention
also applies when OCR ran on a corrected image. The inverse correction matrix
projects all four corners of each OCR rectangle back to the photo. The result
is an axis-aligned enclosing rectangle clipped to the photo canvas. A rectangle
around tilted text can therefore include additional background.

Barcode decoding tries the original image first because another interpolation
can damage blurred modules. If no symbol decodes, it retries the corrected
image. A recovered barcode's box is mapped back with the same inverse matrix,
and `BARCODE_DECODED_AFTER_RECTIFICATION` records recovery. Successful original
decodes keep their original boxes and are not replaced. Multiple decoded
symbols are preserved with `MULTIPLE_BARCODES`; none is selected automatically.
The standalone barcode evaluator above still measures each input separately.

Input EXIF orientation is not applied automatically. Coordinates refer to the
stored pixel array, not an external viewer's automatically rotated display.

### Warnings and failure behavior

- No boundary: retain any original-image barcodes, skip OCR and field mapping,
  and report `LABEL_NOT_FOUND`, `OCR_NOT_RUN` and `FIELD_MAPPING_SKIPPED`.
- OCR inference failure: retain other results and report `OCR_FAILED`, including
  the exception type and message. No text is fabricated.
- No text observations: report `OCR_NO_TEXT` and missing template fields.
- Barcode engine failure: report `BARCODE_ENGINE_FAILED` with the exception
  reason. Both failed attempts or no decoded barcode remain explicit.
- Low engine confidence: retain the observation with `LOW_OCR_CONFIDENCE`.
- Low grayscale Laplacian variance: report `BLUR_SUSPECTED` with its measured
  score and configured threshold. Laplacian variance measures edge variation;
  noise can raise it and hide blur.

Defaults are `min_confidence=0.8` and `blur_threshold=100.0`. These are provisional
warning settings, not calibrated thresholds or guarantees of readability.
Python keyword arguments or CLI `--min-confidence` and `--blur-threshold`
override them. A zero blur threshold disables that warning. Unreadable files,
invalid settings and unrecoverable geometry errors raise rather than returning
a fabricated extraction.

### Integrated smoke checks

Actual extraction was run on base label 001 in all three seed-42 conditions.
Each result validated against `LabelExtraction`. The observed counts were:

| Condition | Images checked | Mapped fields | OCR blocks | Decoded barcodes |
| --- | ---: | ---: | ---: | ---: |
| clean | 1 | 6 | 8 | 1 |
| moderate | 1 | 6 | 8 | 1 |
| hard | 1 | 6 | 8 | 0 |

The hard sample's barcode failure remains a warning; its OCR fields are still
available. The previously observed product-name errors remain uncorrected.
These are integration smoke checks, not dataset-wide extraction accuracy.
The real-engine tests also copy each image into a directory without its truth
JSON, then check schema validity and original-space positions against truth
held separately by the test. Deterministic unit cases cover field ambiguity,
known coordinate transforms, original-first barcode selection, corrected-image
recovery, engine failures, blank images and warning settings.

## Dataset-wide extraction evaluation

Prepare the reproducible input set once, then run the evaluator from the
repository root with the CV environment's Python:

```bash
python -m src.gen.generate_dataset --output-dir data/synthetic/task1 --seed 42
python -m src.cv.eval_extract --dataset data/synthetic/task1 --output results/cv_extract.md
```

The second line is the single evaluation command. It runs the unchanged
`extract_label` on every image listed in the generated manifest and writes
[the computed report](../../results/cv_extract.md). The first full measurement
used the existing temporary seed-42 set; the commands above recreate those
inputs in a persistent local folder. Generated images are not committed.

The evaluator reports every metric separately for clean, moderate and hard,
with image counts and numerator/denominator values:

- OCR character error rate per field is total edit distance divided by total
  reference characters. Insertions, deletions and substitutions each cost one.
  It preserves case, spaces, punctuation and printed prefixes. Missing or
  ambiguous fields count as deletions, not excluded examples. Reference
  character counts and numbers of present fields are printed beside the rates.
- Barcode decode rate uses all images as denominator, including failures.
- GS1 accuracy gives exact matches for each AI and all four together, using
  all images as denominator. Exactly one barcode is required to avoid choosing
  among multiple symbols. A conditional all-four rate among decoded images is
  also shown so decode failures are distinguishable from parsing errors.
- Detection/correction success uses the existing fixed 10-pixel corner
  tolerance. The evaluator repeats the deterministic image-only detector and
  rectifier because the locked extraction schema does not expose their internal
  corners. This measures geometry separately from OCR success.

An extraction exception remains a failed sample: missing text incurs deletion
errors and barcode matches fail. Engine failures already captured by the
extractor remain visible through warning counts. Missing or malformed ground
truth aborts evaluation because no correct score can be computed. Manifest
counts, unique paths, supported conditions and the required references are
validated before any scoring.

The evaluator only reads dataset files and refuses a report path inside that
dataset. Reports include warning counts by image, representative largest text
errors, exception details, Python and package versions, extraction defaults,
and SHA-256 fingerprints for dataset contents, source, template and models.
There are no timestamps in the generated report. Source fingerprints make
changes distinguishable even when no new Git commit has been created yet.

No extraction behavior or warning thresholds were changed for this measurement.
Results are a synthetic baseline for the existing template, not real-label
validation, identifier authentication or a measurement of symbol detection.
