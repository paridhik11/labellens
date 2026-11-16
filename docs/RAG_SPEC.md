# RAG spec (Step 23): cited answers and abstention

Status: PLAN, written in Step 23a. Nothing here is implemented or measured yet. Rubric, thresholds and metrics in sections 7 and 8 are frozen before any evaluation run. Everything marked "decide" needs an answer from Pari before 23b.

## 1. What this is

A question goes in, retrieval finds regulation chunks, a small local language model writes a short answer from those chunks only, and a verifier checks the answer before anyone sees it. If the check fails, or the model is off, the user gets the best chunks as verbatim quotes and the words "needs human check". The system never says a label or a practice "complies". It reports what the cited text says.

Two modules, kept separate in data, rules and results (CLAUDE.md):

| | Public ask | Professional ask |
|---|---|---|
| Operation | `askPublic` (exists in the contract) | `askProfessional` (new, see section 9) |
| Corpus | medicine chunks, 21 CFR Parts 201, 208, 211 only | device chunks (21 CFR 8xx) |
| Banner | "Authenticity not verified. Based on a reference label match." (contract constant) | none |

The reference label corpus (DailyMed, openFDA) does not exist yet. Public answers come from CFR chunks only, so `based_on` names the matched product but no label text is used. State this on screen.

## 2. Pipeline

```
question
  1. scope rule (section 5)                  -> out_of_scope, no retrieval
  2. retrieve: frozen E5b, own module, k = 5
  3. score gate (section 5)                  -> needs_human_check (no quotes)
  4. build numbered context [1]..[5]
  5. provider.generate(prompt, context)      (Ollama, or fake in tests, or none)
  6. parse sentences, resolve [n] to chunk_id
  7. verify (section 4)
  8a. pass -> answered (sentences plus citations)
  8b. fail, or provider off or error -> extractive fallback -> needs_human_check (with quotes)
```

- **Retrieval.** `from src.ir.step18_config import load_system` gives `{"device": ..., "medicine": ...}`. Config and hash are in `data/eval/step18_config.json`; `check_config` runs on load, so a changed corpus stops the service. The bge-large embedding cache is not in the repository and is not present in this checkout (only bge-small caches are). The first 23b task is `python -m src.ir.step18_config rebuild-cache` (about 37 minutes of CPU), in the background. Until it exists, tests use a stub retriever and a service start fails loudly, not silently with another retriever.
- **k = 5.** Chunks are at most 200 words (mean 168), so five chunks are about 1,300 to 1,600 tokens. That fits a 4096 token context with room for the prompt and the answer. k is a setting in one `RagSettings` object, echoed in every response and report.
- **Numbered context.** Each passage is `[n] 21 CFR <section> <title>: <text>`. The model sees only these numbers, never chunk ids, so it cannot invent an id. The code maps `n` back to the real `chunk_id`.
- **Answer format.** At most 4 sentences, each ending with one or more markers like `[2]` or `[2][4]`. If the passages do not answer the question, the model must output exactly `NO_ANSWER`. Temperature 0, fixed seed, so a run is reproducible on the same model build.
- **Sentence rule.** A sentence without a marker fails verification. The marker is stripped from the display text and shown as a citation chip.

## 3. Provider interface

```python
class Provider(Protocol):
    name: str                      # echoed in responses and reports
    def generate(self, system: str, user: str, *, max_tokens: int) -> str: ...
```

- `OllamaProvider`: HTTP to `http://localhost:11434/api/chat` (`stream: false`, `options: {temperature: 0, seed: 42, num_ctx: 4096}`). Uses `httpx`, already a dependency (added for the API tests), so no new package. Timeout 120 s; any error or timeout raises `ProviderError`, which the pipeline turns into the extractive fallback.
- `FakeProvider(script)`: returns canned text, can be told to return an invented marker, a sentence without a marker, `NO_ANSWER`, or to raise. All unit tests and CI use it. CI never needs Ollama.
- `NullProvider` (provider off): always raises `ProviderUnavailable`. This is the default when `LABELLENS_LLM` is unset, so the API works with no model installed.

**Model choice (decide).** Pick one small instruct model. Candidates, sizes from the Ollama tag pages checked on 2026-11-16:

| Tag | Download | Note |
|---|---|---|
| `qwen2.5:3b-instruct-q4_K_M` | 1.9 GB | recommended: smallest, follows format instructions well at this size (my expectation, not measured here) |
| `llama3.2:3b-instruct-q4_K_M` | 2.0 GB | comparable |
| `gemma3:4b-it-q4_K_M` | 3.4 GB | larger, slower on CPU |

Recommendation: `qwen2.5:3b-instruct-q4_K_M`, pinned by full tag. **Speed is not measured yet.** Ollama is not installed on this machine (no `ollama` command, no install folder) and installing it plus the model is a download of about 2 GB plus the Ollama installer. I will not download without your yes. Machine for the measurement: Intel Core Ultra 7 155U, 12 cores, 31 GB RAM, no discrete GPU. Measurement plan (first 23b step, after your yes): 10 prompts of real size (5 chunks), report load time, time to first token and tokens per second for the recommended model, and one fallback model only if the first is too slow. Acceptance: median full answer under 30 s; if not, the spec drops to `qwen2.5:1.5b` or to extractive only, and the report says so.

## 4. Verification

Checks, in order, on the parsed answer. Any failure triggers the extractive fallback and records which check failed.

1. **Marker present.** Every sentence ends with at least one marker.
2. **Id valid.** Every marker `n` is in 1..5 (the retrieved set). An unknown number fails the whole answer, not just that sentence.
3. **No empty answer.** At least one cited sentence remains and `NO_ANSWER` was not output (`NO_ANSWER` goes to needs_human_check without quotes, see section 5).
4. **Quote overlap (cheap grounding guard).** Each sentence must share at least 40 percent of its content words (after `src.ir.tokenizer.tokenize`) with the union of its cited chunks. This catches a sentence glued to the wrong marker. It is a weak guard and is not the faithfulness measure; faithfulness is graded in section 7. The 0.40 value is a guess made now, frozen, and reported as such.
5. **Banned claims.** The answer text must not contain the words "complies", "compliant", "approved by", "safe to use" or "you should take". A match fails the answer. This enforces "never claim compliance" in code; the prompt also forbids it.

**Extractive fallback.** The top 3 retrieved chunks, each shown as section, title, URL and a verbatim `best_quote(chunk.text, question)` (reusing `src/checker/citations.py`, which asserts the quote is a substring of the chunk). It is labelled "These are the closest passages. No answer was generated or verified." Quotes are never reworded.

## 5. Outcomes and abstention

Three outcomes, wire reasons from the contract (`AbstainedAnswer.reason`):

| Outcome | Wire shape | When |
|---|---|---|
| `answered` | `abstained: false`, `answer`, `sources` (every cited chunk, with quote), `based_on`, `banner` | generation passed verification |
| `needs_human_check` | `abstained: true`, `reason: needs_human_check` | verification failed, provider off or errored, model said `NO_ANSWER`, or the score gate fired |
| `out_of_scope` | `abstained: true`, `reason: out_of_scope`, `score_name: scope_rule`, `score: null`, `threshold: null` | scope rule fired |

The contract also has `no_evidence` and `low_confidence`. RAG v1 does not emit them: retrieval always returns hits, and a below-threshold score is reported as `needs_human_check` with the real `score_name`, `score` and `threshold` filled in so the reason is visible. (decide: keep this, or emit `low_confidence` for the score gate; the contract allows both, and the evaluation counts them identically.)

**Scope rule (step 1).** Fires on questions that ask for personal medical advice: dosing or "should I take" phrasing, diagnosis, symptoms, interactions for a person. Implemented as a short, readable list of regular expressions in `src/rag/scope.py`, written now from the contract's own definition, not from the evaluation queries. Public mode also fires it for device-only questions, because public scope is 21 CFR 201, 208, 211. Mentions of other jurisdictions are not hard coded, because that would be fitting the 10 no_answer queries; those must be caught by the score gate or they are counted as failures.

**Score gate (step 3).** Provisional. `score_name = "e5b_top_score"`, the top hit's score from the frozen retriever. Evidence for any abstention score is weak and the spec says so plainly:

- Step 16: hybrid top score AUROC 0.985 [0.930, 1.000], 20 queries, plain hybrid, different retriever.
- Step 18 test split: no score reached AUROC 0.90 or leave-one-out precision 0.80 (best 0.800 [0.500, 1.000], precision 0.429; 13 queries).
- E5b top score itself has not been validated at all. Its RRF scores are rank based (they depend on agreement between the two systems, not on how good the match is), so it may separate worse than the Step 16 score. 23b measures its AUROC on the dev half before use.

**Threshold, conservative by construction.** Fitted on the dev half only (`data/eval/abstain_split.json`: 9 answerable, 5 no_answer) as the smallest score that is above every dev no_answer score, so no dev no_answer query passes. If that threshold would abstain on more than half of the dev answerable queries, the gate is not usable, the system relies on the verifier alone, and the report says that. The final run is not a clean test: the Step 18 test half was already scored for abstention, and q45 to q61 were used to select E5b. The report must say so next to every abstention number.

Every response carries `score_name`, `score` and `threshold` when the score gate was evaluated. The words "confidence" and "probability" are not used for this score.

## 6. Public mode scope

Corpus is `module = medicine` only. A public question never touches device chunks. The corpus has Parts 201, 208 and 211 only; the `medicine` module is built from exactly those (checked in 23b by listing the parts present, and the check is a test). Out-of-corpus questions (EMA, Health Canada, USP, clinical trials, registration) are expected to fail the score gate. Whether they do is what the wrong-answer rate on no_answer measures.

## 7. Evaluation (frozen before the run, run once)

**Query sets, reported per module, never blended.**

| Set | Queries | Module | Used for |
|---|---|---|---|
| web_faq medicine | 10 (`data/eval/fresh_web_faq.tsv`) | public | answerable |
| q45 to q61 | 17 (`queries_t1.tsv`) | public | answerable |
| ab11 to ab20 | 10 (`queries_t1_abstain.tsv`) | public | no_answer |
| web_faq device | 20 | professional | answerable |
| q41 to q44 | 4 | professional | no_answer (small, secondary; decide, default included) |
| advice queries | 10, written in 23b before the run, saved at `data/rag/advice_queries.tsv` | public | scope rule recall |

Public: 27 answerable, 10 no_answer. Professional: 20 answerable, 4 no_answer. Answerable queries with no grade-2 chunk in the qrels are listed and kept (the system is still expected to answer or fall back). The `chunk_derived` queries are not used.

**Conditions.** (A) provider on, Ollama model of section 3. (B) provider off, extractive mode. Same retrieval, same queries. B is a baseline and the supported fallback, not a failure.

**Metrics.** All rates with 95 percent Wilson intervals, `n` and the unit in every cell.

1. **Citation validity rate.** Condition A, before any fallback. Unit 1: sentences whose markers all resolve to the retrieved set, over all generated sentences. Unit 2: answers where all sentences are valid, over all generated answers. Also report how often each verification check fired.
2. **Faithfulness.** Condition A, answers that passed verification. Each sentence is graded against only its cited chunks' text with the rubric below, by Sonnet 5.5 in this session, tagged **LLM-graded, not human**. Grades go to `results/step23_faithfulness_llm.csv`, never to human files, and every batch is logged in `docs/LLM_GRADER_PROMPT.md` with the model id shown by `/model` at grading time. Report supported rate (strict) and supported-or-partly, by sentence, plus query level (all sentences supported). Sentences from one answer are not independent, so the sentence-level interval is too narrow; the query-level one is the honest one. The generator (Qwen) is a different model from the grader, so this is not self-grading, but one LLM grader is stricter than humans at the 0 and 1 boundary (Step 13), and 10 percent of rows (at least 15) should be offered for human grading by Pari or Parth as a check, in a separate file.
3. **Answered rate on answerable queries.** Share ending in `answered`. Reported with the share ending `needs_human_check` split by cause (score gate, verification, NO_ANSWER, provider off).
4. **Wrong-answer rate on no_answer queries.** Share of no_answer queries that end in `answered`. Extractive quotes shown under `needs_human_check` are not counted as answers but are listed and counted separately, because showing irrelevant quotes is also a failure.
5. **Scope rule.** Recall on the 10 advice queries, and false triggers on all other queries (target: 0).
6. **Secondary:** citation relevance, the share of cited chunks with an LLM grade of at least 1 in the existing qrels (unjudged pairs counted separately, not as 0), and latency (median and 90th percentile) per condition.

**Faithfulness rubric (frozen).** For one answer sentence and the text of the passages it cites:

- **supported (2):** every factual claim in the sentence is stated in, or follows directly from, the cited text.
- **partly (1):** the main claim is in the cited text, but the sentence adds a detail, number, condition or scope not in it, or states it more strongly than the text.
- **not supported (0):** the main claim is absent from, or contradicted by, the cited text, even if true elsewhere. Using knowledge outside the passages counts as 0.
- Judge only the text. Do not reward a correct answer that the passages do not contain. A sentence that says a label "complies" is 0.

**Targets, frozen, reported as met or not met only:** citation validity (answer level) at least 0.95; faithfulness supported rate (sentence level) at least 0.80; wrong-answer rate on no_answer at most 0.20; answered rate on answerable at least 0.60. With 10 no_answer queries a Wilson interval on a rate of 0.20 is about 0.06 to 0.51, so a "met" means little. The report says that next to the number. Given Step 18, I expect the wrong-answer target to fail.

**Run order.** (1) 23b writes code and tests with the fake provider. (2) Retrieval cache rebuilt. (3) Dev half used to fit the threshold. (4) This spec's frozen block (rubric, targets, query lists, config hash of `data/eval/step18_config.json`, model tag, prompt text hash) is committed. (5) One final run in the background to `results/step23_run.log`, checked once. (6) Grade faithfulness. No change to the prompt, k, thresholds or rubric after step 4; a failure is reported, not tuned away.

## 8. Files and tests (23b)

New: `src/rag/` (`settings.py`, `provider.py`, `scope.py`, `prompt.py`, `verify.py`, `pipeline.py`, `evaluate.py`), `tests/test_rag_*.py`, `data/rag/advice_queries.tsv`. Not touched: `src/common/schemas.py`, `src/ir` internals, `src/cv`, `src/gen`, `data/eval`. Tests with the fake provider cover: invented marker fails, missing marker fails, `NO_ANSWER`, provider raising, provider off, banned words, quote overlap, scope rule, quotes verbatim, the three outcomes' wire shapes. Dependencies: none new (`httpx` already present).

## 9. API (23c)

- **`askPublic`** becomes real. Its request and answer shapes are unchanged. The extractive fallback needs one additive change: `AbstainedAnswer` gets an optional `sources` array (the quotes). Contract says "no answer text", which stays true. This is a change to `docs/contracts/openapi.yaml`, DATA_MODEL.md and one mock, not to `schemas.py`; proposed as CR-18 in `SCHEMA_CHANGE_REQUESTS.md`. (decide)
- **`askProfessional`** does not exist in the contract. Proposed: `POST /ask` with `{question}`, module fixed to device, answer shape the same as public without the banner, plus a mock and a contract test. Proposed as CR-19. (decide)
- Both run as ordinary synchronous calls (no job) because the provider call is bounded by the 120 s timeout; if the measured latency is worse, switch to the 202 job pattern used by scan and generate.
- Provider chosen by `LABELLENS_LLM` (`ollama:<tag>` or unset). Unset means extractive mode, and responses state `mode: extractive` in the message text.
- Every answer response includes its citations. Tests assert `sources` is non-empty for every `answered` response and that each `chunk_id` exists in the corpus.

## 10. What this does not do

No answer correctness against a gold answer (only faithfulness to the cited text). No check of the matched product's real label. No human grades unless Pari or Parth grade the sample. No claim that an answer is legal or medical advice. Abstention is provisional and weakly validated.

## 11. Decisions needed before 23b

1. Install Ollama and download `qwen2.5:3b-instruct-q4_K_M` (about 1.9 GB plus the installer) to measure speed? Default: yes, one model.
2. Score gate below threshold reports `needs_human_check` (default) or `low_confidence`.
3. Approve CR-18 (optional `sources` on abstain) and CR-19 (`askProfessional`).
4. Include q41 to q44 as the professional no_answer set (default yes).
5. Offer 10 percent of faithfulness grades for human check (default yes).

## 12. Decisions made in 23b (before any evaluation run)

Pari approved the section 11 items on 2026-11-16 (Ollama install, below threshold is needs_human_check, CR-18 and CR-19 because both are additive, include q41 to q44, no human check). Changes to the plan, with reasons:

1. **Model.** Ollama 0.40.16 installed with winget. Speed measured on this machine (Core Ultra 7 155U, 12 cores, 31 GB, no discrete GPU, 5 distinct passages of about 1,270 prompt tokens, temperature 0, 4096 context, first call per model excluded for load):

   | Model | Full answer, uncached prompt | Prompt processing | Generation |
   |---|---|---|---|
   | `qwen2.5:3b-instruct-q4_K_M` (1.9 GB) | about 34 to 39 s (5 runs) | about 55 tokens/s | about 11 tokens/s |
   | `qwen2.5:1.5b-instruct-q4_K_M` (986 MB) | about 18 to 20 s (3 runs) | about 110 tokens/s | about 20 tokens/s |

   The spec's acceptance rule was a median full answer under 30 s. The 3b model fails it (a second set of runs looked faster, 11 to 16 s, only because Ollama reused the cached prompt for repeated passages; that is not what real questions see). **Primary condition A1 is therefore the 1.5b model.** The 3b model is still run once as comparator A2 and reported, so the cost of the smaller model is visible. Prefill dominates the time, so a smaller k would help more than a smaller model; k stays 5 because it was frozen first.
2. **Conditions.** A1 qwen2.5 1.5b (primary), A2 qwen2.5 3b (comparator), B provider off (extractive). Same queries, same retrieval.
3. **Faithfulness check.** Instead of a human check, a random 20 percent of graded sentences (seed 42) is graded again in a second pass with the same frozen rubric, and the agreement is reported. Both passes are the same LLM in the same session, so agreement measures consistency, not correctness.
4. **Threshold rule made literal.** The threshold is the smallest dev score strictly above every dev no_answer score. The gate is switched off if that would abstain on more than half of the dev answerable queries.
5. **503.** A missing embedding cache or a changed corpus gives `503 retrieval_unavailable` on both ask operations. The API never falls back to a different retriever.
6. **Scope rule false trigger test.** The rule must not fire on any of the 112 existing evaluation queries (tested in `tests/test_rag_pipeline.py`). It was not tuned on the advice queries (`data/rag/advice_queries.tsv`, written before the run); adv09 ("how many tablets should my mother take each day") is expected to be missed.
7. **Public `based_on`.** There is no product registry or label corpus yet, so `based_on` names the regulation parts and the product id as given. No label text is used.

## 13. Frozen before the final run

Committed before `python -m src.rag.evaluate run`. Nothing below changes after the run; a failure is reported, not tuned away.

- Config: `data/rag/rag_config.json`, sha256 `2ccb259ab916e5151b520f88e9c4853d80777508987cdebbdf222c60ced7f9a5`. Prompt version `b4cc61aa4994`. Retrieval: frozen E5b (config intact).
- Threshold fitted on the dev half only: smallest dev score above every dev no_answer score, 0.0315136 (dev AUROC of the E5b top score 0.933 on 9 answerable and 5 no_answer queries; the gate would abstain on 2 of 9 dev answerable queries, so it is usable). The dev AUROC is in-sample for the threshold and is not evidence on new queries.
- Query list: 112 + 10 advice queries as in section 7 (code: `load_queries` in `src/rag/evaluate.py`).
- Rubric and targets: section 7, unchanged. Primary condition A1 (qwen2.5 1.5b). Comparators A2 (3b), B (off).
- Faithfulness grader: Sonnet 5.5 in session (`claude-sonnet-5-5`), LLM grades only, in `results/step23_faithfulness_llm.csv`.

## 14. What the final run showed (2026-11-16)

Full numbers: `results/step23_rag.md` (written by `python -m src.rag.evaluate metrics`). Raw model text and outcomes per query: `results/step23_run_*.jsonl`. Run 1 as first written: `results/step23_run1_*.jsonl`.

1. **Result of the frozen protocol: no generated answer passed verification, in either model.** Answered rate on answerable queries 0/27 public and 0/20 professional in A1 (1.5b), A2 (3b) and B (off). Both models mostly returned bare passage numbers such as `[1][3]` (3b: 34 of 45 outputs), or put the number before the sentence (1.5b), against the rule that a sentence ends with its marker. Faithfulness therefore has no sentences to grade, and the planned second-pass re-grade of 20 percent is empty. No faithfulness grade of any kind was made.
2. **Verifier defects found by the run and fixed (code and tests, not thresholds).** (a) A sentence with no words, only markers, passed the overlap check; run 1 counted 14 (1.5b) and 34 (3b) such outputs as `answered`. (b) `NO_ANSWER [1]` passed as an answer (found in a dev check). Outcomes were recomputed from the stored model text (generation is deterministic at temperature 0 and retrieval is frozen, so this equals a rerun); run 1 is kept as `step23_run1_*`. These fixes only make verification stricter. Counting the run 1 numbers as results would be wrong.
3. **Prompt v2 (post hoc, unused).** Two variants (a worked example, then a format-only placeholder) were tried on six dev-half queries (q50, q51, q52, q54, q58, ab13): the 1.5b model copied the example sentence, the 3b model returned only numbers. Tuning further on queries already seen would not give an honest number, so v1 stays the default and v2 is left in `prompt.py` as a recorded failed experiment.
4. **Exploratory only:** accepting a marker at the start of a sentence would let 9 of 40 generated 1.5b answers and 0 of 34 3b answers pass verification. Not graded for faithfulness.
5. **What works.** Scope rule 10/10 on the advice queries and 0 false triggers on the other 61 queries (adv09 was not missed after all). Score gate (threshold 0.0315, fitted on the dev half): all 10 public no_answer queries and all 4 device no_answer queries were not answered; 8 of 10 public and 3 of 4 device no_answer queries were stopped by the gate, the rest by `NO_ANSWER` or, in extractive mode, shown as quotes (2 of 10 public, 1 of 4 device). It also stopped 2 of 27 public and 3 of 20 device answerable queries. 0/10 wrong answers is not evidence of a low rate: the upper Wilson bound is 0.28.
6. **Extractive mode (the working product).** Of the top 3 passages shown for answerable queries, 58 of 75 (0.77, public) and 27 of 51 (0.53, device) have an LLM qrels grade of at least 1 (passages are not independent; LLM grades, stricter than humans). Answer latency 0.3 s. The language-model modes take a median 16 to 17 s (1.5b) and 29 to 33 s (3b) on this CPU.
7. **Decision.** Default provider stays off (extractive mode). `LABELLENS_LLM=ollama:<tag>` still works and any answer it gives is verified, but with these two models it almost always falls back. A larger model, or structured (JSON) output with a different verifier contract, is the next thing to try and needs a new frozen run.

## 15. Shared index store

Built dense indexes are named by model and corpus hash. They live once in `data/cache/indexes` of the main checkout (git-ignored; override with `LABELLENS_INDEX_DIR`), outside any worktree. `src/rag/indexes.py` copies missing files into `data/processed` (where `src/ir` reads them) and saves new ones back, never overwriting, so a matching hash is never rebuilt. `python scripts/build_indexes.py` does all of it (E5b bge-large for both modules, bge-small for the default hybrid) in one command; `--check` only reports. The ask service calls pull and push around loading, so a new worktree or a demo PC with the shared folder starts without rebuilding. `src/ir` was not edited.
