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

## 7. Setup and run the demo (Windows PowerShell)

Needs Python 3.12 and about 6 GB of disk (PyTorch and the models). From a fresh clone:

```powershell
git clone https://github.com/paridhik11/labellens.git
cd labellens
py -3.12 -m venv .venv312
.venv312\Scripts\python.exe -m pip install -r requirements-demo.txt
.venv312\Scripts\python.exe scripts\run_demo.py
```

`scripts/run_demo.py` is the one command. It checks the environment, builds or copies the dense indexes, seeds the demo
database, chooses the checker retrieval, starts the API, warms the models and prints the URLs:
the API at `http://127.0.0.1:8000` (docs at `/docs`), the public medicine page at `/public/medicine`, and the static UI (`ui/`, plain HTML and JS, no build) at `/ui/`,
served next to the API with its mock JSON (`CONFIG.mode` in `ui/js/data.js`, default `mock`). Options: `--port`, `--fresh` (new database), `--skip-indexes`, `--no-golden`.

First run on a new machine:
- The embedding model (BAAI/bge-large-en-v1.5, 1.3 GB) downloads from Hugging Face once. After that the app runs offline.
- Index files are keyed by model and corpus hash. If another checkout of this repo on the PC already built them, they are copied
  from `data/cache/indexes` of the main checkout, or from the folder named by the environment variable `LABELLENS_INDEX_DIR` (set it when you cloned the repo again). Otherwise the bge-large build for the regulation corpus
  takes about 40 minutes of CPU, once (`python scripts/build_indexes.py` does only that step).
- The optional AI answer needs Ollama with `qwen2.5:3b-instruct-q4_K_M`. Without it the AI answer falls back to the extractive passages.

Check that everything works, in a second terminal while the demo runs:

```powershell
.venv312\Scripts\python.exe scripts\demo_e2e.py
```

It calls the real running API with the real extractor on a rendered golden package and on one synthetic photo and prints PASS,
PASS (mock), FALLBACK or FAIL per stage. Developer checks: `python -m pytest -q -m "not slow"` and `ruff check src tests`.
Always run Python as `python -m ...` or `python scripts/...` from the repo root.

### Demo script (about 10 minutes)

Users are stubs chosen by the `X-User-Id` header (`usr_demo_editor`, `usr_demo_reviewer`, `usr_demo_admin`), no login.
Everything below is also one `demo_e2e.py` run.

1. **Product and template.** Register a product and its label template (millimetres, named slots). The seed already holds `Golden Pump (demo)`.
2. **Upload and extract.** Upload the golden label PDF (`data/demo/golden_label.pdf`) or a photo. The photo gate may ask for a retake. The extractor reads text, barcode and symbols and lists unclear fields.
3. **Confirm and check.** Confirm or correct the fields, then inspect. Every finding shows observed, expected and a cited requirement passage.
4. **Change.** Enter a change (lot `LOT1` to `LOT2`). The impact list, the barcode decision (a lot is encoded in the barcode, so REGENERATE) and the checklist appear. Confirm it.
5. **Generate and re-check.** Fill the template. The draft carries `DRAFT, not for production` and test data is marked. Re-check reads the rendered PDF back as an image.
6. **Approve and publish.** As the reviewer approve exactly that version (hash and passed check), then publish. The QR on the label opens `/versions/<version_id>`.
7. **Export.** Download the PDF at physical size, the SVG template and the report (hash verified).
8. **Public mode.** Open `/public/medicine`, type `Childrens Ibuprofen`, read the reference fields and sections, ask `what are the warnings`. Try `Zzyzx Gummies` for the no-match case. Try the AI answer (`/public/ask?mode=ai`).

### Known limits

- The CV is tuned on synthetic labels of one template family. Very hard photos can make clean labels fail with confident false alarms; photos that are too blurry are rejected with a retake request.
- The symbol detector is not trusted: symbol checks always ask a human. Real carton photos were not read.
- Generated labels always carry the DRAFT mark, even after approval (no approved variant is rendered), identifiers are the GS1 test placeholder, and a template with a background image is refused.
- Publishing is local: the page and QR point at this server (`LABELLENS_PUBLIC_BASE_URL`), they are not hosted anywhere.
- Public medicine mode has ten reference products (DailyMed). The manufacturer is not in that corpus, so it is never shown. The scan-a-photo entry (`publicScan`) is still a mock, the name is typed. Brand names such as Lipitor do not match their generics.
- Retrieval evaluation numbers are LLM-graded (`results/`), with wide intervals; the checker and answers are not compliance determinations.
- No UI build exists in the repo yet: the API docs page and the two small HTML pages are the interface.
- Still mocks (header `X-Mock: true`): print verification, `publicScan` and its result, and a few listings. `demo_e2e.py` lists any stage that hit one.

## 8. Scope

Core: IR evaluation, inspection, change impact, template-based revised artwork with conditional barcode, review and approval, PDF at physical size, print verification, reports, version history.

v1 limits (stated openly in the report): one label template family, template-matching symbol detection for a handful of symbols, common fonts only, a narrow public medicine demo.

Out of scope: certifying compliance or authenticity, advising whether to take a medicine, inventing identifiers, publishing without human approval, confidential real manufacturer artwork.

Real manufacturer labels are proprietary. We use public labels (DailyMed, openFDA, GUDID) and synthetic labels with injected errors.

## 9. Team and plan

Pari owns most of the project (IR, crawling, checker, RAG, API, data model, change impact, report). Parth owns computer vision and the template and print-verification engine. Ishanvi owns a small set of static UI pages. Parth and Ishanvi start on Day 6. See `docs/TEAM_PLAN.md`, `docs/TASKS.md` and `docs/API_CONTRACT.md`.

## 10. Disclaimer

Academic project. Not a medical device. Not for clinical or regulatory decisions.
