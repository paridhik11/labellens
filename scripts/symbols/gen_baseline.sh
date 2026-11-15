#!/bin/bash
# Regenerate the baseline sets (seeds 100 to 102) used in results/symbols_experiments.md
for s in 100 101 102; do
  [ -f data/synthetic/fresh$s/manifest.json ] || { rm -rf data/synthetic/fresh$s; ${PY:-python} -m src.gen.generate_dataset --output-dir data/synthetic/fresh$s --seed $s --conditions clean moderate hard very_hard; }
  [ -f data/synthetic/freshneg$s/manifest.json ] || { rm -rf data/synthetic/freshneg$s; ${PY:-python} -m src.gen.generate_negatives --output-dir data/synthetic/freshneg$s --seed $s; }
done
