# Public photo scan: CANDIDATE, not KEPT (gate failed, not merged)

Branch `public-scan`. Backend, contract (CR-27), UI and camera flow are built and tested. The identification method did not meet the gate, so nothing was merged to main and the page there still uses the mock.

## Method
OCR every line (CV4b budget: 1600 px, 55 s), build candidate strings, run the unchanged matcher (threshold 0.65), accept only what it accepts. Three frozen configs A, B, C (protocol.md). On dev they gave identical results and all failed: positives 9 wrong, decoys 20 of 45 wrong, device packs 1 wrong of 20. Cause: many strings per photo, so the best score passes 0.65 by chance. Candidate D (protocol_v3.md, committed before D was scored) adds a name-evidence check (a corpus-derived distinctive word must be visible in the OCR text; a partly visible name is review). D alone had 0 wrong on dev; the selection rule chose it and it was frozen alone in a commit.

## Data
Real DailyMed package-label images (pinned by sha256), photographed virtually with the project's simulator (artwork, moderate, hard). Real artwork with simulated camera conditions, not real phone photos: real-photo performance is unmeasured. One source, software-read. Dev and fresh are disjoint by product. The 50 CV4b device packs were exposed earlier to the CV4b name-in-OCR check (30 right-name, 20 wrong-name, scored once); this method was never fitted to them. They can only test false identification.

## Fresh result (D, scored once)
- 57 positive photos: 34 correct (59.6%, Wilson 46.7 to 71.4), 33 in the pipeline view after the retake gate. Per condition correct: artwork 13/19, moderate 11/19, hard 10/19. About 8 more were review with the right product in the top 3.
- 120 decoy photos: **3 wrong**, all one product (pioglitazone + metformin, a pre-declared confusable decoy) shown as plain metformin in all three conditions. 54 review, 56 not identified, 7 timeouts.
- 50 device packs: 0 wrong, 2 review, 44 not identified, 4 timeouts. Median 28.5 s, max 50.1 s.
- Latency, real set: median 22.0 s, p90 39.9 s, one photo logged 1613.9 s (not killed, no time cut; probably the PC sleeping, not confirmed).

## Gate: FAILED
Wrong identification must be 0 on every not-in-corpus photo (3 wrong), and every photo under 60 s (one over). D's rule accepts a combination pack as its single-ingredient product because "metformin" is its only distinctive word and it is fully visible. The fix (a pack containing words of another ingredient must not match) would be tuned after seeing the fresh set, so it needs a new fresh set.

## State
Not merged, README and main unchanged, pre-merge suites not run. The camera flow passed its fake-camera check earlier. Public uploads would be stored by sha256 under data/api/uploads.
