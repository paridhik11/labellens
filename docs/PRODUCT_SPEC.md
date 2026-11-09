# Product spec

LabelLens is one website with two experiences that share infrastructure but not data, rules or evaluation.

| | Public module (medicines) | Professional module (medical devices) |
|---|---|---|
| Users | Patients, caregivers, no account | Labeling, regulatory, quality teams, signed in |
| Goal | Understand a medicine pack, source-linked | Inspect labels, assess changes, keep history |
| Reference data | DailyMed / openFDA drug labels | Registered product records, GUDID, regulations, internal artwork |
| Checks | Match pack to reference label, flag discrepancies, ask for clearer image | Field, barcode, symbol, warning and revision checks |
| Evaluation | Product match accuracy, summary faithfulness, citation precision | Error detection P/R/F1, requirement retrieval, symbol mAP, generation self-check |
| Never claims | Authenticity, or whether to take the medicine | Compliance. Human approval always required |

Keep separate folders, datasets, rule sets and result tables for the two modules. Share only: auth, storage, OCR/barcode code, retrieval engine, UI components.

## Screens and flows

### 1. Scan and Understand (public)
Entry: Use camera or Upload image. Capture all sides (front, back, sides) in sequence.

Result screen:
- Product identity, with a picker if several candidates match (T2 ranking shown with confidence).
- "Read from your photo" next to "From the reference label" so the user sees observed vs reference values.
- Plain-language tabs: Summary, Ingredients, Warnings, Storage, Sources.
- Chatbot: answers only from the matched label, each answer carries source links, refuses when not supported.
- Banner: "Authenticity not verified. This is based on a reference label match."
- Discrepancy list, or a request for a clearer image when OCR confidence is low.

Output: source-linked product summary plus supported packaging checks.

### 2. Professional workspace
Flow: pick registered product, upload artwork or scan a printed label, run inspection.

Review screen:
- Label image with highlighted fields and discrepancies (bounding boxes from OCR, barcode, symbols).
- Extracted text, symbols, decoded barcode values.
- Expected values from the selected reference (observed vs reference table).
- Relevant requirements with supporting passages.
- Uncertain fields requiring reviewer confirmation.
- Actions: Confirm extraction, Export report.

Output: inspection report listing what was checked, what differed, what is unknown, and evidence for each finding.

### 3. Change impact
User submits a change (e.g. new manufacturer address, sterilization method EO to gamma).

System:
1. Proposes affected fields and linked labels (T3 impact retrieval plus rule engine).
2. Retrieves evidence passages (T1).
3. Generates the draft revision: updated barcode and updated digital artwork (see GENERATION.md).
4. Shows current vs draft artwork side by side with highlighted differences.
5. Produces an impact checklist and a review task.

Timeline states: Draft, Checked, Reviewed, Published. Approved revisions enter version history, earlier versions stay available. Footer on every draft: "Human approval before publication."

### 4. Products, history, QR
Product records, batches, artwork versions, review decisions, reports. A supplementary QR on the label can open the published information page for the right version. Public users only see published information.

## Technology to experience map

| Technology | Where the user sees it |
|---|---|
| CV, OCR, barcode decoding | Camera capture, field extraction, artwork comparison |
| Trained ML | Selected symbol detection, ranking candidate product matches |
| Classical and hybrid IR | Finding the product and the relevant requirements |
| RAG | Cited summaries, explanations, chatbot answers |
| Crawling and APIs | Background collection and refresh of reference sources |
| Cloud storage and DB | Saved documents, linked records, versions, review history |

## Frontend decision
The mockup needs a real web app (camera capture, side navigation, roles). Use Next.js (React, Tailwind) for the frontend and FastAPI for the backend. Keep Streamlit only for internal experiment dashboards (retrieval results, ablations).

Auth: Supabase Auth with two roles, `professional` and `admin`. Public module needs no login.

## Data model (core tables)
products, product_versions, batches, labels, label_versions (artwork file, extraction JSON), reference_docs, chunks, reviews (decision, reviewer, timestamp), flags, change_requests, impact_items, reports, published_pages.
Rule: nothing is overwritten. Every edit creates a new version row.

## Definition of done for the finished project
1. Working website with both modules.
2. Ingestion and retrieval pipeline with scheduled refresh.
3. Evaluated vision and ML components, per-condition numbers.
4. Downloadable review reports (PDF).
5. Reproducible comparison table showing which technique improves which result.
