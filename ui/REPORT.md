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

## 2026-11-17: Professional Workspace Round B (Evidence D5, Changes D6, History D9)

### 1. What is done
- **Screen D5 Evidence**:
  - Success state (`evidence/success.json`): Full BM25 regulatory retrieval view showing search query input, method badge, ranked hits with BM25 scores and document IDs, and official 21 CFR citations with verbatim quotes and eCFR external links.
  - Empty state (`evidence/empty.json`): Clean message when zero regulatory sections match the query.
- **Screen D6 Changes ("Change Impact", Mockup Panel 4)**:
  - Structured change form: Primary entry method with field selector, current/old value, and proposed new value inputs. Free-text description field marked as optional convenience only.
  - Side-by-side revision preview: Compares current version (L2) with draft revision (L3) showing draft purple dashed border, purple background, prominent DRAFT watermark badge, and mandatory review disclaimer: "Draft generated for review. Not a compliance determination."
  - Change lifecycle timeline: 4-step stepper displaying Draft, Checked, Reviewed, Published stages.
  - Barcode decisions: Prominently renders barcode decision status:
    - KEEP (`assess_success.json`, `generated_success.json`): Explains that encoded data does not change so the barcode is kept.
    - NEEDS_INPUT (`generate_needs_input.json`): 422 Job with barcode decision card, reason for new UDI-DI ("Model change ED-100 to ED-200 needs a new device identifier"), previous payload with `[TEST]` badge, and allocated identifier input form with policy notice: "LabelLens never creates or guesses GTIN or UDI-DI values."
  - Needs human review state (`assess_needs_review.json`): Highlights review banner with exact mock message: "NEEDS_HUMAN_REVIEW: no retrieved passage names the symbol for gamma irradiation. The corpus has no symbol standard, so a reviewer must choose the symbol."
  - Confirmed checklist state (`confirm_success.json`): Shows checklist complete banner when all 4 affected items are confirmed or dismissed, enabling the "Generate Draft Artwork" action.
  - Affected packaging hierarchy (`affected_success.json`): Renders impacted packaging components across carton and IFU labels with suggestion badges.
  - Loading generate state (`generate_loading.json`): 202 Job envelope with progress bar (60%) and job status message.
  - Generated draft artwork (`generated_success.json`): Displays generated artwork with DRAFT watermark, `[TEST]` badge for 00000000000000 placeholder, deterministic change log, self-check result (0 findings, passed, SHA-256 hash), SVG/PDF downloads, and link to Review & Approval.
  - Returned and rejected states (`change_returned.json`, `change_rejected.json`): Clear status notices for reviewer return and terminal rejection.
- **Screen D9 History**:
  - Audit trail view (`history/success.json`): Immutable chronological event log (21 CFR 11 and 21 CFR 820.181 DMR) listing 6 regulatory lifecycle events with action badges, actor IDs, timestamps, entity IDs, and version transitions.
  - Label versions lineage view (`history/label_versions.json`): Ordered revisions list (l1, l2, l3) showing artwork and product versions, template ID/version, kind (uploaded/generated), status, parent version links, and SVG/PDF package downloads.
  - Empty audit state (`history/empty.json`): Clean empty message for products with no recorded lifecycle events.

### 2. What is broken
- None. All 36 states across all implemented public and professional screens render cleanly and match the contract definitions in `docs/contracts/openapi.yaml` and `docs/contracts/SCREENS.md`.

### 3. What we need
- None for Round B. Everything required is present in the mock contracts.

## 2026-11-20: Finish (branch ui-finish)

### Report (under 250 words)
- **Round C.** D7 shows blocked reasons from the mock state (failed re-check, self approval 403), the rule coverage table and needs_human items, and a decision panel whose Approve button is disabled when blocked. D8 shows the DRAFT banner on every export, including approved, plus the `draft_watermark` flag; QR only when published. D10 uses the API words `match`, `mismatch`, `rescan_needed` and never "verified"; a rescan shows "No result", never a pass.
- **Check pass.** Headless Chromium (Playwright), `ui/tools/check_screens.cjs`: all 61 mock states and 7 click-throughs pass with 0 console or page errors, in mock mode and in api mode. Per-state tables: `ui/check_results.md`, `ui/check_results_api.md`. The first pass was too weak: it missed D5 not rendering the ask mocks, P3 ignoring AI states and several buttons that rendered an empty payload (D6, D9). All fixed, and the check now asserts what each state must show.
- **Serve.** `scripts/run_demo.py` serves `ui/` at `/ui/` and the mock JSON at `/src/api/mock`. Default `CONFIG.mode` is mock; `?mode=api` switches. A corner badge shows MOCK MODE, LIVE API or X-Mock (fallback).
- **API mode** (done, verified with `ui/tools/live_flows.cjs` on a running demo): job polling, upload with `product_id`, `retake_photo` reasons, extractive answer plus Ask AI, generate, real PDF download with the DRAFT mark.
- **Screenshots:** `ui/screenshots/` (13, demo order).

### Choices and limits
- Only reads with a matching mock state go live; action and error samples stay mock. Point screens at a live package with `?product=&label=&version=&change=`.
- `ask-panel.js` is shared by P3 and D5 for drawing only; no data is shared.
- Not wired: P1 camera scan, D2 template register, D4 inspect and confirm, D7 recheck, D10 upload (mock fallback, badge says so).
- Seeded demo change `chg_0002` cannot generate (template background, D-5); the golden package can.
