# Fixed real-photo extraction protocol, 2026-11-16

Frozen before candidate implementation or new per-image scoring inspection.
Baseline: 88f9c9d. Score ten unchanged clear_online device photos and
transcriptions.csv. Fingerprints/package versions: scripts/cv_experiments/photo_protocol_v1.json.

These photographs, AI readings and aggregate baseline scores were seen in
previous work. This is a fixed previously exposed convenience set, not an unseen
holdout or a statistically independent estimate of generalization.

Development uses invented test text, geometric fixtures and new synthetic
labels only. Do not inspect scoring photos, their OCR outputs, individual
reference values or new scores to choose parameters. No product-specific
vocabulary, filenames, reference copying or manual per-image crop/orientation.

Chosen approach: retain installed RapidOCR CPU models; original-plus-rectified
views, four deterministic quarter-turns, overlapping text crops and generic
spatial key/date rules. This addresses unknown orientation, small text, split
LOT/EXP keys and symbol-only dates without an external service. Keep template geometry explicit; unknown real-photo
aspect ratio is inferred from boundaries, never assumed to be 100:60.

Implementation scope: src/cv/perspective.py, extract.py, new photo OCR/field
helpers; tests; a frozen evaluator in scripts/cv_experiments; contract acceptance,
README, learning log, work summary and report. Shared schemas/retrieval unchanged.

Freeze candidate code after synthetic/unit tests. Run exactly one before/after
comparison, identical photos, blind mode, postcorrect=True, existing confidence
thresholds. Score exact product_name, lot and expiry plus character errors;
count failures as misses. Record runtimes, code/model/input fingerprints and
all per-photo outcomes. Do not tune after seeing scores; report misses honestly.
Human spot-check and symbol-crop review remain deferred; references are
LLM-generated transcriptions, not human ground truth. Real-photo symbol accuracy
remains unmeasured. Use synthetic tests for implementation defects.

Development-only check: 24 tests passed, including the existing synthetic OCR integration.
Keep upright orientation when its text score is within 10% of the best; select
views by populated target fields, total populated fields, then text score.
These rules were frozen before new real-photo scoring.
