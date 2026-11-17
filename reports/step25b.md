# Step 25b: print verification

**Built:** `verifyPrint`, `getPrintVerification`, `listPrintVerifications` are real (CR-26). 202 Job, append-only `print_verifications` rows with every compared field, OCR confidence and box. Needs an approved, current, generated version; refusals are 409 `not_approved`, `rejected`, `version_superseded`, `no_reference`. 11 fake-engine tests (CI needs no CV libraries).

**Deviations:** the job does not call `src.cv.verify_print`: its gate binds approval to a legacy manifest hash, ours binds to the PDF hash, so I enforce approval in the API and run the same CV steps. Symbols are not compared (detector untrusted). The photo-quality gate is skipped for `clean_print_scan` (a white page reads as zero contrast); decided before the run.

**Real run (24 positive, 24 negative photos, 8 per condition).** Photos are SYNTHETIC (approved PDF through the project's photo simulator), not physical prints. Nothing was tuned afterwards.
- False matches: 0/24, 95% interval [0, 14]% (0/8 per condition, [0, 32]%).
- Correct matches: 0/24 [0, 14]%. Every positive, in all conditions (not only clean), ended `rescan_needed` (24/24 [86, 100]%). Cause not diagnosed.
- Missed differences: 3/24 [4, 31]%, all hard photos, all rescan_needed (none called match).
- False alarms: 0.

It never wrongly accepted, and never confirmed a correct print.

Details: `results/step25b_print_verify.md`.
