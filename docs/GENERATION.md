# Draft generation: barcode and digital artwork

After a change is assessed, LabelLens generates a DRAFT revision. It proposes. A reviewer approves. Nothing is published automatically.

## Principle: templates, not image generation
Do not use an image generation model for artwork. Labels are regulated documents, so output must be deterministic and auditable.

Artwork is built from:
1. A label template (SVG) with named slots for each field and symbol.
2. The product record (fields) with the proposed change applied.
3. A symbol registry (vector SVGs with metadata).
4. A barcode generator.
Rendering produces SVG, then PDF and PNG.

## Pipeline

```
Change request
   -> impact engine (affected fields, symbols, labels)
   -> apply change to a copy of the product record (draft version)
   -> rule engine: does an identifier change? which symbols change?
   -> build barcode payload (GS1 AIs) -> render barcode
   -> fill template slots -> render artwork (SVG/PDF/PNG)
   -> mark DRAFT watermark, attach change log
   -> self-check (round trip)
   -> visual diff vs current version
   -> reviewer approval -> published version
```

## Barcode generation
- Format by use: GS1 DataMatrix or GS1-128 for UDI, per product setup.
- Payload built from application identifiers: (01) GTIN, (17) expiry YYMMDD, (10) lot, (21) serial where used.
- Compute the GTIN check digit with the GS1 algorithm, validate length and date formats.
- Important: GTIN and UDI-DI values come from the company's allocated identifiers. LabelLens never invents a GTIN. If the rule engine says a new identifier is needed, it raises a task "new UDI-DI required, enter the allocated value" instead of making one up.
- Libraries: `treepoem` or `bwip-js` for GS1 symbology, `python-barcode` as a fallback.

## Artwork generation
- Text slots: manufacturer address, sterilization text, storage, warnings, IFU reference.
- Symbol slots: chosen by the symbol registry, e.g. sterilization method maps to the matching sterile symbol variant (EO, irradiation, steam). Verify the mapping against the standard and keep it in `data/symbols/registry.json` with a source note.
- Auto-fit: shrink or wrap text within slot bounds, and flag overflow instead of silently clipping.
- Layout constraints: minimum font size, quiet zone around barcodes, minimum symbol size. Violations become flags.
- Template library: one template per label family, 3 to 5 for the project.

## Self-check (closed loop, a great evaluation story)
The generated draft is fed back through our own inspection pipeline:
1. OCR the rendered image and compare to the intended field values.
2. Decode the rendered barcode and compare to the intended payload.
3. Detect symbols and compare to the intended symbol list.
4. Run the checker against the new product record.
Pass means zero critical flags. Metrics: self-check pass rate, field fidelity (CER on rendered text), barcode round-trip success, symbol round-trip recall, overflow rate, time to produce a draft.

## Visual diff
SSIM plus region boxes between current and draft, text diff by field, symbol diff by name. Shown in Change Impact as side by side with highlights.

## Guardrails
- Every draft carries a DRAFT watermark until approved.
- Change log attached: who requested, what changed, which rules fired, evidence passages.
- Publication requires an authorized reviewer, separate from the requester if possible.
- Old versions are immutable.
- UI always states: "Draft generated for review. Not a compliance determination."
