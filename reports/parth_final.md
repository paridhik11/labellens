# Parth final report

`python -m src.gen.golden` rebuilds DailyMed, synthetic and barcode-change demos.
All six PDF/SVG exports show **DRAFT, not for production**. GEN_HANDOFF tests
execute its example and decode its QR. No demo is approved or published.

Previously exposed online photos, n=10: expiry improved 3/10 to 5/10
(95% Wilson: 11-60% to 24-76%).

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
