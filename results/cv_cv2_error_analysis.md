# CV2 development error analysis before fixes

Six development photos only. Baseline field algorithms at 740a0ab are unchanged
in merged main d39b0fb; cached baseline OCR observations are reused for diagnosis.
All reference transcriptions are LLM-generated, not human ground truth.
A correct text observed but misassigned is a parser error; missing/wrong characters
are OCR. A boundary warning is not automatically a causal failure because the
original-photo fallback still ran. No final artwork predictions were inspected.

| Dev photo | Missed field | Primary cause | Observed evidence |
|---|---|---|---|
| 01 Crylrex | expiry | parser | 2027-01 read, but two unkeyed dates cause abstention |
| 04 Cook | name | OCR | retained line only Catheter; footer COOK selected |
| 04 Cook | expiry | parser | correct date read, unkeyed manufacture/expiry ambiguity |
| 05 Stratafix | name | OCR | Stratafix read without trademark glyph |
| 05 Stratafix | lot | OCR | expected alphabetical value absent from retained lines |
| 05 Stratafix | expiry | OCR | expected date absent from retained lines |
| 07 Introcan | name | OCR | spacing/trademark lost; manufacturer logo selected |
| 08 Introcan2 | name | OCR | split name and trademark read as question mark |
| 09 Introcan | name | OCR | quantity merged with name; trademark misread |
| 09 Introcan | lot | parser | correct value read without recognized LOT key |
| 09 Introcan | expiry | parser | correct date read, multiple dates left unresolved |

Primary totals: OCR 7, parser 4, label-not-found 0, perspective 0. Boundary warnings
are secondary on photos 01,05,08; they did not prevent full-image OCR. Perspective
is already connected through warp_label. No destructive warp is established as
the primary cause of these eleven misses.

Fix order: preserve/upscale full label evidence, compare an independent OCR
engine, then tolerant generic keys/date formats. Use decoded or printed GS1
hints only to select a matching observed date, never invent missing print text.
Do not invent trademark glyphs, product dictionaries, identifiers or plausible
lots. Agreement/engine confidence is evidence strength, not correctness probability.
