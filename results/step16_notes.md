## Notes (written AFTER the results above were seen)

- **Primary result:** hybrid top RRF score separates the 20 queries almost perfectly (AUROC 0.985, one near-tie: answerable ab09 at 0.03200 vs hard no_answer ab11 at 0.03202 and ab19 at 0.03200). The interval [0.930, 1.000] is wide for 10 vs 10 queries.
- **Easy-only 1.000 [1.000, 1.000]** is degenerate: with perfect separation every bootstrap resample scores 1.0. It says nothing about uncertainty (3 negatives only).
- **Margin scores run backwards.** Hybrid margin has AUROC 0.26: answerable queries tend to have several near-equal top chunks (rankers agree on a section's chunks), so a small rank-1 minus rank-2 gap goes with answerable. The pre-declared rule "low score means abstain" does not suit margin, so its precision and recall rows (abstains on 15 to 18 of 20) are not meaningful.
- **bm25 top is not comparable across queries** (it grows with query length and term rarity). Hybrid top takes few discrete values (RRF of rank positions), so it mostly measures whether both rankers put the same chunk first.
- **Possible optimism.** I drafted the answerable queries from corpus section titles, so they are probably closer to the corpus wording than real user queries. The existing medicine queries q45 to q62 would be a less biased answerable set; that check was not run. The hard no_answer queries were also written by the same person who built the pool.
- **Labels:** all relevance grades are LLM grades (claude-sonnet-5-5), not human. No no_answer query had a grade 2 chunk, so no relabelling happened; grade 1 chunks exist for 7 of the 10 no_answer queries (see "Highest grade seen").
- Not computed: cross-encoder score (none in the repo).
