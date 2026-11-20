# Symbols, phase 7: lot and expiry format check

**What I did.** `check_extraction` (`src/cv/consistency.py`) used OCR confidence alone to decide between `barcode_mismatch`
(critical) and `needs_human_review`. It now also checks that the printed reading is well formed: the printed key LOT or EXP is
present, a lot has only letters, digits and `._/-` (1 to 20 characters), and an expiry is an ISO date that exists in the calendar.
A damaged reading that differs from the barcode gives `needs_human_review`, never `barcode_mismatch`, whatever the OCR
confidence. A well-formed, confident, different reading is still a mismatch. `check_format=False` restores the old behaviour so both
can be compared on the same OCR (`eval_v2` records both).

**Dev seeds 42 and 43** (rule written from your spec, not tuned on these): false `barcode_mismatch` alarms on very hard labels fell from
5/33 to 1/33 (blind) and 9/33 to 1/33 (template). Wrong barcodes stayed flagged 68/68 and 0/408 false alarms on the other cases.

**New seeds 103 to 105, run once** (51 labels per condition; 612 other-case labels; 102 wrong-barcode labels per mode):

| Very hard, print agrees with barcode | before (confidence only) | after (format check) | now `needs_human_review` |
| --- | --- | --- | --- |
| blind | 7/44 (15.9%; 7.9 to 29.4) | 1/44 (2.3%; 0.4 to 11.8) | 6/44 (13.6%) |
| template | 8/45 (17.8%; 9.3 to 31.3) | 1/45 (2.2%; 0.4 to 11.6) | 8/45 (17.8%) |

Clean to hard_original: 0 false alarms before and after, in both modes. **Real wrong barcodes: 102/102 flagged `barcode_mismatch` in both modes
before and after.** Other negative cases: 0/612 alarms in both modes.

**What it means.** About 85% of the false critical alarms under glare become review requests; the reviewer still sees them
(14 to 18% of very hard labels) but not as a critical mismatch. One false mismatch per 44 remains: a confident misread that
still looks like a valid lot or date, which a format check cannot catch.

**Files.** `src/cv/consistency.py` (`format_problem`, `check_format`), `src/cv/eval_v2.py` (records the old flags too),
`tests/test_cv_text_rules.py`, `scripts/symbols/phase7_report.py`, `scripts/symbols/gen_phase7.sh`.

**Unsure.** `eval_v2` runs for seeds 103 to 105 crashed twice with a Windows process-pool error while other jobs ran, so I re-ran
them one at a time; the numbers come from the complete re-run. Synthetic labels only.
