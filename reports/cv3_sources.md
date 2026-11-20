# CV3 acquisition and reference freeze

Thirty new device-package photographs selected visually from 45 candidates in the
existing Primis Medical online-photo source. DailyMed artwork is not a camera
photo, so previously used DailyMed sources were excluded, not relabelled as new
photos. No search snippets, catalog titles, encoded barcodes or manufacturer
websites supplied reference values. References are LLM-labelled by Codex from
visible printed text, not validated human ground truth. Uncertain/absent values
remain blank: 30 readable names, 24 lots and 27 expiry dates.

`src/gen/cv3_dataset.json` pins URLs, product pages, SHA-256, reference notes,
rights and the family-grouped 20 dev / 10 test split. Related UroMax sizes,
Ethicon suture boxes and Arrow catheterization packages stay together. Images
remain local under `data/cv3_photos/candidates/`. Publisher rights are retained;
these are local research copies, not a redistributable image corpus.

Acquisition used the existing DailyMed pipeline's polite HTTP helper and the
existing online-photo publisher. A collection endpoint returned HTTP 429 once;
it was not retried. The public product feed succeeded. The selected sources had
zero exact duplicates or near-duplicates (63-bit grayscale DCT perceptual hash,
distance <= 5, white margins trimmed) against 194 pre-existing local images,
including the ten previously exposed photos. This is a duplicate check, not a
guarantee of photographic diversity or independent clinical sampling.

Re-fetch the frozen URLs with `python -m src.gen.cv3_acquire --frozen`; it verifies
the pinned bytes. Do not rerun discovery to reconstruct this frozen selection.

Product names use the prominent English product heading, with adjacent product
description where part of that heading, excluding manufacturer branding and
size. Scoring preserves punctuation/trademarks and folds case/whitespace only.
Dates use the original label's standalone use-by row. Vendor inventory stickers,
manufacture dates and barcode human-readable strings are excluded as references.
