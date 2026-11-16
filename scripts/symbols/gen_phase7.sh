#!/bin/bash
# Fresh seeds 103 to 105 for the Phase 7 lot/expiry format-check evaluation (run once, after the code is frozen).
for s in 103 104 105; do
  [ -f data/synthetic/fresh$s/manifest.json ] || { rm -rf data/synthetic/fresh$s; ${PY:-python} -m src.gen.generate_dataset --output-dir data/synthetic/fresh$s --seed $s --conditions clean moderate hard hard_original very_hard; }
  [ -f data/synthetic/freshneg$s/manifest.json ] || { rm -rf data/synthetic/freshneg$s; ${PY:-python} -m src.gen.generate_negatives --output-dir data/synthetic/freshneg$s --seed $s; }
done
