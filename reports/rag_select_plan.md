# RAG selection mode: frozen plan

Branch `rag-select`, written and committed before any selection code and before any run. Nothing below changes after the run; a failure is reported, not tuned away.

## 1. What is tested

A third answer mode. Retrieval, scope rule and score gate are the frozen Step 23 ones (E5b, k=5 chunks, threshold 0.0315136, `data/rag/rag_config.json`). The five retrieved chunks are split into numbered sentences. The local model (qwen2.5:3b-instruct-q4_K_M, Ollama, temperature 0, seed 42, num_ctx 4096, structured output) returns only the numbers of the sentences that answer the question. The answer is those exact sentences, in document order, each with a citation to its chunk. The model writes no text, so every sentence is verbatim from a retrieved chunk. Checks: valid JSON, 1 to 3 numbers, every number in range, no repeats. A failed check falls back to extractive quotes as today. No overlap or banned-word check: the text is the regulation itself.

Sentence splitting (deterministic, tested): split a chunk after `.`, `!`, `?` or `;` followed by a space and a capital letter, digit or `(`, except after a known abbreviation (`No.`, `U.S.`, `e.g.`, `i.e.`, `Inc.`, `sec.`, `approx.`, single capital letter); sentences longer than 60 words are split again after `;` or `:` at the nearest boundary; pieces under 5 words are kept only as part of the previous sentence. Chunk windows are 200 words, so a chunk may start mid-sentence; that piece is a candidate like any other. At most 60 candidates, in retrieval rank order.

Prompt v4 (system): "You answer questions about US drug and medical device labeling regulations (21 CFR). You are given numbered sentences taken from the regulations. Reply with a JSON object. Set no_answer to true and sentences to an empty list if none of the sentences answer the question. Otherwise set no_answer to false and list the numbers of the 1 to 3 sentences that best answer the question, most important first. Use only numbers that appear in the list. Do not write any other text." User: "Sentences:\n{Sentence n (21 CFR section): text per line}\n\nQuestion: {question}". Schema: `{"no_answer": boolean, "sentences": [integer]}`, both required.

## 2. Queries

`data/eval/fresh_rag_select.tsv`: 40 fresh queries (`s01` to `s40`), written before any code: 30 answerable (15 device, 15 medicine), 10 no_answer (5 device, 5 medicine). A script confirmed none appears (exact text) in any other query file under `data/eval` or `data/rag`. The answerable ones were written from the section list of the corpus, not from retrieval output. Each system is run once.

## 3. Comparators (same queries, same retrieval, same gate)

- **extractive**: the current default (provider off): the three best-ranked chunks as verbatim quotes (`best_quote`, about 300 characters).
- **generative 3b**: the Step 23e structured mode (prompt v3, `AI_SETTINGS`, 90 s limit).
- **select**: this plan.

Models are run one after another, never at the same time. One warm-up call (not scored) before the select and generative runs so model load time is not counted. Latency is the pipeline wall time per query.

## 4. Grading (LLM grades, not human, Sonnet 5.5 as `/model` shows at grading time)

Files: `results/rag_select_grades_llm.csv`; batches logged in `docs/LLM_GRADER_PROMPT.md`.

- **Relevance** of every shown unit (extractive quote, selected sentence, generative sentence) to its question, graded blind: units of all modes are pooled, identical text for one query is graded once, order shuffled (seed 42), mode hidden. 2 = states the requirement or definition the question asks for; 1 = same topic, partial or background, does not itself answer; 0 = off topic or only shares words. Judged on the unit text and the question only. Only answerable queries are graded for relevance.
- **Faithfulness** of every selected and generative sentence against the text of its cited chunk, with the frozen rubric of `docs/RAG_SPEC.md` section 7 (2 supported, 1 partly, 0 not supported). Selected sentences are verbatim, so the grade tests whether a sentence cut out of its chunk still says what the chunk says. Extractive quotes are not graded for this.
- Second pass on a random 20 percent of faithfulness units (seed 42), agreement reported (same grader, so it measures consistency only).

## 5. Metrics (all with Wilson 95 percent intervals, modules also shown apart)

1. **Direct hit rate**: share of the 30 answerable queries whose shown units include at least one graded 2. Abstentions and gated queries count as misses.
2. **Unit precision**: share of shown units graded at least 1, over answerable queries; also share graded 2.
3. **Answered rate** on answerable queries (select and generative: outcome `answered`; extractive: it always shows quotes unless gated, so its rate is the share of queries that show quotes, reported for information).
4. **Wrong-answer rate** on no_answer queries (outcome `answered`; for extractive, the share that show quotes, reported separately as shown irrelevant quotes).
5. **Faithfulness**: supported (2) sentence rate.
6. **Latency**: median and p90 over all 40 queries (the Step 23e convention), and the median over queries that reached the model, reported next to it.

## 6. Decision rule (frozen)

Select becomes the optional AI mode (replacing the generative 3b mode behind `?mode=ai`, extractive stays the default of both ask operations) only if ALL hold, as point estimates:

- direct hit rate (select) >= direct hit rate (extractive default);
- unit precision at least 1 (select) >= that of extractive;
- median latency over all 40 queries < 30 s;
- answered rate on answerable >= 0.60;
- wrong-answer rate on no_answer <= 0.20;
- supported sentence rate >= 0.80.

Otherwise the current default and the current AI mode stay, and the report says which condition failed. Generative 3b is a comparison only; nothing is decided from it. Intervals are reported and the report says when a gap is inside them.

## 7. Cross-encoder

Not part of this run. Only if time remains after the run, and then its rule (MiniLM re-rank of the candidate sentences before the model sees them, same top-60 cut) is frozen and committed before it is scored on the same 40 queries, reported as a second, separate result, never swapped in for the main one.

## 8. Known limits stated in advance

LLM grades only, one grader, 40 queries; 15 per module answerable so intervals are wide. The generative comparator was developed on other queries (Step 23e); the select mode has had no tuning on any query. Sentence quality depends on a regex splitter on legal text with 200-word windows.
