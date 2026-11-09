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



