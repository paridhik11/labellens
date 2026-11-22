# NDC scan protocol (written and committed before any gate photo is read or scored)

Goal: identify a medicine from a photo through its NDC (barcode or printed number) instead of the stylised name.
Unchanged by this work: the matcher and its 0.65 threshold, the "a photo never confirms itself" rule (every result is
"Is this X?" plus evidence and goes through the confirm step), method E and every existing gate.

## Step 0 (measured first, existing images only)
`python -m scripts.ndc_scan.step0` -> `results/ndc_scan/step0.json`. (a) zxing-cpp barcode decode on the 145 pinned
package-label images and on the dev photos rendered from them; (b) NDC regex on the cached OCR lines of the dev photos
(no re-reading). Coverage per condition is reported in the final report. Low coverage does not stop the build.

## Method
1. **NDC signal.** (a) barcode: UPC-A starting with 3, EAN-13 starting with 03, GS1 DataMatrix / GTIN-14 with AI 01 and
   the 03 prefix, valid check digit, the 10 NDC digits read in all three hyphen layouts. (b) printed: regex for 4-4-2,
   5-3-2, 5-4-1, bare 11 and bare 10 digits (hyphen, dash or space separators). Everything is normalised to 11 digits and
   looked up EXACTLY in `src/ndc/ndc_table.json`: every package NDC of the 30 pinned corpus SPL files (100 NDCs, built by
   `python -m src.ndc.table`, XML hashes checked against `data/medicine/products.json`). No fuzzy NDC matching.
2. **Text retrieval.** Own BM25 (`src/ir/bm25.py`, k1 1.5, b 0.75) over each product's package-label text (SPL section
   51945-4 text plus product and generic name, `src/ndc/package_text.json`), queried with all OCR tokens of the photo.
3. **Image similarity (DINOv2): not built.** Time box. It would have been evaluated only on a different image of the same
   product than the reference, and only 10 of the 30 products have two images. Stated as not done.
4. **Fusion and result.**
   - Barcode is read first (about a second). An NDC found by barcode or by OCR that is in the table wins outright:
     outcome `matched` (still "Is this X?", never auto-confirmed) with the digits as evidence. Barcode and printed NDC
     naming different products, or one NDC naming two products, give `needs_review` with both.
   - Otherwise method E runs unchanged on the OCR lines. Its outcome stands.
   - Text rank can only ADD a review: when E returns `no_reference_match` (not identified, not a timeout) and the BM25
     top product has score at least TAU, the result is `needs_review` with the top 3 BM25 products. It never creates
     `matched`. TAU is the only tuned value and is chosen on dev (below).
   - A barcode NDC that is not in the table is kept as evidence ("NDC read, not a reference product"), it identifies nothing.
5. **Live DailyMed lookup by NDC:** the `live-dailymed` branch is not merged into main, so only a hook is left
   (`src/ndc/scan.py`, `outside_corpus_lookup`, returns None) and the unmatched barcode NDC is reported.

## Sets
- Dev (selection of TAU only): the cached dev OCR lines `results/public_scan/lines_dev_real.jsonl` (108 photos). The NDC
  regex and barcode rules above are fixed by the NDC specification, not tuned.
- Gate E photos (never touched by this work before scoring): the 57 `fresh_real` positive photos (15 products, 19 images,
  artwork, moderate, hard) and the 45 `unused_decoy` photos (15 products x 3 conditions).
- New unused set, pinned now (`results/ndc_scan/new_set.json`, SPL XML sha256, image sha256, rendered photo sha256, seed
  rule as in the public scan photos): products never used by any earlier run, all decoys (not in the corpus), x 3 conditions.
  Rule and name list in `scripts/ndc_scan/make_new_set.py`, fixed before the SPLs were fetched.
- Every photo is OCR-read once by the unchanged reader (`public_scan.read_lines`, 50 s kill) into
  `results/ndc_scan/lines_<set>.jsonl`; reading is not scoring. Method E is REPLAYED on exactly those lines and is the
  baseline for the paired comparison. The recorded E run on the 45 unused decoys (0 wrong, 13 timeouts) is also quoted.

## Selection (dev only)
TAU: grid 0, 2, 4, ..., 40 (BM25 scores). Take the smallest TAU for which no dev decoy photo receives a text-rank review
suggestion. If no grid value does, the text suggestion is switched off (TAU = infinity) and BM25 stays a reported
diagnostic. Written to `src/ndc/ndc_config.json`, committed alone BEFORE scoring.

## Scoring (the frozen version, once)
Categories per photo (as in the public scan): `correct` (matched, right product), `wrong` (matched, wrong product or any
matched on a decoy), `review`, `not_identified`, `timeout` (OCR killed or time cut, and no barcode NDC). Latency per photo
= barcode time, plus (only when the barcode does not decide) OCR seconds as measured and matching time. OCR seconds were
measured with several readers running at once on a CPU shared with another session, so absolute times are not production times.
Reported per product and per photo, per condition, with Wilson 95% intervals, the coverage of each signal (barcode NDC
read, printed NDC read, either, in table), latency median and max, and E replay next to the new method on the same photos.

## Gate (all three must hold, else no merge and a negative result is written)
1. **0 wrong at product level on the unused decoys** (the 15 `unused_decoy` products and the new-set products; a product
   is wrong when any of its photos is `matched`). Also reported, not gated: decoy photos with any product shown in a review list.
2. **Timeouts not higher than E**: on the 45 unused decoy photos and on the 57 positives, new method timeouts <= E replay
   timeouts on the same lines, and <= 13/45 on the unused decoys (E recorded).
3. **Correct-product rate on the 57 positives higher than E** on the same photos (E replay, same lines).

## Limits stated in advance
Real DailyMed artwork with simulated camera conditions, one source, software-read; real phone photos are unmeasured.
Decoys are tested only against the 30-product table, so the NDC path cannot misfire on them except by an OCR misread
forming a table code. Only 15 products and 57 positive photos: wide intervals. Package label text is short for several
products, so BM25 is weak by construction. The 30-product table is the corpus, not all of DailyMed.
