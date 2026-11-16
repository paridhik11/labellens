# Frozen-protocol real-photo comparison

Condition: photo. Ten fixed device photographs. References: LLM-generated transcriptions.
Human spot-check and symbol-crop human review deferred. Real-photo symbol accuracy unmeasured.
Previously exposed convenience cohort, not an unseen holdout. No tuning on this scoring run.

Baseline: 88f9c9d. Candidate: c2759e9.

| Field | Before exact | After exact | Before character edits | After character edits |
|---|---|---|---|---|
| product_name | 1/10 | 1/10 | 161/193 | 158/193 |
| lot | 0/10 | 7/10 | 78/78 | 19/78 |
| expiry | 0/10 | 3/10 | 93/93 | 63/93 |

An extraction exception remains a miss. Empty references are unscored.
Exact matching preserves case, punctuation and printed date format; only printed field keys are removed.
Improvement does not establish 80% real-world accuracy, human validation or approved-print accuracy.
Choice: installed RapidOCR CPU, original and rectified views, quarter-turn search, overlapping crops,
generic spatial keys and dates. No scoring-specific names or identifiers. Pari owns app integration.

Reproduction, from the repository root with the CV Conda Python:

```bash
mkdir -p /tmp/ll-photo-before /tmp/ll-photo-after
git archive 88f9c9d | tar -x -C /tmp/ll-photo-before
git archive c2759e9 | tar -x -C /tmp/ll-photo-after
python scripts/cv_experiments/eval_photo_protocol.py --code-root /tmp/ll-photo-before --revision 88f9c9d --output data/real_photos/protocol_v1/before.json
python scripts/cv_experiments/eval_photo_protocol.py --code-root /tmp/ll-photo-after --revision c2759e9 --output data/real_photos/protocol_v1/after_frozen.json
python scripts/cv_experiments/eval_photo_protocol.py --before data/real_photos/protocol_v1/before.json --after data/real_photos/protocol_v1/after_frozen.json --output results/cv_photo_before_after.md
```

Both sides use the same ten byte-pinned photographs and CSV, package versions
recorded in scripts/cv_experiments/photo_protocol_v1.json, and installed bundled
RapidOCR models. The candidate has zero extraction exceptions. A first attempt
that overlapped the main merge was discarded without score inspection; the
reported candidate was run from an isolated archive. No scoring results changed
the implementation. The later main merge adds an optional v2 symbol selector;
this comparison retains the unchanged v1 default.
