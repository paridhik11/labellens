# Symbols: union rule on dev styles

**Question.** Does accepting a symbol when v1 or v2 finds it help on very hard labels? Measured on the dev styles only
(`styled_dev`: 4 styles, 64 symbols per condition, 120 absent symbols per condition), frozen settings, `scripts/symbols/union_eval.py`.
A symbol is found if either detector has a matching box (IoU >= 0.5); an absent symbol is a false positive if either reports it.

| Detector | Very hard recall | Clean / moderate / hard recall | Very hard false positives |
| --- | --- | --- | --- |
| v1 | 2/64 (3.1%; 0.9 to 10.7) | 0/64, 0/64, 2/64 | 0/120 (0.0%; 0.0 to 3.1) |
| v2 silhouette | 51/64 (79.7%; 68.3 to 87.7) | 64/64, 63/64, 63/64 | 1/120 (0.8%; 0.1 to 4.6) |
| v1 or v2 silhouette | 51/64 (79.7%; 68.3 to 87.7) | 64/64, 63/64, 63/64 | 1/120 (0.8%; 0.1 to 4.6) |
| v2 CNN | 51/64 (79.7%; 68.3 to 87.7) | 64/64, 63/64, 63/64 | 0/120 (0.0%; 0.0 to 3.1) |
| v1 or v2 CNN | 51/64 (79.7%; 68.3 to 87.7) | 64/64, 63/64, 63/64 | 0/120 (0.0%; 0.0 to 3.1) |

False positives in clean, moderate and hard: 0/120 each for every row.

**Result.** On the dev styles the union equals v2 exactly: no gain and no new false positive. v1 only knows our original drawing,
so on styles drawn differently it finds almost nothing (4/256 over all conditions) and adds nothing to v2.

**What this does not show.** The reason to want a union is to keep v1's 91.2% on very hard labels of the original artwork (v2: 76.5% and
80.4%). That set is not a dev style, so I did not measure it, as agreed. The default stays `symbol_detector="v1"`.
