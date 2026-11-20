# CV round 3: frozen protocol and release gate

Branch cv3 from origin/main. Hard stop: Saturday 2026-11-21 13:00 Asia/Kolkata
(07:30 UTC). No evaluation, model probe or fetch run preceded this plan commit.
Stop work at the deadline; no rushed promotion. Existing checker thresholds,
schemas and CV2 default stay unchanged. Keep all experiments isolated on cv3.

## New reference set

Target approximately 30 new real medical-device package photos through the
existing DailyMed/online source pipeline. Preserve URL, source rights, SHA-256,
image identity and reference provenance. Exclude the ten clear_online photos,
all previously scored source images, duplicates and near-duplicate product views.
DailyMed flat artwork must be tagged artwork, not mislabeled as camera photos;
it can supplement development only. No invented unreadable names/identifiers.
Transcriptions are LLM-labelled, not human truth. Missing/unreadable fields stay
unscored. Record annotator and uncertainty. Images remain local, scripts and
provenance catalogs versioned. A shortfall in genuine new photos blocks release.

Before predictions, freeze acquisition manifest and family-grouped dev/test split:
20 development and 10 test photos if 30 valid inputs exist. Fixed seed 20261121;
no source/product family crosses splits. Do not read test predictions until the
candidate is frozen. Existing ten images may support diagnosis, never scoring.

## Sequential candidates, development only

1. Barcode prefill: only one unambiguous parsed GS1 barcode can supply AI 10/17.
   Validate AI 17 calendar conversion. Emit prefill values and provenance separately
   from observed print OCR. Keep existing lot/expiry fields and consistency-check
   inputs unchanged. Printed text must never be fabricated from the barcode.
2. Audit existing perspective wiring first. Add only a demonstrated missing path;
   original-photo fallback remains. Coordinate evidence must project to input pixels.
3. Anchor LOT/EXP/BATCH crops on observed OCR keys, enlarge and OCR pixels only.
   No expected-value hints or label-specific dictionaries; abstain on ambiguity.
4. Inspect installed RapidOCR and model availability. Try newest available PP-OCR
   only on dev; absence must fall back cleanly without a forced new engine/API.

Retain a stage only when dev exact correct-field count increases and no per-field
count decreases. Resolve ties in favor of the earlier simpler stage. Report both
printed-only OCR and record-prefill metrics; primary effective fields prefer a
validated prefill but never suppress a printed/barcode discrepancy warning.
Names use case/whitespace normalization; lot identifiers preserve characters;
expiry uses validated calendar normalization without guessing ambiguous dates.

## Final scoring and gate

Freeze selected candidate and models before one paired test run. Fresh synthetic
seeds 12000-12015 per clean/moderate/hard condition, same pinned device template,
varied names/lots/expiry and valid GS1 payloads; include deliberate print/barcode
conflicts as safety cases. Never tune on those seeds. No schema/checker changes.
All exceptions/timeouts count as misses; fixed 300-second per-image deadline
for both systems. Preserve observations durably. No final reruns after scores.

Report exact k/n and Wilson 95% intervals per field, per real-photo split and
synthetic condition. Print/barcode conflicts must still be flagged by the existing
consistency checker. Merge only if at least one effective field improves, no
field regresses on held-out photos or any synthetic condition, and no conflict
check is suppressed. Incomplete acquisition/evaluation blocks release. Otherwise
merge nothing and report the negative/incomplete outcome in reports/cv3.md.
Run full fast pytest and ruff before any no-ff merge; check exact merge CI by API.
