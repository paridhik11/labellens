# Antigravity task prompts

Paste one at a time. Start each session with: "Read README.md, AGENTS.md and docs/WORKFLOW.md first."

Starter code already exists: schemas, BM25 and TF-IDF, metrics, eval harness and tests. Extend them, do not rewrite them. Run `make test` and `make eval-sample` first to confirm the baseline works.

## Which prompt on which day

| Day | A (IR) | B (CV and gen) | C (Systems) |
|---|---|---|---|
| 1 | P2 (extend), P20 | P5 | P1 |
| 2 | P3 | P6 | P11, P15 scaffold |
| 3 | P4, P20 | P5 error injector, P7 dataset | P16, P15 auth and products |
| 5 | P19 | P7 eval | P8 checker, P9 |
| 6 | P8 matching, P17 | P12, P13 | P15 workspace |
| 7 | P18, P10 retrieval | P13, P14 | P15 change impact and public flow |
| 8 | eval and ablations | eval | P11 reports |


## P0 Scaffold
Create the repo skeleton from the README layout. Add `requirements.txt`, `.env.example`, `.gitignore`, `pyproject.toml` (ruff, pytest), a GitHub Actions workflow running ruff and pytest, and `src/common/schemas.py` with pydantic models for Chunk, LabelExtraction, ProductRecord, Hit, Flag. Add one passing test per schema.

## P1 Crawlers
Implement `src/crawl/openfda.py` and `src/crawl/ecfr.py`. Fetch device labeling regulations (21 CFR 801, 830) and a sample of openFDA device and drug label records. Save raw JSON to `data/raw/`. Write `src/crawl/chunk.py` that turns documents into chunks following the schema in docs/WORKFLOW.md, with hashes. Add rate limiting, retries and a re-crawl change detector. Output `data/processed/regs.jsonl`.

## P2 BM25 from scratch
In `src/ir/`, implement a tokenizer (lowercase, stopwords, optional stemming), an inverted index with postings and term frequencies, TF-IDF cosine scoring and BM25 scoring with tunable k1 and b. Include index save and load. Add tests that compare our BM25 ranking against `bm25s` on a small corpus (top-10 overlap above 0.9).

## P3 Dense and hybrid
Implement `dense.py` (sentence-transformers plus FAISS), `hybrid.py` (RRF and weighted fusion) and `rerank.py` (cross-encoder). All expose `search(query, k)`. Add a CLI `python -m src.ir.search "query"`.

## P4 Evaluation harness
Implement `src/ir/eval.py` reading TREC style qrels and a queries file, computing nDCG@10, Recall@20, MRR and MAP for every registered system, with paired bootstrap significance. Output a markdown results table to `results/`. Use 20 placeholder queries so the pipeline runs end to end before real qrels exist.

## P5 Synthetic label generator
Write `src/cv/synth.py` that renders labels (product name, model, UDI, lot, expiry, storage text, symbols, a GS1 barcode) with Pillow, from product records. Add augmentation levels: clean, scan (noise, slight skew), photo (perspective, blur, glare). Also an error injector that applies the error types in docs/EVALUATION.md and records ground truth in a JSON sidecar.

## P6 OCR and barcode
Implement preprocessing, a PaddleOCR wrapper and zxing-cpp barcode decoding with GS1 parsing. Output the LabelExtraction schema. Add `src/cv/eval_ocr.py` computing CER, WER and barcode decode rate per condition.

## P7 Symbol detection
Build a YOLOv8 training script using synthetic composites of ISO 15223-1 style symbols pasted on label backgrounds with augmentation. Export a dataset in YOLO format, train, and evaluate mAP@0.5 per class. Document the exact commands.

## P8 Matching and checker
Implement T2 product matching (fuzzy plus BM25 plus dense, with the barcode as a strong signal) and the checker that produces Flag objects with evidence passages from T1 retrieval. Evaluate on the error injection benchmark.

## P9 RAG explanations
Implement the grounded explanation module with a strict citation prompt, a cite-checker that verifies every cited passage id exists and overlaps the claim, and the abstain rule. Add tests for hallucinated citations.

## P10 Revision diff and impact
Implement text diff by field and image diff (SSIM plus region boxes) between label versions. Implement T3 impact retrieval: given a changed product field, rank labels likely affected.

## P11 API and report
FastAPI endpoints (upload, analyze, decision, change request, report) and Supabase tables from docs/PRODUCT_SPEC.md. Versioned rows only, never overwrite. PDF inspection report generator listing checks run, differences, unknowns and evidence.

## P12 Barcode builder
In `src/gen/barcode.py`, build GS1 payloads from application identifiers (01, 17, 10, 21) with GTIN check digit calculation and date validation, render GS1 DataMatrix and GS1-128 with treepoem or bwip-js, and decode back with zxing-cpp. Never generate a GTIN: take it from the product record or raise `IdentifierRequired`. Tests for check digits, bad dates and round trip.

## P13 Symbol registry and artwork templates
Create `data/symbols/registry.json` (symbol id, name, standard clause, source note, SVG path) and 3 SVG label templates with named slots in `src/gen/templates/`. Implement `src/gen/render.py` that fills slots from a product record, auto-fits text, flags overflow and minimum size violations, and outputs SVG, PDF and PNG with a DRAFT watermark.

## P14 Change impact and self-check
Implement the change request flow: apply the change to a copy of the product record, run T3 impact retrieval plus rules, generate draft barcode and artwork, then run the self-check (OCR, barcode decode, symbol detection, checker) and the visual diff. Output an impact checklist JSON and a review task. Report self-check metrics with `python -m src.gen.eval`.

## P15 Web app
Next.js and Tailwind app following docs/PRODUCT_SPEC.md and the mockup: public Scan and Understand flow (camera capture, observed vs reference, cited chatbot) and the professional workspace (Products, Inspect, Evidence, Changes, History) with highlighted bounding boxes and the change timeline Draft, Checked, Reviewed, Published. Supabase Auth with professional and admin roles. Every draft shows "Human approval before publication."

## P16 Public module data
Build a separate corpus and evaluation set for medicines from DailyMed and openFDA drug labels. Own folder `data/public_meds/`, own qrels and own results table. Chatbot answers only from the matched label, cites sections, refuses medical advice and unsupported questions.

## P17 Learning to rank for product matching
Build a feature table for T2 candidates (BM25 score, dense score, fuzzy ratio on name and model, barcode agreement, manufacturer match). Train LightGBM LambdaMART with grouped cross validation, compare against hand-tuned weights, and add both to `build_systems` in `src/ir/eval.py`. Report nDCG and accuracy@1.

## P18 Relevance feedback
Implement Rocchio query refinement in `src/ir/feedback.py` using reviewer accepted and rejected passages from the decision log. Evaluate with a simulated reviewer on the qrels (accept relevant, reject non relevant) and report the gain over no feedback.

## P19 Query expansion
Implement field-aware query building (field name plus OCR text) and a regulatory synonym list in `data/eval/synonyms.json`. Add as a system variant and an ablation row.

## P20 Qrels tooling
Write `src/ir/qrels_tool.py`: for each query, pool the top 10 from every system, optionally ask an LLM to propose a grade with a one line reason, then write a CSV for humans to confirm. Export TREC qrels and compute Cohen's kappa on the overlapping subset. The LLM output is only a suggestion, humans make the final judgment.
