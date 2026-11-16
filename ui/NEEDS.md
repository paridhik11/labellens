# UI Needs and Missing Mock Fields

This file logs missing mock fields, pending UI assets, API integrations, and schema clarification requests per the project guidelines.

## 1. Screen P2 (Product information)
- **Requested Fields**: Structured `ingredients` and `warnings` data in `PublicMatchResult` or `MedicineMatch`.
- **Reference**: `docs/contracts/SCREENS.md` (panel 2) specifies tabs for "Summary, Ingredients, Warnings, Sources".
- **Current Mock State**: `src/api/mock/public/product/success.json` and `docs/contracts/openapi.yaml` define `summary` (string), `candidates` (list with `read_from_photo` and `from_reference_label`), and `sources` (list of citations). Neither `ingredients` nor `warnings` exist in the mock contract.
- **UI Treatment**: Following the strict ground rule ("If a screen needs a field the mock lacks, add it to ui/NEEDS.md and leave it out"), separate Ingredients and Warnings tab contents are left out of Screen P2.

## 2. Screen P3 (Ask about this label)
- **Requested Field**: `question` string in `AnswerResponse` / `src/api/mock/public/ask/*.json`.
- **Reference**: User interface displays a question query box above the cited answer or abstention card.
- **Current Mock State**: The mock responses (`success.json` and the four `abstained_*.json` files) define `abstained`, `answer`, `sources`, `based_on`, `banner`, `reason`, `score_name`, `score`, `threshold`, and `message`, but omit the incoming user question text.
- **UI Treatment**: Question input displays a clean placeholder instead of invented mock text.
