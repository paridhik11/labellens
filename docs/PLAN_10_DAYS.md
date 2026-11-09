# 10 day plan: full scope, run in parallel

Nothing is cut. Every feature has a v1 that must work and a v2 that upgrades it. If time runs short, ship v1 of the last items.

Each person runs 2 to 3 Antigravity agents on separate folders and branches. Slow work (training, crawling, indexing) runs in the background while humans do human-only work (qrels, review, report).

## Tracks

| Track | Owner | Scope |
|---|---|---|
| IR | A | Own BM25 and TF-IDF, dense, hybrid, rerank, query expansion, learning to rank, relevance feedback, qrels, eval, ablations |
| CV, ML, generation | B | Synthetic labels, OCR, barcode, YOLO symbols, image diff, barcode and artwork generation, self-check |
| Systems | C | Crawlers, Supabase, auth, FastAPI, RAG, Next.js web app, public module, reports |

## Day plan

| Day | A (IR) | B (CV and gen) | C (Systems) |
|---|---|---|---|
| 1 | Lock schemas, own BM25 and TF-IDF (starter included) | Synthetic label generator | Crawlers, chunking, Supabase |
| 2 | Dense, hybrid, rerank | OCR, barcode decode | Corpus done, FastAPI, Next.js scaffold from the mockup |
| 3 | Eval harness on real corpus, LLM-proposed qrels candidates | Error injector, YOLO dataset export, training starts (GPU, overnight) | Public module corpus (DailyMed), auth, product pages |
| 4 | Everyone annotates qrels | Everyone annotates | Everyone annotates |
| 5 | Results table, ablations, query expansion | OCR eval, YOLO results | Checker, RAG with citation check |
| 6 | Product matching, LTR | Barcode builder, symbol registry | Professional workspace UI wired up |
| 7 | Relevance feedback, change impact retrieval | Artwork templates, self-check, visual diff | Change Impact screen, public Scan flow and chatbot |
| 8 | Final ablations, failure analysis | Final CV and generation numbers | Reports PDF, QR page, end to end test |
| 9 | Report: IR chapters | Report: CV and generation | Report: system, demo script |
| 10 | Buffer, slides, rehearsal | Buffer | Buffer |

## Version ladder

| Feature | v1 (guaranteed) | v2 (if time) |
|---|---|---|
| Symbols | Template matching on a few symbols | YOLO trained on all synthetic classes |
| UI | Core screens working | Polish, mobile, QR page |
| Public module | Small drug set, cited chatbot | Wider coverage, photo robustness |
| Learning to rank | Hand-tuned feature weights | LambdaMART (LightGBM) |
| Artwork | One template | More templates |
| Qrels | 60 queries | 100+ queries |
| Relevance feedback | Rocchio on reviewer accepts and rejects | Feedback as LTR features |

## Gates

| Gate | Check |
|---|---|
| End of Day 3 | A retrieval results table exists from `python -m src.ir.eval` |
| End of Day 4 | Qrels done (60+ queries judged). No exceptions |
| End of Day 6 | One label goes upload to flags to explanation end to end |
| End of Day 8 | Feature freeze. Only fixes and report after this |

## Using Antigravity well

1. Day 1 before any agent runs: schemas and the `search(query, k)` interface are already locked in `src/common/schemas.py` and `src/ir/base.py`. Do not change them without all 3 agreeing.
2. One agent per folder, one branch each. Two agents never touch the same files.
3. You run the eval and test commands yourself. Never trust a number an agent reports without a command output.
4. One prompt from `docs/ANTIGRAVITY_PROMPTS.md` at a time. Review the diff before merging.
5. Merge to `main` at least twice a day so integration problems show early.

## Biggest risks

| Risk | Mitigation |
|---|---|
| Qrels not finished | Day 4 is reserved. LLM proposes candidates, humans judge, second annotator checks 30% |
| CV is new to the team | Report scan vs photo separately. Template matching as symbol fallback |
| Integration on Days 6 and 7 | Shared schemas, merge often, end to end test on Day 6 |
| Report left to the end | Write each results section the day its table appears |
| Compute for YOLO | Free Colab or Kaggle GPU, synthetic data gives boxes for free |
