# Checker evaluation: checker_dev_vh

Commit 28ca94f (src/checker has uncommitted changes). Seeds [200, 201], 34 base labels, 170 images (5 image variants x 3 conditions per base; the udi_mismatch and rx_missing kinds reuse the clean image with a changed record). Retrieval: {'method': 'hybrid_rrf', 'module': 'device', 'k': 10, 'rrf_k': 60, 'stem': False, 'prefix': False}. Symbol detector trusted: False. Wilson 95% intervals, n in every cell, conditions never blended.

## Layer: oracle extraction (perfect CV, so the photo condition does not apply; shown once)

### Recall on injected errors

| kind | condition | n | flagged (any flag of the expected rule) | confident (needs_human false) | extraction raised |
|---|---|---|---|---|---|
| expiry_format | clean | 0 | n=0 | n=0 | 0 |
| barcode_mismatch | clean | 0 | n=0 | n=0 | 0 |
| missing_symbol | clean | 0 | n=0 | n=0 | 0 |
| wrong_name | clean | 0 | n=0 | n=0 | 0 |
| udi_mismatch | clean | 0 | n=0 | n=0 | 0 |
| rx_missing | clean | 0 | n=0 | n=0 | 0 |

### Precision

| kind | condition | TP | FP (group flags on labels not expecting that rule) | precision |
|---|---|---|---|---|
| expiry_format | clean | 0 | 0 | n=0 |
| barcode_mismatch | clean | 0 | 0 | n=0 |
| missing_symbol | clean | 0 | 0 | n=0 |
| wrong_name | clean | 0 | 0 | n=0 |
| udi_mismatch | clean | 0 | 0 | n=0 |
| rx_missing | clean | 0 | 0 | n=0 |

### False alarms on clean labels

Share of clean labels (no injected error, true record) with at least one finding, per condition.

| condition | n clean | any finding | any confident finding (needs_human false) | extraction raised |
|---|---|---|---|---|
| clean | 0 | n=0 | n=0 | 0 |

Per rule (share of clean labels where that rule raised a finding):

| rule | clean |
|---|---|
| (no rule raised a finding on any clean label) | n=0 |

### Citations

| rule | n findings | finding has a citation (hit@10 for the accepted section) | quote verbatim |
|---|---|---|---|
| B-EXP | 18 | 18/18 = 1.00 [0.82, 1.00] | ok |
| B-GS1 | 0 | n=0 | ok |
| B-LOT | 16 | 16/16 = 1.00 [0.81, 1.00] | ok |
| B-READ | 0 | n=0 | ok |
| D-FMT | 34 | 34/34 = 1.00 [0.90, 1.00] | ok |
| P-ADDR | 0 | n=0 | ok |
| P-MFR | 0 | n=0 | ok |
| P-UDI | 34 | 34/34 = 1.00 [0.90, 1.00] | ok |
| R-NAMEPLACE | 0 | n=0 | ok |
| R-RX | 34 | 34/34 = 1.00 [0.90, 1.00] | ok |
| R-UDI | 0 | n=0 | ok |
| S-EXP | 16 | 16/16 = 1.00 [0.81, 1.00] | ok |
| S-MFR | 18 | 18/18 = 1.00 [0.82, 1.00] | ok |

Citations whose quote is not a verbatim substring of its chunk: 0

## Layer: real extraction, template mode

### Recall on injected errors

| kind | condition | n | flagged (any flag of the expected rule) | confident (needs_human false) | extraction raised |
|---|---|---|---|---|---|
| expiry_format | very_hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 32/34 = 0.94 [0.81, 0.98] | 0 |
| barcode_mismatch | very_hard | 34 | 24/34 = 0.71 [0.54, 0.83] | 24/34 = 0.71 [0.54, 0.83] | 0 |
| missing_symbol | very_hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| wrong_name | very_hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 33/34 = 0.97 [0.85, 0.99] | 0 |
| udi_mismatch | very_hard | 34 | 27/34 = 0.79 [0.63, 0.90] | 27/34 = 0.79 [0.63, 0.90] | 0 |
| rx_missing | very_hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |

### Precision

| kind | condition | TP | FP (group flags on labels not expecting that rule) | precision |
|---|---|---|---|---|
| expiry_format | very_hard | 34 | 18 | 34/52 = 0.65 [0.52, 0.77] |
| barcode_mismatch | very_hard | 24 | 26 | 24/50 = 0.48 [0.35, 0.61] |
| missing_symbol | very_hard | 34 | 32 | 34/66 = 0.52 [0.40, 0.63] |
| wrong_name | very_hard | 34 | 24 | 34/58 = 0.59 [0.46, 0.70] |
| udi_mismatch | very_hard | 27 | 0 | 27/27 = 1.00 [0.88, 1.00] |
| rx_missing | very_hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |

### False alarms on clean labels

Share of clean labels (no injected error, true record) with at least one finding, per condition.

| condition | n clean | any finding | any confident finding (needs_human false) | extraction raised |
|---|---|---|---|---|
| very_hard | 34 | 26/34 = 0.76 [0.60, 0.88] | 13/34 = 0.38 [0.24, 0.55] | 0 |

Per rule (share of clean labels where that rule raised a finding):

| rule | very_hard |
|---|---|
| B-EXP | 1/34 = 0.03 [0.01, 0.15] |
| B-LOT | 3/34 = 0.09 [0.03, 0.23] |
| B-READ | 7/34 = 0.21 [0.10, 0.37] |
| D-FMT | 3/34 = 0.09 [0.03, 0.23] |
| P-ADDR | 4/34 = 0.12 [0.05, 0.27] |
| P-MFR | 3/34 = 0.09 [0.03, 0.23] |
| P-NAME | 4/34 = 0.12 [0.05, 0.27] |
| P-REF | 5/34 = 0.15 [0.06, 0.30] |
| R-NAMEPLACE | 1/34 = 0.03 [0.01, 0.15] |
| S-EXP | 4/34 = 0.12 [0.05, 0.27] |
| S-MFR | 1/34 = 0.03 [0.01, 0.15] |

### Citations

| rule | n findings | finding has a citation (hit@10 for the accepted section) | quote verbatim |
|---|---|---|---|
| B-EXP | 18 | 18/18 = 1.00 [0.82, 1.00] | ok |
| B-GS1 | 0 | n=0 | ok |
| B-LOT | 32 | 32/32 = 1.00 [0.89, 1.00] | ok |
| B-READ | 49 | 49/49 = 1.00 [0.93, 1.00] | ok |
| D-FMT | 52 | 52/52 = 1.00 [0.93, 1.00] | ok |
| P-ADDR | 28 | 28/28 = 1.00 [0.88, 1.00] | ok |
| P-MFR | 21 | 21/21 = 1.00 [0.85, 1.00] | ok |
| P-UDI | 27 | 27/27 = 1.00 [0.88, 1.00] | ok |
| R-NAMEPLACE | 7 | 7/7 = 1.00 [0.65, 1.00] | ok |
| R-RX | 34 | 34/34 = 1.00 [0.90, 1.00] | ok |
| R-UDI | 0 | n=0 | ok |
| S-EXP | 41 | 41/41 = 1.00 [0.91, 1.00] | ok |
| S-MFR | 25 | 25/25 = 1.00 [0.87, 1.00] | ok |

Citations whose quote is not a verbatim substring of its chunk: 0

## Layer: real extraction, blind mode

### Recall on injected errors

| kind | condition | n | flagged (any flag of the expected rule) | confident (needs_human false) | extraction raised |
|---|---|---|---|---|---|
| expiry_format | very_hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 30/34 = 0.88 [0.73, 0.95] | 0 |
| barcode_mismatch | very_hard | 34 | 23/34 = 0.68 [0.51, 0.81] | 23/34 = 0.68 [0.51, 0.81] | 0 |
| missing_symbol | very_hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| wrong_name | very_hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 33/34 = 0.97 [0.85, 0.99] | 0 |
| udi_mismatch | very_hard | 34 | 27/34 = 0.79 [0.63, 0.90] | 27/34 = 0.79 [0.63, 0.90] | 0 |
| rx_missing | very_hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |

### Precision

| kind | condition | TP | FP (group flags on labels not expecting that rule) | precision |
|---|---|---|---|---|
| expiry_format | very_hard | 34 | 24 | 34/58 = 0.59 [0.46, 0.70] |
| barcode_mismatch | very_hard | 23 | 21 | 23/44 = 0.52 [0.38, 0.66] |
| missing_symbol | very_hard | 34 | 38 | 34/72 = 0.47 [0.36, 0.59] |
| wrong_name | very_hard | 34 | 24 | 34/58 = 0.59 [0.46, 0.70] |
| udi_mismatch | very_hard | 27 | 0 | 27/27 = 1.00 [0.88, 1.00] |
| rx_missing | very_hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |

### False alarms on clean labels

Share of clean labels (no injected error, true record) with at least one finding, per condition.

| condition | n clean | any finding | any confident finding (needs_human false) | extraction raised |
|---|---|---|---|---|
| very_hard | 34 | 28/34 = 0.82 [0.66, 0.92] | 7/34 = 0.21 [0.10, 0.37] | 0 |

Per rule (share of clean labels where that rule raised a finding):

| rule | very_hard |
|---|---|
| B-LOT | 3/34 = 0.09 [0.03, 0.23] |
| B-READ | 7/34 = 0.21 [0.10, 0.37] |
| D-FMT | 4/34 = 0.12 [0.05, 0.27] |
| P-ADDR | 1/34 = 0.03 [0.01, 0.15] |
| P-MFR | 1/34 = 0.03 [0.01, 0.15] |
| P-NAME | 4/34 = 0.12 [0.05, 0.27] |
| P-REF | 6/34 = 0.18 [0.08, 0.34] |
| R-NAMEPLACE | 4/34 = 0.12 [0.05, 0.27] |
| S-EXP | 4/34 = 0.12 [0.05, 0.27] |
| S-MFR | 2/34 = 0.06 [0.02, 0.19] |

### Citations

| rule | n findings | finding has a citation (hit@10 for the accepted section) | quote verbatim |
|---|---|---|---|
| B-EXP | 12 | 12/12 = 1.00 [0.76, 1.00] | ok |
| B-GS1 | 0 | n=0 | ok |
| B-LOT | 32 | 32/32 = 1.00 [0.89, 1.00] | ok |
| B-READ | 49 | 49/49 = 1.00 [0.93, 1.00] | ok |
| D-FMT | 58 | 58/58 = 1.00 [0.94, 1.00] | ok |
| P-ADDR | 7 | 7/7 = 1.00 [0.65, 1.00] | ok |
| P-MFR | 7 | 7/7 = 1.00 [0.65, 1.00] | ok |
| P-UDI | 27 | 27/27 = 1.00 [0.88, 1.00] | ok |
| R-NAMEPLACE | 28 | 28/28 = 1.00 [0.88, 1.00] | ok |
| R-RX | 34 | 34/34 = 1.00 [0.90, 1.00] | ok |
| R-UDI | 0 | n=0 | ok |
| S-EXP | 41 | 41/41 = 1.00 [0.91, 1.00] | ok |
| S-MFR | 31 | 31/31 = 1.00 [0.89, 1.00] | ok |

Citations whose quote is not a verbatim substring of its chunk: 0

## Citation retrieval by method (rank of the first accepted-section chunk, k = 10)

| rule | accepted section | bm25 | tfidf | dense | hybrid_rrf |
|---|---|---|---|---|---|
| B-EXP | 801.40 | rank 1 | rank 1 | rank 3 | rank 1 |
| B-GS1 | 830.20 | rank 1 | rank 1 | rank 1 | rank 1 |
| B-LOT | 801.40 | rank 1 | rank 1 | rank 3 | rank 1 |
| B-READ | 801.40 | rank 1 | rank 1 | rank 1 | rank 1 |
| D-FMT | 801.18 | rank 1 | rank 1 | rank 1 | rank 1 |
| P-ADDR | 801.1 | rank 1 | rank 1 | rank 1 | rank 1 |
| P-MFR | 801.1 | rank 1 | rank 1 | rank 1 | rank 1 |
| P-UDI | 801.20 | rank 1 | rank 1 | rank 2 | rank 1 |
| R-NAMEPLACE | 801.1 | rank 1 | rank 1 | rank 1 | rank 1 |
| R-RX | 801.109 | rank 1 | rank 1 | rank 1 | rank 1 |
| R-UDI | 801.20 | rank 1 | rank 1 | rank 2 | rank 1 |
| S-EXP | 801.15 | rank 2 | rank 2 | rank 1 | rank 2 |
| S-MFR | 801.15 | rank 2 | rank 2 | rank 1 | rank 2 |
