#!/bin/bash
# The single final run of the frozen detectors (see results/symbols_frozen_config.json). Logged in results/heldout_log.jsonl.
mkdir -p results/logs/final
for d in styled_heldout styled_heldout_anch real_artwork real_labels_eval; do
  grp="style condition"; [ "$d" = real_labels_eval ] && grp="style"
  ${PY:-python} scripts/symbols/final_eval.py --dataset $( [ "$d" = real_labels_eval ] && echo data/real_labels_eval || echo data/synthetic/$d ) --allow-heldout --group $grp --records results/logs/final/$d.json > results/logs/final/$d.md 2> results/logs/final/$d.err
done
