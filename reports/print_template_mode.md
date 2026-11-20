# Print-template-mode result

Plan committed at ed8bcb9 before tests; candidate frozen at 357c5f0 before
one final run, seeds 9000-9015. Only 7000-7001 were used for debug changes.
Correct template fields are read as single-line slot crops, using pixel-only
perspective and blank-margin trimming. The 9 mm DRAFT band is masked. Expected
values never enter OCR. Confidence remains 0.8; missing binding/multiline slots
rescan. The API uses its approved version's immutable template version, record
and expected payload; approval gates remain intact. CV2 default is unchanged.

Synthetic PDF-derived photos, 16 correct and 16 different-label prints per
condition. Negatives cycle other lot, other expiry and other name; some retain
the correct barcode, others change encoded lot/expiry too.

| Condition | Correct matches, 95% Wilson | False matches | Missed differences | Rescans, all 32 |
|---|---|---|---|---|
| clean | 16/16 (80.6-100%) | 0/16 (0-19.4%) | 0/16 (0-19.4%) | 0/32 (0-10.7%) |
| moderate | 16/16 (80.6-100%) | 0/16 (0-19.4%) | 0/16 (0-19.4%) | 0/32 (0-10.7%) |
| hard | 14/16 (64.0-96.5%) | 0/16 (0-19.4%) | 0/16 (0-19.4%) | 2/32 (1.7-20.1%) |

Gate PASS. All wrong-label prints mismatched. Zero false alarms; two hard
correct prints rescanned. Missed differences include negative rescans or matches.
Raw per-field evidence: local data/synthetic/print_template_final9000/rows.jsonl.
Reproduce with `python -m src.gen.eval_template_print --final --output NEW_PATH`;
do not tune on these exposed final seeds. Flat white full-frame fallback requires
matching aspect and white perimeter. One template/family and simulated photos
do not establish real print/camera performance. API quality gating is separate;
this paired run scores the real verification engine, not HTTP upload quality.

Validation: full fast suite 950 passed, 5 deselected, 1 warning; ruff src/tests
clean. Existing API approval, supersession and storage tests passed. No checker
threshold or shared schema changed.
