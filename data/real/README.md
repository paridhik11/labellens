# DailyMed real medicine-label artwork

Source: National Library of Medicine. This dataset contains original company-
submitted package artwork and matched Structured Product Labeling (SPL) XML.
These are **label artwork, not phone photos**. This is the medicine dataset;
it is not pooled with the professional-device synthetic dataset.

## What the ground truth means

`truth.csv` contains fields taken from the saved, same-version XML. Each selected
image is referenced by an `observationMedia` object in a principal-display-panel
section (code `51945-4`). Its section text names one package NDC that also appears
in the structured product's packaging data. Both XML and image come from the
same versioned ZIP, rather than unrelated current-image/current-XML endpoints.
Multi-product documents and panels containing multiple separate images are
excluded. Original image and XML bytes are retained without resizing or editing.

These are source-backed reference fields, not human-verified pixel transcriptions.
A product's registered name can differ in formatting or word order from its
artwork. `field_evidence` records whether the product name, strength and company
name can also be found in the paired section text; it does not certify their
visibility in the image. `visible_fields_verified` is false. Do not score exact
OCR transcription blindly against every CSV cell without defining normalization
and checking field visibility for that evaluation.

The `manufacturer` column uses only an explicitly supplied manufacturer
organization in the structured product. It is not filled with the SPL author:
that organization is recorded separately as `labeler`. Missing manufacturer is
unknown, not a guessed alias. Strength is a JSON list of active-ingredient names,
numerator values/units and denominator values/units, preserving source quantities
without silently converting or choosing one ingredient in a combination product.

Lot and expiry remain blank because no per-image values were independently
verified. They are not inferred from XML publication, effective, marketing or
revision dates. Blank does not mean that no such field is printed. Symbols and
barcodes have not been annotated or decoded. No OCR was run on this dataset.
There is no real-label accuracy result yet, and no symbol-detection score can be
computed from these files without additional annotations.

## Files

- `manifest.json`: selected IDs, set IDs, SPL versions, original image filenames,
  source/ZIP URLs, UTC download dates, field evidence, image geometry and SHA-256
  fingerprints (file checksums used to detect changed bytes).
- `truth.csv`: one row per selected image, generated from the same manifest.
- `images/`: unmodified original JPEG, PNG or GIF package-artwork images.
- `source/`: unmodified SPL XML from each selected versioned ZIP.
- `candidates.json`: frozen seeded candidate order and discovery URLs.

A selected record's `media_id`, `section_id` and `section_text` make its image
association inspectable. In the XML, inspect `setId` and `versionNumber`, the
`manufacturedProduct` or `manufacturedMedicine`, and the principal-display-panel
section's `renderMultiMedia`/`observationMedia` link. NDCs use the source spelling;
no GTIN or other identifier is synthesized from them.

## Selection and reproducibility

Build target: 60 labels. Seed: 42. Discovery is interleaved across 20 medicine-name
queries and caps each labeler at three selected records. Duplicate image bytes
are excluded. Selected documents are human OTC or prescription labels. The
collector records exclusions and stops with `complete=false` if the target
cannot be reached or a network failure prevents collection. Source image shapes
and resolutions are recorded objectively; no unmeasured image-quality grade is
invented. This is a small, purposive evaluation set, not a representative sample
of all DailyMed products.

Discovery results can change on the live service. Rebuilding from the committed
manifest uses pinned set IDs and SPL versions and checks exact image/XML hashes.
The live current XML is used only to avoid downloading unsuitable ZIPs; accepted
records always come from and are verified against the pinned versioned ZIP.

```sh
# Offline integrity/source validation, with no network or OCR:
/opt/anaconda3/envs/labellens-cv/bin/python scripts/build_real_set.py --output data/real --validate

# Rebuild the pinned files into a new folder:
/opt/anaconda3/envs/labellens-cv/bin/python scripts/build_real_set.py --rebuild-from data/real/manifest.json --output /tmp/labellens-real-rebuilt

# Start a NEW selection in a new folder; live discovery may differ:
/opt/anaconda3/envs/labellens-cv/bin/python scripts/build_real_set.py --output /tmp/labellens-real-new --count 60 --seed 42

# Resume only an incomplete selection, using its frozen candidates:
/opt/anaconda3/envs/labellens-cv/bin/python scripts/build_real_set.py --output /tmp/labellens-real-new --count 60 --seed 42 --resume

# Offline builder and committed dataset tests:
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider tests/test_real_set.py
```

The builder uses Python's standard library and the project's existing Pillow
installation. No dependency was added. Each response is bounded, archives are
read without extracting paths, source requests are paced, transient failures have
bounded retries, and permanent network failures stop the build. The dataset is
kept below 200 MB, including source XML. The final committed images are included
in Git because the measured set is below that limit.

## Source access and rights checked before downloading

Checked on 2026-11-15:

1. DailyMed offers structured label XML and package-image downloads through its
   documented public services; no login or API key is required for these URLs.
2. The SPL media service supplies source-image links, while the archive download
   supports a pinned set ID plus SPL version.
3. NLM's web policy permits reuse of government works but separately notes that
   company-contributed text and images may retain copyright. We do not claim a
   blanket open license for package artwork, brands or logos.
4. This small set is collected for LabelLens research/evaluation. Original
   notices and source attributions are retained. Further redistribution or reuse
   must respect any applicable rights; NLM does not guarantee an item's status.
5. DailyMed says its in-use labeling may differ from FDA-approved labeling and
   NLM does not review SPL content before publication. This set is not a source
   of medical advice, a compliance determination or an endorsement.

Sources:

- XML API: https://dailymed.nlm.nih.gov/dailymed/webservices-help/v2/spls_setid_api.cfm
- Image API: https://dailymed.nlm.nih.gov/dailymed/webservices-help/v2/spls_setid_media_api.cfm
- Discovery filters: https://dailymed.nlm.nih.gov/dailymed/webservices-help/v2/spls_api.cfm
- Versioned ZIP downloads: https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm
- DailyMed source/disclaimer: https://dailymed.nlm.nih.gov/dailymed/about-dailymed.cfm
- NLM copyright policy: https://www.nlm.nih.gov/web_policies.html#copyright

## Completed snapshot and actual results

Collected on 2026-11-15, from 14:09:22 to 14:27:42 UTC. The completed snapshot
contains **60 images and 60 same-version XML records**, from **44 labelers** after
normalizing capitalization. Original image/XML files total **27,040,032 bytes**;
the whole dataset is about **27.5 MB**, below the 200 MB limit. Shape counts are
37 compact, 16 wide and 7 tall; these describe geometry, not photo conditions or
quality grades. All 60 images were also reviewed in contact sheets to confirm
that they contain package artwork, not pill photos or unrelated diagrams.

| Field | Available in saved structured source | Mention supported by paired panel text |
|---|---:|---:|
| Product name | 60 | 41 |
| Package NDC | 60 | 60 |
| Ingredient strength quantities | 60 | 40 |
| Labeler | 60 | 10 |
| Explicit manufacturer organization | 0 | 0 |
| Lot | 0, unverified | 0 |
| Expiry | 0, unverified | 0 |

The panel-text column is the collector's conservative normalized-text presence
check, not OCR or proof of visibility. No field has been declared a verified
pixel transcription. In particular, do not count the 60 labelers as 60 known
manufacturers. Missing manufacturer, lot and expiry data is a limitation of this
reference set, not evidence that these fields are absent on the artwork.

Executed offline dataset tests:

```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider tests/test_real_set.py
16 passed in 0.58s
```

These checks open every image, verify hashes and source/CSV agreement, reject
corrupt or mismatched data and exercise collection, interrupted-build resume,
blocked-network handling and pinned rebuilding. A separate live rebuild of three
actual selected records also reproduced their exact original image/XML hashes;
the complete 60-record set was validated locally. No OCR or barcode decoding was
run on these real images. The existing device/photo evaluator is not changed;
this source-backed medicine set needs its own evaluation mapping and any desired
pixel/symbol annotations before scoring those tasks.
