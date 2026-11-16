# Completion protocol, 2026-11-16

Merged origin/main first. Preserve its CV fixes, checker thresholds, APIs and schemas.

Files planned: src/cv/extract.py and lazy dependency adapter, photo OCR/field helpers,
scripts/cv_experiments/photo_split_v2.json and evaluation runner, tests for these;
src/export and src/gen draft headings; src/gen/medicine.py loader;
docs/GEN_HANDOFF.md, summary/log and short report. Data binaries remain local.

Freeze photo families and byte hashes before inspecting new development outputs.
Seed 20261116 shuffles distinct groups, assigning whole groups to test until at
least four images are covered. Introcan variants stay together. Tune only dev;
freeze implementation before one paired test scoring command. Both baseline
740a0ab and candidate are scored once on the test partition. All ten originals
were previously exposed/scored: never describe this split as a new unseen holdout.
Report exact k/n and Wilson 95% intervals per field and partition. Do not pool
photo and artwork scores. Exceptions count as misses; missing references are unscored.

Use DailyMed device artworks as development material only. Try more public
photographs where provenance/readability permit; do not force unreadable values.
References and symbol annotations remain LLM-generated. Human photo/crop review
stays deferred; real-symbol accuracy remains unmeasured.

Keep installed CPU OCR and generic pixel/text rules, with development-only model
choices; no product dictionaries, reference copying or new API/model dependencies.
Lazy CV imports must permit API import in minimal CI. Verify that separately.

Audit tracked DailyMed binaries; remove any from index while preserving disk files,
and retain pinned re-fetch scripts/catalogs. Drafts with placeholders or synthetic
pictograms must visibly say DRAFT, not for production, including approved test
exports. Verify PDF/SVG and legacy rendering. Supply executable handoff examples
and medicine Chunk loader tests. Run full fast suite, CV/export tests and Ruff,
then merge to main with --no-ff, push both branches and check public-API CI.
