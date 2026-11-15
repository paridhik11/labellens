# Symbols, phase 1: style library and real artwork

**What I did.** I wrote a parametric library of both pictograms in 16 styles (render mode outline, filled, duo or white-on-black
badge; stroke weight; rounded or sharp; five factory and five hourglass geometry families) plus six wrong-symbol
distractors. Styles are split train (8), dev (4) and held-out (6); the held-out ones use geometry families and a render mode
no other split has. A generator prints them on whole labels (random place or beside their text) under clean, moderate,
hard and very hard conditions, with empty and distractor negatives. I also fetched real artwork and label images.

**Result.** The old detector finds 4/256 dev symbols (1.6%; Wilson 0.6 to 3.9) with 0/480 false positives. Same lesson as
the 0/204: it only knows its own drawing.

**Real data.** 14 Wikimedia Commons files (4 ISO 7000 / 15223 pictograms: public domain or CC BY-SA 4.0; 10 generic icons of
the same concept: CC0, public domain, CC BY, CC BY-SA, MIT) with URLs and licenses in
`scripts/symbols/real_symbol_sources.json`. 12 DailyMed images from 6 device-type labels
(`real_label_sources.json`). Only two carry the pictograms: a lancet carton (hourglass, factory-with-date) and a pregnancy
test carton (manufacturer). The glucose boxes carry none. Images stay local (not committed).

**Files.** `src/gen/symbol_styles.py`, `generate_styled.py`, `generate_real_artwork.py`, `scripts/symbols/fetch_real_*.py`,
the two sources JSON files, `src/gen/test_symbol_styles.py` (150 tests), `docs/SYMBOLS_V2.md`.

**Check yourself.** The held-out split really excludes F3, F4, H3, H4 and badge from train and dev (test checks it).
Truth is the glyph's tight box.

**Unsure.** All 16 styles are one author's drawings, so "held out" means unseen, not independent. The real artwork is the
independent evidence, and only 2 real labels carry the symbols.
