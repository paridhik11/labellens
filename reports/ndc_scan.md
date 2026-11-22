# NDC scan: identify a medicine photo through its NDC

Branch `ndc-scan`. Protocol `results/ndc_scan/protocol.md`, amendment `results/ndc_scan/protocol_amendment.md`, full
tables `results/ndc_scan/results.md`. The matcher thresholds, the never-auto-confirm rule and every existing gate
are unchanged. Every result is still "Is this X?" with its evidence.

## What was built
- `src/ndc/`: NDC parsing (printed 4-4-2, 5-3-2, 5-4-1 and 11-digit; UPC-A, EAN-13 and GTIN-14 barcodes with the check
  digit), normalised to 11 digits, exact lookup in a table of 100 package NDCs from the 30 corpus SPLs (no fuzzy
  matching); zxing-cpp barcode reader; our own BM25 over each product's package-label (PDP) text; fusion rule.
- `src/api/ndc_glue.py`, `public_scan.scan_photo(ndc=True)`: the barcode is read first, a table NDC from the barcode
  ends the scan without OCR, then a printed table NDC wins, otherwise method E decides unchanged, and only when E finds
  nothing a BM25 review list (tau 22.0, top 3, chosen on dev only) may be shown.
- Not built: DINOv2 image similarity (time box). The live DailyMed hook `outside_corpus_lookup` returns None (live
  DailyMed was merged during this work; it is not wired into this scan).

## Run 1: invalid
Scored once at commit `e85c5cb` (`2ea1cd0` after the rebase onto main). Invalid as a test of the method: the harness
read photos in parallel (up to 6 OCR readers) on 12 cores shared with another session's OCR worker and a pytest run, so
most photos timed out before any text was read (0 lines on 33/45 unused decoys, 63/80 positive readings). Gate check 2
failed on that run. Kept in `results/ndc_scan/run1_invalid/`.

The amendment was committed and pushed before the re-run (`0adb158`, `a9c84b6` after the rebase): same frozen code,
config, budget, sets and gate; one photo at a time on an idle machine (calibration: per-photo time matched a lone
request only at concurrency 1).

## Gate run (run 2), scored once
Positives 57 photos (15 products), unused gate E decoys 45 photos (15 products), new unused set 54 photos (18 decoy
products). Wilson 95% intervals.

| photo level | new | E replay |
|---|---|---|
| positives correct | 46/57 (69 to 89%) | 34/57 (47 to 71%) |
| positives wrong | 0/57 (0 to 6%) | 0/57 (0 to 6%) |
| positives timeouts | 0 | 0 |
| unused decoys wrong | 0/45 (0 to 8%) | 0/45 (0 to 8%) |
| unused decoy timeouts | 6 (E recorded 13) | 6 |
| new set wrong | 0/54 (0 to 7%) | 0/54 (0 to 7%) |
| decoy photos with a review candidate shown | 42/99 | 32/99 |

| product level | new | E replay |
|---|---|---|
| positive products with at least one correct photo | 13/15 (62 to 96%) | 11/15 (48 to 89%) |
| unused decoy products wrong | 0/15 (0 to 20%) | 0/15 (0 to 20%) |
| new-set decoy products wrong | 0/18 (0 to 18%) | 0/18 (0 to 18%) |
| decoy products with a review candidate shown | 22/33 | 19/33 |

Positives by condition (new vs E): artwork 16/19 vs 13/19, moderate 16/19 vs 11/19, hard 14/19 vs 10/19.

Gate: 1 pass (0 wrong decoy products), 2 pass (timeouts 6 vs E 6 and E recorded 13), 3 pass (46 vs 34). Gate passed.

Two photos timed out because the machine idle-slept between agent turns (wall time 1595 s on an unused decoy, 1472 s
on a new-set photo, both 0 lines). Both count as timeouts for both methods. The new method shows more review
candidates on decoy photos (42 vs 32): more "Is this X?" prompts, never a confirmation.

## Coverage of each signal (gate run)
- Positives: printed NDC in the table on 32/57 photos, barcode NDC in the table on 10/57, either 33/57. Every
  NDC-decided photo was the right product (33/33).
- Decoys: no table NDC on any of 99 photos (an NDC barcode was read on 28, a printed NDC-shaped string on 47).

## Supplementary (not a gate run)
Single-reader re-read of the 57 positives with the other session still busy, scored before the amendment by the same
frozen code: correct 42/57 (61 to 83%) new vs 27/57 (35 to 60%) E replay, 0 wrong.

## Pre-merge suite
Rebased onto main `152cdf7` without conflicts; `src` diff against main is identical to the original diff (method
code unchanged). Run on the rebased branch, server on port 8031, nothing else running:
- Fast tests 994 passed, 9 skipped; ruff clean.
- UI states 67 (61 plus the 6 live DailyMed states), mock and api mode: 0 failed.
- live_flows 13 flows, 0 FAIL (golden e2e 9/9); camera_check ALL PASSED; confirm_check ALL PASSED.
- demo_e2e.py 20 of 20 PASS, no mock, no fallback.

The rebase rewrote the branch commits, so the rebased branch was pushed as `ndc-scan-rebased` (no force push);
`ndc-scan` keeps the original history with the original hashes named above.

## Limits
Synthetic photos rendered from DailyMed artwork, 30-product corpus, one machine; OCR timings depend on load.
