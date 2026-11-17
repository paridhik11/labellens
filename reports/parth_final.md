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

All fields together remain 0/10. References are LLM-generated; human spot-check
and symbol-crop review are deferred, and real-symbol accuracy is unmeasured.
These photos are not an unseen holdout or an 80% claim. Fresh-set gate: PASS,
with 32/96 clean, 27/96 moderate and 17/96 hard complete images, versus 0/96
baseline in each condition. Native QR stalls remain a production issue; evaluation
deadlines count timeouts as misses.
