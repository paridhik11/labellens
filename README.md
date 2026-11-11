# LabelLens

AI-assisted inspection, change assessment and artwork revision for medical device labels, built around information retrieval.

CSD358 Information Retrieval course project. Team: Pari (lead), Parth, Ishanvi.

> LabelLens supports human reviewers. It does not certify compliance or authenticity. Every flag and every generated label is a proposal with evidence attached, and a human approves or rejects it.

## 1. Problem

Reviewing a medical label means checking text, symbols, barcodes and warnings against product specs, regulations and the previous label version. When a product detail changes, someone must also work out which labels need revising, produce the new artwork, and check the printed result. Doing this by hand across documents and systems is slow and easy to get wrong.

## 2. The workflow LabelLens supports

Upload or scan, extract information, retrieve evidence, check the label, assess changes, generate updated artwork, review and approve, download for printing, verify the printed label.

1. **Register product and label template (once).** Product record (specs, market, identifiers, label version) plus the existing artwork turned into an editable template that keeps size, layout, fonts, symbols and field positions.
2. **Upload or scan a label.** PDF, image or camera. OCR, barcode decoding and selected symbol detection, shown beside the original, with confirmation requested for unclear fields.
3. **Inspect automatically.** Compare extraction with the product record and reference artwork. Retrieve requirement passages with classical and hybrid IR. Every finding shows observed value, expected value and supporting evidence.
4. **Assess a change.** Enter a change in plain language or edit a structured field. LabelLens lists linked labels and fields, explains the proposed edits, retrieves evidence and shows a checklist before touching artwork.
5. **Generate the revised label in the same template.** Unaffected content stays. The user sees current vs revised side by side, highlighted changes, a change log and unresolved layout problems. The barcode is kept if its encoded data is unchanged and regenerated only when confirmed encoded values change. Identifiers come from the product record or an authorized user, never invented.
6. **Review, approve, download.** Checks rerun on the generated artwork (field consistency, overflow, clipping, required fields, barcode decode). A reviewer approves or returns it. The approved label is a PDF at the configured physical size, with the editable template and an inspection report.
7. **Verify the physical print.** Photograph the printed label. LabelLens compares it to the approved revision and highlights discrepancies or asks for a clearer scan.
8. **Preserve versions.** Artwork, images, reports, evidence and approvals are stored with history. Earlier versions stay available. A supplementary QR can open the published product page.

**Public mode (extension):** patients and caregivers scan supported medication packaging, confirm the product match and get plain-language summaries and cited chatbot answers. It uses separate medicine data and checks, does not manage approvals, and never claims to authenticate the medicine.

The professional workspace is the main project. See `docs/PRODUCT_SPEC.md`.

## 3. Where IR sits (the core of the project)

| Task | Query | Documents | Why it is real IR |
|---|---|---|---|
| T1 Requirement retrieval | A label field or claim | Regulation passages (21 CFR, later FDA guidance, EU MDR) | Vocabulary mismatch between label wording and legal wording |
| T2 Product matching | Noisy OCR text plus decoded barcode | Product records | Fuzzy entity retrieval under OCR noise |
| T3 Impact retrieval | A changed product field | Label versions and their fields | Ranking affected items |
| T4 Grounded explanation | A flag plus retrieved passages | n/a | Generation limited to retrieved passages, abstains when weak |

Systems compared: TF-IDF, BM25 (own implementation), dense (BAAI/bge-small-en-v1.5 with FAISS), hybrid RRF, plus later query expansion, learning to rank and relevance feedback. Evaluation uses pooled qrels, nDCG@10, Recall@20, MRR and MAP, at chunk and section level, with ablations. See `docs/EVALUATION.md`.

## 4. Architecture

```
Upload -> preprocess (OpenCV) -> OCR + barcode + symbols -> LabelExtraction JSON
   -> T2 product match -> product record
   -> T1 requirement retrieval (hybrid) -> evidence
   -> checker -> flags -> RAG explanation (cited, abstains)
Change request (text or field) -> parse -> T3 impact retrieval -> checklist
   -> template fill (+ conditional barcode) -> draft artwork
   -> self-check (OCR, decode, overflow, fields) -> review -> approve -> PDF at physical size
Printed photo -> perspective correction -> compare with approved revision -> discrepancies
```

## 5. Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Backend | FastAPI |
| Frontend | Next.js, Tailwind (mock JSON first) |
| Lexical IR | Own inverted index, BM25, TF-IDF |
| Dense IR | sentence-transformers, FAISS |
| OCR, vision | PaddleOCR (Tesseract fallback), OpenCV |
| Barcodes | zxing-cpp (decode), treepoem or bwip-js (GS1 generate) |
| Artwork | SVG templates with named slots, cairosvg or reportlab for PDF in mm |
| Storage | SQLite or Postgres, local file storage first, Supabase later if time |
| RAG | Claude API with a strict citation prompt |
| Experiments | pandas, ranx or own metrics |

## 6. Repo layout

```
src/ir/ crawl/ cv/ gen/ rag/ api/ common/
data/raw processed eval synthetic symbols
docs/   product spec, generation, workflow, evaluation, team plan, API contract
ui/     Next.js app and ui/mock JSON
tests/
```

## 7. Quick start (Windows PowerShell)

```powershell
cd labellens
py -3.12 -m venv .venv312
.venv312\Scripts\Activate.ps1
pip install pydantic pytest ruff requests numpy faiss-cpu sentence-transformers
python -m pytest -q -m "not slow"
python -m src.ir.search "unique device identifier on label" --module device
```

Install heavier packages (OCR, YOLO) only when their step starts. Always run Python as `python -m ...` from the repo root.

## 8. Scope

Core: IR evaluation, inspection, change impact, template-based revised artwork with conditional barcode, review and approval, PDF at physical size, print verification, reports, version history.

v1 limits (stated openly in the report): one label template family, template-matching symbol detection for a handful of symbols, common fonts only, a narrow public medicine demo.

Out of scope: certifying compliance or authenticity, advising whether to take a medicine, inventing identifiers, publishing without human approval, confidential real manufacturer artwork.

Real manufacturer labels are proprietary. We use public labels (DailyMed, openFDA, GUDID) and synthetic labels with injected errors.

## 9. Team and plan

Pari owns most of the project (IR, crawling, checker, RAG, API, data model, change impact, report). Parth owns computer vision and the template and print-verification engine. Ishanvi owns a small set of static UI pages. Parth and Ishanvi start on Day 6. See `docs/TEAM_PLAN.md`, `docs/TASKS.md` and `docs/API_CONTRACT.md`.

## 10. Disclaimer

Academic project. Not a medical device. Not for clinical or regulatory decisions.
