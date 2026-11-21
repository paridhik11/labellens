# RAG sentence reranker: frozen plan

Branch `rag-rerank` (from origin/main, not from rag-select). Written and committed before any rerank code and before any scored run. Nothing below changes after the run; a failure is reported, not tuned away.

## 1. What is tested

A fourth way to display an extractive answer, with no language model. Retrieval, scope rule and score gate are the frozen ones (E5b, k=5 chunks, gate threshold 0.0315136 from `data/rag/rag_config.json`). The five retrieved chunks are split into sentences with the existing splitter (`src.rag.selection.build_candidates`, at most 60 sentences, retrieval rank order). Each sentence is scored against the question by a small CPU cross-encoder, `cross-encoder/ms-marco-MiniLM-L-6-v2` (`max_length` 512, raw logit, no sigmoid). The answer is the top 1 to 3 sentences by score whose score is at least a threshold T, shown in score order, each cited to its chunk with the sentence as the verbatim quote. If no sentence reaches T the query is a no_answer outcome (nothing shown as an answer). Nothing is generated, so every shown sentence is verbatim from a retrieved chunk.

`BAAI/bge-reranker-base` is not used. A speed probe on three Step 23e style queries that are in none of the 40 below (pipeline stages only, nothing scored) measured about 0.5 s for 22 candidate sentences with MiniLM and about 5.2 s with bge-reranker-base, which alone breaks the 3 s latency gate. The probe also measured 0.35 to 0.41 s for one warm retrieval.

## 2. Queries and split

`data/eval/fresh_rag_rerank.tsv`: 40 new queries (`r01` to `r40`), 30 answerable (15 device, 15 medicine) written from the section list of the corpus, and 10 no_answer (5 device, 5 medicine). A script confirmed that none appears (exact lowercased text) in any file under `data/eval` or `data/rag`; two queries that did were reworded before this commit. `data/eval/split_rag_rerank.json` fixes the halves, 20 dev and 20 held-out, stratified by module and answerability (dev: 7 device and 8 medicine answerable, 3 device and 2 medicine no_answer; held-out: 8 device and 7 medicine answerable, 2 device and 3 medicine no_answer). The held-out half has 15 answerable and 5 no_answer queries.

## 3. Threshold T (dev half only)

For each of the 20 dev queries the pipeline is run with T set to minus infinity and stores the top 3 scored sentences, their scores and the outcome of the stages before reranking (scope rule, score gate). The top 3 sentences of every answerable dev query are graded (section 5). For T on the grid of integers from -10 to 8, a dev query shows the stored top 3 sentences with score >= T. T is the grid value with the highest dev direct hit rate (some shown sentence graded 2, answerable dev queries) subject to a dev no_answer wrong rate (query reaches the answered outcome) of at most 0.2, ties broken to the higher T. One T for both modules. T is then written to `data/rag/rag_rerank_config.json` with the query file hash, split hash and model name and committed before the held-out run.

## 4. Held-out run (once)

Both systems run once on the 20 held-out queries, same retrieval and same gate: **extractive** (the current default, `best_quote` of the three best-ranked chunks, provider off) and **rerank** (this plan, frozen T). One warm-up call (not scored) loads retrieval and the cross-encoder before each run. Latency is pipeline wall time per query, over all 20 queries (so queries stopped by the scope rule or the gate count with their short time).

## 5. Grading (LLM grades, not human, `claude-sonnet-5-5` as `/model` shows at grading time)

Same procedure and rubric as `reports/rag_select_plan.md` section 4. Every shown unit of an answerable query (extractive quote, reranked sentence, and for dev the top 3 stored sentences) is graded for relevance to its question: 2 = states the requirement or definition the question asks for; 1 = same topic, partial or background, does not itself answer; 0 = off topic or only shares words. Judged on the unit text and the question only, blind (system hidden), units of all systems pooled, identical text for one query graded once, order shuffled with seed 42. Grades go to `results/rag_rerank_grades_llm.csv` and batches are logged in `docs/LLM_GRADER_PROMPT.md`. Faithfulness is not graded: reranked sentences are copied, not written.

## 6. Metrics (Wilson 95 percent intervals, held-out, device and medicine also shown apart)

1. Direct hit rate: share of the 15 answerable held-out queries whose shown units include at least one graded 2. Gated, out-of-scope and no_answer outcomes count as misses.
2. Unit precision: share of shown units graded at least 1, and share graded 2.
3. Answered rate on answerable queries.
4. Wrong rate on no_answer queries: share whose outcome is answered (rerank). For extractive the share that show quotes is reported separately.
5. Latency: median and p90 over the 20 queries.

## 7. Decision rule (frozen, point estimates)

Rerank becomes the default extractive display only if ALL hold:

- direct hit rate (rerank) >= direct hit rate (extractive);
- wrong rate on held-out no_answer queries <= 0.20;
- median latency over the 20 queries < 3 s.

If it passes, the reranked sentences become the sources of the default extractive display (same outcome and message as today, sources are cited sentences instead of chunk quotes), and the old quotes stay as the fallback when the cross-encoder is unavailable or no sentence reaches T. Otherwise nothing is merged and the report says which condition failed. Intervals are reported and the report says when a gap is inside them.

## 8. Known limits stated in advance

LLM grades only, one grader, 15 answerable and 5 no_answer held-out queries, so intervals are wide and a hit rate difference of one query is not evidence. The ms-marco model was trained on web passages, not regulations. The sentence splitter is a regex on legal text with 200-word windows, so a sentence can start mid-sentence. T is fitted on 15 answerable and 5 no_answer dev queries.
