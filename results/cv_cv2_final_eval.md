# CV2 fresh transformed-artwork result

LLM-generated references. Human review deferred. Real symbols unmeasured.
Framewise conditional Wilson intervals; repeated artwork is not independent
product validation. The source configuration and candidate were committed before
the score run. Both systems used the same 300-second per-image deadline; timeout
is a scored miss.

| Condition | Complete baseline (95% CI) | Complete CV2 (95% CI) |
|---|---|---|
| clean | 0/96 (0.000 to 0.038) | 32/96 (0.247 to 0.432) |
| moderate | 0/96 (0.000 to 0.038) | 27/96 (0.201 to 0.378) |
| hard | 0/96 (0.000 to 0.038) | 17/96 (0.114 to 0.265) |

**Predeclared release gate: PASS.** Complete-image correctness did not decrease
in any condition and increased in all three. CV2 is now the default; baseline
remains an explicit profile and is the availability fallback if Tesseract is absent.

| Condition | Field | Baseline normalized | CV2 normalized | Strict baseline/CV2 |
|---|---|---|---|---|
| clean | product name | 0/96 | 32/96 | 0/32 |
| clean | lot | 0/48 | 48/48 | 0/48 |
| clean | expiry | 48/48 | 48/48 | 48/48 |
| moderate | product name | 0/96 | 27/96 | 0/27 |
| moderate | lot | 26/48 | 38/48 | 26/38 |
| moderate | expiry | 47/48 | 47/48 | 47/47 |
| hard | product name | 2/96 | 20/96 | 2/19 |
| hard | lot | 12/48 | 0/48 | 12/0 |
| hard | expiry | 24/48 | 12/48 | 22/12 |

Strict cells are two counts with the stated field denominator. Product-name n=96
per condition; lot and expiry n=48. There were 288 frames but only 198 unique
images: clean repeats six unchanged artworks 16 times. A unique-image secondary
summary is clean 0/6 to 2/6, moderate 0/96 to 27/96, hard 0/96 to 17/96.
Baseline had 1 extraction exception and CV2 had 3, each scored as misses.
Four source families, repeated artwork and LLM references limit generalization.
This does not establish real-phone or symbol accuracy.
