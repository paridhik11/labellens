# Task checklist

Tick items as they are done. Day numbers match `docs/TEAM_PLAN.md`.

## Done (Steps 1 to 10, built with Antigravity)
- [x] Own inverted index, TF-IDF, BM25, metrics, eval harness
- [x] eCFR crawler (11 parts), chunker, 903 chunks
- [x] Dense retrieval (BGE and FAISS), cache keyed by content hash
- [x] Hybrid RRF, module filter, section-level evaluation
- [x] Qrels tooling (pool, to-qrels, kappa), 62 queries drafted

## Pari
- [ ] D1 Put 62 queries in `data/eval/queries_t1.tsv`, re-run pooling, report rows per module
- [ ] D1 Exclude no_answer queries from main averages, report separately
- [ ] D1 to D2 Grade device queries
- [ ] D2 First real results table
- [ ] D3 Grade medicine queries
- [ ] D3 Ablations (RRF k, weights, stemming, BGE prefix, chunk size, module filter)
- [ ] D4 Corpus expansion (openFDA, FDA guidance, EU MDR annex), re-pool new chunks
- [ ] D4 Query expansion, LTR for product matching
- [ ] D5 Checker (Flag objects with evidence)
- [ ] D5 Data model, template spec schema, API contract, mock JSON
- [ ] D5 Basic synthetic label generator
- [ ] D6 Relevance feedback, API endpoints, change parser
- [ ] D7 T3 change impact retrieval, RAG with citation check and abstain rule
- [ ] D7 Template registration flow
- [ ] D8 Approval flow, database, public mode (small), PDF inspection report
- [ ] D9 Feature freeze, integration, final ablations, tag release
- [ ] D10 Report, slides, rehearsal

## Parth (from Day 6)
- [ ] D6 `extract_label` with OCR and barcode decode, CER and decode rate per condition
- [ ] D6 Re-grade 30% of qrels, run kappa
- [ ] D7 Template rendering engine (slots to SVG to PDF at physical size)
- [ ] D8 Conditional barcode (GS1), layout checks, self-check loop
- [ ] D9 Print verification, final CV and generation numbers
- [ ] D10 Report chapter

## Ishanvi (from Day 6, small tasks only)
- [ ] D6 Scan and Understand page from mock JSON
- [ ] D7 Inspect page layout from mock JSON
- [ ] D8 Change Impact side-by-side layout from mock JSON
- [ ] D9 History page and visual polish
- [ ] D10 Screenshots and slide visuals
