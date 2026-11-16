# Fixed real-photo extraction protocol, 2026-11-16

Frozen before candidate implementation or new per-image scoring inspection.
Baseline: commit 88f9c9d. Score all ten unchanged clear_online device photos,
with their unchanged transcriptions.csv. Inputs and package versions are
fingerprinted in local data/real_photos/protocol_v1/frozen_inputs.json.

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
LOT/EXP keys and symbol-only dates without training on ten scoring images or
adding an external service. Keep template geometry explicit; unknown real-photo
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
remains unmeasured. Fix implementation defects using synthetic tests, not scores.
