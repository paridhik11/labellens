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

## Step 17a + 17b: dev / held-out split and synonym expansion
1. **What I did:** Split the 57 answerable queries into a development half (29) and a held-out half (28) with seed 42, stratified by query type and spread over both modules (`data/eval/split_t1.json`). Wrote a general regulatory synonym list (`data/eval/synonyms.json`, 19 groups, each tagged `cfr_definition` or `failure_derived`) and an expander that adds the other terms of a group when any term appears in the query. BM25 counts added terms at a lower weight than the user's own words.
2. **Files changed:** `src/ir/split.py`, `src/ir/expand.py`, `data/eval/split_t1.json`, `data/eval/synonyms.json`, `tests/test_split.py`, `tests/test_expand.py`, this log.
3. **How it works:** "address of the maker on the box" fires the maker group and the box group and adds manufacturer, labeler, package and carton. Held-out is scored once after tuning on dev, so the headline number is not fitted to the queries.
4. **Verified:** `pytest -m "not slow"`: 105 passed; `ruff check src tests`: clean; `python -m src.ir.expand --check`: PASS (every cfr_definition group has a CFR section containing at least two of its terms). Nothing was run for retrieval quality yet.
5. **Check yourself:** The failure_derived groups, which are not independent of the queries; terms that occur in no chunk (maker, barcode, expiry date, repack); the split file against the type counts.
6. **Assumptions:** No stemming, so word forms are listed explicitly. Source tags reflect how I came to write each group.
