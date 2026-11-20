# CV2 plan and frozen evaluation policy

Deadline: 2026-11-18 evening, Asia/Kolkata. Work autonomously within this window.
Main was merged first. Perspective is already connected through warp_label;
verify its path and coordinates rather than adding a duplicate correction.

First diagnose all eleven baseline misses on the six existing dev photographs.
Use the first failing stage: absent usable image -> label-not-found, destructive
warp -> perspective, missing/wrong recognized characters -> OCR, present correct
text assigned incorrectly -> parser. Boundary warnings alone are not a causal
failure when full-photo fallback still reads text.

Files: new CV2 OCR/field helpers and an opt-in extraction profile; dataset builder,
frozen config and evaluator under scripts/cv_experiments; tests; fixed golden
package script under src/gen; documentation and the two requested short reports.
No checker threshold, common schema, retrieval or app integration edits.

Develop only on six previously exposed dev photos and four dev artworks from
three families. Final artworks belong to four different families. Generate 288
fresh final frames: six original artwork crops x16 repetitions x three conditions
(clean, moderate, hard including glare), using fixed seeds. No injected text or
identifiers. Blank source fields stay unscored. All transcriptions are LLM-generated.
Commit source crops, source hashes, references, seeds, scoring and release rules
before scoring. Final frames/predictions are not inspected during development.

Primary: complete-image normalized field exactness (all available references
correct), per condition. Normalize name case/spacing/trademark only, date formats
by calendar, identifiers by printed keys/spacing only; also report strict exact.
Report per-field counts and Wilson 95% intervals. These are conditional augmentation
intervals, not independent-product or real-phone confidence. Repeated artworks
and only four final families limit conclusions.

Choose the dev-best of upscaled RapidOCR and optional Tesseract consensus. Freeze
candidate before one paired final scoring invocation. Promote only if complete
image counts never decrease by condition and strictly increase in at least one.
Otherwise retain baseline. Phone results remain a separate, previously exposed
check, never a fresh-set selection criterion. No second scoring or test tuning.

Also build three repeatable golden demos and verify every label PDF/SVG warning,
including approved prototypes. Existing GEN_HANDOFF execution test is retained.
Merge with --no-ff only after tests/lint and check CI using the public API.

Development selection tie-break, recorded before reading the revised candidates:
maximize complete dev frames summed across conditions, then normalized correct
fields; an exact tie selects upscaled RapidOCR alone to avoid the external binary
and extra latency. Initial OCR-only voting was diagnostic (0/8 complete per
condition). The revised candidates share frozen CV code at 806c9d0.
The archived baseline final job was queued while dev jobs ran; its output remains
sealed until candidate selection. No final predictions or scores informed edits.
Clean has six unique images repeated 16 times, because clean augmentation is an
identity operation. Report 288 frames but only 198 unique pixels overall; clean
frame intervals are descriptive and do not create 96 independent observations.
