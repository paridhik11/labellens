# Step 25b: print verification, what the real verifier gets wrong

Real renderer, real extractor, real quality gate; 8 synthetic photos per condition and kind (seeds 5000 and up), made from the approved PDF with the project's photo simulator. No physical print was photographed. Nothing was tuned on these photos.

Right answers: positive (the approved label) is `match`; negative (a label of another lot) is `mismatch`.

| kind | condition | n | match | mismatch | rescan_needed | job failed | right |
|---|---|---|---|---|---|---|---|
| positive | clean | 8 | 0 | 0 | 8 | 0 | 0/8 |
| positive | moderate | 8 | 0 | 0 | 8 | 0 | 0/8 |
| positive | hard | 8 | 0 | 0 | 8 | 0 | 0/8 |
| negative | clean | 8 | 0 | 8 | 0 | 0 | 8/8 |
| negative | moderate | 8 | 0 | 8 | 0 | 0 | 8/8 |
| negative | hard | 8 | 0 | 5 | 3 | 0 | 5/8 |

- False alarms (approved label called mismatch): 0 of 24
- Missed differences (other lot called match): 0 of 24
- Fields behind the false alarms: none
- Rescan reasons: {'Weak or missing evidence': 21, 'Photo quality': 6}

False alarm details (field, expected, observed):

Missed difference details (what the verifier said about the other lot):

Symbols are not compared (the symbol detector is not trusted).

## Per condition with 95% Wilson intervals (percent, in brackets)

| condition | photos (pos/neg) | false match (neg called match) | correct match (pos called match) | missed difference (neg not called mismatch) | rescan rate pos | rescan rate neg |
|---|---|---|---|---|---|---|
| clean | 8/8 | 0/8 (0%) [0, 32] | 0/8 (0%) [0, 32] | 0/8 (0%) [0, 32] | 8/8 (100%) [68, 100] | 0/8 (0%) [0, 32] |
| moderate | 8/8 | 0/8 (0%) [0, 32] | 0/8 (0%) [0, 32] | 0/8 (0%) [0, 32] | 8/8 (100%) [68, 100] | 0/8 (0%) [0, 32] |
| hard | 8/8 | 0/8 (0%) [0, 32] | 0/8 (0%) [0, 32] | 3/8 (38%) [14, 69] | 8/8 (100%) [68, 100] | 3/8 (38%) [14, 69] |
| all | 24/24 | 0/24 (0%) [0, 14] | 0/24 (0%) [0, 14] | 3/24 (12%) [4, 31] | 24/24 (100%) [86, 100] | 3/24 (12%) [4, 31] |

Other outcomes: positives called mismatch (false alarms): 0; jobs that failed: 0.
