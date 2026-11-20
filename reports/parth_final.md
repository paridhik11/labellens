# Parth final report

Three repeatable golden packages now rebuild with `python -m src.gen.golden`:
clean DailyMed review sheet, synthetic device, and TESTLOT1 to TESTLOT2 barcode
change (REGENERATE). They remain local in `data/golden_demo/`; no package is
approved or published. All six PDF/SVG exports visibly show **DRAFT, not for
production**. Tests execute the documented GEN_HANDOFF example and decode its QR.

Previously exposed online package photos, n=10, strict exact counts (95% Wilson):

| Field | Baseline | CV2 |
|---|---|---|
| Name | 1/10 (2-40%) | 1/10 (2-40%) |
| Lot | 7/10 (40-89%) | 4/10 (17-69%) |
| Expiry | 3/10 (11-60%) | 5/10 (24-76%) |

Limits: CV2 remains the default despite these field-level weaknesses.

| Condition / field | Baseline | CV2 |
|---|---|---|
| Hard lot | 12/48 | 0/48 |
| Hard expiry | 24/48 | 12/48 |
| Real-photo lot | 7/10 | 4/10 |
| Real-photo product name | 1/10 | 1/10 |

All fields together remain 0/10 on real photos. Initially LLM-generated references
were subsequently user-confirmed; symbol annotations are AI-assisted,
human-confirmed. Standalone v1 found 0/4 manufacturer and 0/9 hourglass
presences; four other categories are unsupported. See parth_symbol_eval.md.
These photos are not an unseen holdout or an 80% claim. Fresh-set gate: PASS,
with 32/96 clean, 27/96 moderate and 17/96 hard complete images, versus 0/96
baseline in each condition. Native QR stalls remain a production issue; evaluation
deadlines count timeouts as misses.
