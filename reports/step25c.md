# Step 25c: why correct prints end as rescan_needed

Fresh seeds 7000 to 7007, 8 correct prints per condition (24), synthetic photos of the approved label, real verifier. `results/step25c_diagnosis.md` has one line per rescan. No threshold, rule or code was changed (so there is no after run).

**Result:** 0 match, 23 rescan_needed, 1 mismatch (a false alarm).

**Cause (22 of 23 rescans, all conditions):** the golden label prints bare values (`GP-100`, `LOT2`), not keyed lines. The blind extractor maps fields by keys (`REF:`, `LOT:`): `GP-100` is never mapped to model (FIELD_MISSING, no evidence) and `LOT2` is read as key `LOT` plus value `2` (expected `LOT2`). Text, address, expiry and barcode all matched at 0.98 to 1.00 confidence. The other rescan: glare gate (1). Not a bug in `printverify.py`; the comparison is correct.

**False alarm (hard 7001):** the blind mapper took `duction`, a fragment of the DRAFT band, as the product name at 0.9999 confidence, so the verifier said mismatch.

**v2 items (design, not changed):**
1. Print keys on the label (template prefix slots `REF: `, `LOT: `) or verify in template mode, where slot positions name the fields.
2. Blind mapper must ignore the DRAFT and TEST DATA band.
3. Both live in `src/cv` and the template, not in the API.
