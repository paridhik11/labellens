# NDC scan: frozen version scored once

Config commit `8c9b5409`, config {'tau': 22.0, 'top': 3}. Protocol: `protocol.md`. Gate run 2 (protocol_amendment.md): one reader at a time on an idle machine. Two photos (1595 s, 1472 s) were stalled by machine idle sleep between agent turns and read 0 lines (timeouts). Run 1 is invalid (run1_invalid/).

## Gate

| check | result | pass |
|---|---|---|
| 1 wrong products on unused decoys (33 products) | new 0, E replay 0 | True |
| 2 timeouts, unused decoy photos | new 6, E replay 6, E recorded 13 | |
| 2 timeouts, positives | new 0, E replay 0 | True |
| 3 correct on 57 positive photos | new 46, E replay 34 | True |
| **all** | | **True** |

Decoy photos where any product was shown (review lists included): new 42, E replay 32.

## Coverage of each signal

| set | photos | barcode NDC read | barcode in table | printed NDC-shaped | printed in table | either in table | NDC decided |
|---|---|---|---|---|---|---|---|
| positives | 57 | 10 | 10 | 35 | 32 | 33 | 33 |
| unused_decoy | 45 | 10 | 0 | 14 | 0 | 0 | 0 |
| new_set | 54 | 18 | 0 | 33 | 0 | 0 | 0 |
| all_decoys | 99 | 28 | 0 | 47 | 0 | 0 | 0 |
| positives/artwork | 19 | 4 | 4 | 10 | 10 | 11 | 11 |
| positives/moderate | 19 | 4 | 4 | 12 | 11 | 11 | 11 |
| positives/hard | 19 | 2 | 2 | 13 | 11 | 11 | 11 |

## Results by set (Wilson 95%)

| set | method | photos | correct | wrong | review | not identified | timeout | median s | max s |
|---|---|---|---|---|---|---|---|---|---|
| positives | new | 57 | 46/57 (69 to 89%) | 0/57 (0 to 6%) | 8 | 3 | 0 | 16.9 | 48.3 |
| positives | E replay | 57 | 34/57 (47 to 71%) | 0/57 (0 to 6%) | 17 | 6 | 0 | 19.9 | 48.9 |
| unused_decoy | new | 45 | 0/45 (0 to 8%) | 0/45 (0 to 8%) | 20 | 19 | 6 | 37.0 | 1595.2 |
| unused_decoy | E replay | 45 | 0/45 (0 to 8%) | 0/45 (0 to 8%) | 15 | 24 | 6 | 36.9 | 1595.1 |
| new_set | new | 54 | 0/54 (0 to 7%) | 0/54 (0 to 7%) | 22 | 10 | 22 | 46.5 | 1472.2 |
| new_set | E replay | 54 | 0/54 (0 to 7%) | 0/54 (0 to 7%) | 17 | 15 | 22 | 46.5 | 1471.5 |

## Positives by condition

| condition | new correct | E replay correct |
|---|---|---|
| artwork | 16/19 (62 to 94%) | 13/19 (46 to 85%) |
| moderate | 16/19 (62 to 94%) | 11/19 (36 to 77%) |
| hard | 14/19 (51 to 88%) | 10/19 (32 to 73%) |

## Per product (categories of artwork, moderate, hard in file order)

| product | role | new | E replay | sources |
|---|---|---|---|---|
| ALBUTEROL SULFATE | positive | review, review, review, correct, correct, review | review, review, review, correct, review, review | e, e, e, ndc_printed, ndc_printed, e |
| ALLERGY RELIEF (CETIRIZINE HCL) TABLET [PION | decoy | timeout, review, review | timeout, review, not_identified | e_none, e, text_rank |
| ALPRAZOLAM TABLET [PD-RX PHARMACEUTICALS, IN | decoy | timeout, not_identified, not_identified | timeout, not_identified, not_identified | e_none, none, none |
| ANASTROZOLE TABLET [CHARTWELL RX, LLC] | decoy | timeout, review, not_identified | timeout, not_identified, not_identified | e_none, text_rank, none |
| Amitriptyline Hydrochloride | decoy | timeout, review, not_identified | timeout, review, not_identified | e_none, e, none |
| Amlodipine Besylate | positive | not_identified, not_identified, not_identified | not_identified, not_identified, not_identified | none, none, none |
| Aripiprazole | decoy | review, review, review | review, review, not_identified | e, e, text_rank |
| Aspirin | positive | correct, correct, review | review, not_identified, not_identified | ndc_barcode, ndc_both, text_rank |
| BISOPROLOL FUMARATE AND HYDROCHLOROTHIAZIDE  | decoy | review, review, review | review, review, review | e, e, e |
| Bupropion Hydrochloride | decoy | timeout, not_identified, not_identified | timeout, not_identified, not_identified | e_none, none, none |
| CLONAZEPAM TABLET [PD-RX PHARMACEUTICALS, IN | decoy | timeout, not_identified, not_identified | timeout, not_identified, not_identified | e_none, none, none |
| Carvedilol | decoy | timeout, not_identified, not_identified | timeout, not_identified, not_identified | e_none, none, none |
| Childrens Ibuprofen | positive | review, review, review | review, review, review | e, e, e |
| Clonidine Hydrochloride | decoy | review, review, not_identified | review, review, not_identified | e, e, none |
| DIGOXIN INJECTION [HENRY SCHEIN, INC.] | decoy | timeout, review, not_identified | timeout, review, not_identified | e_none, e, none |
| Doxycycline Hyclate | positive | correct, correct, correct | review, review, review | ndc_printed, ndc_printed, ndc_printed |
| Duloxetine | decoy | review, not_identified, review | review, not_identified, review | e, none, e |
| ELIQUIS | decoy | not_identified, not_identified, not_identified | not_identified, not_identified, not_identified | none, none, none |
| FAMOTIDINE | positive | correct, correct, correct | correct, correct, correct | ndc_both, ndc_both, ndc_both |
| FUROSEMIDE | positive | correct, correct, correct | correct, review, review | ndc_printed, ndc_printed, ndc_printed |
| Fluoxetine | positive | correct, correct, correct | correct, correct, correct | e, e, ndc_printed |
| Glipizide | decoy | timeout, not_identified, not_identified | timeout, not_identified, not_identified | e_none, none, none |
| HALOPERIDOL TABLET [MAJOR PHARMACEUTICALS] | decoy | timeout, review, not_identified | timeout, review, not_identified | e_none, e, none |
| HYDROXYZINE HYDROCHLORIDE | decoy | review, review, review | review, not_identified, review | e, text_rank, e |
| IRBESARTAN TABLET [BRYANT RANCH PREPACK] | decoy | timeout, review, review | timeout, review, review | e_none, e, e |
| LABETALOL HYDROCHLORIDE TABLET [BLUEPOINT LA | decoy | timeout, review, review | timeout, not_identified, not_identified | e_none, text_rank, text_rank |
| LETROZOLE (LETROZOLE TABLETS) TABLET, FILM C | decoy | timeout, review, review | timeout, review, review | e_none, e, e |
| LITHIUM CARBONATE TABLET, EXTENDED RELEASE [ | decoy | timeout, review, review | timeout, review, review | e_none, e, e |
| LORAZEPAM TABLET [REMEDYREPACK INC.] | decoy | timeout, review, not_identified | timeout, review, not_identified | e_none, e, none |
| METFORMIN HYDROCHLORIDE | positive | correct, correct, correct | correct, correct, correct | ndc_both, ndc_both, ndc_both |
| METHYLPREDNISOLONE ACETATE INJECTION, SUSPEN | decoy | timeout, review, review | timeout, review, review | e_none, e, e |
| Mirtazapine | decoy | review, review, review | not_identified, not_identified, review | text_rank, text_rank, e |
| Naproxen | positive | correct, correct, correct | correct, correct, correct | e, e, ndc_printed |
| PANTOPRAZOLE SODIUM TABLET, DELAYED RELEASE  | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| PREDNISOLONE SODIUM PHOSPHATE SOLUTION [AMER | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Pain Relief Extra Strength | positive | correct, correct, correct | correct, correct, correct | ndc_printed, ndc_printed, ndc_printed |
| PredniSONE | positive | correct, correct, correct | correct, correct, correct | e, e, ndc_printed |
| Pregabalin | decoy | not_identified, not_identified, not_identified | not_identified, not_identified, not_identified | none, none, none |
| RAMIPRIL CAPSULE [BRYANT RANCH PREPACK] | decoy | timeout, review, review | timeout, review, review | e_none, e, e |
| RISPERIDONE TABLET, FILM COATED [WESTMINSTER | decoy | timeout, timeout, review | timeout, timeout, not_identified | e_none, e_none, text_rank |
| Rosuvastatin Calcium | positive | correct, correct, correct, correct, correct, correct | review, correct, not_identified, correct, review, review | ndc_printed, ndc_printed, ndc_printed, ndc_printed, ndc_printed, ndc_printed |
| Sertraline Hydrochloride | positive | correct, correct, correct, correct, correct, correct | correct, correct, correct, correct, correct, correct | e, e, e, e, e, e |
| TAMOXIFEN CITRATE TABLET [MYLAN PHARMACEUTIC | decoy | timeout, not_identified, not_identified | timeout, not_identified, not_identified | e_none, none, none |
| Tadalafil | decoy | timeout, review, review | timeout, review, review | e_none, e, e |
| Topiramate | decoy | review, review, not_identified | review, review, not_identified | e, e, none |
| Zetia | decoy | not_identified, review, review | not_identified, not_identified, review | none, text_rank, e |
| Zolpidem Tartrate | decoy | timeout, not_identified, not_identified | timeout, not_identified, not_identified | e_none, none, none |
| valsartan and hydrochlorothiazide | positive | correct, correct, correct, correct, correct, correct | correct, correct, correct, correct, correct, correct | ndc_both, ndc_both, ndc_printed, ndc_printed, ndc_printed, e |

## Product level (Wilson 95%)

| measure | new | E replay |
|---|---|---|
| positive products with at least one correct photo | 13/15 (62 to 96%) | 11/15 (48 to 89%) |
| positive products with any wrong photo | 0/15 | 0/15 |
| unused decoy products wrong (gate E decoys) | 0/15 (0 to 20%) | 0/15 (0 to 20%) |
| new-set decoy products wrong | 0/18 (0 to 18%) | 0/18 (0 to 18%) |
| decoy products with any product shown (review lists) | 22/33 | 19/33 |

Supplementary (not a gate run, positives only, single reader with the other session busy, scored before the amendment):
correct 42/57 (61 to 83%) new vs 27/57 (35 to 60%) E replay, 0 wrong.

Pre-merge suite not run: the gate run finished at 17:22 IST, after which the suite could not finish by the 17:30 hard stop.
Not merged.
