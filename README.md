# LabelLens

AI-assisted review of medical device and medication labels, built around information retrieval.

CSD358 Information Retrieval course project. Team of 3.

> LabelLens supports human reviewers. It does not certify compliance or authenticity. Every flag is a suggestion with evidence attached, and a human approves or rejects it.

---

## 1. Problem

A label reviewer has to check text, symbols, barcodes and warnings against product specs, regulations and the previous label version. When a product detail changes, they also have to work out which labels are now out of date. This is slow, repetitive and easy to get wrong.

## 2. What LabelLens does

One website, two modules that share infrastructure but not data, rules or evaluation (see `docs/PRODUCT_SPEC.md`):

- **Scan and Understand (public, medicines):** patients and caregivers scan a pack with no account and get a source-linked summary, a chatbot restricted to the matched label, and supported packaging checks. It never claims authenticity or advises whether to take the medicine.
- **Professional workspace (medical devices):** labeling, regulatory and quality teams inspect labels, assess changes, and keep version history.
- **Change Impact:** a proposed change produces affected items, evidence, and a draft revision with regenerated barcode and digital artwork for human approval (see `docs/GENERATION.md`).
- **Products, history and QR:** records, batches, artwork versions, decisions, reports, and a supplementary QR to the published information page.

Professional inspection flow. Upload a label (image, photo or PDF). The system:

1. Extracts text with OCR, decodes barcodes, detects selected regulatory symbols.
2. Finds the matching product record (retrieval, not exact lookup, because OCR is noisy).
3. Retrieves the regulatory passages and spec fields relevant to each label claim.
4. Compares label content against the record and the requirements, and flags mismatches with cited evidence.
5. Diffs the label against its previous revision (text diff plus visual diff).
6. When a product record changes, retrieves the labels that probably need updating.
7. Produces an inspection report. The reviewer approves, rejects or comments, and every decision is versioned.
8. After a change is assessed, generates a draft barcode (GS1 payload) and draft artwork from templates, self-checks them through the same inspection pipeline, and sends them for approval.

## 3. Where IR sits (the core of the project)

We treat LabelLens as three IR problems plus a grounded generation layer.

| Task | Query | Documents | Why it is real IR |
|---|---|---|---|
| T1 Requirement retrieval | A label field or claim (e.g. "Rx only", "Store below 25 C", sterility symbol) | Passages from FDA / EU MDR / ISO / GS1 documents | Vocabulary mismatch between label text and legal text, so lexical and semantic must be combined |
| T2 Product matching | Noisy OCR text plus decoded barcode | Product records (name, model, manufacturer, UDI, GTIN) | Fuzzy entity retrieval under OCR noise |
| T3 Impact retrieval | A changed product field | Label versions and their extracted fields | Retrieval of affected items with ranking by likelihood |
| T4 Grounded explanation (RAG) | Flagged issue plus retrieved passages | n/a | Generation must cite retrieved passages only, and abstain when evidence is weak |

Retrieval stack, all evaluated against each other:

- Inverted index and BM25 implemented from scratch (course credit, and we understand it), checked against a library implementation.
- TF-IDF baseline.
- Dense retrieval (sentence-transformers, e.g. bge or e5) with FAISS.
- Hybrid fusion (Reciprocal Rank Fusion and weighted score fusion).
- Cross-encoder reranker on the top 50.
- Query expansion (field-aware, plus synonym lists for regulatory terms).

## 4. Architecture

```
Upload -> Preprocess (OpenCV) -> OCR + Barcode + Symbol detection
                                      |
                       Structured label fields (JSON)
                                      |
        +-----------------------------+-----------------------------+
        |                             |                             |
   T2 Product match             T1 Requirement retrieval       Version diff
   (BM25 + fuzzy + dense)       (hybrid + rerank)              (text + image)
        |                             |                             |
        +--------------> Rule + evidence checker <------------------+
                                      |
                        RAG explanation (cited, abstains)
                                      |
                  Review UI -> decision log -> inspection report (PDF)
```

Change impact (T3) runs when a product record is edited: it ranks labels by how likely they are affected.

See `docs/WORKFLOW.md` for the full pipeline and `docs/EVALUATION.md` for metrics.

## 5. Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.11 |
| API | FastAPI |
| Frontend | Next.js (React, Tailwind), camera capture in browser |
| Internal dashboards | Streamlit for retrieval experiments and ablations only |
| Auth and storage | Supabase Auth (professional, admin roles), Supabase Storage |
| Barcode generation | treepoem or bwip-js (GS1 DataMatrix, GS1-128) |
| Artwork generation | SVG templates, cairosvg for PDF and PNG |
| OCR | PaddleOCR (fallback Tesseract) |
| Image processing | OpenCV, scikit-image |
| Barcodes | zxing-cpp, GS1 parser for UDI/GTIN |
| Symbol detection | YOLOv8 (ultralytics) trained on synthetic data from ISO 15223-1 symbols |
| Lexical IR | Own inverted index + BM25, `bm25s` for comparison |
| Dense IR | sentence-transformers + FAISS |
| Reranker | cross-encoder (ms-marco MiniLM or bge-reranker) |
| Crawling | requests, BeautifulSoup, Playwright when needed, official APIs (openFDA, DailyMed) |
| Storage | PostgreSQL (Supabase free tier or local Docker), local or S3-style file storage |
| LLM for RAG | Claude API (or any API LLM), strict citation prompt |
| Experiments | pandas, ranx or pytrec_eval for IR metrics |

## 6. Repo layout

```
src/
  ir/        index, bm25, tfidf, dense, hybrid, rerank, eval
  cv/        preprocess, ocr, barcode, symbols, image_diff
  crawl/     openfda, dailymed, regulatory crawlers, change tracker
  rag/       prompts, cite-check, abstain logic
  gen/       barcode builder, symbol registry, artwork templates, self-check
  api/       FastAPI app
  common/    schemas, config, db
data/
  raw/ processed/ eval/ synthetic/
docs/        workflow, evaluation, data sources, agent prompts
notebooks/   experiments and ablations
tests/
ui/          Next.js web app (public and professional modules), Streamlit dashboards in ui/dashboards
```

## 7. Quick start

```bash
git clone <repo> && cd labellens
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add API keys
make test                   # 12 tests should pass
make eval-sample            # runs BM25 and TF-IDF on the toy sample, writes results/sample_results.md
make api                    # FastAPI on :8000, GET /health
make db-up                  # local Postgres via docker compose
```

The toy sample in `data/processed/sample_regs.jsonl` is for pipeline testing only. It is not real regulatory text. Replace it with the crawled corpus on Day 2 and the real qrels on Day 4.

## 8. Evaluation summary

- Retrieval: nDCG@10, Recall@20, MRR, MAP across BM25, dense, hybrid, hybrid+rerank, with ablations.
- Error detection: precision, recall, F1 per injected error type on a synthetic benchmark plus a small real set.
- Vision: OCR character error rate, barcode decode rate, symbol mAP@0.5.
- RAG: citation precision, faithfulness, abstention rate.
- Generation: self-check pass rate, barcode round-trip success, field fidelity (CER on rendered text), symbol round-trip recall.
- Public module: product match accuracy, summary faithfulness, chatbot citation precision and refusal rate, reported separately from the professional module.
- Reviewer task: time and accuracy on a small simulated review study.

Details in `docs/EVALUATION.md`.

## 9. Scope and limits

In scope: label upload, extraction, retrieval, flagging, version diff, change impact, reports, decision log.

Core (must ship): professional inspection, hybrid retrieval with evaluation, change impact with draft barcode and artwork, reports, version history.

Public module: ship a narrow version (a limited set of medicines from DailyMed, one language), clearly labeled as a reference match.

Stretch: QR published pages, batch tracking, multi-language labels, mobile polish.

Out of scope: claiming regulatory compliance, authenticity verification, advising on taking medicine, inventing identifiers (GTIN, UDI-DI), publishing anything without human approval, handling confidential real manufacturer artwork.

Real manufacturer labels are proprietary. We use public labels (DailyMed, openFDA, GUDID) and synthetic labels generated with injected errors, and we say so openly in the report.

## 10. Plan

10 days, 3 people, full scope, built in parallel with Antigravity. Day plan, gates, version ladder and risks: `docs/PLAN_10_DAYS.md`. Task checklist: `docs/TASKS.md`. UI reference: `docs/mockup/website_concept.png`.

## 11. Team

| Role | Owner | Focus |
|---|---|---|
| IR lead | TBD | Indexes, retrieval, fusion, reranking, qrels, evaluation |
| CV lead | TBD | Preprocessing, OCR, barcode, symbols, image diff, synthetic labels |
| Systems lead | TBD | Crawlers, DB, API, RAG, UI, report generation |

Everyone reviews each other's PRs and everyone contributes to qrels annotation.

## 12. License and disclaimer

Academic project. Not a medical device. Not for clinical or regulatory decisions.
