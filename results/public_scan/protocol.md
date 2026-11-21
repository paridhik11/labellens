# Public scan evaluation protocol (written before any scoring)

Method under test: OCR every line (cv2 profile, CV4b budget c2: max_side 1600, budget 55 s, search_side 800), build
candidate strings (lines, adjacent pairs, whole text), match with the unchanged medicine matcher (threshold 0.65),
keep the best. See `src/api/public_scan.py`.

## Sets

| Set | What | Used for |
|---|---|---|
| dev_device | the 20 CV4 dev photos (`src/gen/cv4_dataset.json`, split dev), device packs, none is in the medicine corpus | tuning |
| dev_packs | 20 synthetic packs of corpus names plus 10 synthetic decoys (names of medicines not in the corpus), seeds 7000 to 7029 (`scripts/public_scan/make_packs.py dev`) | tuning |
| fresh | the 50 CV4b fresh photos (`src/gen/cv4b_fresh.json`, hashes verified), device packs, none is in the medicine corpus | scored ONCE with the frozen config |
| heldout_packs | 30 synthetic packs (one per corpus product) plus 15 decoys, seeds 7100 to 7144 | scored ONCE with the frozen config |

The fresh photos were never used to fit this method. They were exposed to the older CV4b name-in-OCR check
(`reports/cv4b.md`, 30 right-name and 20 wrong-name photos, scored once there). That check asked a different
question and its misses were not analysed per cause.

## Candidate configurations (at most three, fixed here)

- A: 12 strings sent to the matcher, pairs and full text on, best cosine wins.
- B: as A but a `matched` outcome beats a higher-scoring `needs_review` (order "outcome").
- C: 20 strings, otherwise A.

## Selection rule (on dev_device and dev_packs only)

1. Drop any configuration with a wrong identification on a dev photo (an accepted product that is not the expected
   one, or any accepted product on a photo whose product is not in the corpus).
2. Of the rest, take the highest correct-identification count on dev_packs positives.
3. Ties: the smaller `max_candidates` (faster, fewer chances for an accidental match).
4. If every configuration has a wrong identification, take the one with the fewest and say so.

The chosen configuration is written to `src/api/public_scan_config.json` in its own commit before the fresh set
or the held-out packs are read.

## Measures (every photo falls in exactly one)

correct (matched, expected product), wrong (matched, other product or not-in-corpus photo), review (needs_review;
the expected product in the top 3 is counted), not_identified (no_match or no_text), timeout (budget cut or
child killed), retake (the quality gate refused the photo). Both views are reported: the pipeline view (gate first)
and the stricter view that ignores the gate and runs every photo. Latency is the whole identification (child OCR
plus matching) after one warm-up match; median, p90, max. Wilson 95% intervals.

## Gate

Wrong identification 0 on every photo whose product is not in the corpus (fresh, dev_device, decoys), and every
photo under 60 s. The correct-identification rate is reported whatever it is.
