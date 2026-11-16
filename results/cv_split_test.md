# Photo test: frozen paired comparison

Condition: photo. References: LLM-generated, human review deferred.
Real-symbol accuracy unmeasured. Original photos were previously exposed, not an unseen holdout.

Before: 740a0ab. After: c50fb4a.

| Field | Before exact (95% Wilson CI) | After exact (95% Wilson CI) |
|---|---|---|
| product_name | 0/4 (0.0% to 49.0%) | 0/4 (0.0% to 49.0%) |
| lot | 3/4 (30.1% to 95.4%) | 2/4 (15.0% to 85.0%) |
| expiry | 1/4 (4.6% to 69.9%) | 0/4 (0.0% to 49.0%) |

Intervals are descriptive marginal intervals, not paired-effect significance tests.
Related layouts and the tiny convenience sample limit independence and generalization.
Errors remain in denominators. Printed keys alone are removed; case/trademarks remain exact.
No checker threshold changed. No tuning followed the single test scoring invocation.

## Deployment decision

The dev-selected candidate **regressed on test**: lot fell 3/4 to 2/4 and expiry
1/4 to 0/4; name stayed 0/4. Keep the existing 740a0ab photo-field and crop-merge
algorithms as the live default. This is a release rollback, not another tuned
candidate: no further parameter/feature selection or test scoring was performed.
The failed candidate remains reproducible at c50fb4a, including its unit tests.
Lazy CV imports, mandatory draft warnings, loaders and handoff are retained.

The photo-accuracy goal remains open. Additional independent, human-reviewed
material is needed before claiming a reliable improvement. Old all-ten scores
and dev scores must not be pooled into a new held-out result.
