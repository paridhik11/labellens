# CV4: frozen protocol and gate

Branch cv4 from origin/main c4ac3d9. Deadline: Sunday 2026-11-22 13:00
Asia/Kolkata (07:30 UTC). Stop earlier if complete; stop at deadline regardless
of outcome. This plan must be committed before installs, acquisition or trials.

## First experiment: isolated OCR upgrade

Create a throwaway Python 3.12 venv under /private/tmp. Run pip install --upgrade
rapidocr onnxruntime, then try paddleocr (and its compatible CPU runtime only if
installable cleanly). Never upgrade labellens-cv. Inspect official documentation
and installed assets for PP-OCRv5/v6. Test available models on dev only. Record
versions, model names, hashes, install/download failures and fallback behavior.
No absent model gets a fabricated score. Use existing CV2/CV3 when unavailable.
New model chosen only if right-product dev found count increases with zero
false found on fixed dev wrong-name pairings. Ties keep existing OCR. Freeze
the chosen implementation, environment and models before final predictions.

## Known-product name evidence

Only professional uploads with a product_id use its registered name. Compare
that expected string to observed OCR, never overwrite observations with the
registered name. Return status found/not_found, exact observed matched line(s),
OCR confidence, similarity and evidence boxes. Missing product/name/text means
not_found. Public/blind extraction and schemas/checker thresholds stay unchanged.

Freeze matching now: Unicode NFKC, case-fold, remove trademark glyphs, tokenize
letters/numbers. Match tokens one-to-one by edit similarity (SequenceMatcher),
minimum token similarity 0.80; numeric tokens must match exactly. Expected-token
coverage is character-length weighted; require coverage >= **0.90** and every
distinctive expected token matched >= 0.80. OCR confidence must be >= **0.80**.
Allow one observed line or up to three spatially adjacent, aligned lines; no
arbitrary distant text concatenation. Generic-only expected names abstain.
Generic words fixed now: medical, device, catheter, introducer, set, kit, suture,
sterile, disposable, system, guidewire, needle, surgical, balloon, delivery,
single, use, and, the, for, of. No reference-value dictionaries or OCR hints.
Similarity/confidence are evidence scores, not calibrated probabilities.

## Acquisition and split

Use the existing DailyMed/online photo source pipeline. Target 30 new real
device-package photos plus 15 separate wrong-product photos. Exclude the old
ten, all CV3 candidates and every previously scored source/near duplicate.
Flat DailyMed artwork is development supplement only, never called a photo.
Images local and ignored; URLs, rights, hashes and LLM-labelled transcriptions
versioned. Never infer reference names from barcodes/catalog titles. Preserve
unreadable/ambiguous exclusions before predictions; no human-validation claim.

Freeze names, product families and split before inference: 20 dev/10 test
positive photos, seed 20261122, no family crossing. Fifteen further photos are
held-out negatives from other product families. Pair each to a different
registered product using maximal normalized token overlap, deterministic ties;
freeze pairings before predictions. Dev negatives use other dev photos/names
only, never the 15 held-out negatives. Baseline is unchanged CV2 blind discovery
on the same ten positive photos. Exact-name baseline normalization uses the
same normalized tokens, without fuzzy reference scoring.

## Once-only final scoring and merge gate

Image-only OCR receives no expected names. Name matching is a separate step
after OCR with the registered name, never a source of invented OCR evidence.
Fixed 300-second/image bound, equal baseline/candidate resource limits; durable
journals, failures counted misses on positives. Failures on negative photos
make the gate incomplete, never successful negative evidence.

Score final 10 right-product and 15 wrong-product cases once after candidate
freeze. Gate: right-product found count strictly above CV2 blind exact-name
count on identical photos AND false found **0/15**, all observations complete.
Report Wilson 95% intervals, counts, failures and fallback coverage separately
in reports/cv4.md. No tuning/fallback selection after final results. If gate
fails, merge nothing. If it passes, full fast pytest, ruff, --no-ff merge from
main checkout, push and verify exact merge CI through GitHub public API.

## Planned files and verification

src/cv/known_product.py: evidence-only matcher; src/cv/ocr_modern.py: lazy optional
modern OCR adapter with existing-engine fallback. src/api/scans.py and a small
src/api helper: registered-name check stored separately and returned with upload
extraction; no shared schema/database migration. tests/test_cv4*.py: tokens,
wrong-product abstention, coordinates, API isolation, model absence/failure.
src/gen/cv4_acquire.py and src/gen/cv4_dataset.json: reproducible source freeze.
scripts/cv_experiments/cv4_*.py plus isolated requirements lock: experiments and
one-command evaluation. requirements.txt only if a runtime dependency is needed;
optional OCR versions documented separately. reports/cv4*.md/json, results/cv4/
and docs/LEARNING_LOG.md: protocol, actual evidence, limits and step report.
No UI, src/ir, checker or src/common/schemas.py changes.
