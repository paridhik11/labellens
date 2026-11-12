# Label preprocessing

This first extraction step finds and straightens a single dominant label.
It uses OpenCV and NumPy already installed in the CV environment. OCR, barcode
parsing, field mapping and `LabelExtraction` integration are later steps.

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
