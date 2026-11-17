# Parth's LabelLens CV and Synthetic Label Work

**For:** Paridhi  
**Branch:** [parth-gen](https://github.com/paridhik11/labellens/tree/parth-gen)
**Base work:** CV and template work from `parth-cv`, reviewed and merged to `main`.

## CV2 review, 2026-11-17

The fresh transformed-artwork gate passed, so CV2 is the default extraction
profile. Complete extraction rose from 0/96 baseline images in every condition
to 32/96 clean, 27/96 moderate and 17/96 hard. This benchmark contains 288
frames but 198 unique images from four source families; it is not population or
real-phone accuracy. Its references are LLM-generated and real-symbol accuracy
is unmeasured.

The previously exposed online photo check did not establish a real-photo gain:
names were 1/10 to 1/10, lots 7/10 to 4/10, and expiry 3/10 to 5/10. Human
spot-check and crop review remain deferred. Detailed fresh, photo and
reproduction records are in `reports/parth_cv2.md`, `reports/parth_final.md`
and `results/cv_cv2_*.md`.

Three repeatable review packages now rebuild with `python -m src.gen.golden`:
clean DailyMed, synthetic and a confirmed barcode change. All PDF/SVG exports
show `DRAFT, not for production`; no package is approved or published. Native
QR decoding can stall, so the final evaluation used equal 300-second deadlines
and counted timeouts as misses. This is an evaluation guard, not a production fix.

## Latest review: grouped dev/test and generation handoff, 2026-11-16

Merged origin/main first. Existing contract acceptance by Pari is confirmed for
CR-2,3,4,5,9,10,11. Human spot-check and crop review remain deferred. All reference
transcriptions/annotations are LLM-generated; real-symbol accuracy is unmeasured.

**The new photo candidate did not improve test performance.** The fixed seed
20261116 split has six dev and four test photos, with Introcan variants kept in
one group. All ten were exposed in previous work; this is not an unseen holdout.
Two development iterations improved exact dev product name from 1/6 to 2/6, while
lot stayed 4/6 and expiry 2/6. Code c50fb4a was frozen before one guarded paired
test invocation. Test exact results and descriptive Wilson 95% intervals:

| Field | Baseline 740a0ab | Candidate c50fb4a |
|---|---|---|
| Product name | 0/4 (0.0% to 49.0%) | 0/4 (0.0% to 49.0%) |
| Lot | 3/4 (30.1% to 95.4%) | 2/4 (15.0% to 85.0%) |
| Expiry | 1/4 (4.6% to 69.9%) | 0/4 (0.0% to 49.0%) |

Keep the existing baseline photo algorithms live after this regression. No test
retuning or second scoring occurred. The failed candidate and its tests remain
reproducible in Git at c50fb4a. Do not combine dev/test or prior all-ten metrics
into a new held-out accuracy number. The photo-accuracy improvement goal remains
open; 80% accuracy is not established. Tiny related convenience data and
unvalidated references limit these intervals and conclusions.

Completed independently of that negative result:

- Lazy CV imports: src.cv.extract imports without NumPy/OpenCV/Pillow/zxing/OCR
  packages. Actual extraction still needs the CV environment. Checker code and
  thresholds were not changed.
- Every draft says DRAFT, not for production. Placeholder/test/synthetic-symbol
  or unverified raster prototypes retain it after test approval too. Both export
  writers and the legacy renderer are covered; audit sidecars list markings.
- [GEN_HANDOFF.md](GEN_HANDOFF.md) documents exact renderer signatures, input and
  output payloads, confirmed REGENERATE to PDF/SVG, QR and approval boundaries.
  Its executable example is tested. Pari retains auth, review storage,
  publication and step-24b snapshot mapping.
- src.gen.medicine.load_medicine_corpus returns 147 validated medicine Chunk
  objects with exact existing keys, module checks, duplicate/hash validation.
  Source URLs and SPL effective dates remain in the adjacent metadata/catalog.
  The loader imports without CV libraries; retrieval code is untouched.
- Zero downloaded real-label/DailyMed binaries are tracked already. Existing
  ignore rules and the pinned re-fetch script were verified offline: 20 device
  artworks and 44 AI-labelled crops. Two synthetic reference PNGs are retained.
  History was not rewritten.
- Two additional Swissmedic-hosted annotated packaging illustrations were
  downloaded, cataloged and made reproducible for development only. These are
  related artwork examples, not new real photos. No additional suitable photo
  was accepted in this search. Artwork is not pooled with photo scores.

Actual release validation: fast suite 840 passed, 5 deselected, 1 warning in
35.04s after merging latest RAG main; generation/CV 398 passed, 1 skipped in 82.71s; export/interface checks
41 passed in 8.39s; synthetic blind/template regression 1 passed in 33.07s;
Ruff All checks passed. The lazy-import test blocks optional CV libraries in a
fresh process. See [short report](../reports/parth_remaining_review.md),
[test results](../results/cv_split_test.md), [dev results](../results/cv_split_dev.md)
and [choice/release decision](../reports/parth_dev_choice.md).

Older checkpoints below retain their historical results and branch locations.
This work is delivered on parth-gen and promoted to main through a no-ff merge;
consult Git history and the final report for the promotion commit.

## Prior checkpoint: integrated photo pipeline, 2026-11-16

Pari accepted CR-2,3,4,5,9,10,11; acceptance is recorded in the contract requests.
Perspective correction is now wired into the extractor. Known templates supply
physical proportions; blind photos use observed edges without assuming the
synthetic ratio. Fixed CPU OCR uses original/rectified views, quarter-turns,
overlapping crops, split-key association and date validation. No new OCR model,
product-specific dictionary, external API or scoring-set tuning was used.

Development and corrections used invented examples and synthetic labels. The
candidate was frozen at c2759e9, and both sides were evaluated from isolated
archives against byte-pinned images and unchanged AI transcriptions. These ten
images were exposed in earlier work, so this is not an unseen holdout.

| Photo field | Baseline 88f9c9d | Frozen candidate c2759e9 |
|---|---|---|
| Product name, exact | 1/10 | 1/10 |
| Lot, exact | 0/10 | 7/10 |
| Expiry, exact | 0/10 | 3/10 |

**Still flagged:** names remain weak, expiry remains weak, and an 80% real-photo
accuracy claim is unsupported. Human spot-check and crop review remain deferred;
transcriptions and symbol annotations are LLM-generated. Real-photo symbol
accuracy remains unmeasured. Approved-print accuracy is not established.
Earlier 1/10,0/10,0/10 reports remain historical baselines, not current results.

Pari owns app integration: authentication, review storage and publication.
Task 2 snapshot-to-data-model mapping belongs to her step 24b. No shared schema,
retrieval or app implementation was changed by this CV fix. Merging origin/main
imports Pari's existing work without replacing it.

Verification after merging origin/main: fast suite **790 passed, 5 deselected,
1 warning in 127.17s**; scoped generation/CV **398 passed, 1 skipped in 162.27s**;
Ruff **All checks passed!**. Main's declared FastAPI, HTTPX, SQLAlchemy and
scikit-learn packages were installed in the Conda environment for merged tests;
no new dependency was added to the repository.

See [paired results](../results/cv_photo_before_after.md),
[fixed protocol](../reports/parth_photo_protocol.md), and
[short report](../reports/parth_photo_fix.md). The older sections below describe
prior task checkpoints and retain their historical metrics.

## Required status note for future summaries and handoffs

Updated 2026-11-16 at Parth's request. Carry this unresolved item into every
future progress summary, README or handoff Markdown prepared for Parth, Paridhi
or anyone else. Do not describe photo extraction or Task 4 as fully solved.

- **Photo extraction remains incomplete; the newer grouped candidate failed its release gate.** Ten clear online
  device-package photos are now collected, with product name, lot/batch and
  expiry readable in each image according to AI inspection. All 30 reference
  readings are LLM-labelled, not human-validated truth.
- The original baseline performed poorly on this clear set:
  exact product name **1/10**, lot **0/10**, expiry **0/10**. The earlier
  improved baseline pipeline gave **1/10**, **7/10**, **3/10** respectively in that earlier all-ten evaluation, with the name and
  expiry weaknesses unresolved. Historical source:
  [clear-photo results](../results/cv_real_photos_clear.md). No 80% real-photo
  accuracy claim is supported. Do not present dataset selection as a model fix.
- The three-photo human spot-check is **DEFERRED / NOT_RUN**, not zero errors.
  Parth explicitly said he cannot do it now; independent work continues without
  treating AI labels as human-validated truth. Images stay
  local under `data/real_photos/clear_online/`; source URLs and fingerprints are
  in [SOURCES.md](../data/real/SOURCES.md).
- The earlier 12-photo convenience set and its separate baseline are preserved
  in [cv_real_photos.md](../results/cv_real_photos.md). Do not blend either set
  with synthetic results or with medicine evaluation.
- Task 3's newer device-symbol collection contains 20 images and 44 visually
  assigned LLM-labelled crops. Human symbol validation and real-symbol/blind-mode
  accuracy remain unmeasured. The legacy medicine artworks are separate.

When this deferred work is actually fixed and reviewed, update this status using
new executed results and real human feedback. Until then, include the limitation
explicitly even when describing completed generator/export work.

## Project goal

Build a reproducible synthetic medical-device label workflow and a computer-vision baseline for reading fields and GS1 barcodes, locating symbols, and preserving positions through distortion. Generated labels remain test drafts, use supplied identifiers, and are evaluated separately by condition.

## Work completed

### Synthetic labels and augmentation

- Aligned augmentation tests with the augmentation API and tested coordinate transforms for label, text and symbol positions.
- Added fixed-seed label generation with varied product, manufacturer, address, model, lot, expiry and serial values. Each base label has clean, moderate and hard variants with matching ground-truth JSON and a manifest.
- Ground truth includes transformed corners, homography, GS1 data, change log and self-check. Failed samples remain in evaluation.
- Added harder synthetic conditions including glare and occlusion. These are controlled synthetic stress cases, not real capture conditions.

### Computer vision and barcode handling

- Added label-boundary detection, perspective correction, OCR, GS1 parsing, template and blind extraction paths, and coordinates mapped to the original image.
- Barcode decoding supports blind image search and template-assisted recovery. The template-assisted path uses known barcode-slot information, so its scores should not be presented as blind decoding.
- Blind symbol search scans the label at multiple scales. Detection still uses references derived from the same synthetic symbol drawing code, so these results do not establish performance on independently drawn or real-world symbols.
- Added negative cases for absent or incorrect symbols and barcode/text mismatches.

### Draft rendering and verification

- Added deterministic SVG, physical-size PDF and preview rendering for the test-device template.
- Draft output carries DRAFT marking, a change log, artifact hashes and self-check results. Barcode content is retained when unchanged and regenerated only for confirmed changes.
- Print comparison is bound to an approval record and artifact hash. The verification code does not create approvals or publish artwork.

### Structured revisions (Task 6)

- Added a local revision engine that copies the old template and ProductRecord,
  increments their versions, binds updated text into a new export snapshot and
  records the actor, reason and change ID. Original inputs remain unchanged.
- Reuses the exact existing barcode for KEEP, regenerates and decode-checks
  confirmed encoded changes, and returns no artwork for NEEDS_INPUT. Missing
  allocated identifiers are never supplied by the engine. A sterilization
  method change updates its bound synthetic symbol without changing the barcode.
- Actual GS1 content type and raw bytes are checked when reusing a barcode;
  a plain DataMatrix containing GS1-looking text is rejected.
- New PDF/SVG outputs remain drafts with the named groups. Layout and barcode
  checks run; OCR and symbol detection for revisions are NOT_RUN. Application
  storage, trusted confirmation/authorization and publication remain separate.

Task 6 verification: **411 passed, 3 deselected**, with both formats decoded
from 600-DPI revised PDFs. See [Task 6 report](../reports/parth_task6.md).

## Current assignment checklist, 2026-11-16

The original Parth guide used different task numbers for generation, extraction
and measurement. That earlier CV work is described below. This checklist uses
PARTH_NEXT_TASKS.md plus Paridhi's latest message, including new Tasks 7a and 9.
This is a local module/data handoff, not a claim that the entire application or
all real-world validation is finished.

| Task | Implemented and checked | Remaining or flagged |
|---|---|---|
| Original synthetic generator/extractor/evaluation | Fixed seeds, varied fields, GS1, transformed ground truth, three difficulty levels, separate blind/template evaluation | One synthetic template family; real performance does not follow from synthetic scores |
| 1: GS1 module | KEEP, confirmed REGENERATE, NEEDS_INPUT; syntax/decode tests; no identifier invention | Allocation/ownership cannot be established by a check digit |
| 2: PDF/SVG/QR export | Physical-size PDF; named layer-* and slot-{id} groups; offline published-URL QR; repeated field slots | Physical printer calibration and Windows runtime not validated here |
| 3: DailyMed real labels | 20 device artworks, 17 records, eight families, 44 LLM-labelled symbol crops; pinned script/catalog rebuild | Human symbol review and detector accuracy NOT_RUN. Legacy 60 medicine artworks excluded from device evaluation; no reviewed medicine-symbol subset claimed |
| 4: real photos | Ten clear online device photos, 30 AI transcriptions, fixed paired evaluation | Human spot-check DEFERRED / NOT_RUN; names 1/10, lots 7/10, expiry 3/10 |
| 5: contract gaps | Sterile/EO/R artwork, SVG groups, approval/check/hash mappings, contract tests | Synthetic pictograms are not certified ISO artwork; app must provide trusted reviewer identity |
| 6: revisions | New immutable draft versions; field/symbol changes; three barcode outcomes; audit and blocked-output guards | Task 2 snapshots and legacy packages need explicit application mapping; revision OCR/symbol self-checks NOT_RUN |
| 9: medicine corpus | Ten pinned products, 147 source-text chunks, effective dates and source links; same Chunk keys | Retrieval integration/evaluation belongs to Pari; no src/ir edits |
| 7a: perspective | Independent template-ratio correction, 90 fresh synthetic images, all-corner scoring | Now integrated; blind aspect inferred from edges. No independent real-photo corner ground truth |
| 7: print verification | Approved-package gate and per-field evidence/confidence; ten-photo provisional comparison | Real approved-print evaluation NOT_RUN without actual approved references; no approvals fabricated |

No Task 8 was supplied. No new backend, UI, shared-schema, retrieval or contract
implementation was added in this completion pass. Task reports stay under 400
words. Raw images/XML stay local; the medicine text corpus and provenance are
versioned so Pari can inspect them directly.

## New medicine corpus (Task 9)

Ten DailyMed product records were fetched at pinned SPL versions. SPL means
Structured Product Label, the source document format. The builder checks exact
XML fingerprints, identity, product name, version and effective date. The date
is the document effectiveTime, not the date downloaded. Data stays separate:
`data/medicine/corpus.jsonl`, with product metadata and a source catalog.

- 147 unique medicine chunks: labelling 32, warnings 79, dosage 36.
- A chunk is a source passage of at most 200 words, with 25-word overlap.
  Rows have exactly the existing shared Chunk fields; module is medicine.
- Nested sections are included once. Labelling includes indications,
  description and principal display panels. This is selected coverage, not all
  possible SPL sections, all medicines or a clinically validated answer system.
- Online construction and offline rebuild produced SHA-256
  `2b9dd48d230ee52938c564700d61d6db19ebe68eee4beb285c2c74b601aa018f`.
- No retrieval ranking, public chatbot answers or medicine matching was tested.
  Pari can integrate retrieval after reviewing the source metadata. Do not mix
  these medicine passages with the device dataset or device result tables.

Commands and results: [Task 9](../reports/parth_task9.md).
Source catalog: [medicine sources](../data/medicine/SOURCES.md).

## New independent perspective module (Task 7a)

`src.cv.perspective.correct_perspective` finds four corners from pixels and maps
them to the supplied template aspect ratio. It returns corrected pixels, source
corners and a homography, the coordinate mapping between views. No supported
boundary returns None. This historical standalone benchmark preceded the integration described at the top.

Benchmark: seeds 7001, 7002, 7003; ten base labels per seed, each rendered in
three conditions. Success requires every corner within 10 original-image
pixels; absent detections remain failures in the denominator.

| Synthetic condition | Detected | Successful corner detection | Success rate |
|---|---|---|---|
| Clean | 30/30 | 30/30 | 100% |
| Moderate | 30/30 | 30/30 | 100% |
| Hard | 30/30 | 30/30 | 100% |

These are fresh synthetic geometry results from one family, not photo OCR or
real-world detection accuracy. The module assumes roughly upright labels and
does not recognize 90/180-degree text orientation. The rectangle height is
rounded from the requested ratio. It does not recover obscured text.

Reproduce: `python -m scripts.cv_experiments.eval_perspective`.
Local raw evidence: `data/synthetic/perspective_task7a/evaluation.json`.
See [Task 7a report](../reports/parth_task7a.md).

## Per-field print verification (Task 7)

The new `src.cv.print_verify.verify_print` checks authorized reviewer evidence,
a matching passed check_id, exact version and manifest/artifact fingerprints
before blind OCR. Each field has expected and observed text, an evidence box,
OCR confidence and MATCH/MISMATCH/NEEDS_HUMAN_REVIEW. Missing, ambiguous or weak
evidence requires review. Confidence is not a calibrated correctness probability.
It uses legacy manifest packages; Task 2 Label snapshots need explicit mapping.
The old verifier and extractor remain unchanged.

The separate `python -m src.cv.print_verify` evaluation compared the clear online
set with AI transcriptions, without manufacturing approvals:

| Photo field | Exact text | MATCH | MISMATCH | NEEDS_HUMAN_REVIEW |
|---|---|---|---|---|
| Product name | 1/10 | 1 | 5 | 4 |
| Lot | 0/10 | 0 | 0 | 10 |
| Expiry | 0/10 | 0 | 0 | 10 |

Each mismatch here is a comparison to an AI reading, not a human finding of a
physical print defect. The photos have no trusted approved source packages, so
real approved-print accuracy is NOT_RUN. The human spot-check is explicitly
deferred by Parth. Local evidence for all 30 decisions is in
`data/real_photos/clear_online/print_comparison_llm.json`.
See [Task 7 report](../reports/parth_task7.md).

## Contract review and integration handoff

Technical recommendations for CR-2, 3, 4, 5, 9, 10 and 11 are YES, with explicit
version, confidence, audit and artifact-mapping conditions. These recommendations
are recorded in [the review](../reports/parth_contract_review.md); they are not
formal team approval and do not change locked schemas or contracts. Pari still
owns application integration, trusted authentication, review storage and
publication. No real approvals have been issued and nothing was published.

## Items that must stay flagged in every future summary

1. INCOMPLETE: after the first fixed-protocol fix, real-photo exact extraction
   is name 1/10, lot 7/10, expiry 3/10. The previous baseline was 1/10,0/10,0/10.
   The 80% real-photo target is not met; no scoring-set tuning is permitted.
2. DEFERRED / NOT_RUN: three-photo human spot-check, explicitly deferred by
   Parth. AI labels stay AI labels; never report zero human errors.
3. NOT_RUN: human review of the 44 real symbol crops and real-symbol/blind
   accuracy. The CV detector has only two original synthetic references despite
   the generator/exporter's broader symbol support. Medicine-symbol artwork
   is not yet a curated evaluated subset.
4. NOT_RUN: real approved-print validation. Need real authorized reference
   packages and corresponding print photos; online product photos do not supply
   that approval history. No approval records may be invented to close this.
5. INTEGRATION: medicine retrieval and API adapters,
   trusted confirmations, auth, persistence and publication need application
   work by their owners. Perspective is now integrated; Pari owns auth, review storage, publication and step-24b snapshot mapping.
6. LIMIT: revision self-check is partial; OCR and symbol detection are NOT_RUN.
   Synthetic artwork and check-digit validation do not certify label compliance,
   ISO pictograms, identifiers or authenticity.
7. NOT_RUN HERE: three slow tests, Windows execution, physical printer calibration
   and clinical validation. The full fast-suite result is shown separately.

## Fresh-seed results

The following results are from seeds 100, 101 and 102 in `results/cv_final_eval.md`: 51 synthetic labels per condition and 102 expected symbol instances per condition. All use one synthetic template family.

| Condition | Exact GS1, blind | Exact GS1, template-assisted | Blind symbol matches | Template symbol matches | Corners within 10 px |
| --- | ---: | ---: | ---: | ---: | ---: |
| Clean | 51/51 | 51/51 | 102/102 | 102/102 | 51/51 |
| Moderate | 51/51 | 51/51 | 102/102 | 102/102 | 51/51 |
| Hard | 51/51 | 51/51 | 102/102 | 102/102 | 51/51 |
| Original hard | 51/51 | 50/51 | 102/102 | 102/102 | 51/51 |
| Very hard | 43/51 | 44/51 | 93/102 | 93/102 | 51/51 |

“Very hard” includes synthetic glare and occlusion. On that condition, OCR character error rate was 9.35% in blind mode and 3.85% in template mode after format post-correction. Clean, moderate, hard and original-hard post-corrected OCR error rates were 0.00% for both modes. In the variation cases, absent symbols produced 0 false positive detections; the exact counts and confidence intervals are in the evaluation report.

The older “15/17 hard” figure only applied to an easier, reduced blur/noise setting and is not the result to use for the original hard benchmark. The old “4/17 baseline” comparison mixed settings; the same-image fresh-seed comparisons are reported in `results/cv_final_eval.md`. No seed-42 or seed-43 figures are used here.

## Limits and remaining work

- The results table above uses synthetic artwork from one template family. Separate real-photo evaluations now exist and remain poor, as recorded in the required status note above.
- The very-hard barcode result is lower than the other conditions. OCR naming in blind mode is heuristic and performs worse than template mapping under very hard glare and occlusion.
- Symbol detection is not validated on independent artwork: the references come from the same code as the synthetic symbols, and independently drawn variants were not detected in the fresh evaluation.
- The test GTIN is an all-zero placeholder, not an allocated GTIN or UDI-DI. No real identifier is fabricated.
- Pictograms are simplified test artwork, not certified ISO symbols. No reviewer approval was issued and no artwork was published.
- Cross-platform output bytes are not identical, even though the reported evaluation metrics matched. On Windows without Poppler's `pdftoppm`, one render test fails.
- The shared schemas and retrieval modules were not changed in the CV work.

## Verification

Historical scoped Mac verification before the newer tasks used:

```bash
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q src/gen src/cv
/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check src/gen src/cv
```

Historical output, not the current completion-pass test count:

```text
233 passed in 123.86s (0:02:03)
All checks passed!
```

The Windows caveat above is recorded in `docs/CV_STATUS.md`. Reproduction commands and all fresh-seed tables are in [`results/cv_final_eval.md`](../results/cv_final_eval.md).

## Key implementation files

- [`src/gen/generate_dataset.py`](../src/gen/generate_dataset.py): fixed-seed synthetic labels and matching ground truth.
- [`src/gen/augment.py`](../src/gen/augment.py): image effects and coordinate transforms.
- [`src/cv/barcode.py`](../src/cv/barcode.py) and [`src/cv/barcode_blind.py`](../src/cv/barcode_blind.py): template-assisted and blind barcode paths.
- [`src/cv/extract.py`](../src/cv/extract.py), [`src/cv/fields.py`](../src/cv/fields.py), and [`src/cv/symbols.py`](../src/cv/symbols.py): extraction, field naming and symbol detection.
- [`src/gen/render.py`](../src/gen/render.py) and [`src/cv/verify.py`](../src/cv/verify.py): draft rendering and approval-bound print comparison.


## Earlier completion-pass verification, before the photo fix

Environment: Mac Apple Silicon, Conda labellens-cv, Python 3.12.
No dependencies were added. Existing shared schemas, retrieval, API and UI were
not edited. These executed checks are separate from the earlier frozen metrics.

```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider -m "not slow"
........................................................................ [ 16%]
........................................................................ [ 33%]
........................................................................ [ 49%]
........................................................................ [ 66%]
........................................................................ [ 82%]
........................................................................ [ 99%]
....                                                                     [100%]
436 passed, 3 deselected in 158.85s (0:02:38)

/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider src/gen src/cv/test_verify.py tests/test_mock_contracts.py
142 passed in 125.57s (0:02:05)

/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check --no-cache src tests scripts/real scripts/cv_experiments/eval_perspective.py
All checks passed!
```

Existing export/device-set/new-medicine targeted tests additionally reported
`59 passed in 48.25s`. The device offline rebuilder returned images=20 and
symbol_crops=44, with evaluation NOT_RUN and tags LLM-labelled. Source photos
remain local; only their provenance/README is tracked.

## Where the work is delivered

Repository: https://github.com/paridhik11/labellens
Branch: [parth-gen](https://github.com/paridhik11/labellens/tree/parth-gen).
Earlier reviewed CV fixes and contracts were merged into main by Pari; the new
completion-pass work is pushed only to parth-gen and is not claimed merged.

- `6748387`: pinned separate medicine corpus, sources and tests.
- `fb3090a`: independent perspective module and reproducible geometry benchmark.
- `c697a85`: per-field print verification and deferred human-review note.

GitHub's minimal environment does not install the full CV stack, so green CI
is supplemented by the executed Mac Conda checks above. It is not Windows or
real-photo validation. Task-specific reports are in reports/parth_task1.md
through parth_task7.md, plus parth_task7a.md and parth_task9.md. The technical
contract recommendations are in reports/parth_contract_review.md.
