# NDC scan: frozen version scored once

Config commit `8c9b5409`, config {'tau': 22.0, 'top': 3}. Protocol: `protocol.md`. OCR seconds were measured with 2 readers running on a CPU shared with another session.

## Gate

| check | result | pass |
|---|---|---|
| 1 wrong products on unused decoys (33 products) | new 0, E replay 0 | True |
| 2 timeouts, unused decoy photos | new 35, E replay 35, E recorded 13 | |
| 2 timeouts, positives | new 36, E replay 50 | False |
| 3 correct on 57 positive photos | new 17, E replay 2 | True |
| **all** | | **False** |

Decoy photos where any product was shown (review lists included): new 6, E replay 5.

## Coverage of each signal

| set | photos | barcode NDC read | barcode in table | printed NDC-shaped | printed in table | either in table | NDC decided |
|---|---|---|---|---|---|---|---|
| positives | 57 | 10 | 10 | 9 | 6 | 15 | 15 |
| unused_decoy | 45 | 10 | 0 | 4 | 0 | 0 | 0 |
| new_set | 54 | 18 | 0 | 3 | 0 | 0 | 0 |
| all_decoys | 99 | 28 | 0 | 7 | 0 | 0 | 0 |
| positives/artwork | 19 | 4 | 4 | 0 | 0 | 4 | 4 |
| positives/moderate | 19 | 4 | 4 | 4 | 3 | 6 | 6 |
| positives/hard | 19 | 2 | 2 | 5 | 3 | 5 | 5 |

## Results by set (Wilson 95%)

| set | method | photos | correct | wrong | review | not identified | timeout | median s | max s |
|---|---|---|---|---|---|---|---|---|---|
| positives | new | 57 | 17/57 (20 to 43%) | 0/57 (0 to 6%) | 4 | 0 | 36 | 59.1 | 157.1 |
| positives | E replay | 57 | 2/57 (1 to 12%) | 0/57 (0 to 6%) | 4 | 1 | 50 | 60.9 | 151.5 |
| unused_decoy | new | 45 | 0/45 (0 to 8%) | 0/45 (0 to 8%) | 6 | 4 | 35 | 55.1 | 77.5 |
| unused_decoy | E replay | 45 | 0/45 (0 to 8%) | 0/45 (0 to 8%) | 5 | 5 | 35 | 54.9 | 77.5 |
| new_set | new | 54 | 0/54 (0 to 7%) | 0/54 (0 to 7%) | 0 | 2 | 52 | 62.9 | 135.4 |
| new_set | E replay | 54 | 0/54 (0 to 7%) | 0/54 (0 to 7%) | 0 | 2 | 52 | 62.6 | 135.4 |

## Positives by condition

| condition | new correct | E replay correct |
|---|---|---|
| artwork | 4/19 (8 to 43%) | 0/19 (0 to 17%) |
| moderate | 7/19 (19 to 59%) | 1/19 (1 to 25%) |
| hard | 6/19 (15 to 54%) | 1/19 (1 to 25%) |

## Per product (categories of artwork, moderate, hard in file order)

| product | role | new | E replay | sources |
|---|---|---|---|---|
| ALBUTEROL SULFATE | positive | timeout, review, review, timeout, correct, review | timeout, review, review, timeout, timeout, review | e_none, e, e, e_none, ndc_printed, e |
| ALLERGY RELIEF (CETIRIZINE HCL) TABLET [PION | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| ALPRAZOLAM TABLET [PD-RX PHARMACEUTICALS, IN | decoy | timeout, timeout, not_identified | timeout, timeout, not_identified | e_none, e_none, none |
| ANASTROZOLE TABLET [CHARTWELL RX, LLC] | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Amitriptyline Hydrochloride | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Amlodipine Besylate | positive | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Aripiprazole | decoy | review, timeout, review | review, timeout, not_identified | e, e_none, text_rank |
| Aspirin | positive | correct, correct, review | timeout, timeout, not_identified | ndc_both, ndc_barcode, text_rank |
| BISOPROLOL FUMARATE AND HYDROCHLOROTHIAZIDE  | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Bupropion Hydrochloride | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| CLONAZEPAM TABLET [PD-RX PHARMACEUTICALS, IN | decoy | timeout, not_identified, timeout | timeout, not_identified, timeout | e_none, none, e_none |
| Carvedilol | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Childrens Ibuprofen | positive | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Clonidine Hydrochloride | decoy | timeout, review, not_identified | timeout, review, not_identified | e_none, e, none |
| DIGOXIN INJECTION [HENRY SCHEIN, INC.] | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Doxycycline Hyclate | positive | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Duloxetine | decoy | not_identified, timeout, review | not_identified, timeout, review | none, e_none, e |
| ELIQUIS | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| FAMOTIDINE | positive | correct, correct, correct | timeout, timeout, timeout | ndc_barcode, ndc_barcode, ndc_barcode |
| FUROSEMIDE | positive | timeout, timeout, correct | timeout, timeout, review | e_none, e_none, ndc_printed |
| Fluoxetine | positive | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Glipizide | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| HALOPERIDOL TABLET [MAJOR PHARMACEUTICALS] | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| HYDROXYZINE HYDROCHLORIDE | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| IRBESARTAN TABLET [BRYANT RANCH PREPACK] | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| LABETALOL HYDROCHLORIDE TABLET [BLUEPOINT LA | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| LETROZOLE (LETROZOLE TABLETS) TABLET, FILM C | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| LITHIUM CARBONATE TABLET, EXTENDED RELEASE [ | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| LORAZEPAM TABLET [REMEDYREPACK INC.] | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| METFORMIN HYDROCHLORIDE | positive | correct, correct, correct | timeout, timeout, timeout | ndc_barcode, ndc_barcode, ndc_barcode |
| METHYLPREDNISOLONE ACETATE INJECTION, SUSPEN | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Mirtazapine | decoy | timeout, timeout, review | timeout, timeout, review | e_none, e_none, e |
| Naproxen | positive | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| PANTOPRAZOLE SODIUM TABLET, DELAYED RELEASE  | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| PREDNISOLONE SODIUM PHOSPHATE SOLUTION [AMER | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Pain Relief Extra Strength | positive | timeout, timeout, correct | timeout, timeout, timeout | e_none, e_none, ndc_printed |
| PredniSONE | positive | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Pregabalin | decoy | timeout, not_identified, timeout | timeout, not_identified, timeout | e_none, none, e_none |
| RAMIPRIL CAPSULE [BRYANT RANCH PREPACK] | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| RISPERIDONE TABLET, FILM COATED [WESTMINSTER | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Rosuvastatin Calcium | positive | timeout, timeout, correct, timeout, correct, timeout | timeout, timeout, timeout, timeout, timeout, timeout | e_none, e_none, ndc_printed, e_none, ndc_printed, e_none |
| Sertraline Hydrochloride | positive | timeout, correct, correct, timeout, timeout, timeout | timeout, correct, correct, timeout, timeout, timeout | e_none, e, e, e_none, e_none, e_none |
| TAMOXIFEN CITRATE TABLET [MYLAN PHARMACEUTIC | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Tadalafil | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Topiramate | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| Zetia | decoy | not_identified, timeout, review | not_identified, timeout, review | none, e_none, e |
| Zolpidem Tartrate | decoy | timeout, timeout, timeout | timeout, timeout, timeout | e_none, e_none, e_none |
| valsartan and hydrochlorothiazide | positive | correct, correct, timeout, timeout, timeout, timeout | timeout, timeout, timeout, timeout, timeout, timeout | ndc_barcode, ndc_barcode, e_none, e_none, e_none, e_none |
