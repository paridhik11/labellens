# Step 14d: bootstrap intervals on LLM-vs-human agreement

**Agreement of the LLM grades (claude-sonnet-5-5) with human grades on the human sample.**
This part compares the LLM-assessed qrels with human grades, so the human sample is the
only reference and it is small: 15 queries in total.

## Method
- Same agreement numbers as Step 13 (`agreement_report`), here with 95% percentile bootstrap
  intervals, 10000 resamples, seed 42.
- **The queries are resampled, not the rows.** Rows from one query share the query and the
  pool, so they are not independent, and resampling rows would give intervals that are too
  narrow. A resample draws as many queries as the slice has, with replacement, and keeps all
  graded rows of each drawn query.
- With 8 to 15 queries per slice, a percentile bootstrap is itself rough: the intervals may be
  too narrow, and a few queries with unusual grade mixes dominate them.
- 'Excluding no_answer' removes q44, whose rows are nearly all 0 and easy to agree on.
- Pari only (9 queries) is the cleanest single-annotator set. The merged set uses Pari's
  grade where both humans graded a row (Parth's file adds 6 queries of his own).

## All rows

| Slice | rows | queries | exact agreement | weighted kappa (linear) | weighted kappa (quadratic) | binary agreement | binary kappa |
|---|---|---|---|---|---|---|---|
| pari only (headline) | 182 | 9 | 0.819 [0.668, 0.930] | 0.746 [0.574, 0.886] | 0.823 [0.695, 0.921] | 0.879 [0.735, 0.977] | 0.752 [0.486, 0.950] |
| all human rows (merged) | 308 | 15 | 0.782 [0.685, 0.872] | 0.675 [0.554, 0.793] | 0.768 [0.667, 0.858] | 0.825 [0.728, 0.913] | 0.636 [0.468, 0.806] |

Format: point estimate [95% interval]. Resamples where one rater gave a single grade to
every row (kappa is then degenerate): pari only (headline): 0; all human rows (merged): 0.

## Excluding no_answer queries

| Slice | rows | queries | exact agreement | weighted kappa (linear) | weighted kappa (quadratic) | binary agreement | binary kappa |
|---|---|---|---|---|---|---|---|
| pari only (headline) | 158 | 8 | 0.791 [0.637, 0.910] | 0.725 [0.544, 0.872] | 0.807 [0.670, 0.914] | 0.861 [0.707, 0.972] | 0.724 [0.436, 0.943] |
| all human rows (merged) | 284 | 14 | 0.764 [0.663, 0.853] | 0.663 [0.538, 0.785] | 0.759 [0.654, 0.851] | 0.810 [0.707, 0.902] | 0.618 [0.440, 0.796] |

Format: point estimate [95% interval]. Resamples where one rater gave a single grade to
every row (kappa is then degenerate): pari only (headline): 0; all human rows (merged): 0.

