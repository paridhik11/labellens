# Known limits

The README keeps a short summary. This file is the full list.

## Full list of known limits

Numbers below come from the reports named in brackets. Every relevance grade in this project is an LLM grade (claude-sonnet-5-5) except a 308-row human validation sample (`results/step13_llm_vs_human.md`); nothing here is a compliance determination.

- **Real-photo extraction is weak.** CV3 on 30 new real device-package photos (10 test): product name 0/10, lot 5/7, expiry 7/8, with the OCR models not upgraded (`reports/cv3.md`). The CV is otherwise tuned and scored on synthetic labels of one template family; very hard photos can make clean labels fail with confident false alarms; photos that are too blurry are rejected with a retake request.
- **CV2 field regressions.** On the 10 previously exposed real photos CV2 lowered lot reads from 7 to 4 and left product name at 0 (`reports/parth_cv2.md`). CV2 also needs the Tesseract executable; without it the profile falls back to the baseline.
- **Print verification is measured on simulated photos only.** Template mode: 46/48 correct prints confirmed, 0/48 false matches, 2 hard prints sent to rescan (`reports/print_template_mode.md`). Real print photos were not measured. Symbols are not compared in print verification.
- **Symbols are not measured on real photos.** The symbol detector is not trusted: symbol checks always ask a human. Real carton photos were not read (`docs/CV_STATUS.md`).
- **Abstention is weak.** On the 13-query test split no score reaches AUROC 0.90 or precision 0.80 (best 0.800 AUROC); a different 20-query set looked better (hybrid top AUROC 0.985) and was not confirmed (`results/step18_final.md`).
- **The AI answer is slow and optional.** Extractive passages are the default. The generative 3b answer answered 70% of answerable queries at a median of 38.3 s, with no wrong answers on the 10 no_answer queries; the sentence-selection mode failed its frozen gate and stays off (`reports/rag_select.md`). The AI answer needs Ollama, and always falls back to the passages.
- **The reranked display is a small gain on a small test.** Held-out hit rate 9/15 vs 8/15 (one query), median latency 1.04 s vs 0.37 s, 1 of 5 no_answer queries still shows quotes; LLM grades, one grader, 20 queries (`reports/rag_rerank.md`). Costs about 1 s per ask and an 87 MB model.
- **Medicine corpus is 30 products** (DailyMed, 618 chunks). Name matching: 31 of 45 fresh names confidently correct, 10 sent to review, 4 rejected, and 15 of 15 decoys rejected; authored names are not photo-OCR accuracy (`reports/medicine_aliases.md`). Medicine mode stays at 30 products: the 100-product expansion failed its gate and was not merged (`reports/med100.md`). The manufacturer is the SPL labeler, not necessarily the physical manufacturer. Brand names without an alias do not match their generics. Photo scan: see the next limit.
- **Exports are DRAFT only.** Generated labels always carry the DRAFT mark, even after approval (no approved variant is rendered). Identifiers are the GS1 test placeholder, and a template with a background image is refused (D-5).
- **Public photo scan is real but slow, and a person confirms it.** It never auto-confirms: a match asks "Is this X?" with the OCR lines as evidence, and label information appears only after Confirm. It can take up to a minute (median 47.0 s, max 54.5 s in the gate; 13 of 45 photos timed out) and often falls back to review or a typed name (15 of 45 sent to review, 17 not identified). Gate on 15 never-used decoy products (45 photos): 0 wrong (0 of 15 products, Wilson 0 to 20%; 0 of 45 photos, 0 to 8%). It was evaluated on pinned DailyMed package-label images with simulated camera conditions, not real phone photos. Correct identification was not measured on fresh photos with the final version (`reports/public_scan.md`).
- **Template registration checks shape and layout only** (slot geometry and the DRAFT band).
- **No multi-side scan.** One label side per upload.
- **Publishing is local:** the page and QR point at this server (`LABELLENS_PUBLIC_BASE_URL`), they are not hosted anywhere.
- **LLM-graded labels.** Retrieval and RAG numbers use LLM relevance grades with wide intervals; the LLM is stricter than humans at the 0/1 boundary (`results/step13_llm_vs_human.md`).
- **Mocks:** none. All 39 operations of `docs/contracts/openapi.yaml` are real (a mock response would carry `X-Mock: true`). `demo_e2e.py` lists any stage that hit a mock or a fallback.
