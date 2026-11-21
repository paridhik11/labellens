# Public scan evaluation protocol, amendment v2 (written before anything is scored)

This amendment replaces the data of `protocol.md` (v1). The method, the three candidate configurations A, B and C
and the selection rule of v1 are unchanged. The synthetic stand-in packs of v1 (`make_packs.py`) were never scored:
the only thing ever run on them was OCR caching of 4 dev images, whose output was deleted. The generator was removed.

## Data: real package-label artwork from DailyMed

- Source: the images inside the principal display panel section (LOINC 51945-4) of the PINNED SPL of each product
  (`src/gen/public_scan_acquire.py`; pinned SPL xml files from the med100 branch, sha256 in
  `src/gen/public_scan_images.json`). Image bytes come from the DailyMed media service by file name. Every image is
  pinned by sha256 in that file (145 images, 0 products skipped).
- Positives: the 30 reference products, up to 2 images each (40 images). Decoys: the 70 extra human medicines of the
  med100 candidate list, none of them in the 30 (105 images, first image only is used). No product was skipped.
- Product-level split (seed 42, `scripts/public_scan/make_real_photos.py`): positives 15 dev, 15 fresh; decoys 15 dev,
  40 fresh, 15 unused. No product appears in both sets (checked: overlap is empty).
- Conditions: `artwork` (the image unchanged; the project simulator's `clean` condition applies no change, so
  clean and unaltered artwork are the same row), `moderate` and `hard` (`src/gen/augment.py`). Artwork under 1400 px
  on the long side is enlarged before moderate and hard. Seed per photo = first 8 hex digits of
  sha256(image sha256 + condition). JPEG quality 90.
- List and hashes: `results/public_scan/photos_v2.json` (every photo with source sha256, rendered sha256, seed,
  set, expected product). 285 photos: dev_real 108 (63 positive, 45 decoy), fresh_real 177 (57 positive, 120 decoy).
- Device packs: the 20 CV4 dev photos (dev) and the 50 CV4b fresh photos (scored once, reported separately, they
  can only test false identification; exposure to the older name-in-OCR check as stated in v1).

## Known risk, registered now

Four decoys share a word with a reference product name, so a correct reading of their label can legitimately sit
close to a reference product: Hydrochlorothiazide and olmesartan/amlodipine/HCTZ (dev), Valsartan and
pioglitazone with metformin (fresh). They stay in the evaluation, count as decoys, and are listed separately in the
report. A match of any of them to a reference product counts as a wrong identification.

## Sets and use

| Set | Content | Use |
|---|---|---|
| dev_real | 15 positive products, 15 decoy products, three conditions each | tuning of A, B, C |
| dev_device | 20 CV4 dev device photos | tuning (false identification) |
| fresh_real | 15 positive products, 40 decoy products, three conditions each | scored ONCE with the frozen config |
| fresh | the 50 CV4b device photos | scored ONCE with the frozen config, reported separately |

Measures, selection rule and gate are those of `protocol.md`, with these additions: results are reported per
condition (artwork, moderate, hard) with Wilson 95% intervals, and the confusable decoys are listed separately.

## What this can and cannot show

Real label artwork with simulated camera conditions. Not real phone photos of real packs: glare on a bottle, curved
surfaces, shelf clutter, motion blur and real lighting are not represented, and the artwork is the flat label that
the corpus product itself publishes, so reading it is easier than reading a pack in a hand. Real-photo performance
stays unmeasured. All labels were read by software; positives' expected names are the SPL product names.
