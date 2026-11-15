#!/bin/bash
# The single CLIP run on held-out and real data (threshold frozen in results/symbols_frozen_clip.json). Logged.
export SYMBOLS_TORCH_THREADS=${SYMBOLS_TORCH_THREADS:-4}
for d in styled_heldout styled_heldout_anch real_artwork real_labels_eval; do
  path=data/synthetic/$d; [ "$d" = real_labels_eval ] && path=data/real_labels_eval
  ${PY:-python} scripts/symbols/clip_eval.py score --dataset $path --allow-heldout --group style --records results/logs/final/clip_$d.json > results/logs/final/clip_$d.md 2> results/logs/final/clip_$d.err
done
