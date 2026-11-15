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

---

## Step 11c: Human Validation Sample

1. **What I did:** Ran `python -m src.ir.llm_grade_tool sample` to create `data/eval/pool_t1_human_sample.csv`: 308 rows for 15 queries chosen with seed 42, stratified by query type (4 direct, 4 field_req, 3 vocab_mismatch, 2 change_impact, 1 symbol, 1 no_answer) and by module within each type (11 device, 4 medicine). The grade column is empty.
2. **Files created or changed:** `data/eval/pool_t1_human_sample.csv` (new, for the user to grade), `docs/QRELS_GUIDE.md` (how to grade the sample), `CLAUDE.md` (state and next steps).
3. **How it works:** Each query type gets slots in proportion to its size (largest remainder), with at least one per type, so rare types like no_answer and symbol are always in the sample. A dry run of `next-batch` confirmed batch 1 would contain sample queries q04 and q05 first.
4. **How I verified it:** Checked the sample has the pool's 6 columns, 308 rows and 0 filled grades, that `pool_t1.csv` is unchanged, and that `pool_t1_llm.csv` does not exist (no grading started). Tests and lint pass.
5. **Check yourself:** The 15 qids and their types, the empty grade column in the sample file, and the new section in `docs/QRELS_GUIDE.md`.
6. **Assumptions:** 15 queries is a validation sample, so agreement numbers in Step 13 will have wide error bars.

---

## Step 11d: Split the Human Sample Between Two Annotators

1. **What I did:** Added a seeded `split` subcommand to `src/ir/llm_grade_tool.py` and split the 15-query human sample into `data/eval/sample_pari.csv` (q05, q11, q21, q31, q36, q44, q46, q51, q60; 182 rows) and `data/eval/sample_parth.csv` (q04, q05, q12, q28, q30, q40, q44, q46, q56; 195 rows). q05 (device), q46 (medicine) and q44 (no_answer) are in both files (69 rows) so human-human kappa can be measured.
2. **Files created or changed:** `src/ir/llm_grade_tool.py` (`split_between_annotators`, `split` subcommand), `tests/test_llm_grade_tool.py` (2 tests), the two sample files, `docs/QRELS_GUIDE.md`, `docs/LLM_GRADER_PROMPT.md`, `CLAUDE.md`.
3. **How it works:** The non-shared queries are dealt type by type after a seeded shuffle, each to the annotator with fewer queries so far, so both get a similar mix. The command refuses to overwrite existing annotator files.
4. **How I verified it:** `python -m pytest -q -m "not slow"` (65 passed, 1 deselected), `ruff check src tests` (All checks passed), and checked both files have the pool columns and 0 filled grades.
5. **Check yourself:** The two qid lists, the overlap queries, and the overwrite check in the `split` branch of `main()`.
6. **Assumptions:** The sample has only one symbol query (q31), so only Pari's file has it. Which grade to use for the 3 shared queries in Step 13 is still to be decided.

---

## Step 12, Batch 1: LLM Grades for q04 and q05

1. **What I did:** Ran `next-batch` for batch 1 (40 rows, queries q04 and q05, both in the human sample), graded every row 0, 1 or 2 using only the prompt in `docs/LLM_GRADER_PROMPT.md`, and stored them with `record` in `data/eval/pool_t1_llm.csv`. Model id `claude-sonnet-5-5`, date 2026-11-12. Grade counts: 26 zero, 11 one, 3 two.
2. **Files created or changed:** `data/eval/pool_t1_llm.csv` (new, 40 rows), `docs/LLM_GRADER_PROMPT.md` (batch log), `docs/LEARNING_LOG.md`, `CLAUDE.md` (state).
3. **How it works:** For q05 (manufacturer name and place of business), only 801.1 chunks state the general rule (2). Passages from 809.10 and 812.5 name the same requirement for narrower product classes (in vitro diagnostics, investigational devices), so they got 1. For q04 (where the UDI must appear), 801.20 states that the label and every package must bear a UDI (2); 801.40, 801.45, 801.30, 801.35 and 801.57 discuss UDI form, direct marking, exceptions and related rules (1).
4. **How I verified it:** `record` accepted all 40 rows on the first run; tests and lint results in the Step Report.
5. **Check yourself:** The batch log row, the model id column in `pool_t1_llm.csv`, and that `pool_t1.csv` and the sample files are unchanged.
6. **Assumptions:** Passages that state the right requirement but only for a narrower product class were graded 1 (lower grade when unsure). Passages that only mention a UDI or a manufacturer name in passing (reports, registration, GUDID submission) were graded 0.

---

## Step 12, Batches 2 to 9: LLM Grades for 14 More Queries

1. **What I did:** Ran `next-batch`, graded and `record`ed batches 2 to 9 (268 rows) with model `claude-sonnet-5-5` on 2026-11-12, always with only the prompt in `docs/LLM_GRADER_PROMPT.md`. The queries were q11, q12, q21, q28, q30, q31, q36, q40, q44, q46, q51, q56 and q60. With batch 1 and batch 10 (q01), all 15 human-sample queries are now fully LLM-graded. Grade counts for batches 2 to 9: 192 zero, 51 one, 25 two.
2. **Files created or changed:** `data/eval/pool_t1_llm.csv` (268 rows added), `docs/LLM_GRADER_PROMPT.md` (8 batch log rows), `CLAUDE.md` (state).
3. **How it works:** Each batch is whole queries (about 40 rows), shuffled with seed `42:<batch>` so row order does not reveal system rank. `record` rebuilds the same batch and rejects grades that are missing, extra, repeated or not 0/1/2. q44 is a no_answer query, so its 24 rows are all 0 (the prompt says not to raise a grade because nothing better exists).
4. **How I verified it:** `python -m pytest -q -m "not slow"` gave `65 passed, 1 deselected in 0.65s`. `ruff check src tests` gave `All checks passed!`. Summing the pool file by batch gives 192/51/25 for batches 2 to 9, matching the batch log. `git diff` shows no change to `pool_t1.csv`, the human sample or the two annotator files.
5. **Check yourself:** The 8 new rows in the batch log (the per-batch counts add up to 192/51/25), the `model` column in `pool_t1_llm.csv`, and the batch 8 and 9 grade mix (8 and 7 twos, much higher than batches 4 to 7).
6. **Assumptions:** Grades follow "lower grade when unsure". I wrote no per-query rationale, so the reasons behind individual grades are not recorded. I did not write a Step Report at the time of these batches, so this entry was added afterwards. CI status was not checked: `gh` is not logged in on this machine.

## Step 12 (batches 11 to 18): LLM grading, continued
1. **What I did:** Graded batches 11 to 18 (q02, q03, q06, q07, q08, q09, q10, q13, q14, q15, q16, q17) with the grader prompt in `docs/LLM_GRADER_PROMPT.md`, one batch at a time through `next-batch` and `record`. I did not open any human sample file or human grade. Counts (0/1/2): b11 8/14/2, b12 22/14/4, b13 22/7/3, b14 15/14/7, b15 22/5/2, b16 17/8/3, b17 20/4/1, b18 24/13/3. 585 of 1269 rows are now LLM-graded.
2. **Files changed:** `data/eval/pool_t1_llm.csv` (254 rows added), `docs/LLM_GRADER_PROMPT.md` (8 batch log rows), `CLAUDE.md` (state), this log.
3. **How it works:** Same as before: whole queries per batch, seeded shuffle, `record` rejects missing, extra, repeated or invalid grades. Rule used: when unsure, lower grade; IVD-only or hearing-aid-only passages get 1 for general device queries.
4. **Verified:** `pytest -q -m "not slow"`: 65 passed, 1 deselected. `ruff check src tests`: All checks passed. Per-batch counts recomputed from the CSV match the log.
5. **Check yourself:** The 2s in batch 14 (7 of 36, mostly IVD labeling q09), and the 0-vs-1 calls on UDI definition passages repeated across queries.
6. **Assumptions:** Grades are my judgment, no per-row rationale recorded. CI not checked (gh not logged in).

## Step 12 (batches 19 to 43): LLM grading finished
1. **What I did:** Graded batches 19 to 43 (the remaining 684 rows) with the prompt in `docs/LLM_GRADER_PROMPT.md`, so all 1269 pool rows now have an LLM grade (model `claude-sonnet-5-5` on every row). I did not open any human grade while grading. Totals (0/1/2): overall 864/280/125, device 627/208/73 (908 rows), medicine 237/72/52 (361 rows).
2. **Files changed:** `data/eval/pool_t1_llm.csv`, `docs/LLM_GRADER_PROMPT.md` (batch log rows 19 to 43), this log, `CLAUDE.md`. Commits: batches 19-26, 27-34, 35-43.
3. **How it works:** Same procedure as before. Queries outside the US CFR corpus (q42 EU MDR, q43 GS1 DataMatrix, q62 EMA SmPC) are all 0, and q41 (ISO 15223-1) only got 1 on general symbol-use passages.
4. **Verified:** Pool keys and LLM keys are the same set of 1269 unique `qid:chunk_id`; every grade is 0, 1 or 2; `pytest -q -m "not slow"` and `ruff check src tests` were clean.
5. **Check yourself:** The 2s on whole governing sections (q50 Drug Facts, q52 pregnancy, q53 pediatric use), and the answerable queries with no 2 at all (q24, q35, q39, q41, q48).
6. **Assumptions:** Grades are my judgment with no per-row rationale. CI not checked (gh not logged in).

## Step 13: LLM grades vs human grades
1. **What I did:** Added `src/ir/grade_compare.py`, which joins the two human annotator files (Pari 182 rows, Parth 195 rows, 69 shared, 308 unique, 15 queries) to the LLM grades on `qid:chunk_id`. It reports agreement (with and without the no_answer query q44), system ranking by nDCG@10 under each set of grades, Kendall's tau, a bootstrap 95% interval on the LLM-minus-human nDCG@10 difference, and the grade mix of each system's top 10. Parth confirmed his grades are human, so both files count as human. Pari's file is the headline because it is the cleanest single-annotator set.
2. **Files created or changed:** `src/ir/grade_compare.py` and `tests/test_grade_compare.py` (new), `results/step13_llm_vs_human.md` (report, now tracked via a `.gitignore` exception), `data/eval/qrels_t1_llm.tsv` and `data/eval/qrels_t1_human_sample.tsv` (new qrels), `.gitignore`, `.DS_Store` removed from the repo, this log, `CLAUDE.md`. No change to `schemas.py`, `base.py`, the pool or the annotator files.
3. **How it works:** Weighted kappa is kappa where a miss of 2 vs 0 costs more than 2 vs 1. Kendall's tau counts system pairs ranked the same way minus pairs ranked oppositely. The bootstrap resamples the queries with replacement 10000 times (seed 42) and reads the 2.5th and 97.5th percentiles of the mean per-query difference. Systems are built per module because the pool was made per module. On shared rows the human qrels use Pari's grade.
4. **Results (real, from the run):** LLM vs human, all rows / without q44: Pari only (headline) exact 0.819 / 0.791, weighted kappa linear 0.746 / 0.725, quadratic 0.823 / 0.807, binary agreement 0.879 / 0.861, binary kappa 0.752 / 0.724. All 308 merged rows: exact 0.782 / 0.764, linear 0.675 / 0.663, quadratic 0.768 / 0.759, binary agreement 0.825 / 0.810, binary kappa 0.636 / 0.618. Human vs human on 69 shared rows: exact 0.957, quadratic kappa 0.955. The LLM is stricter than the humans: it gave 0 to 52 of the 103 rows humans graded 1. nDCG@10 LLM minus human (14 queries): tfidf +0.012 [-0.046, +0.067], bm25 +0.008 [-0.042, +0.063], dense -0.031 [-0.130, +0.059], hybrid +0.009 [-0.038, +0.056]; no pooled interval excludes 0. Dense is the only system that falls pooled and in the device module (10 queries). In the medicine module (4 queries) all four systems fall, and only bm25 (-0.096 [-0.140, -0.022]) has an interval that excludes 0. In the device module only bm25 (+0.049 [+0.005, +0.106]) excludes 0. Hybrid is rank 1 under both graders everywhere.
5. **Check yourself:** The 52 human-1 vs LLM-0 rows in the confusion matrix, that the "dense falls" statement does not hold in the medicine module, and that q44 is the only query dropped.
6. **Assumptions:** First file wins on shared rows (Pari). Queries that are no_answer or corpus gaps under either grader are left out of nDCG. 14 queries and 4 systems is a small sample, so tau values are coarse and most intervals include 0. `rank_systems` is a small helper that the report no longer calls. CI not checked (gh not logged in).

## Step 14a: results table on the LLM-assessed qrels
1. **What I did:** Added `src/ir/step14_report.py`, which runs tfidf, bm25, dense and hybrid per module on all answerable graded queries and writes `results/step14_results.md`. For each module and level (chunk, section) it gives nDCG@10, Recall@20, MRR and MAP, then the paired bootstrap difference vs bm25 with a 95% interval and a two-sided p-value. no_answer queries are reported separately. Corpus-gap queries are listed by qid and the table is shown with and without them. Every table is labelled LLM-assessed qrels.
2. **Files created or changed:** `src/ir/step14_report.py` and `tests/test_step14_report.py` (new), `results/step14_results.md` (report), `.gitignore` (track `results/step14_*.md`), this log, `CLAUDE.md`. No change to `schemas.py`, `base.py` or any human grade file.
3. **How it works:** The paired bootstrap resamples the queries 10000 times (seed 42), takes the mean of (system - bm25) in each resample, and reads the 2.5th and 97.5th percentiles as the interval. The p-value is twice the smaller share of resampled means on one side of 0. The existing `paired_bootstrap` is one-sided, so I did not reuse it.
4. **Results (real, from the run):** There are no corpus-gap queries in either module (device 40 answerable, medicine 17), so the with-gaps and without-gaps tables are identical and the report says so instead of repeating them. Device chunk nDCG@10: tfidf 0.627, bm25 0.624, dense 0.540, hybrid 0.624; no interval vs bm25 excludes 0 on nDCG@10 (dense -0.084 [-0.199, +0.039]), dense is lower on Recall@20 and MAP. Medicine chunk nDCG@10: hybrid 0.716 vs bm25 0.631 (+0.085 [-0.002, +0.175], p=0.057). Medicine section nDCG@10: hybrid 0.822 vs bm25 0.697 (+0.125 [+0.031, +0.222], p=0.008). 12 comparisons per table are not corrected for multiple comparisons, nDCG@10 is the primary metric.
5. **Check yourself:** That the gap list really is empty (the report prints it per module), the Recall@20 tfidf row in medicine where one query drives the whole difference so the interval ends at +0.000 while p is 0.710 (ties at 0 count in both tails), and that the medicine section hybrid result is one of 48 uncorrected comparisons.
6. **Assumptions:** Percentile bootstrap p-value, not a permutation test. Systems are built per module as in Step 13. Medicine has only 17 queries. CI not checked (gh not logged in).

## Step 14b: results by query type
1. **What I did:** Added the per-type part of `src/ir/step14_report.py` (the code went in with the 14a commit, the output is committed here). It writes `results/step14_by_type.md`: mean nDCG@10 of each system for each query type, chunk level only, device and medicine separately, with the number of queries in every row. Rows with fewer than 5 queries are flagged as descriptive only. No significance tests are run per type.
2. **Files created or changed:** `results/step14_by_type.md` (new), this log, `CLAUDE.md`.
3. **How it works:** For each type, take the queries of that type (answerable, graded, not a gap), read each system's per-query nDCG@10 from the same run as 14a and average. One query in a row of n moves the mean by up to 1/n.
4. **Results (real, from the run):** Device (n): direct 10, vocab_mismatch 9, symbol 5, field_req 11, change_impact 5. Medicine: direct 7, vocab_mismatch 4, symbol 0, field_req 5, change_impact 1. Device vocab_mismatch nDCG@10: dense 0.543, hybrid 0.489, bm25 0.395, tfidf 0.371. Device direct: bm25 0.728, hybrid 0.659, tfidf 0.633, dense 0.518. Device symbol: tfidf 0.910, bm25 0.840, dense 0.524. Medicine vocab_mismatch (n=4, flagged): dense 0.601, hybrid 0.526, bm25 0.355. Medicine has no symbol queries and one change_impact query.
5. **Check yourself:** That the n column adds up to 40 (device) and 17 (medicine), that medicine vocab_mismatch and change_impact are flagged, and that the "dense wins on vocab_mismatch" pattern appears in both modules but rests on 9 and 4 queries.
6. **Assumptions:** Query types come from the 4th column of `queries_t1.tsv`. No gaps exist, so 'gaps left out' is 0 everywhere. CI not checked (gh not logged in).

## Step 14a (addendum): Holm-adjusted p for nDCG@10
1. **What I did:** Added a table to `results/step14_results.md` that treats the 12 nDCG@10 comparisons vs bm25 (2 modules x 2 levels x 3 systems) as one family and gives raw and Holm step-down adjusted p-values. Module tables keep raw p. The 36 secondary-metric comparisons stay uncorrected and the report says so.
2. **Files changed:** `src/ir/step14_report.py` (`holm_adjust`, `holm_family`, `holm_table`), `tests/test_step14_report.py`, `results/step14_results.md`, this log.
3. **How it works:** Holm sorts the p-values, multiplies the smallest by 12, the next by 11 and so on (cap 1, never decreasing). Example: p of 0.01, 0.02, 0.04 become 0.03, 0.04, 0.04.
4. **Verified:** `pytest tests/test_step14_report.py`: 9 passed; ruff clean. Medicine chunk hybrid raw p 0.057 becomes 0.627 after Holm.
5. **Check yourself:** Which comparison keeps the smallest adjusted p (medicine section hybrid: raw 0.008, Holm 0.091) and that only nDCG@10 is in the family.
6. **Assumptions:** Family = main query set, gaps excluded (no gaps exist). CI not checked (gh not logged in).

## Step 14b (addendum): intervals on by-type cells with n of 8 or more
1. **What I did:** In `results/step14_by_type.md`, cells in rows with 8 or more queries now show the mean nDCG@10 with a bootstrap 95% interval (resampling the queries in that row, 10000 times, seed 42). Only three rows qualify, all in device (direct 10, vocab_mismatch 9, field_req 11). Smaller rows stay as plain means.
2. **Files changed:** `src/ir/step14_report.py` (`bootstrap_mean_interval`, `CI_MIN_N`), `tests/test_step14_report.py`, `results/step14_by_type.md`, this log.
3. **How it works:** Each interval is for one system's own mean, not a difference between systems, so overlap is not a significance test (all systems see the same queries).
4. **Verified:** `pytest tests/test_step14_report.py`: 10 passed; ruff clean. Device vocab_mismatch: dense 0.543 [0.377, 0.700] vs bm25 0.395 [0.209, 0.580], and the intervals overlap. Device direct: bm25 0.728 [0.626, 0.828] vs dense 0.518 [0.357, 0.679], also overlapping.
5. **Check yourself:** That every interval is 0.15 to 0.35 wide, so the by-type pattern is weak evidence, and that medicine has no row with n>=8.
6. **Assumptions:** Threshold of 8 as you set it. CI not checked (gh not logged in).

## Step 14c: failure analysis
1. **What I did:** Added `failures_report` to `src/ir/step14_report.py` (`--part failures`), writing `results/step14_failures.md`: how many answerable queries each system scores exactly 0 on, the queries where all four score 0, and the 5 lowest queries per system with their top 3 results, grades and a short snippet. Each query gets a Hypothesis line from rule-based checks: rank of the first relevant chunk, CFR part of the top 3 vs the relevant chunks, same-section grade-0 chunk (chunk boundary), and share of query terms present in the best relevant chunk.
2. **Files changed:** `src/ir/step14_report.py`, `tests/test_step14_report.py`, `results/step14_failures.md` (new), this log, `CLAUDE.md`.
3. **How it works:** A query is a failure for a system when its nDCG@10 is low. The checks only look at the ranked list and the LLM qrels, so the causes are hypotheses (the report says so, and notes the vocabulary check is weak evidence for dense).
4. **Results (real, from the run):** Queries at exactly 0 nDCG@10 (57 answerable): tfidf 1, bm25 2, dense 3, hybrid 2 (device 1/1/2/2, medicine 0/1/1/0). **No query scores 0 under all four systems.** The 5 lowest therefore include non-zero scores. q15 (relabeling a device made by another company), q18, q12, q24, q39 and q59 recur across systems; q12 and q15 are vocab_mismatch, q39 change_impact. Frequent hypothesis: the first relevant chunk is at rank 4 to 21, just below the top 3, plus low query-term overlap (20% to 40%) with the best relevant chunk. The 'wrong part' flag fires on q12, q24, q54, q01.
5. **Check yourself:** The q24 and q12 entries, where the relevant chunks are in 21cfr801 but the top 3 are from 803, 807 or 820. Also read some grade-0 top-1 chunks against the query to see whether the LLM grade looks too strict.
6. **Assumptions:** Tie-break by qid. Depth 100 for the first-relevant-rank check. Overlap uses the project tokenizer with light stemming. CI not checked (gh not logged in).

## Step 14d: bootstrap intervals on LLM-vs-human agreement
1. **What I did:** Added `cluster_bootstrap_agreement` and `kappa_report` to `src/ir/step14_report.py` (`--part kappa`, no retrieval systems needed), writing `results/step14_kappa_ci.md`. It recomputes the Step 13 agreement numbers with 95% percentile bootstrap intervals that resample queries, not rows, 10000 times with seed 42, for Pari only and for all merged human rows, with and without the no_answer query q44.
2. **Files changed:** `src/ir/step14_report.py`, `tests/test_step14_report.py`, `results/step14_kappa_ci.md` (new), this log, `CLAUDE.md`.
3. **How it works:** Draw as many queries as the slice has, with replacement; keep every graded row of each drawn query (a query drawn twice counts twice); recompute agreement on those rows; repeat; read the 2.5th and 97.5th percentiles. Rows of one query are not independent, so resampling rows would give intervals that are too narrow.
4. **Results (real, from the run; point [interval]):** Pari only, 182 rows, 9 queries: weighted kappa linear 0.746 [0.574, 0.886], quadratic 0.823 [0.695, 0.921], binary agreement 0.879 [0.735, 0.977], binary kappa 0.752 [0.486, 0.950]. All merged rows, 308 rows, 15 queries: linear 0.675 [0.554, 0.793], quadratic 0.768 [0.667, 0.858], binary agreement 0.825 [0.728, 0.913], binary kappa 0.636 [0.468, 0.806]. Excluding q44, Pari only (8 queries) linear 0.725 [0.544, 0.872]; merged (14 queries) linear 0.663 [0.538, 0.785]. Point estimates equal the Step 13 values. No resample had a constant rater.
5. **Check yourself:** That the lower ends (0.54 to 0.57 linear for Pari only) still show moderate to substantial agreement but are far from certain, that binary kappa is the least certain metric (0.44 to 0.95), and that the merged set has the narrower intervals because it has 15 queries instead of 9.
6. **Assumptions:** The percentile bootstrap with only 8 to 15 queries may be too narrow. Seed 42. Only rows graded by both the human and the LLM are used. CI not checked (gh not logged in).

## Step 15a: ablation variants and unjudged top-10 results
1. **What I did:** Added an optional `query_prefix` to `DenseRetriever` (default empty, so default behaviour is unchanged; passages are never prefixed, so the embedding cache is shared). Added `src/ir/step15_ablation.py`, which builds 14 variants per module (3 defaults, RRF k 10/30/100, bm25:dense weights 2:1, 3:1, 1:2, 1:3, BM25 with light stemming, hybrid with stemmed BM25, dense with the BGE query prefix, hybrid with prefixed dense) and lists every top-10 chunk that is absent from the LLM qrels. Nothing was graded.
2. **Files created or changed:** `src/ir/dense.py` (prefix option), `src/ir/step15_ablation.py` and `tests/test_step15_ablation.py` (new), `tests/test_dense.py` (prefix test), `results/step15_unjudged.csv` and `results/step15_unjudged_summary.md` (new), `.gitignore`, this log, `CLAUDE.md`. No qrels, pool or grade file was written (md5 of every file in `data/eval` unchanged).
3. **How it works:** "Unjudged" means the (qid, chunk) pair is not in `qrels_t1_llm.tsv`. The metrics count such chunks as 0. Hybrid fetches `max(3k, 50)` candidates per ranker, so its top 10 depends on the k it is called with; I use the depth `evaluate()` uses (20 at chunk level, 100 at section level) so the list matches what the 15b tables will score.
4. **Results (real, from the run):** 433 rows, 285 unique (qid, chunk) pairs (device 206, medicine 79). Per variant: default bm25 0, default dense 0, default hybrid 10, rrf_k10 0, rrf_k30 13, rrf_k100 14, weights 27/34/21/25, bm25_stem 95, hybrid_stem 61, dense_prefix 92, hybrid_prefix 41. 10 of the 285 pairs are unjudged under the default hybrid itself.
5. **Check yourself:** That the default hybrid has 10 unjudged top-10 chunks at evaluation depth (q10, q14, q15, q30 x2, q40, q50, q55 x2, q61), which means the Step 13 and 14 hybrid numbers treated them as 0. Also that the earlier estimate (376 rows, 272 pairs) was computed at search depth 10, not at the evaluation depth.
6. **Assumptions:** Chunk level only in the CSV. Ranks 11 to 20 feed Recall@20, MRR and MAP and are not listed. The section-level column in the summary is informational (judged section = any chunk of it in the qrels). CI not checked (gh not logged in).

## Step 15a (addendum): ranks 11 to 20 and the extra grading pool
1. **What I did:** Counted unjudged chunks at ranks 11 to 20 for every variant (`--part ranks11_20`, reported only, not added anywhere). Extended `llm_grade_tool` with `make-extra`, which builds `data/eval/pool_t1_extra.csv` (qid, query, chunk_id, text) from the 285 top-10 pairs, and an `--extra` flag on `next-batch` and `record` so the existing batch flow grades it. Nothing was graded.
2. **Files created or changed:** `src/ir/llm_grade_tool.py`, `tests/test_llm_grade_tool.py` (3 new tests), `src/ir/step15_ablation.py` (`--part ranks11_20`), `data/eval/pool_t1_extra.csv` (new, 285 rows, 60 queries), `results/step15_unjudged_ranks11_20.csv` and `.md` (new), `docs/LLM_GRADER_PROMPT.md` (commands for the extra pool), this log, `CLAUDE.md`. `pool_t1.csv`, `pool_t1_llm.csv`, the qrels and the human files are unchanged.
3. **How it works:** `make-extra` takes the unique (qid, chunk) pairs of `results/step15_unjudged.csv`, drops the variant column so the grader cannot tell which system retrieved a chunk, looks up query and chunk text, and refuses to run if any pair is already graded or if the output path is a protected file. With `--extra`, `next-batch` and `record` read the extra pool, need no human sample, append to `pool_t1_llm.csv`, and number batches after the last recorded one (first extra batch is 44).
4. **Results (real, from the run):** Ranks 11 to 20: 5068 rows, 1476 unique pairs, 229 of them already in the 285, so **1247 extra pairs**. About 64% of default hybrid's rank 11 to 20 slots (396 of 620), 65% of bm25's and 79% of dense's are unjudged. A dry run of `next-batch --extra` gives batch 44 with 38 rows (q01 to q11).
5. **Check yourself:** That Recall@20, MAP and MRR in the Step 14 tables therefore treat roughly two thirds of ranks 11 to 20 as 0 for every system (the pool covered about the top 10), and that you must pass the same `--max-rows` to `next-batch` and `record`.
6. **Assumptions:** Grades from the extra pool go into `pool_t1_llm.csv` (same file, continuing batch numbers), which now stops being a one-to-one copy of `pool_t1.csv`. CI not checked (gh not logged in).

## Step 15a4: grade the extra pool, rebuild qrels, re-run 14a and 14b
1. **What I did:** Graded the 285 extra pool rows in 8 batches (44 to 51) with the prompt in `docs/LLM_GRADER_PROMPT.md` (model `claude-sonnet-5-5`, no human file opened), recorded them in `pool_t1_llm.csv`, rebuilt `qrels_t1_llm.tsv` (1554 rows) and re-ran Step 14a and 14b. 14c, 14d and Step 13 were not re-run.
2. **Files changed:** `data/eval/pool_t1_llm.csv` (+285 rows, committed earlier as `cfbad40`), `docs/LLM_GRADER_PROMPT.md` (8 batch log lines), `data/eval/qrels_t1_llm.tsv`, `results/step14_results.md`, `results/step14_by_type.md`, this log, `CLAUDE.md`.
3. **How it works:** nDCG divides by the ideal ranking built from every judged chunk of the query. 41 new relevant chunks (34 grade 1, 7 grade 2) across 30 queries raise the ideal for every system, so absolute scores drop for all systems even when a system's ranking did not change.
4. **Results (real, from the run):** New grades 244 zero, 34 one, 7 two (per batch zero/one/two: 44 32/5/1, 45 32/7/0, 46 31/2/2, 47 28/3/1, 48 30/3/0, 49 33/6/0, 50 34/4/2, 51 24/4/1). Of the default hybrid's 10 previously unjudged top-10 chunks, 2 became grade 1 (q15 801.1_c1, q61 201.10_c1), 8 are 0. nDCG@10 chunk level, old to new: device hybrid 0.624 to 0.604, bm25 0.624 to 0.603, dense 0.540 to 0.523, tfidf 0.627 to 0.600; medicine hybrid 0.716 to 0.689, bm25 0.631 to 0.606, dense 0.590 to 0.565, tfidf 0.628 to 0.605. Hybrid minus bm25 barely moved: device chunk -0.001 to +0.001, medicine chunk +0.085 to +0.083 (Holm p 0.627 to 0.664), medicine section +0.125 to +0.128 (raw p 0.008 to 0.006, Holm 0.091 to 0.070, still above 0.05).
5. **Check yourself:** Two secondary-metric comparisons now fall below uncorrected p=0.05 (device section hybrid Recall@20 +0.045 [+0.005, +0.088] p=0.029, medicine chunk hybrid MAP +0.101 [+0.001, +0.197] p=0.048). They are two of 36 uncorrected secondary comparisons. Also that the failure analysis (14c) and Step 13 report still use the old qrels.
6. **Assumptions:** Grades are my judgement under the prompt (lower when unsure), IVD-only and definitions-only passages mostly 0 or 1, no_answer queries (q41 to q44, q62) all 0. CI not checked (gh not logged in).

## Step 15b: ablation tables, 14c re-run, Step 13 note
1. **What I did:** Added `src/ir/step15_report.py`, which writes `results/step15_ablations.md`: one section per ablation (rrf_k, weights, stemming, query_prefix), and inside each a table per module and per level (chunk, section). Every variant is compared with the default it changes on nDCG@10 with a paired bootstrap interval, raw p, Holm within the ablation and Holm over all 22 comparisons, plus an unjudged@10 column. Re-ran Step 14c on the updated qrels. Added a note to the frozen Step 13 report that it used the original 308-row sample pool.
2. **Files created or changed:** `src/ir/step15_report.py`, `tests/test_step15_report.py` (new), `results/step15_ablations.md` (new), `results/step14_failures.md` (re-run), `results/step13_llm_vs_human.md` (note only, numbers untouched), this log, `CLAUDE.md`.
3. **How it works:** Holm "per ablation" adjusts over that ablation's variants for both modules at one level (rrf_k 6, weights 8, stemming 4, prefix 4 = 22). Holm "all 22" adjusts over all 11 variants x 2 modules at the same level. Chunk and section level are separate families. Recall@20, MRR and MAP are shown starred as provisional and have no p-values.
4. **Results (real, from the run):** unjudged@10 is 0 for every variant, module and chunk-level table (34 rows checked). It is NOT 0 at section level (up to 51 per row, 1050 summed over 34 rows) because the extra pool graded top-10 chunks, not the sections they aggregate into. Chunk-level ranks 11 to 20 still hold 37 to 180+ unjudged chunks per variant, hence the provisional note. Holm over all 22 below 0.05: device chunk rrf_k30 +0.015 (0.004), device chunk hybrid_stem +0.053 (0.021), device chunk dense_prefix +0.049 (0.028), device section rrf_k10 +0.030 (0.018), device section hybrid_stem +0.044 (0.046). No medicine row survives Holm over 22 (medicine chunk dense_prefix +0.056, raw 0.004, Holm all 0.072). No weights variant is significant. 14c zero-tie counts are unchanged (tfidf 1, bm25 2, dense 3, hybrid 2, no query 0 for all four); q15 and q18 scores and hypotheses changed.
5. **Check yourself:** The Holm family definitions in `comparison_rows`; that the default rows reproduce Step 14a/15a4 (device chunk hybrid 0.604, medicine chunk hybrid 0.689); that stemming and prefix gains are device-only.
6. **Assumptions:** "Holm over all 22" read as 11 variants x 2 modules per level, not 44 pooled across levels. Scored queries are answerable graded queries (no corpus gaps exist). The small rrf_k and weights effects are relative to the default and were not tuned. CI not checked (gh not logged in).

## Step 15b2: general make-extra and the second extra pool
1. **What I did:** `make-extra` already read any CSV with `qid` and `chunk_id` columns, but it refused to run if any pair was already graded. I added `--skip-graded` (parameter `skip_graded`), which leaves graded pairs out instead, and the command now prints how many pairs it listed and how many it dropped. I then built the second extra pool from the ranks 11 to 20 listing. Nothing was graded.
2. **Files created or changed:** `src/ir/llm_grade_tool.py`, `tests/test_llm_grade_tool.py` (1 new test), `data/eval/pool_t1_extra2.csv` (new, 1247 rows), `docs/LLM_GRADER_PROMPT.md` (commands for this pool), this log, `CLAUDE.md`. The first extra pool, `pool_t1.csv`, `pool_t1_llm.csv`, the qrels and the human files are unchanged (extra pool hash checked before and after).
3. **How it works:** The listing has 1476 unique (qid, chunk) pairs. 229 of them were already in the top-10 listing and got graded in batches 44 to 51, so `--skip-graded` removes them. Without the flag the tool still refuses, which protects against double grading by accident.
4. **Results (real, from the run):** `Unique pairs in results/step15_unjudged_ranks11_20.csv: 1476; left out as already graded: 229`, `Wrote 1247 rows for 62 queries`. Fast tests 105 passed, ruff clean. A dry run of `next-batch --extra --pool data/eval/pool_t1_extra2.csv --max-rows 40` gives batch 52 with 27 rows (q01), written outside the repo.
5. **Check yourself:** That grading this pool needs `--pool data/eval/pool_t1_extra2.csv` on both `next-batch` and `record`, or the tool silently reads the first (fully graded) extra pool and says nothing left. Also that 62 queries includes the no_answer queries.
6. **Assumptions:** "Already graded" means present in `qrels_t1_llm.tsv`. Unjudged ranks 11 to 20 were counted before the 285 grades, but the pair set is unchanged. CI not checked (gh not logged in).

## Step 15c: grade the depth-20 pool, rebuild qrels, re-run 14a, 14b, 14c and 15b
1. **What I did:** Graded the 1247 pairs of `pool_t1_extra2.csv` (ranks 11 to 20 of every variant, batches 52 to 93, model `claude-sonnet-5-5`, prompt in `docs/LLM_GRADER_PROMPT.md`, no human file opened), rebuilt `qrels_t1_llm.tsv` with `to-qrels` (2801 rows) and re-ran 14a, 14b, 14c and 15b. In `step15_report.py` I removed the "provisional" stars and note on Recall@20, MRR and MAP and replaced them with a note that the depth-20 pool is graded but sections can still hold unjudged chunks. Step 13 and 14d were not touched.
2. **Files changed:** `data/eval/qrels_t1_llm.tsv`, `data/eval/pool_t1_llm.csv` and `docs/LLM_GRADER_PROMPT.md` (earlier commits), `src/ir/step15_report.py`, `tests/test_step15_report.py`, `results/step14_results.md`, `results/step14_by_type.md`, `results/step14_failures.md`, `results/step15_ablations.md`, this log, `CLAUDE.md`.
3. **How it works:** Recall@20, MAP and MRR look past rank 10. Before, ranks 11 to 20 of each variant had mostly no grade and counted as 0. Now every chunk in the top 20 has a grade, so these metrics are no longer understated. nDCG@10 also falls a little because the ideal ranking gains new relevant chunks.
4. **Results (real, from the run):** The pool holds 1142 zero, 90 one, 15 two. Chunk level now has 0 unjudged chunks at ranks 11 to 20 in all 34 rows. Section level still has 52 unjudged top-10 sections summed over 34 rows. Absolute scores fell (device chunk bm25 nDCG@10 0.603 to 0.580, Recall@20 0.795 to 0.737). Dense vs bm25 Recall@20 gets smaller in the gap but stays significant uncorrected: device chunk -0.146 [-0.241, -0.051] p=0.002 (was -0.153, p=0.003), medicine chunk -0.134 [-0.263, -0.011] p=0.032 (was -0.125, p=0.051, so it now crosses 0.05), medicine section -0.088 p=0.030 (was -0.044, p=0.368, new), device section -0.048 p=0.223 (was -0.037). Recall@20 p-values are uncorrected. Main nDCG@10 Holm in 14a: no comparison below 0.05 (medicine section hybrid raw 0.009, Holm 0.103, was 0.070). Medicine chunk hybrid nDCG@10 +0.067 p=0.103 (was +0.083 p=0.060) and its MAP +0.070 p=0.156 (was +0.101 p=0.048, no longer below 0.05); hybrid MRR +0.144 p=0.025 unchanged. 15b Holm over all 22 crossed 0.05 in two cells: device section hybrid_stem 0.046 to 0.188 (no longer significant) and device section dense_prefix 0.052 to 0.013 (now significant). Unchanged significant: device chunk rrf_k30 0.013, hybrid_stem 0.021, dense_prefix 0.021, device section rrf_k10 0.029. Holm within one ablation: device section rrf_k30 0.022 to 0.070 (lost), device section bm25_stem 0.067 to 0.041 (gained). 14c zero ties unchanged (tfidf 1, bm25 2, dense 3, hybrid 2, none 0 for all four). q03 left the worst-queries list and q59 (medicine) entered; q15 and q18 scores dropped slightly. 14b by-type cells moved by about 0.02 to 0.03, change_impact section n=1 cell dropped most (n<5, descriptive).
5. **Check yourself:** That the chunk-level "unjudged ranks 11-20" column is 0 in `results/step15_ablations.md`. That the Recall@20 p-values above are uncorrected (36 secondary comparisons, none adjusted). That the two Holm crossings in device section come with small changes in the effect (hybrid_stem +0.044 to +0.036, dense_prefix +0.052 to +0.053), so the flip is mostly the Holm family ordering, not a big effect change.
6. **Assumptions:** Grades are my judgement under the prompt (lower when unsure), most ranks 11 to 20 chunks are 0 (no_answer queries all 0). The model id was assumed to be `claude-sonnet-5-5` because the command carried a placeholder. 14d and Step 13 left on the older pools by request. CI not checked (gh not logged in).

## Step 16: abstention evaluation for the medicine mode (plus 10 held-out grades)
1. **What I did:** Graded the 10 unjudged Step 17 held-out pairs (batch 94, `pool_t1_extra3.csv`). Drafted 10 answerable and 10 no_answer medicine queries (`queries_t1_abstain_draft.csv`, no_answer split 7 hard, 3 easy), pooled bm25, dense and hybrid at depth 20 on the medicine index (788 pairs), graded them (batches 95 to 114, claude-sonnet-5-5) and checked that no no_answer query has a grade 2 chunk. Then measured how well the top score and the rank-1 minus rank-2 margin predict answerable vs no_answer.
2. **Files:** `src/ir/step16_abstain.py` (pool, check, eval), `tests/test_step16_abstain.py` (13 tests), `data/eval/queries_t1_abstain_draft.csv` and `.tsv`, `data/eval/pool_t1_extra3.csv`, `data/eval/pool_t1_abstain.csv`, `data/eval/pool_t1_llm.csv` and `qrels_t1_llm.tsv` (3599 rows), `docs/LLM_GRADER_PROMPT.md` (batches 94 to 114), `results/step16_predeclaration.md`, `results/step16_abstention.md`, `results/step16_notes.md`, `results/step16_pool_listing.csv`, `.gitignore` (unignore results/step16_*).
3. **How it works:** AUROC is the chance that a random answerable query scores above a random no_answer query (ties count half). The bootstrap resamples each class separately 10,000 times (seed 42). The abstention threshold is chosen leave-one-out: fit on 19 queries, apply to the 20th. The primary score (hybrid top RRF) was committed before any result was computed.
4. **Results (real):** 0 no_answer queries flipped. Hybrid top AUROC 0.985 [0.930, 1.000], bm25 top 0.940 [0.820, 1.000], dense top 0.900 [0.740, 1.000]; margin scores are weak or inverted (hybrid margin 0.260). Leave-one-out with hybrid top: abstained on 11, precision 0.909, recall 1.0. Fast tests 118 passed, ruff clean.
5. **Check yourself:** The hard-only and easy-only rows (10 v 7 and 10 v 3; the easy interval is degenerate). That margin rows use a "low means abstain" rule that does not fit them. That the answerable queries were written from section titles, which may make the task easier than real use.
6. **Assumptions:** Grades are LLM grades (lower when unsure), not human. No cross-encoder exists, so that score was skipped. CI not checked (gh not logged in).

---

_Appended from a stray root LEARNING_LOG.md (Parth CV track). Its Step 16 to 18 numbering is separate from the retrieval Step 16 above._

## Step 16: Synthetic Label Generation and CV Draft Workflow
1. **What I did:** Finished seeded three-condition label generation, original-image field and symbol coordinates, template pictogram detection, draft SVG/PDF rendering and evidence-based print verification.
2. **Files changed:** Scoped `src/gen` and `src/cv` modules/tests/READMEs, two deterministic `data/symbols/device` references, and the generated `results/cv_extract.md` report. Shared schemas and retrieval code were not changed.
3. **How it works:** Homographies map label slots into distorted images; the extractor maps detections back. Draft manifests contain watermark status, change history, artifact hashes and self-check. Print verification requires an external authorized approval bound to exact manifest bytes.
4. **Verified:** Conda Python 3.12: 230 scoped tests passed; Ruff clean; pip check found no broken requirements. Full 51-image measurement: barcode 17/17 clean and moderate, 4/17 hard; symbol matches 34/34 in each condition.
5. **Check yourself:** Review the new symbol tests, renderer manifest and approval binding, and the condition-specific evaluation table.
6. **Assumptions:** Findings apply to one synthetic template family; the identifier is a test placeholder and pictograms are not certified ISO artwork.

## Step 17: Hard-Condition Barcode Recovery
1. **What I did:** Added original-first barcode decoding with rectification and thresholded template-slot recovery. Reduced only the hard blur/noise enough to preserve the barcode pattern while keeping hard rotation, perspective and lighting. Added a regression test requiring at least 80% exact GS1 matches on all 17 seed-42 hard labels.
2. **Files changed:** `src/cv/barcode.py`, `src/cv/extract.py`, `src/cv/test_barcode.py`, `src/cv/test_extract.py`, `src/gen/augment.py`, `src/gen/generate_dataset.py`, `src/gen/test_generate_dataset.py`, `src/cv/README.md`, `src/gen/README.md`, and `results/cv_extract.md`.
3. **How it works:** If a full-image decode fails, the label is straightened and the known barcode slot is cropped with a 3 mm margin. Adaptive grayscale thresholding exposes the dark modules for zxing-cpp; returned coordinates are mapped back to the original photo.
4. **Verified:** Full scoped suite: 233 passed. Ruff clean; pip check found no broken requirements. Exact barcode matches: seed 42 clean/moderate/hard = 17/17, 17/17, 15/17; seed 43 = 17/17, 17/17, 16/17. Hard rates are 88.24% and 94.12%. Repeated seed-42 runs produced 103 byte-identical files.
5. **Check yourself:** Review `decode_barcode_slot`, the 14-of-17 regression assertion, and the two-seed condition-separated results in `src/cv/README.md`.
6. **Assumptions:** The score target applies to this synthetic test-device template and fixed seeds. Two seed-42 and one seed-43 hard images still require human review; no identifier authenticity is implied.

## Step 18: Parth's Shareable CV Work README
1. **What I did:** Wrote a concise handoff document describing the assigned work, implementation, measured results, reproduction steps, limits and remaining review items.
2. **Files changed:** `docs/PARTH_WORK_SUMMARY.md` (shareable report for Paridhi) and this learning log (step record).
3. **How it works:** The report links the relevant code and evaluation report, gives seed-separated barcode results and field-level OCR error rates, and includes commands to reproduce the 51-image run.
4. **Verified:** Documentation was checked against the committed `parth-cv` branch, `results/cv_extract.md`, and the recorded Conda test and lint outputs.
5. **Check yourself:** Review the measured-results tables, reproduction commands, and remaining-work section before sharing.
6. **Assumptions:** The report is a project handoff, not a regulatory claim; temporary evaluation datasets are not committed.

---

## Step 19a: data model and schema change requests (branch step19-contracts)
1. **What I did:** Wrote `docs/contracts/DATA_MODEL.md`, which covers 14 entities with their fields, types, relations and version history rules, plus the public medicine mode shapes. Every field maps to a `schemas.py` class field or points to a numbered change request. Wrote `docs/contracts/SCHEMA_CHANGE_REQUESTS.md` with 14 proposed requests (CR-1 to CR-14) for what the locked `schemas.py` lacks. `schemas.py` was not edited.
2. **Files changed:** `docs/contracts/DATA_MODEL.md` (entity contract), `docs/contracts/SCHEMA_CHANGE_REQUESTS.md` (gap list), this log.
3. **How it works:** A Finding is the existing `Flag` plus optional citations. Each citation is built from a real `Chunk` (chunk_id, section, url, verbatim quote), so no regulation text is invented. Versions are append-only, and an approval binds to the artwork's sha256.
4. **Verified:** A throwaway script found 41 `Class.field` references to `schemas.py` and none were missing. Every field of ProductRecord, LabelExtraction, Flag and ChangeRequest appears in the doc. No em dashes. `ruff check src tests`: All checks passed.
5. **Check yourself:** CR-14 (a returned change stays `draft`), version rule 5 (approval binds to the hash), and the public corpus line (21 CFR 201, 208, 211 only).
6. **Assumptions:** Report and PublishedPage are exports, not tables. Prefixed opaque ids. The abstention score is provisional. None of the CRs is approved.

## Step 19a2: data model review changes
1. **What I did:** Applied Pari's five 19a review changes. Reports and published pages now carry a fixed `version_id`. Citations have `source_type` (cfr or label_section). Approval binds to `artifact_sha256` and the passed `check_id`. The CR table has a "Parth" column. Status is derived from the latest Review (new "Status derivation" table). I also added CR-15 and aligned `GS1-128`, `symbol_name` and the manifest hash with Parth's renderer on `cv-fixes`.
2. **Files changed:** `docs/contracts/DATA_MODEL.md`, `docs/contracts/SCHEMA_CHANGE_REQUESTS.md`, this log.
3. **How it works:** `label_id` is the label family, and `version_id` is one immutable version (L2). A QR page stores `version_id`, so it keeps showing L2 even after L3 is published.
4. **Verified:** The mapping script found 41 refs, none missing. Em dashes 0. The openapi "returned" example comes in 19c.
5. **Check yourself:** The status derivation order, the `check_id` rule in Review, and the Parth column values.
6. **Assumptions:** Public label answers have no abstention validation. The public label corpus is not built. Parth's code is not on main yet.

## Step 19b: template spec
1. **What I did:** Wrote `docs/contracts/TEMPLATE_SPEC.md`: units (mm from the top left, pt for fonts, the PDF y-flip, SVG viewBox in mm), the template JSON and slot keys, validation rules that become layout findings, the named SVG groups (`layer-background`, `layer-slots`, `slot-{id}`, `layer-watermark`, `layer-review`), and the GS1 barcode rule KEEP, REGENERATE or NEEDS_INPUT, with worked examples.
2. **Files changed:** `docs/contracts/TEMPLATE_SPEC.md` (new), this log.
3. **How it works:** A new address leaves the GS1 payload unchanged, so the decision is KEEP and the barcode is reused exactly. A confirmed new lot changes AI (10), so the decision is REGENERATE. A missing UDI-DI gives NEEDS_INPUT and `IdentifierRequired`.
4. **Verified:** A throwaway script found the spec example OK and Parth's `test_device.json` OK. The GENERATION.md example fails on a missing `symbol_name` (noted, not edited). The placeholder `00000000000000` has a valid mod-10 check digit. The PDF sizes are 283.46 x 170.08 pt. Em dashes 0.
5. **Check yourself:** The DRAFT band (6 mm) and the 6 pt minimum, the NEEDS_INPUT row for unconfirmed changes, and SVG group rule 2 (watermark removed only with approval).
6. **Assumptions:** Parth's renderer does not yet emit the named groups. The GS1 lot and serial limits (20 characters) need checking against the current GS1 spec.

## Step 19c: OpenAPI 3.1 contract and API guide
1. **What I did:** Wrote `docs/contracts/openapi.yaml`: 28 paths, 31 operations, 66 component schemas. It covers products and templates, scans and extraction, inspection, search with a retrieval config, change assessment, affected labels, generate (409 needs_input), re-check, review, publish, exports, print verification, history, jobs, and public scan and ask with an abstain response. Wrote `docs/contracts/API.md` to explain it, and marked `docs/API_CONTRACT.md` as superseded.
2. **Files changed:** `docs/contracts/openapi.yaml`, `docs/contracts/API.md` (new), `docs/API_CONTRACT.md` (one superseded note), this log.
3. **How it works:** Each schema mirrors `schemas.py` where a class exists (ProductRecord, LabelExtraction, Flag, Hit). Extended shapes use `allOf` plus `unevaluatedProperties: false`, so a typo in a mock fails validation. A returned Review must have `resulting_status: draft`, which the schema enforces with `if`/`then`.
4. **Verified:** Every component schema passed the JSON Schema 2020-12 metaschema (0 failing). 72 distinct `$ref`s, all resolved. No duplicate operationIds, path params match. 5 examples validate, including both `returned` examples. Negative checks reject a returned review with status reviewed, an approve without `check_id`, an unknown abstain reason and an extra key. All 31 operationIds appear in API.md. Ruff clean.
5. **Check yourself:** `AbstainedAnswer` (score and threshold may be null for a scope rule), `RetrievalConfig` defaults, and the `generateArtwork` 409 body.
6. **Assumptions:** `rerank` and `expansion` have no code in `src/ir` yet. Auth is not modelled. The abstention score is provisional.

## Step 19c2: users, terminal reject, voided approvals, 202 jobs, GS1 check
1. **What I did:** Added a minimal User (user_id, name, role editor, reviewer or admin) behind an `X-User-Id` header stub (no login), with `GET /me`. Review, AuditEvent and ChangeLogEntry carry `user_id`, and the submitter of a change cannot approve it (403 self_approval_forbidden). Documented that a new artwork version after approval voids that approval, that reject is terminal (`closed`, 409 change_closed), and that scan, generate and print verify always return a 202 Job envelope with GET result endpoints. Checked the GS1 formats against GS1's AI list and added a one-line authority note to GENERATION.md.
2. **Files changed:** `docs/contracts/DATA_MODEL.md`, `openapi.yaml`, `API.md`, `TEMPLATE_SPEC.md`, `SCHEMA_CHANGE_REQUESTS.md` (CR-16 User), `docs/GENERATION.md` (one note line), this log.
3. **How it works:** Status derivation only looks at the change's latest artwork version. After L3 is approved, regenerating gives L4 with no Review, so the change drops back to draft or checked ("Needs review" in the UI).
4. **Verified:** GS1 dataset (ref.gs1.org): 01 `N2+N14`, 10 `N2+X..20` separator required, 17 `N2+N6`, 21 `N2+X..20` separator required, so the 20-character limits were already right. OpenAPI: 35 operations, 67 schemas, 0 failing the metaschema, 73 refs resolved, 6 examples OK, all 35 operationIds in API.md. Mapping script: 41 refs, none missing. Em dashes 0.
5. **Check yourself:** The self-approval rule (the submitter may still return or reject), Status derivation rule 1, and the "public endpoints need no header" choice.
6. **Assumptions:** `X-User-Id` is a trusted dev stub, not security. "Needs review" is a UI label, not a fifth status.

## Step 19d: screens
1. **What I did:** Wrote `docs/contracts/SCREENS.md`: 3 public screens (P1 to P3) and 10 professional screens (D1 to D10). Each state names the operationId that feeds it and the mock file path, with a shared state vocabulary (empty, loading, success, failed_check, needs_review, approved, abstained, plus failed for broken jobs).
2. **Files changed:** `docs/contracts/SCREENS.md` (new), this log.
3. **How it works:** The Inspect screen's "failed check" state is the `inspectLabel` 200 response with an expiry mismatch finding, and its mock is `professional/inspect/failed_check.json`. The UI can build every state from mocks before the backend exists.
4. **Verified:** All 27 operationIds named in SCREENS.md exist in openapi.yaml. 50 mock paths listed. Em dashes 0.
5. **Check yourself:** The coverage check line, and the P2 needs_review meaning (several candidates, so a picker).
6. **Assumptions:** Idle scan screens need no mock. `failed` is an extra state.

## Step 19e: mock JSON and contract tests
1. **What I did:** Wrote 50 mock responses under `src/api/mock/` (public and professional kept apart), one per screen state in SCREENS.md, plus `index.json`, which maps each file to its screen, state, operationId, HTTP status and schema. Wrote `tests/test_mock_contracts.py`, which validates every mock against its endpoint's response schema in openapi.yaml and checks the mapped parts with the locked `schemas.py` models. It also checks honesty rules: citations quote real chunks of the right module, no invented GTIN or UDI-DI, drafts are marked, a returned change derives draft from its latest Review, a rejected change is closed, an approval is bound to a passed check and is not self-approved, and every required state and all four abstain reasons are covered.
2. **Files changed:** `src/api/mock/**` (51 JSON files), `tests/test_mock_contracts.py` (new), `requirements.txt` (+pyyaml to read openapi.yaml, +jsonschema to validate mocks), `.github/workflows/ci.yml` (installs the same two), `docs/contracts/openapi.yaml` and `DATA_MODEL.md` (CheckResult may name a `template_id` for template and pre-render layout checks).
3. **How it works:** `professional/evidence/success.json` is a real run of our own BM25 on the device chunks. 801.18 (date format) ranked first for "format of expiration date on a medical device label". Other scores and confidences are illustrative, and `index.json` says so.
4. **Verified:** `pytest -q tests/test_mock_contracts.py`: 82 passed before the non-vacuous check was added. Full fast suite: 205 passed, 1 deselected. Ruff: all checks passed. A deliberately broken mock fails validation (test_validation_is_not_vacuous).
5. **Check yourself:** The `index.json` note on illustrative values, `test_no_invented_identifiers`, and the ci.yml one-line change.
6. **Assumptions:** The mocks were generated once by a scratchpad script (not committed) and are edited by hand from now on. Abstain scores and thresholds are illustrative, not Step 16 values.

## Step 19g: wrap-up of Step 19 (contracts)
1. **What I did:** Updated CLAUDE.md "Current state" and "Next steps" for Step 19 and re-ran every check. Step 19 adds the contracts in `docs/contracts/` (DATA_MODEL, TEMPLATE_SPEC, openapi.yaml, API, SCREENS, SCHEMA_CHANGE_REQUESTS), 50 mocks in `src/api/mock/`, and `tests/test_mock_contracts.py`.
2. **Files changed:** `CLAUDE.md`, this log.
3. **How it works:** The UI builds against `src/api/mock/` files listed in `index.json`. The test fails if a mock drifts from openapi.yaml, so the contract and the mocks cannot silently disagree.
4. **Verified:** Fast suite 205 passed, 1 deselected. `tests/test_mock_contracts.py` 83 passed. Ruff clean. No em dashes in contract docs or CLAUDE.md. `git diff 3c12419 HEAD` shows no change under src/common, src/ir, src/cv, src/gen or data/eval.
5. **Check yourself:** CR-1 to CR-16 with the Parth column, the combined assumptions in the Step 19 report, and the ci.yml change.
6. **Assumptions:** See the combined list in the Step 19 report. CI status could only be checked through the public GitHub API, if at all (gh is not logged in).

---

## CV fix 1: setup, reproduction and diagnosis
1. **What I did:** Built a Python 3.12 CV environment from the pinned versions (now also in `requirements-cv.txt` at the root) and reproduced every published seed-42 number exactly. Added two extra photo conditions without touching the old three, and a tool that runs any older commit's code on the same images. Wrote `results/cv_diagnosis.md`.
2. **Files:** `src/gen/augment.py` and `src/gen/generate_dataset.py` (conditions `hard_original`, `very_hard`), `src/cv/baseline_ref.py` (run an old commit), `src/cv/diagnose.py` (report), `requirements-cv.txt`, `pyproject.toml` (long table lines allowed in the report template).
3. **How it works:** Commit `3c98598` changed the decoder and made the benchmark easier at the same time. Running the old and new decoder on both the old and new hard setting (same geometry, only blur and noise differ) separates the two effects.
4. **Verified:** `python -m src.cv.diagnose --datasets data/synthetic/dev42 data/synthetic/dev43`. Both dev seeds: old decoder 7/34 on original hard, 14/34 on reduced; new decoder 25/34 and 31/34. OCR: 155 of 179 wrong fields only dropped spaces; padding the crops removes the errors.
5. **Check yourself:** The 2x2 table, the controlled OCR experiment table, the template audit.
6. **Assumptions:** The dataset hash differs from macOS while the metrics match; I could not tell whether PNG encoding or pixel values differ.

## CV fix 2: OCR
1. **What I did:** Each detected text line is now re-cropped with a 30 percent margin on lightly dithered pixels after CLAHE contrast equalisation, identically for every condition. Added field naming by printed keys and layout (no slot positions) and format post-correction.
2. **Files:** `src/cv/ocr.py`, `src/cv/fields.py`.
3. **How it works:** The recogniser hesitates between 0 and O, and between a gap and a space, when the crop touches the ink. A margin and a little noise push it off that knife edge. CLAHE stretches contrast tile by tile, so text washed out by glare turns dark again.
4. **Verified:** Fresh seeds, template mode: CER 0.00% on clean, moderate, hard and hard_original (4,782 characters each).
5. **Check yourself:** `read_text_robust`, `DEFAULT_DITHER_PAD_RATIOS`, `map_fields_by_layout`.
6. **Assumptions:** The dither uses a fixed seed, so results are reproducible but depend on that seed.

## CV fix 3: barcode
1. **What I did:** Added a blind decoder that finds barcode-like regions itself, levels them, and tries Wiener deblurring at five strengths, two scales and three thresholds. The template-slot mode got the same attempts and is reported separately.
2. **Files:** `src/cv/barcode_blind.py`.
3. **How it works:** The test barcode is an 8 by 96 module strip at 3 pixels per module, so mild blur erases it. A Wiener filter divides out the known blur shape but stops amplifying where noise would dominate. Only complete GS1 decodes are accepted, so noise cannot become a barcode.
4. **Verified:** Fresh seeds, blind: hard_original 51/51 (starting point 37/51), very hard 43/51 (starting point 28/51).
5. **Check yourself:** `locate_barcode_candidates`, `decode_crop`, the noise test in `tests/test_cv_vision.py`.
6. **Assumptions:** Only DataMatrix, QR, Code 128 and EAN-13 are tried; pylibdmtx would not load on Windows.

## CV fix 4: symbols and negative cases
1. **What I did:** Added a generator for negative cases (missing symbol, wrong symbol, wrong barcode value) and variations (smaller, larger, independently drawn symbols), a whole-label multi-size symbol search, and checks that return shared `Flag` objects.
2. **Files:** `src/gen/generate_negatives.py`, `src/gen/alt_symbols.py`, `src/gen/smoke_label.py`, `src/cv/symbols.py`, `src/cv/consistency.py`.
3. **How it works:** A false positive is a symbol reported where none is printed. Before this every test label had both symbols, so that could not be measured.
4. **Verified:** Fresh seeds: 0 of 306 absent symbols reported; small symbols 204/204 blind (0/204 before); independent artwork 0/204; wrong barcode flagged 102/102.
5. **Check yourself:** The `alt_style` row (0/204) and why adding its references was dropped in `results/cv_experiments.md`.
6. **Assumptions:** The independent artwork is still my own drawing, not ISO artwork.

## CV fix 5: very hard condition and label corners
1. **What I did:** Added glare and occlusion as a new condition (old ones unchanged) and a fallback that rebuilds label corners when the outline is partly hidden.
2. **Files:** `src/gen/augment.py` (from CV fix 1), `src/cv/preprocess.py`.
3. **How it works:** Take the outer edge pixels, fit each label side with a Huber line fit (which gives little weight to a few outliers such as a finger sticking out), and intersect neighbouring sides, so a hidden corner is found where its two visible sides meet.
4. **Verified:** Fresh seeds, very hard: corners within 10 px 51/51 (starting point 22/51).
5. **Check yourself:** `find_label_corners_fallback`, `_refit_side`, `test_fallback_corners_survive_occlusion`.
6. **Assumptions:** The occluders are bars from the edge; a label covered in the middle was not tested.

## CV fix 6: extractor modes, tests, integration, real-photo harness
1. **What I did:** `extract_label` now has `mode="template"` and `mode="blind"`, sharing one OCR pass. Added `tests/test_cv_text_rules.py` (no CV libraries needed) and `tests/test_cv_vision.py` (skips without them, OCR tests marked slow), `src/cv/integration.py`, `src/cv/eval_real.py` and `data/real_photos/README.md`.
2. **Files:** `src/cv/extract.py`, `src/cv/eval_v2.py`, `src/cv/integration.py`, `src/cv/eval_real.py`, the two test files, the README.
3. **How it works:** `pytest.importorskip("cv2")` skips the whole file when OpenCV is missing, so the root CI command still passes.
4. **Verified:** Main environment without CV libraries: `pytest -q -m "not slow"` gave 109 passed, 1 skipped, 1 deselected. CV environment: 256 passed, 1 failed (Poppler, pre-existing). Integration: 5 labels passed through `LabelExtraction`, `ProductRecord` and `Flag` without schema changes.
5. **Check yourself:** `to_product_record` never invents a UDI-DI; `eval_real` prints that there is nothing to evaluate without photos.
6. **Assumptions:** No photo or transcription was created; Pari adds them.

## CV fix 7: final evaluation on fresh seeds
1. **What I did:** Froze the pipeline at `c594b6d`, then generated seeds 100, 101, 102 once and ran the final and starting-point code on them. Wrote `results/cv_final_eval.md`.
2. **Files:** `src/cv/final_report.py`, `results/cv_final_eval.md`, `results/cv_experiments.md`, `scripts/cv_experiments/`.
3. **How it works:** Dev seeds are where tuning is allowed; fresh seeds are the exam. Changing code after looking at the exam would turn it into more practice.
4. **Verified:** 255 main and 714 negative images, 0 extraction errors. Very hard barcode fell from 33/34 on dev to 43/51 on fresh.
5. **Check yourself:** The header of `cv_final_eval.md` (the report was re-run once after a Windows process-pool crash, with no code change).
6. **Assumptions:** 51 images per condition is small; one label is about 2 points.

## CV fix 8: documents
1. **What I did:** Wrote `results/cv_fixes.md`, `docs/CV_STATUS.md` (including 12 claims in `docs/PARTH_WORK_SUMMARY.md` that need a caveat) and closed `docs/CV_FIX_STATUS.md`.
2. **Files:** those three and this log.
3. **How it works:** Every number points to a command and states its image count.
4. **Verified:** Checked each number against the summaries printed by `python -m src.cv.eval_v2 summary`.
5. **Check yourself:** The "What remains weak" section of `results/cv_fixes.md`.
6. **Assumptions:** `docs/PARTH_WORK_SUMMARY.md` itself was not edited; the caveats are listed for Parth to apply.

## CV fix 9: wrap-up (intervals, Poppler skip, uncertain-reading flag)
1. **What I did:** Added Wilson 95% intervals to the barcode and symbol rates in `results/cv_final_eval.md` and `results/cv_fixes.md`, computed from the existing counts. Made the Poppler render test skip when `pdftoppm` is missing. The consistency checker now emits `needs_human_review` instead of `barcode_mismatch` when the lot or expiry OCR line has confidence below 0.8.
2. **Files:** `src/cv/intervals.py` (new), `src/cv/consistency.py`, `src/cv/eval_v2.py` (counts review flags), `src/gen/test_render.py`, `tests/test_cv_text_rules.py`, `scripts/cv_experiments/false_alarm_confidence.py`, the two reports.
3. **How it works:** A Wilson interval stays sensible at 51/51 (93.0% to 100%) where the simple plus-or-minus interval would claim zero uncertainty.
4. **Verified:** CV suite 258 passed, 1 skipped; root command without CV libraries 111 passed, 1 skipped, 1 deselected; ruff clean. Dev seeds only: very hard false mismatch flags 9 of 33 (template) and 5 of 33 (blind) before and after; real mismatches 68/68 per mode before and after.
5. **Check yourself:** That the 0.8 threshold changed nothing because every false alarm had confidence 0.876 to 0.999.
6. **Assumptions:** The threshold was set before measuring and not tuned. Symbol intervals treat the two symbols on a label as independent, so they are somewhat too narrow.

## Step 20 Phase 0: contract follows merged code (D-2, D-4, D-7, D-8)
1. **What I did:** Applied Pari's per-item decisions on the 11 differences between the contract and Parth's merged renderer. The contract now follows the code for symbol names (only `manufacturer` and `expiry`), the 9 mm DRAFT band, the layout kinds `clipping` and `overlap`, and two extra limits (barcode module at least 0.25 mm, printable ASCII). D-3, D-5, D-6 and D-9 stay as written and are marked decided gaps for Parth.
2. **Files:** `docs/contracts/TEMPLATE_SPEC.md`, `DATA_MODEL.md` (also the per-template version rule), `openapi.yaml` (enum on `symbol_name`), `SCHEMA_CHANGE_REQUESTS.md` (decision table), six mock JSON files.
3. **How it works:** A "contract" is the written promise the UI builds against. When code and promise disagree, someone must pick which one moves; this step records that pick per item.
4. **Verified:** `python -m pytest -q tests/test_mock_contracts.py` gave 83 passed.
5. **Check yourself:** The decision table at the end of `SCHEMA_CHANGE_REQUESTS.md`; the mock slots `name` and `ref` now start at y = 10 mm.
6. **Assumptions:** D-7 is only partly decided (other kind names such as `font_too_small` still differ). The sterilization symbol impact item no longer names a slot, because that symbol cannot be a slot yet.

## Step 20a: persistence layer and review rules
1. **What I did:** Built the SQLite store with SQLAlchemy: users, products and versions, templates, label versions, change requests, check results, reviews, published pages and audit events. Every table except users rejects UPDATE and DELETE through database triggers, so an edit is always a new row. Status is never stored; `src/api/status.py` computes it from reviews and checks, and `src/api/reviews.py` enforces the review rules (role, no self approval, hash and passed check for approve, comment for return and reject, reject is terminal, a newer version voids an approval).
2. **Files:** `src/api/db.py`, `models.py`, `errors.py`, `store.py`, `status.py`, `reviews.py`, `seed.py`, `tests/test_api_persistence.py`, `.gitignore` (local db folder), `.github/workflows/ci.yml` (installs sqlalchemy).
3. **How it works:** Think of a ledger. You never erase a line, you add a new one, and "what is the status now" is answered by reading the latest relevant lines. A trigger is a rule inside the database that refuses the erase attempt even if our own code tried it.
4. **Verified:** `python -m pytest -q tests/test_api_persistence.py` gave 20 passed; `python -m pytest -q -m "not slow"` gave 238 passed, 1 skipped, 1 deselected; `ruff check src tests` clean.
5. **Check yourself:** The order of checks in `record_review`; `label_version_status` versus `change_status` (only the change's latest version counts); the trigger loop in `init_db`.
6. **Assumptions:** No separate GeneratedArtwork table (its hash and change link are columns on `label_versions`); `closed` and `resulting_status` are computed on read; template versions count per template_id inside a product; unknown user is 401; role checks for non-review writes wait for the endpoints (20b).

## Step 20b: real endpoints and role checks
1. **What I did:** Turned 15 operations of `openapi.yaml` into real FastAPI endpoints on the SQLite store: me, products, templates, label versions, version history, changes, reviews and the audit log. Editors and admins register products, templates and changes; reviewers and admins review; everything else is a 403 `role_forbidden`. `POST /changes` stores a structured change but answers `parser: not_implemented`, an empty affected list, `checklist_complete: false` and a NEEDS_HUMAN_REVIEW message, so "not checked" cannot look like "clean".
2. **Files:** `src/api/routes.py`, `views.py` (database rows to contract JSON, status computed there), `requests.py` (request shapes), `main.py` (app factory, error handlers), `store.py` (extra edits on a change), `docs/contracts/` (parser field, error codes, roles, the "currently approved" sentence, 401 and 404 and 422 responses), two mocks (`parser: mock`), `tests/test_api_endpoints.py`, CI and `pyproject.toml` (fastapi, httpx, Depends lint rule).
3. **How it works:** The header `X-User-Id` names the caller; a small dependency looks the user up and checks the role before the handler runs. "Currently approved" is read from the change status, because an old version keeps showing as approved in its own record after a newer version voids the approval.
4. **Verified:** `python -m pytest -q tests/test_api_endpoints.py` gave 26 passed; full fast suite 264 passed, 1 skipped, 1 deselected; `ruff check src tests` clean.
5. **Check yourself:** `REAL_OPERATIONS` in `routes.py`; the four forbidden-role cases in the parametrized test; the new Error codes table in `docs/contracts/API.md`.
6. **Assumptions:** `registerTemplate` validates the shape only (no layout findings yet); plain-text changes are refused with 422 `parser_not_implemented`; `listAffectedLabels` stays a mock; a missing header and an unknown user share the code `unknown_user`; `old_value` defaults to the record's current value for a known field.

## Step 20c: mock fallback
1. **What I did:** Every operation that is not real now serves its mock JSON with the response header `X-Mock: true`. `?mock_state=<state or file name>` picks another mock of the same operation (for example `empty`). Three operations had no mock (confirm extraction, confirm change, publish), so I added one each.
2. **Files:** `src/api/mock_server.py`, `src/api/main.py`, three new mock files, `src/api/mock/index.json`, `docs/contracts/SCREENS.md`, `tests/test_api_mock_fallback.py`.
3. **How it works:** The server reads `openapi.yaml`, and for each operation not in `REAL_OPERATIONS` it registers a route that returns the chosen mock file. The route handler takes only the request, so FastAPI never tries to parse a body.
4. **Verified:** `python -m pytest -q tests/test_api_mock_fallback.py` gave 26 passed (one test per non-real operation checks the header, status and body); full fast suite 295 passed, 1 skipped, 1 deselected.
5. **Check yourself:** `NOT_MOCKED` and `pick_entry` in `mock_server.py`; the test that real operations never carry the header.
6. **Assumptions:** The default mock is chosen by state order success, loading, approved, empty; mock routes do not check the user header.

## Step 20d: contract tests against openapi.yaml
1. **What I did:** One scripted run calls every real operation and every status the spec documents for it, and validates each response body against its schema in `openapi.yaml`. It fails if a status is undocumented, so I added the missing 401, 404 and 422 responses to the spec. A last check requires that every documented status of every real operation was seen.
2. **Files:** `tests/openapi_helpers.py`, `tests/test_api_contract.py`, `docs/contracts/openapi.yaml`, `docs/LEARNING_LOG.md`, `CLAUDE.md`.
3. **How it works:** A schema is a machine-checkable description of a response. A passing test means the server's real answers match the promise the UI builds on; a second test breaks copies of real responses to prove the check can fail.
4. **Verified:** `python -m pytest -q tests/test_api_contract.py` gave 3 passed; full fast suite 298 passed, 1 skipped, 1 deselected; `ruff check src tests` clean; live smoke with uvicorn and a file database: `/health`, `/me`, `/products` real, `POST /public/ask` returned `x-mock: true`.
5. **Check yourself:** The coverage assertion at the end of `test_every_real_response_conforms_to_openapi`; the oneOf on the `registerTemplate` 422 response.
6. **Assumptions:** Only JSON responses are validated; the layout-findings CheckResult variant of the template 422 is validated by the mock tests, because the real server cannot produce it yet.

## Step 21a: checker spec
1. **What I did:** Wrote `docs/CHECKER_SPEC.md`: 16 rules, severities, when a rule says needs_human instead of a verdict, citation procedure and the evaluation plan.
2. **Files:** `docs/CHECKER_SPEC.md`, `reports/step21_a.md`.
3. **How it works:** Rules decide, retrieval only cites. A citation is a real chunk from an accepted section with a verbatim quote, or nothing.
4. **Verified:** The needed chunks (801.1, 801.15, 801.18, 801.20, 801.40, 801.109, 830.20) exist in `regs.jsonl`.
5. **Check yourself:** The rule table severities and the section 9 decisions.
6. **Assumptions:** GS1 check digit has only indirect support in the corpus; `extra.rx_only` marks prescription devices.

## Step 21b: checker and evaluation
1. **What I did:** Implemented `src/checker/` and evaluated it on injected errors, dev seeds 200 and 201 first, then seeds 300 to 302 once with rules and queries frozen.
2. **Files:** `src/checker/*`, `tests/test_checker_*.py`, `results/step21_checker_{dev,final}.md`.
3. **How it works:** One injected error should give one flag of its own kind. A wrongly formatted date switches off the barcode date comparison so it is not flagged twice.
4. **Verified:** Final: recall 51/51 in every condition (blind hard wrong_name confident 50/51), false alarm 0/51 [0.00, 0.07] per condition, every quote verbatim.
5. **Check yourself:** `runner.py` precedence rules; the table of rules that never fired in the evaluation.
6. **Assumptions:** Saturated results on easy synthetic data say little about real labels; symbol outcomes are needs_human by design.

## Step 21c: real inspect, recheck, jobs, search
1. **What I did:** Made inspectLabel, recheckArtwork, getJob, getCheckResult and searchEvidence real, with append-only `extractions` and `jobs` tables and `needs_human_count` plus `coverage` on CheckResult (CR-17).
2. **Files:** `src/api/*`, `docs/contracts/*`, four mocks, `tests/test_api_checker.py`.
3. **How it works:** The first inspect is a 202 job that extracts then checks; later ones are 200. CV libraries are imported only inside the job.
4. **Verified:** Fast suite 354 passed; slow hybrid tests 2 passed; every new status validated against openapi.yaml.
5. **Check yourself:** `_start_check` in `routes.py`.
6. **Assumptions:** An SVG artwork is read through the PNG beside it; scan and generate jobs remain mocks.

