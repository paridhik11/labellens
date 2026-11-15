# Real label photos (to be added by Pari)

This folder is empty on purpose. Every CV number in this repo so far comes from synthetic labels made by
`src/gen`. Synthetic results do not show how the pipeline behaves on a real printed label photographed with
a phone. This folder is where that check will live. No photo and no transcription here was made by the
coding agent, and none may be.

## What to add

1. About 10 phone photos of printed labels, as `.jpg`, `.jpeg` or `.png`, directly in this folder.
   - Use labels you are allowed to photograph and share. Printed copies of our own synthetic test labels
     are the safest choice (they carry the DRAFT mark and the all-zero test identifier).
   - Vary the conditions: flat and angled, good light and a visible glare spot, one with a finger on an edge.
   - Do not crop or edit the photos.
2. One file `transcriptions.csv` in this folder, typed by hand while looking at the printed label
   (not copied from any program output). One row per photo, three fields each.

## Format of `transcriptions.csv`

A header row, then one row per photo. The first column is `filename`. Every other column is a field name
from this list: `product_name`, `manufacturer`, `manufacturer_address`, `model`, `lot`, `expiry`, `serial`.
Pick the same three for every photo if you can, for example:

```csv
filename,product_name,lot,expiry
photo_01.jpg,<product name exactly as printed>,<lot value>,<expiry value>
```

Rules for typing the values:

- Type exactly what is printed, including capital letters, spaces and hyphens.
- For `model`, `lot`, `expiry` and `serial` type only the value, not the printed key. For a label that
  shows `LOT: ABC123`, type `ABC123`.
- Leave a cell empty if the field is not on the label or cannot be read by eye. Empty cells are skipped.

## How to evaluate

From the repo root, in the CV environment:

```bash
python -m src.cv.eval_real
```

With no photos or no CSV it prints that there is nothing to evaluate and stops. With both, it runs the
blind extraction mode (no template knowledge) with post-correction on every transcribed photo and prints,
per field, the number of exact matches and the character error rate. Report those numbers next to the
synthetic ones, never mixed with them.
