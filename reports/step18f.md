# Step 18f report

**Done.** E5b frozen (`data/eval/step18_config.json`, hash checked, load and cache-rebuild line in docs/EVALUATION.md). The 242 accumulated pairs (batches 115 to 131) and the 424 web_faq fresh pairs were graded with the frozen grader (claude-sonnet-5-5, LLM grades only). The fresh set and the abstention test split were each scored once. Summary: `results/step18_final.md`.

**Fresh web_faq (30 queries), nDCG@10:** plain hybrid 0.701, hybrid+stem+prefix 0.762, E5b 0.783 (device 0.746, medicine 0.857). E5b over plain hybrid +0.082 [+0.037, +0.136]. E5b over hybrid+stem+prefix +0.021 [-0.011, +0.054], not distinguishable. chunk_derived queries were not graded and are not scored (you chose web_faq only).

**Against targets:** 0.75 nDCG@10 met pooled but not for device alone, and not in cross-validation (about 0.70). Recall@20 0.99 on the fresh set is optimistic (shallow pool); judged to rank 20 on CV it is about 0.81, below 0.90. E5b was selected on CV, so CV gains are optimistic.

**Abstention test (13 queries):** no score meets AUROC 0.90 or LOO precision 0.80; best 0.800 [0.500, 1.000]. Dev half looked better and did not hold.

**Problems:** the first abstention test run crashed (z-score features for dev missing in test mode); no output was written, I fixed it, then ran once. CI went red after the first main merge because scikit-learn was missing from ci.yml; fixed.

**State:** step17-opt merged into main (--no-ff, 768cd70, then 81e48bc for the CI fix), pushed. CI green on 81e48bc. Fast tests 461 passed, ruff clean.
