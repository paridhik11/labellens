# Checker evaluation: checker_dev

Commit 98ec8e2 (src/checker has uncommitted changes). Seeds [200, 201], 34 base labels, 510 images (5 image variants x 3 conditions per base; the udi_mismatch and rx_missing kinds reuse the clean image with a changed record). Retrieval: {'method': 'hybrid_rrf', 'module': 'device', 'k': 10, 'rrf_k': 60, 'stem': False, 'prefix': False}. Symbol detector trusted: False. Wilson 95% intervals, n in every cell, conditions never blended.

## Layer: oracle extraction (perfect CV, so the photo condition does not apply; shown once)

### Recall on injected errors

| kind | condition | n | flagged (any flag of the expected rule) | confident (needs_human false) | extraction raised |
|---|---|---|---|---|---|
| expiry_format | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| barcode_mismatch | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| missing_symbol | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| wrong_name | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| udi_mismatch | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| rx_missing | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |

### Precision

| kind | condition | TP | FP (group flags on labels not expecting that rule) | precision |
|---|---|---|---|---|
| expiry_format | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| barcode_mismatch | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| missing_symbol | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| wrong_name | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| udi_mismatch | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| rx_missing | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |

### False alarms on clean labels

Share of clean labels (no injected error, true record) with at least one finding, per condition.

| condition | n clean | any finding | any confident finding (needs_human false) | extraction raised |
|---|---|---|---|---|
| clean | 34 | 0/34 = 0.00 [0.00, 0.10] | 0/34 = 0.00 [0.00, 0.10] | 0 |

Per rule (share of clean labels where that rule raised a finding):

| rule | clean |
|---|---|
| (no rule raised a finding on any clean label) | 0/34 = 0.00 [0.00, 0.10] |

### Citations

| rule | n findings | finding has a citation (hit@10 for the accepted section) | quote verbatim |
|---|---|---|---|
| B-EXP | 54 | 54/54 = 1.00 [0.93, 1.00] | ok |
| B-GS1 | 0 | n=0 | ok |
| B-LOT | 48 | 48/48 = 1.00 [0.93, 1.00] | ok |
| B-READ | 0 | n=0 | ok |
| D-FMT | 102 | 102/102 = 1.00 [0.96, 1.00] | ok |
| P-ADDR | 0 | n=0 | ok |
| P-MFR | 0 | n=0 | ok |
| P-UDI | 102 | 102/102 = 1.00 [0.96, 1.00] | ok |
| R-NAMEPLACE | 0 | n=0 | ok |
| R-RX | 102 | 102/102 = 1.00 [0.96, 1.00] | ok |
| R-UDI | 0 | n=0 | ok |
| S-EXP | 48 | 48/48 = 1.00 [0.93, 1.00] | ok |
| S-MFR | 54 | 54/54 = 1.00 [0.93, 1.00] | ok |

Citations whose quote is not a verbatim substring of its chunk: 0

## Layer: real extraction, template mode

### Recall on injected errors

| kind | condition | n | flagged (any flag of the expected rule) | confident (needs_human false) | extraction raised |
|---|---|---|---|---|---|
| expiry_format | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| expiry_format | moderate | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| expiry_format | hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| barcode_mismatch | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| barcode_mismatch | moderate | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| barcode_mismatch | hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| missing_symbol | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| missing_symbol | moderate | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| missing_symbol | hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| wrong_name | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| wrong_name | moderate | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| wrong_name | hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| udi_mismatch | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| udi_mismatch | moderate | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| udi_mismatch | hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| rx_missing | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| rx_missing | moderate | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| rx_missing | hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |

### Precision

| kind | condition | TP | FP (group flags on labels not expecting that rule) | precision |
|---|---|---|---|---|
| expiry_format | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| expiry_format | moderate | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| expiry_format | hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| barcode_mismatch | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| barcode_mismatch | moderate | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| barcode_mismatch | hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| missing_symbol | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| missing_symbol | moderate | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| missing_symbol | hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| wrong_name | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| wrong_name | moderate | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| wrong_name | hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| udi_mismatch | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| udi_mismatch | moderate | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| udi_mismatch | hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| rx_missing | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| rx_missing | moderate | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| rx_missing | hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |

### False alarms on clean labels

Share of clean labels (no injected error, true record) with at least one finding, per condition.

| condition | n clean | any finding | any confident finding (needs_human false) | extraction raised |
|---|---|---|---|---|
| clean | 34 | 0/34 = 0.00 [0.00, 0.10] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| moderate | 34 | 0/34 = 0.00 [0.00, 0.10] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| hard | 34 | 0/34 = 0.00 [0.00, 0.10] | 0/34 = 0.00 [0.00, 0.10] | 0 |

Per rule (share of clean labels where that rule raised a finding):

| rule | clean | moderate | hard |
|---|---|---|---|
| (no rule raised a finding on any clean label) | 0/34 = 0.00 [0.00, 0.10] | 0/34 = 0.00 [0.00, 0.10] | 0/34 = 0.00 [0.00, 0.10] |

### Citations

| rule | n findings | finding has a citation (hit@10 for the accepted section) | quote verbatim |
|---|---|---|---|
| B-EXP | 54 | 54/54 = 1.00 [0.93, 1.00] | ok |
| B-GS1 | 0 | n=0 | ok |
| B-LOT | 48 | 48/48 = 1.00 [0.93, 1.00] | ok |
| B-READ | 0 | n=0 | ok |
| D-FMT | 102 | 102/102 = 1.00 [0.96, 1.00] | ok |
| P-ADDR | 0 | n=0 | ok |
| P-MFR | 0 | n=0 | ok |
| P-UDI | 102 | 102/102 = 1.00 [0.96, 1.00] | ok |
| R-NAMEPLACE | 0 | n=0 | ok |
| R-RX | 102 | 102/102 = 1.00 [0.96, 1.00] | ok |
| R-UDI | 0 | n=0 | ok |
| S-EXP | 48 | 48/48 = 1.00 [0.93, 1.00] | ok |
| S-MFR | 54 | 54/54 = 1.00 [0.93, 1.00] | ok |

Citations whose quote is not a verbatim substring of its chunk: 0

## Layer: real extraction, blind mode

### Recall on injected errors

| kind | condition | n | flagged (any flag of the expected rule) | confident (needs_human false) | extraction raised |
|---|---|---|---|---|---|
| expiry_format | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| expiry_format | moderate | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| expiry_format | hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| barcode_mismatch | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| barcode_mismatch | moderate | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| barcode_mismatch | hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| missing_symbol | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| missing_symbol | moderate | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| missing_symbol | hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| wrong_name | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| wrong_name | moderate | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| wrong_name | hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| udi_mismatch | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| udi_mismatch | moderate | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| udi_mismatch | hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 34/34 = 1.00 [0.90, 1.00] | 0 |
| rx_missing | clean | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| rx_missing | moderate | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| rx_missing | hard | 34 | 34/34 = 1.00 [0.90, 1.00] | 0/34 = 0.00 [0.00, 0.10] | 0 |

### Precision

| kind | condition | TP | FP (group flags on labels not expecting that rule) | precision |
|---|---|---|---|---|
| expiry_format | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| expiry_format | moderate | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| expiry_format | hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| barcode_mismatch | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| barcode_mismatch | moderate | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| barcode_mismatch | hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| missing_symbol | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| missing_symbol | moderate | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| missing_symbol | hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| wrong_name | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| wrong_name | moderate | 34 | 1 | 34/35 = 0.97 [0.85, 0.99] |
| wrong_name | hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| udi_mismatch | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| udi_mismatch | moderate | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| udi_mismatch | hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| rx_missing | clean | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| rx_missing | moderate | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |
| rx_missing | hard | 34 | 0 | 34/34 = 1.00 [0.90, 1.00] |

### False alarms on clean labels

Share of clean labels (no injected error, true record) with at least one finding, per condition.

| condition | n clean | any finding | any confident finding (needs_human false) | extraction raised |
|---|---|---|---|---|
| clean | 34 | 0/34 = 0.00 [0.00, 0.10] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| moderate | 34 | 0/34 = 0.00 [0.00, 0.10] | 0/34 = 0.00 [0.00, 0.10] | 0 |
| hard | 34 | 0/34 = 0.00 [0.00, 0.10] | 0/34 = 0.00 [0.00, 0.10] | 0 |

Per rule (share of clean labels where that rule raised a finding):

| rule | clean | moderate | hard |
|---|---|---|---|
| (no rule raised a finding on any clean label) | 0/34 = 0.00 [0.00, 0.10] | 0/34 = 0.00 [0.00, 0.10] | 0/34 = 0.00 [0.00, 0.10] |

### Citations

| rule | n findings | finding has a citation (hit@10 for the accepted section) | quote verbatim |
|---|---|---|---|
| B-EXP | 54 | 54/54 = 1.00 [0.93, 1.00] | ok |
| B-GS1 | 0 | n=0 | ok |
| B-LOT | 48 | 48/48 = 1.00 [0.93, 1.00] | ok |
| B-READ | 0 | n=0 | ok |
| D-FMT | 102 | 102/102 = 1.00 [0.96, 1.00] | ok |
| P-ADDR | 0 | n=0 | ok |
| P-MFR | 0 | n=0 | ok |
| P-UDI | 102 | 102/102 = 1.00 [0.96, 1.00] | ok |
| R-NAMEPLACE | 0 | n=0 | ok |
| R-RX | 102 | 102/102 = 1.00 [0.96, 1.00] | ok |
| R-UDI | 0 | n=0 | ok |
| S-EXP | 48 | 48/48 = 1.00 [0.93, 1.00] | ok |
| S-MFR | 54 | 54/54 = 1.00 [0.93, 1.00] | ok |

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
