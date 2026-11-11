# Product spec

LabelLens is one website with a professional workspace (main project) and a public mode (extension). They share infrastructure, but not datasets, rules or evaluation.

## Professional workflow

Upload or scan, extract, retrieve evidence, check, assess changes, generate updated artwork, review and approve, download for printing, verify the printed label.

### 1. Register product and label template (one time per product)
- Product record: specifications, intended market, identifiers (UDI-DI and others), current label version.
- Upload existing artwork (PDF or image). The user marks each field, symbol and barcode region. The system stores a template spec (see `docs/GENERATION.md`): label size in mm, background artwork, and named slots with position, font, size, alignment and the product field each slot shows.
- Later revisions reuse the template.

### 2. Upload or scan a label
Upload PDF or image, or use the camera. Show extracted text, decoded barcodes and detected symbols beside the original. Ask for confirmation when a field is unclear.

### 3. Automatic inspection
Compare extraction with the product record and reference artwork. Retrieve requirement passages (hybrid IR). Each finding shows observed value, expected value and evidence, with severity and confidence. Weak evidence becomes "needs human review", not a guess.

### 4. Assess a change
Plain-language change ("new manufacturer address is ...") or a structured field edit. A parser proposes a structured change that the user confirms. The system lists affected labels and fields, explains the edits, retrieves evidence, and shows a checklist before any artwork is modified.

### 5. Generate revised label (same template)
Fill the template with updated values. Unaffected content is preserved. Show current vs revised side by side, highlighted text, symbol and barcode changes, a change log, and unresolved fields or layout problems. Barcode rule: keep it if encoded data is unchanged, regenerate only when confirmed encoded values change. Identifiers come from the record or an authorized user.

### 6. Review, approve, download
Rerun checks on the generated artwork: field consistency, text overflow, clipping, required fields present, barcode decodes. A reviewer approves or returns for correction. Approved output: PDF at the configured physical size, the editable template, and an inspection report.

### 7. Verify the physical print
Photograph the printed label. Correct perspective, read text and barcode, compare with the approved revision, highlight discrepancies or request a clearer scan.

### 8. Versions and published information
Artwork, images, reports, evidence and approval history are stored. Earlier versions remain accessible. A supplementary QR opens the published product page for the right version.

## Public mode
Scan supported medication packaging, confirm the product match (picker if several), see "read from your photo" next to "from the reference label", plain-language summary, warnings and storage, and a chatbot that answers only from the matched label with source links and refuses unsupported or medical-advice questions. Banner: "Authenticity not verified. Based on a reference label match." Uses separate medicine data (DailyMed, openFDA drug labels and 21 CFR 201, 208, 211) and its own evaluation.

## Screens (mockup: `docs/mockup/website_concept.png`)
1. Scan and Understand (public)
2. Product information (public result)
3. Professional: Products, Inspect, Evidence, Changes, History
4. Template setup (draw and name slots)
5. Change Impact with side-by-side revised label and timeline Draft, Checked, Reviewed, Published
6. Print verification

## Technology to experience map

| Technology | Where the user sees it |
|---|---|
| CV, OCR, barcode decoding | Camera capture, field extraction, print verification, artwork comparison |
| Trained or template-based symbol detection | Selected symbol checks |
| Classical and hybrid IR | Finding the product and the relevant requirements, finding affected labels |
| RAG | Cited explanations, change explanations, public chatbot |
| Crawling and APIs | Background collection and refresh of reference sources |
| Storage and database | Saved artwork, versions, evidence, approvals, reports |

## Core tables
products, product_versions, label_templates, label_versions (artwork file, extraction JSON), reference_docs, chunks, flags, change_requests, impact_items, reviews (decision, reviewer, timestamp), print_verifications, reports, published_pages.
Rule: nothing is overwritten. Every edit creates a new version row.

## Frontend
Next.js and Tailwind, built against mock JSON in `ui/mock/` first. Streamlit only for internal experiment dashboards.
