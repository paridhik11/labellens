# UI Report and Issue Log

All UI notes, gaps, schema clarifications, and step reports are maintained in this file with one dated entry per step.

## 2026-11-17: Public Medicine Mode Review and Hardening

### 1. Screen P2 (Product information)
- **Ingredients and Warnings Tabs**: `docs/contracts/SCREENS.md` (mockup panel 2) specifies tabs for "Summary, Ingredients, Warnings, Sources". Currently `src/api/mock/public/product/success.json` and `docs/contracts/openapi.yaml` define `summary` (string), `candidates` (with `read_from_photo` and `from_reference_label`), and `sources` (list of citations). The Ingredients and Warnings tabs stay hidden for now; the backend will add those fields later.
- **Side-by-side Columns**: The two comparison views ("Read from your photo" and "From the reference label") are rendered as prominent side-by-side columns from the mock.
- **Authenticity Banner**: The static banner "Authenticity not verified. Based on a reference label match. This information does not confirm that your product is genuine." is displayed directly on Screen 2.
- **Scan Another Side Action**: The "Scan another side" button is hidden because the API and mock contract do not supply a field for multi-side scanning (`can_scan_another` or `another_side`).

### 2. Screen P3 (Ask about this label)
- **User Question Text**: Maintained directly in UI client state. Whatever question the user types is preserved across renders and queries without waiting for an API response field.
- **Abstention Responses**: All four abstained states (`out_of_scope`, `low_confidence`, `no_evidence`, `needs_human_check`) display the exact reason name, explanatory message, and only display score/threshold when non-null (never rendering "null" or "NaN").
- **Regulatory Citations**: Citations display the source type badge (`cfr`), regulation section, title, and verbatim quoted text.

## 2026-11-17: Professional Workspace Round A (Products D1, Template setup D2, Inspect D4)

### 1. What is done
- **Screen D1 Products**:
  - Empty state (`empty.json`): Clean empty message when no products are registered yet.
  - List state (`products/success.json`): Product cards listing product name, model number, manufacturer, UDI-DI with prominent `[TEST]` badge for placeholder `00000000000000`, open findings count pill, and navigation buttons ("View Details", "Inspect Labels", "Create Change").
  - Detail state (`product_detail/success.json`): Full product record with specifications grid (material, sterile status, shelf life, storage instructions), registered templates list, and associated labels list.
- **Screen D2 Template setup**:
  - Success state (`template_setup/success.json`): Interactive 100x60mm template canvas with scaled mm grid. Shows reserved top 9mm DRAFT watermark band with red diagonal hatch lines and label "RESERVED DRAFT WATERMARK BAND (TOP 9mm)". Renders all defined slots (title, udi_barcode, storage, sterile_symbol, symbol_grid, caution) with dimension labels and coordinates. Shows slot table and validation status.
  - Failed check state (`template_setup/failed_check.json`): Highlights layout collisions in red with finding cards for watermark overlap (slot `name` at y=2mm) and slot collision (slot `name` overlapping `udi_barcode`).
  - Mandatory disclaimer: Prominently renders "Draft generated for review. Not a compliance determination." on every template view.
- **Screen D4 Inspect**:
  - OCR / Barcode extraction states:
    - `extraction_success.json`: Extracted fields grid with field key, value, bounding box, confidence score, and raw text preview.
    - `extraction_needs_review.json`: Highlights low-confidence extraction fields (e.g. lot_number) with review warnings and an interactive confirmation button.
    - `extraction_confirmed.json`: Displays confirmed status with confirmed extraction values.
  - Inspection compliance check states:
    - `loading.json`: Progress bar and status indicator for queued inspection job.
    - `success.json`: Passed checks list with 21 CFR 801 regulatory citations.
    - `failed_check.json`: Displays critical finding for expiry date mismatch between OCR human-readable text ("EXP 2026-05-31") and 2D barcode payload ("(17)260430" / 2026-04-30), citing 21 CFR 801.40. Draws visual bounding box overlay on the label preview canvas highlighting the mismatched barcode region.
- **Session and Header**:
  - Top navigation bar loads `/src/api/mock/professional/session/me.json` via `professional-app.js`, populating the user badge with initials ("JD"), full name ("Jane Doe"), and role ("Editor").
  - Brand logo and "Portal Home" links in header link directly back to `/ui/index.html`.

### 2. What is broken
- None. All mock states render cleanly and match the contract definitions in `docs/contracts/openapi.yaml` and `docs/contracts/SCREENS.md`.

### 3. What we need
- None for Round A. Everything required is present in the mock contracts.
