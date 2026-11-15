# Team plan

Refreshed after Step 19 (contracts). Day 1 was Friday 13 Nov 2026. Shift dates to match the real deadline, keep the order and the gates. Facts about what is done come from `CLAUDE.md` "Current state"; this file does not repeat them.

## People and share of work

| Person | Share | Role |
|---|---|---|
| Pari | about 75% | Lead. IR and its evaluation, checker, change parser, RAG, backend API and database, approval flow, public mode, template registration flow, reports, integration |
| Parth | about 20% | Computer vision (`extract_label`), template rendering engine, conditional GS1 barcode, layout checks, print verification. Joins from Day 6 |
| Ishanvi | about 5% | A few static UI pages built from the mock JSON in `src/api/mock/`. Joins from Day 6. No backend work, no integration work |

Parth and Ishanvi get no project tasks before Day 6. Parth's earlier CV and generation work is merged into main (`cv-fixes`); what remains for him is listed below.

## Ownership (no one edits another person's folders without asking)

| Folders | Owner |
|---|---|
| `src/ir`, `src/crawl`, `src/rag`, `src/api`, `src/common`, `data/eval`, `data/processed`, `results`, `docs`, `tests/test_mock_contracts.py` | Pari |
| `src/cv`, `src/gen`, `data/synthetic`, `data/symbols` | Parth |
| `ui/` | Ishanvi (Pari scaffolds the app and wires data) |

Locked files (change only if Pari agrees): `src/common/schemas.py`, `src/ir/base.py`, everything in `docs/contracts/`. `docs/API_CONTRACT.md` is superseded by `docs/contracts/`.

## Contracts (Step 19, in `docs/contracts/`)

1. The UI and the backend meet at `docs/contracts/openapi.yaml` (35 operations; scan, generate and print verify return 202 Job envelopes). `docs/contracts/API.md` explains it, `SCREENS.md` lists the 13 screens, their states and the mock file behind each state.
2. Ishanvi builds against `src/api/mock/*.json` only (indexed in `src/api/mock/index.json`). `tests/test_mock_contracts.py` fails if a mock drifts from the contract. Switching a page to the real API is Pari's job.
3. Parth delivers three functions that match `DATA_MODEL.md` and `TEMPLATE_SPEC.md`: `extract_label(image_path)`, `render_label(template_spec, record)` (SVG, PDF at size_mm, slot report) and `verify_print(photo_path, approved_label)`.
4. Open differences between the contract and Parth's merged code are D-1 to D-11 in `docs/contracts/SCHEMA_CHANGE_REQUESTS.md`. Decided so far: the contract follows the code for D-2, D-4, D-8 and part of D-7; Parth fixes D-3 (background), D-5 (one `artifact_sha256`), D-6 (approval record names, `check_id`) and D-9 (named SVG groups); the other layout kind names in D-7 are still open. CR-1 to CR-16 (changes to `schemas.py`) are not approved.

## Where we are

| Track | State |
|---|---|
| Retrieval Steps 1 to 15 | Done: own BM25 and TF-IDF, dense and hybrid, LLM-assessed qrels with a human validation sample, results, failures, ablations |
| Step 16 | Abstention evaluation for the medicine mode (hybrid top score AUROC 0.985, tiny sample, LLM grades only). Branch `step16-abstain` |
| Steps 17 and 18 | Retrieval improvements (expansion, part boost, rerank, then CV-based experiments with bigger embedders and heading enrichment). On branch `step17-opt`, not merged into main. Dev gains shrank on held-out, so nothing is claimed as an improvement yet |
| CV fixes | Merged (`cv-fixes`). Fresh-seed results in `results/cv_final_eval.md`; symbol detector finds 0/204 independently drawn pictograms (`docs/CV_STATUS.md`) |
| Step 19 | Done and merged: data model, template spec, OpenAPI, API guide, screens, 50 mocks, contract tests |
| Step 20 | Backend, on branch `step20-backend`, not merged. Phase 0 (contract follows merged renderer) and 20a (SQLite store, append-only triggers, derived status, review rules) done. 20b endpoints, 20c mock fallback, 20d response tests not started |

## v1 build order

This is the order the pieces are built so that the end-to-end demo works as early as possible. Each item names the contract it relies on.

1. Backend (Step 20): endpoints (20b), mock fallback behind an `X-Mock` header (20c), OpenAPI response tests (20d). Pari.
2. Static UI pages from the mocks, in screen order: Scan and Understand, Inspect, Change Impact, History. Ishanvi from Day 6.
3. Checker with evidence (Flag objects from T1 retrieval) and the natural-language change parser, then T3 change impact retrieval. Pari.
4. Renderer, barcode and layout checks aligned to the contract (D-3, D-5, D-6, D-9, remaining D-7 names). Parth from Day 6.
5. Generate endpoint and self-check wired to Parth's renderer, DRAFT mark on every draft. Pari with Parth.
6. Review and approval flow: approval bound to `artifact_sha256` and a passed `check_id`, new version voids an approval, reject is terminal. Pari (rules already in `src/api/reviews.py` on the Step 20 branch).
7. Template registration flow (draw and name slots). Pari.
8. Public medicine mode: scan, product match, cited answers, abstain with a reason. Pari. Small drug set.
9. Print verification endpoint. Parth's `verify_print` behind a Job, Pari wires it.
10. Integration, final retrieval numbers, report and slides.

Steps 1 to 4 are the critical path. Steps 7 to 9 are cut or shrunk first if time runs out (see the version ladder).

## Day by day (from Day 6 onward)

| Day | Pari | Parth | Ishanvi |
|---|---|---|---|
| 6 | Step 20b endpoints for products, templates, label versions. Change parser | Align renderer to D-3, D-5, D-6, D-9. OCR and barcode behind `extract_label` | Scan and Understand page (static, mock data) |
| 7 | Checker with evidence. T3 change impact retrieval. RAG with citations | Template rendering engine against `TEMPLATE_SPEC.md`. Layout kind names (rest of D-7) | Inspect page layout (static) |
| 8 | Generate and approval endpoints. Template registration. Public mode (small) | Conditional barcode, layout checks, self-check loop | Change Impact side-by-side layout (static) |
| 9 | Feature freeze. Integration, final retrieval numbers, tag release | Print verification. Final CV and generation numbers | History page and polish (static) |
| 10 | Report, slides, demo rehearsal | Report chapter | Screenshots and slide visuals |

## Gates
- Step 19 contracts exist: met (Step 19 merged).
- End of Day 7: backend endpoints answer from the real database for products, templates and label versions, and every UI screen state has a mock.
- End of Day 8: one synthetic label goes upload, extract, retrieve, flags, change, revised label, self-check, approval, end to end (a script is enough).
- End of Day 9: feature freeze.

## Version ladder (squeeze, do not cut)

| Feature | v1 (guaranteed) | v2 (if time) |
|---|---|---|
| Symbols | `manufacturer` and `expiry` pictograms only (contract D-2) | More symbols, YOLO |
| Template | One label family, slots marked by hand | More families |
| Fonts | Common fonts | Font matching |
| Print verification | Perspective correction, OCR, barcode, field compare | Symbol and layout compare |
| Public mode | Small drug set, cited answers, abstain with a reason | Wider coverage |
| UI | 4 static pages from mock JSON | More pages, mobile polish |
| Ranking | Best retrieval system that survives held-out testing | Learned ranking |

## Risks

| Risk | Mitigation |
|---|---|
| Pari is the bottleneck | Backend and checker first, everything else is v1. Plan mode keeps each task small |
| Retrieval gains do not hold on held-out queries | Report them as they are (Step 17 and 18 results). Do not tune further on the held-out half |
| Contract and renderer drift apart | D-1 to D-11 decision table. `tests/test_mock_contracts.py` guards the mocks |
| Parth gets few days for a lot of work | One template family only, gaps already listed as D-3, D-5, D-6, D-9 |
| UI not ready | Mock JSON screens are enough for the demo; use screenshots in the report |
| LLM grades are stricter than human grades | Keep the Step 13 caveat next to every results table |

## Working rules
1. Commit small, push daily, pull request for anything outside your folders.
2. Every number in the report comes from a rerunnable command.
3. Use Claude Code with `CLAUDE.md`. Plan mode first, then approve. One step at a time, stop after each step report.
4. Stuck for more than 45 minutes: ask in the group chat.
5. 15 minute sync per day from Day 6.
