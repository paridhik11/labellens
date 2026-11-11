# Team plan

Day 1 is Friday 13 Nov 2026. Shift dates to match the real deadline, keep the order and the gates.

## People and share of work

| Person | Share | Role |
|---|---|---|
| Pari | about 75% | Lead. IR, crawling, product matching, change impact, checker, RAG, API, data model, template registration, approval flow, public mode, reports, integration |
| Parth | about 20% | Computer vision, template rendering engine, conditional barcode, layout checks, print verification. Starts Day 6 |
| Ishanvi | about 5% | A small set of static UI pages built from mock JSON. Starts Day 6. No backend work, no integration work |

Days 1 to 5: Pari works alone. Parth and Ishanvi may learn on their own time (OpenCV basics, Next.js basics) but have no project tasks.

## Ownership (no one else edits another person's folders without asking)

| Folders | Owner |
|---|---|
| `src/ir`, `src/crawl`, `src/rag`, `src/api`, `src/common`, `data/eval`, `data/processed`, `results`, `docs` | Pari |
| `src/cv`, `src/gen`, `data/synthetic`, `data/symbols` | Parth |
| `ui/` | Ishanvi (Pari scaffolds the app and wires data) |

Locked files (change only if Pari agrees): `src/common/schemas.py`, `src/ir/base.py`, `docs/API_CONTRACT.md`.

## Contracts

1. Parth delivers `extract_label(image_path) -> LabelExtraction` and `render_label(template_spec, record) -> RenderResult` (SVG, PDF at size_mm, slot report) and `verify_print(photo_path, approved_label) -> VerificationResult`.
2. Pari delivers the template spec schema, the FastAPI app and `docs/API_CONTRACT.md` by Day 5, plus mock JSON in `ui/mock/`.
3. Ishanvi builds against `ui/mock/*.json` only. Switching to the real API is Pari's job.

## Day by day

| Day | Pari | Parth | Ishanvi |
|---|---|---|---|
| 1 | Pool the 62 queries. Grade device queries. Exclude no_answer from main averages | none | none |
| 2 | Finish device grading. First real results table (tfidf, bm25, dense, hybrid, chunk and section level) | none | none |
| 3 | Grade medicine queries. Ablations: RRF k, fusion weights, stemming, BGE prefix, chunk size | none | none |
| 4 | Corpus expansion (openFDA, FDA guidance). Query expansion. LTR for product matching (T2) | none | none |
| 5 | Checker with evidence. Data model and template spec schema. API contract and mock JSON. Basic synthetic label generator | none | none |
| 6 | Relevance feedback. API endpoints. Natural-language change parser | OCR and barcode decode in `extract_label`. Re-grade 30% of Pari's qrels for kappa (about 2 hours) | Scan and Understand page (static, mock data) |
| 7 | T3 change impact retrieval. RAG with citations. Template registration flow (draw slots) | Template rendering engine: slots to SVG to PDF at size_mm | Professional Inspect page layout (static) |
| 8 | Approval flow and database. Public mode (small). PDF inspection report | Conditional barcode, layout checks, self-check loop | Change Impact side-by-side layout (static) |
| 9 | Feature freeze. Integration, final ablations, tag release | Print verification. Final CV and generation numbers | History page and polish (static) |
| 10 | Report, slides, demo rehearsal | Report chapter | Screenshots and slide visuals |

## Gates
- End of Day 2: a real results table exists.
- End of Day 5: the API contract and mock JSON exist so Parth and Ishanvi can start without questions.
- End of Day 8: one synthetic label goes upload, extract, retrieve, flags, change, revised label, self-check, end to end (a script is enough).
- End of Day 9: feature freeze.

## Version ladder (squeeze, do not cut)

| Feature | v1 (guaranteed) | v2 (if time) |
|---|---|---|
| Symbols | Template matching on a handful of symbols | YOLO |
| Template | One label family, slots marked by hand | More families |
| Fonts | Common fonts | Font matching |
| Print verification | Perspective correction, OCR, barcode, field compare | Symbol and layout compare |
| Public mode | Small drug set, cited chatbot | Wider coverage |
| UI | 4 static pages from mock JSON | More pages, mobile polish |
| LTR | Hand-tuned weights | LambdaMART |

## Risks

| Risk | Mitigation |
|---|---|
| Pari is the bottleneck | Gates are IR first. Everything else is v1. Use Claude Code plan mode to keep each task small |
| Qrels take too long | Device queries first, 15 per session, never shrink the pool |
| Parth gets 5 days for a lot of work | Pari prepares the synthetic generator and template spec on Day 5. One template family only |
| UI not ready | Mock JSON screens are enough for the demo; use screenshots in the report |
| Integration trouble | Contracts frozen on Day 5, end-to-end gate on Day 8 |

## Working rules
1. Commit small, push daily, pull request for anything outside your folders.
2. Every number in the report comes from a rerunnable command.
3. Use Claude Code with `CLAUDE.md`. Plan mode first, then approve.
4. Stuck for more than 45 minutes: ask in the group chat.
5. 15 minute sync per day from Day 6.
