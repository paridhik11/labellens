# LabelLens Learning Log

A sequential log of progress, implementation decisions, worked examples, and verification steps.

---

## Step 1: Environment and Baseline Evaluation

1. **What I did:** Checked repository structure and confirmed test suite execution. Ran sample evaluation comparing TF-IDF and BM25 on the toy regulatory dataset without changing code.
2. **Files created or changed:** results/sample_results.md (benchmark table output).
3. **How it works:** Inverted index maps terms to document IDs. Metrics (nDCG@10, Recall@20, MRR, MAP) assess retrieval quality against ground truth relevance judgements.
4. **How I verified it:** Executed `python -m pytest -q` (12 passed) and `python -m src.ir.eval --corpus data/processed/sample_regs.jsonl --queries data/eval/queries_sample.tsv --qrels data/eval/qrels_sample.tsv --out results/sample_results.md`.
5. **Check yourself:** Inspect results/sample_results.md and tests/test_bm25.py.
6. **Assumptions:** Evaluated inside labellens/labellens using local python environment.
7. **Questions:** What does MRR measure when the first relevant hit is at rank 2? (1/2 = 0.5).

---

## Step 2: IR Code Walkthrough and Worked Example

1. **What I did:** Walked through tokenizer.py, bm25.py, and metrics.py. Traced a 3-document, 1-query example by hand and verified all formulas with a script.
2. **Files created or changed:** None (code walkthrough only).
3. **How it works:** Tokenization strips stopwords and punctuation. BM25 computes IDF and balances term frequency saturation against document length normalization.
4. **How I verified it:** Ran python script calculating scores for d1 (1.10589), d2 (0.67143), and d3 (0.40870), with nDCG@3 = 1.0, Recall@2 = 1.0, MRR = 1.0, MAP = 1.0.
5. **Check yourself:** Check BM25 score calculation in src/ir/bm25.py lines 86-90 and stopword list in src/ir/tokenizer.py.
6. **Assumptions:** Default BM25 hyperparameters k1 = 1.5, b = 0.75; 3-point relevance scale (0, 1, 2).
7. **Questions:** How does b = 0 affect document length normalization? (Disables length penalty).

---

## Step 3: Working Agreement and Learning Log Setup

1. **What I did:** Added the Working Agreement section to AGENTS.md specifying the step-by-step reporting contract. Created docs/LEARNING_LOG.md with a short header and backfilled concise step reports.
2. **Files created or changed:** AGENTS.md (added Working agreement), docs/LEARNING_LOG.md (created learning log).
3. **How it works:** The working agreement establishes a structured peer review cadence so every incremental change is explained, verified, and audited without rush.
4. **How I verified it:** Checked git diff on AGENTS.md and verified docs/LEARNING_LOG.md formatting with pytest passing.
5. **Check yourself:** Review git diff on AGENTS.md to ensure no existing rules were overwritten.
6. **Assumptions:** Log is kept updated sequentially with shortened summaries.
7. **Questions:** Why is having a strict step report useful when building IR systems? (Ensures every formula and score is verified before building on top).

---

## Step 4: eCFR Crawler for Parts 801 and 830

1. **What I did:** Verified official eCFR Versioner API endpoints. Built src/crawl/ecfr.py with rate limiting, retries, and section extraction, and fetched 21 CFR Part 801 and Part 830 saving raw XML to data/raw/.
2. **Files created or changed:** src/crawl/ecfr.py (API crawler and parser), tests/test_ecfr.py (unit tests for parser and session), data/raw/ecfr_title21_part801.xml (raw XML), data/raw/ecfr_title21_part830.xml (raw XML).
3. **How it works:** First resolves the title snapshot date from the titles endpoint, then downloads full XML for each Part, retrying transient failures and throttling requests.
4. **How I verified it:** Ran pytest (15 passed) and `python -m src.crawl.ecfr` fetching 38 sections for Part 801 and 20 sections for Part 830 (58 total).
5. **Check yourself:** Inspect data/raw/ to verify both XML files exist and review tests/test_ecfr.py for mock fixture testing.
6. **Assumptions:** Official API requires specific date format (YYYY-MM-DD) obtained from titles.json rather than literal "current".
7. **Questions:** Why should a crawler query titles.json for the active amendment date instead of hardcoding today's calendar date? (Regulations are published up to specific issue dates).

---

## Step 5: Chunking Pipeline and regs.jsonl

1. **What I did:** Built src/crawl/chunk.py to turn the crawled regulatory text into Chunk objects (see src/common/schemas.py), splitting long sections into ~200-word windows with 25-word overlap, computing SHA-256 hashes, and writing data/processed/regs.jsonl.
2. **Files created or changed:** src/crawl/chunk.py (chunking and hashing logic), tests/test_chunk.py (offline chunking tests), data/processed/regs.jsonl (150 processed chunks).
3. **How it works:** Short sections become a single chunk; long sections use sliding word windows with overlap so regulatory context is preserved across chunk boundaries.
4. **How I verified it:** Ran pytest (21 passed) and `python -m src.crawl.chunk`, outputting 150 chunks with an average length of 162.7 words.
5. **Check yourself:** Inspect data/processed/regs.jsonl for schema conformity and tests/test_chunk.py for overlapping window assertions.
6. **Assumptions:** Configured window size to 200 words with 25 words overlap; source set to "FDA" and module to "device".
7. **Questions:** Why is an overlap between consecutive text chunks useful in search? (Prevents critical query phrases from being severed across chunk boundaries).

---

## Step 6: Interactive BM25 Search CLI

1. **What I did:** Built src/ir/search.py providing a command-line interface to index data/processed/regs.jsonl and search using BM25. Added unit tests in tests/test_search.py and executed 5 domain queries across device labeling and identification regulations.
2. **Files created or changed:** src/ir/search.py (search CLI and result formatting), tests/test_search.py (unit tests for search and formatting).
3. **How it works:** Loads processed chunks from JSONL, builds an inverted index, scores candidate passages using BM25, and outputs the top 5 ranked chunks with section IDs and titles.
4. **How I verified it:** Ran pytest (22 passed) and executed `python -m src.ir.search` on 5 queries ("unique device identifier on label", "sterile symbol", "expiration date", "prescription use only statement", "manufacturer name and address"), successfully retrieving relevant sections like 801.40, 801.15, 801.18, 801.109, and 801.1.
5. **Check yourself:** Run `python -m src.ir.search "sterile symbol"` in your terminal to see the ranked output format.
6. **Assumptions:** Default k is 5 and default corpus is data/processed/regs.jsonl.
7. **Questions:** Why does the query "manufacturer name and address" rank section 801.1 at rank 1 with high score? (Because 801.1 contains all matching terms and has high term saturation for manufacturer).

---

## Step 7: Corpus Expansion to 11 Parts and Configurable Chunker

1. **What I did:** Expanded the regulatory corpus from 2 parts (801, 830) to 11 parts (801, 803, 806, 807, 809, 812, 820, 830, 201, 208, 211) covering medical devices and human medicines. Verified all parts against the official eCFR API. Parameterized the chunker module ("device" vs "medicine") and source, filtered out short sections under 5 words (skipping 5 reserved sections), rebuilt data/processed/regs.jsonl to 903 chunks, and logged distribution metrics.
2. **Files created or changed:** src/crawl/ecfr.py (PART_COVERAGE, default parts lists), src/crawl/chunk.py (module and source parameterization, min_words filter, distribution reporting), tests/test_chunk.py (medicine module test and min_words tests), data/processed/regs.jsonl (903 rebuilt chunks), .gitignore (added .venv312/ and *.npy).
3. **How it works:** Chunker extracts the part number from each input file name and looks up its target module in PART_MODULE: device parts map to module="device" while drug parts (201, 208, 211) map to module="medicine". Chunker checks word count and skips any section under 5 words (e.g. [Reserved]). Remaining sections are chunked into 200-word windows with 25-word overlap.
4. **How I verified it:** Ran pytest (25 passed) and executed `python -m src.crawl.chunk`, outputting 903 chunks across 11 parts (average length 167.9 words) after skipping 5 reserved sections.
5. **Check yourself:** Inspect min_words filtering in src/crawl/chunk.py and line count `(Get-Content data\processed\regs.jsonl).Count` yielding 903.
6. **Assumptions:** Empty or reserved sections containing only [Reserved] carry no regulatory value and should be omitted; 200-word window with 25-word overlap remains appropriate across all parts.
7. **Questions:** How does filtering out 5 reserved sections improve the quality and precision of the BM25 inverted index?

---

## Step 8: Dense Retrieval with Embeddings, FAISS, and Caching

1. **What I did:** Implemented and reviewed dense semantic retrieval in `src/ir/dense.py` using `BAAI/bge-small-en-v1.5` embeddings and a FAISS `IndexFlatIP` index behind the `Retriever` interface. Added disk caching keyed by corpus SHA-256 fingerprint, fixed `cache_dir=None` handling and instance-level model caching, updated `.gitignore` for `dense_cache_*` files, and ran side-by-side comparisons against BM25 on the 5 Step 6 benchmark queries via `src/ir/query_compare.py`.
2. **Files created or changed:** `src/ir/dense.py` (fixed `cache_dir=None` bug, reused loaded model across searches), `src/ir/query_compare.py` (5-query Step 6 comparison CLI), `src/ir/search.py` (`--system dense` option), `.gitignore` (ignored `data/processed/dense_cache_*`), `tests/test_dense.py` and `tests/test_search.py` (cache, JSONL loader, and comparison tests).
3. **How it works:** Sentences are mapped to 384-dimensional float vectors capturing semantic meaning, L2-normalised to unit length so inner product equals cosine similarity, and indexed in FAISS `IndexFlatIP` for exact nearest-neighbour search. Embeddings and chunk IDs are cached to `data/processed/` as `.npy` and `.json`.
4. **How I verified it:** Ran `ruff check` (All checks passed), `pytest tests -q` (36 passed in 126.60s), `python -m src.ir.query_compare`, and `python -m src.ir.search "sterile symbol" --system dense -k 3` in `.venv312` (Python 3.12.10).
5. **Check yourself:** Inspect `_corpus_fingerprint`, `DenseRetriever.__init__` normalization, and `from_chunks` cache guard in `src/ir/dense.py`, plus `data/processed/dense_cache_*` exclusion in `git status`.
6. **Assumptions:** Used `BAAI/bge-small-en-v1.5` (384-dim, ~134.5 MB snapshot) symmetrically without query instruction prefixes; `IndexFlatIP` exact scan is fast enough for 903 chunks.
7. **Questions:** (1) Why does editing chunk text without changing `chunk_id` fail to invalidate the current fingerprint cache? (2) Why did Dense catch `211.137_c1` ("Expiration dating") while drifting to `806.10_c3` on manufacturer address?

---

## Step 9: Hybrid Retrieval with Reciprocal Rank Fusion (plus Pre-Step-9 Fixes)

1. **What I did:** Pushed pending commits to GitHub, fixed CI ruff lint errors and added `numpy`/`faiss-cpu` with `-m "not slow"` to `.github/workflows/ci.yml`, updated `_corpus_fingerprint` to hash `chunk_id:content_hash` pairs, injected `FakeTransformer` into fast dense/hybrid unit tests while marking 1 real-model test `slow`, added `--module device|medicine|all` pre-ranking filters to `search.py` and `query_compare.py`, walked through `src/ir/hybrid.py` and verified `build_systems` in `src/ir/eval.py` registers `tfidf`, `bm25`, `dense`, and `hybrid`, and ran all 4 systems on the 5 benchmark queries.
2. **Files created or changed:** `src/ir/dense.py` (content-hash fingerprint + `model` param), `src/ir/search.py` and `src/ir/query_compare.py` (`--module` pre-ranking filter), `src/ir/hybrid.py` (fixed docstring RRF arithmetic typo), `src/crawl/chunk.py` and `.github/workflows/ci.yml` (CI ruff/test fixes), `pyproject.toml` (`slow` marker), `tests/test_dense.py`, `tests/test_hybrid.py`, `tests/test_search.py` (fake encoder, fingerprint invalidation, module filter tests).
3. **How it works:** RRF combines BM25 and Dense rankings without calibrating raw scores by summing `1 / (k + rank)` with `k=60` over an over-fetched top `max(k*3, 50)` list from each retriever. Documents appearing high in both ranked lists overtake single-list winners.
4. **How I verified it:** Ran `ruff check src tests` (All checks passed), `pytest tests -q -m "not slow"` (39 passed, 1 deselected), `python -m src.ir.query_compare --systems bm25 dense --module device`, and `python -m src.ir.query_compare --systems tfidf bm25 dense hybrid`.
5. **Check yourself:** Inspect `_corpus_fingerprint` in `src/ir/dense.py`, `--module` filtering in `src/ir/search.py` and `src/ir/query_compare.py`, and `_rrf_score`/`search` in `src/ir/hybrid.py`.
6. **Assumptions:** Equal RRF weights (`bm25_weight=1.0`, `dense_weight=1.0`, `k=60`) and over-fetch window `max(k*3, 50)`; no full-corpus qrels exist yet, so quality comparison on the 5 queries is qualitative.
7. **Questions:** Ask without answers in Step Report.

---

## Step 10: Queries, Pooling, Qrels Tooling, and Section-Level Eval

1. **What I did:** Updated `src/ir/eval.py` so `build_systems` preserves `Chunk.hash` to reuse the disk embedding cache, added `--module device|medicine|all` filtering and `--section-level` max-score aggregation, created `data/eval/queries_t1.tsv` with 10 placeholder queries, and wrote `src/ir/qrels_tool.py` (`pool`, `to-qrels`, `kappa`) plus tests. Ran pooling over all 4 systems to produce `data/eval/pool_t1.csv` with empty `grade` values.
2. **Files created or changed:** `src/ir/eval.py` (cache hash passthrough, `--module`, `--section-level`, UTF-8), `data/eval/queries_t1.tsv` (10 placeholder queries), `src/ir/qrels_tool.py` (pooling, TREC qrels export, Cohen's kappa), `data/eval/pool_t1.csv` (184 ungraded pooled rows), `tests/test_eval.py` and `tests/test_qrels_tool.py` (unit tests).
3. **How it works:** Pooling takes top-10 candidates per system within each query's module, deduplicates by `chunk_id`, and shuffles with a deterministic seed so annotators judge 184 unique passages without knowing which system retrieved them. `to-qrels` writes graded `{0, 1, 2}` rows to TREC format, `kappa` measures inter-annotator agreement `(po - pe) / (1 - pe)`, and section-level eval aggregates chunk scores and qrels by `max`.
4. **How I verified it:** Ran `ruff check src tests` (All checks passed), `pytest tests -q -m "not slow"` (46 passed, 1 deselected), `python -m src.ir.eval --corpus data/processed/sample_regs.jsonl --queries data/eval/queries_sample.tsv --qrels data/eval/qrels_sample.tsv --out results/sample_results.md --no-dense --section-level`, and `python -m src.ir.qrels_tool pool --queries data/eval/queries_t1.tsv --out data/eval/pool_t1.csv` (184 rows across 10 queries, device cache reused).
5. **Check yourself:** Inspect `data/eval/queries_t1.tsv`, `data/eval/pool_t1.csv` (verify empty `grade` column), `src/ir/qrels_tool.py`, and `aggregate_hits_by_section` in `src/ir/eval.py`.
6. **Assumptions:** `pool_t1.csv` uses placeholder queries and leaves `grade` empty so no synthetic relevance labels are fabricated; `Section-level` fetch depth multiplies `max(k_ndcg, k_recall)` by 5 before max-pooling to prevent multi-chunk sections from collapsing top-k depth.
7. **Questions:** Asked without answers in Step Report.





---

## Step 10b: Pool Check and Separate Reporting of no_answer Queries and Corpus Gaps

1. **What I did:** Checked that `data/eval/pool_t1.csv` already covers all 62 queries in `data/eval/queries_t1.tsv` (1269 rows: 908 device, 361 medicine, 0 grades filled), so no re-pooling was needed. Changed `src/ir/eval.py` so the main averages leave out `no_answer` queries and answerable queries with no document graded 1 or higher (corpus gaps). Both groups are now reported in their own sections, and every table header shows how many queries it covers.
2. **Files created or changed:** `src/ir/eval.py` (new `split_no_answer`, `find_corpus_gaps`, `mean_top1_score`, `evaluate_no_answer`, `no_answer_to_markdown`, new output sections, no crash when nothing is graded yet), `tests/test_eval.py` (5 new tests, CLI test extended), `docs/QRELS_GUIDE.md` (how no_answer queries and gaps are reported), `CLAUDE.md` (current state).
3. **How it works:** If 4 answerable queries score nDCG 1.0 and 1 no_answer query scores 0.0, the old average was 0.8, which punishes systems for a question with no answer. Now the average is 1.0 over 4 queries. The no_answer table separately shows whether a grade 1 passage (related, fine) or a grade 2 passage (states the rule, so the label may be wrong) reached the top 10.
4. **How I verified it:** `ruff check src tests` (All checks passed), `python -m pytest -q -m "not slow"` (51 passed, 1 deselected), plus a smoke run of eval on the real ungraded pool (0 queries evaluated in every table, no crash).
5. **Check yourself:** The `queries = {...}` filter in `main()`, the `any(g >= 2 ...)` line in `evaluate_no_answer`, and `find_corpus_gaps` treating ungraded queries as not gaps.
6. **Assumptions:** no_answer metrics use chunk level and k=10. Mean top-1 scores are only comparable within one system.
7. **Questions:** Asked without answers in the Step Report.

---

## Step 11a: Rules and Prompt for LLM Relevance Grading

1. **What I did:** Restored the full Step Report (items 1 to 6, no quiz) in `CLAUDE.md` and `AGENTS.md`, and replaced the "humans only" grading rule: LLM grades are allowed only in separate `_llm` files, and the agent never writes to the human `grade` column, `pool_t1.csv` or the human sample. Created `docs/LLM_GRADER_PROMPT.md` with the exact grader prompt, procedure and an empty batch log.
2. **Files created or changed:** `CLAUDE.md` and `AGENTS.md` (report format, grading rules, state and next steps), `docs/LLM_GRADER_PROMPT.md` (new), `docs/LEARNING_LOG.md` (this entry).
3. **How it works:** One fixed prompt plus fixed, seeded batches makes the LLM grading auditable. Keeping LLM grades in their own files means human and LLM grades can later be compared (kappa, system ranking) instead of being mixed.
4. **How I verified it:** No code changed. Searched the changed docs for em dashes (none found) and ran the fast tests and lint (results in the Step Report).
5. **Check yourself:** The grader prompt text in `docs/LLM_GRADER_PROMPT.md`, the two new grading rules in `CLAUDE.md`, and the restored report list in `AGENTS.md`.
6. **Assumptions:** The grader output format (`chunk_id<TAB>grade`) is fixed now and Step 11b's `record` command will read it. The batch log is empty because nothing has been graded.

---

## Step 11b: LLM Grading Batch Tool

1. **What I did:** Added `src/ir/llm_grade_tool.py` with `next-batch` (writes the next about-40-row batch of whole, ungraded queries, human-sample queries first, shuffled with seed `42:<batch>`), `record` (checks the grader output covers exactly that batch with grades 0/1/2, then appends it to `data/eval/pool_t1_llm.csv` with batch, model id and date) and `to-qrels`. The `sample` code is in the same file and is run in Step 11c.
2. **Files created or changed:** `src/ir/llm_grade_tool.py` (new tool), `tests/test_llm_grade_tool.py` (12 tests), `docs/LLM_GRADER_PROMPT.md` (row id output format and commands).
3. **How it works:** Rows are identified by `qid:chunk_id` because 253 passages appear under more than one query. The tool reads only qid, query, chunk_id and text from the pool, never the human grade or section.
4. **How I verified it:** `python -m pytest -q -m "not slow"` (63 passed, 1 deselected), `ruff check src tests` (All checks passed).
5. **Check yourself:** `build_next_batch` (whole queries, max rows), `check_batch_grades` (exact row match), `load_pool_rows` (which columns are read).
6. **Assumptions:** `next-batch` refuses to run until the human sample exists, so sample queries are always graded first. `--model` has no default, so the model id is never guessed.
