# Task checklist

Copy these into GitHub issues. Tag each with owner and day.

## A: IR
- [ ] D1 Own inverted index, TF-IDF, BM25 (starter in `src/ir/bm25.py`), tests pass
- [ ] D2 Dense retrieval (sentence-transformers + FAISS)
- [ ] D2 Hybrid fusion (RRF and weighted)
- [ ] D2 Cross-encoder rerank
- [ ] D3 Eval harness reads the real corpus and qrels, results table written to `results/`
- [ ] D3 LLM proposes qrels candidates (pooled top 10 from each system)
- [ ] D4 Annotate qrels, 60+ queries, kappa on 30% overlap
- [ ] D5 Ablations: chunk size, k1 and b, fusion weights, OCR noise
- [ ] D5 Query expansion (field-aware plus regulatory synonyms)
- [ ] D6 Product matching retrieval (T2) with LTR
- [ ] D7 Relevance feedback (Rocchio)
- [ ] D7 Change impact retrieval (T3)
- [ ] D8 Failure analysis of 10 queries, final tables
- [ ] D9 IR report chapters

## B: CV, ML, generation
- [ ] D1 Synthetic label generator (Pillow) with clean, scan, photo augmentation
- [ ] D2 OCR (PaddleOCR) and barcode decode (zxing-cpp), GS1 parsing
- [ ] D3 Error injector with JSON ground truth
- [ ] D3 YOLO dataset export and training started on Colab or Kaggle
- [ ] D4 Annotate qrels
- [ ] D5 OCR eval per condition (CER, WER), YOLO mAP
- [ ] D6 Barcode builder with GS1 check digits and round trip
- [ ] D6 Symbol registry (verify mapping against ISO 15223-1)
- [ ] D7 Artwork templates and renderer with DRAFT watermark
- [ ] D7 Self-check loop and visual diff
- [ ] D8 Final CV and generation numbers
- [ ] D9 CV and generation report chapters

## C: Systems
- [ ] D1 Crawlers (openFDA, eCFR) and chunking with hashes
- [ ] D1 Supabase project, tables from `docs/PRODUCT_SPEC.md`
- [ ] D2 FastAPI routes: upload, analyze, decision, change, report
- [ ] D2 Next.js scaffold following `docs/mockup/website_concept.png`
- [ ] D3 Public module corpus (DailyMed), auth with professional and admin roles, product pages
- [ ] D4 Annotate qrels
- [ ] D5 Checker producing Flag objects with evidence
- [ ] D5 RAG with citation check and abstain rule
- [ ] D6 Professional workspace wired to API (Inspect, Evidence, Changes, History)
- [ ] D7 Change Impact screen with timeline
- [ ] D7 Public Scan and Understand flow with cited chatbot
- [ ] D8 PDF reports, QR published page, end to end test
- [ ] D9 System report chapters and demo script

## Everyone
- [ ] D4 Qrels annotation day
- [ ] D8 Feature freeze
- [ ] D10 Rehearse demo, slides, final tag
