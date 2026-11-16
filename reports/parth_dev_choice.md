# Development choice before test scoring

Baseline: main at 740a0ab. The pinned, family-grouped seed-20261116 split has six
dev and four test photos. All ten were exposed in earlier work; this is not a
new unseen holdout. New choices used dev only, plus invented geometry/text tests.

First candidate: allow alphabetic split-key lots, join adjacent name parts and
suppress repeated logos. Dev exact name/lot/expiry stayed 1/6,4/6,2/6.

Selected candidate: also preserve confident full OCR lines when overlapping crops
produce higher-confidence fragments, favor headings over footer logos, and join
observed name pieces on either side. Dev exact scores became 2/6,4/6,2/6. Name
character edits fell from 95/113 to 63/113. This corrects general crop/layout
failures without a product dictionary, invented trademark glyphs or reference
copying. Select it because dev name accuracy improves without losing lot/expiry
exact matches. The same installed CPU OCR, orientation policy and confidence
settings remain. No checker threshold changes.

Freeze code before one guarded paired test invocation; do not tune after test
results. Report before/after k/n and Wilson 95% intervals per field. Tiny selected
samples and related layouts limit generalization. Human spot-check and crop
review remain deferred; all reference annotations/transcriptions are LLM-generated.
Real-symbol accuracy remains unmeasured.

Twenty pinned DailyMed artworks were re-verified offline. Two related, annotated
Swissmedic-hosted packaging illustrations were downloaded as extra dev material;
they are artwork, not new photographs or independent tests. No additional real
photo was accepted from this search. Downloads stay local and are reproducible.
