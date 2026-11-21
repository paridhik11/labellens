# RAG sentence reranker (branch rag-rerank)

Plan: `reports/rag_rerank_plan.md` (committed before any run). Results: `results/rag_rerank.md`.

- MiniLM cross-encoder (ms-marco-MiniLM-L-6-v2) scores the sentences of the 5 retrieved chunks; the answer is the top 1 to 3 at or above T. No LLM. bge-reranker-base dropped on speed (about 5.2 s for 22 sentences, alone over the 3 s gate).
- T = 1 (raw logit), chosen on the 20 dev queries (dev hit 11/15, wrong 0/5).
- Held-out, 20 queries (15 answerable, 5 no_answer), each system run once, LLM grades (not human):

| | extractive | rerank |
|---|---|---|
| direct hit rate | 8/15 | 9/15 |
| units graded >= 1 | 33/42 | 36/40 |
| units graded 2 | 8/42 | 15/40 |
| wrong on no_answer | 2/5 shows quotes | 1/5 |
| median latency | 0.37 s | 1.04 s |

Gate met on all three points (9 >= 8, 0.20 <= 0.20, 1.04 s < 3 s). The hit gap is one query and the no_answer rate sits exactly on its limit with 5 queries, so neither is evidence beyond the gate; unit precision is the clearer gain.

Integration: reranked sentences are now the sources of the default extractive display (outcome and message unchanged). The old chunk quotes remain when the cross-encoder is unavailable, no config exists or no sentence reaches T (`RagSettings.rerank_display=False` forces them). Cost: about 1 s extra per ask and the 87 MB model must be cached locally. Test suite never loads the model (`tests/conftest.py`).
