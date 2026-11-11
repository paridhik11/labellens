# Template-based artwork revision and print verification

LabelLens proposes revised artwork. A reviewer approves it. Nothing is published automatically.

## Principle
Labels are regulated documents, so output is deterministic and auditable. We fill a template. We never use an image generation model for label artwork.

## Template spec (JSON, stored per product and version)
```json
{
  "template_id": "tpl_001", "version": 1,
  "size_mm": {"w": 100, "h": 60},
  "background": "artwork/base.svg",
  "slots": [
    {"id": "mfr_address", "type": "text", "field": "manufacturer_address",
     "bbox_mm": [5, 40, 60, 12], "font": "Arial", "size_pt": 7, "align": "left", "max_lines": 3},
    {"id": "sterile_symbol", "type": "symbol", "field": "sterilization", "bbox_mm": [70, 5, 10, 10]},
    {"id": "udi_barcode", "type": "barcode", "field": "udi", "symbology": "GS1_DataMatrix", "bbox_mm": [70, 30, 20, 20]}
  ]
}
```
The base artwork keeps everything that does not change (logos, borders, fixed text).

## Setup (once per product)
The user uploads artwork and draws a box per field, symbol and barcode, naming each slot and choosing the product field it shows. Fonts: choose from available fonts. We cannot recover an unknown font from an image, which is stated as a limitation.

## Generation pipeline
```
Change request (text or field) -> parse to structured change -> user confirms
   -> apply to a copy of the product record (draft version)
   -> impact: affected slots, symbols, linked labels (T3 retrieval + rules)
   -> checklist shown, user confirms
   -> fill template slots -> render SVG -> PDF at size_mm (vector)
   -> barcode decision (below) -> DRAFT watermark and change log
   -> self-check -> side-by-side visual diff -> reviewer approve or return
```

## Conditional barcode
- Build the GS1 payload from application identifiers: (01) GTIN or UDI-DI, (17) expiry YYMMDD, (10) lot, (21) serial where used.
- If the encoded payload for the revision equals the existing payload, keep the existing barcode image.
- If a confirmed change alters the payload, regenerate (GS1 DataMatrix or GS1-128, per product setup), validate check digit, length and date format.
- GTIN and UDI-DI values come from the product record or an authorized user. If a change needs a new identifier, raise `IdentifierRequired` and create a task "enter allocated identifier". Never invent one.

## Layout checks (become flags)
Text overflow past `max_lines` or slot bounds, clipping, font below minimum size, barcode quiet zone, symbol below minimum size, required field empty.

## Self-check (closed loop)
Run our own pipeline on the generated output: OCR the render and compare to intended fields, decode the barcode and compare to the intended payload, detect symbols and compare to the intended list, run layout checks, run the checker against the new record. Pass means zero critical flags.

## Review and approval
States: Draft, Checked, Reviewed, Published. A reviewer approves or returns for correction with a comment. Publication is separate from request where possible. Old versions are immutable. Approved package: PDF at physical size, editable template, inspection report.

## Print verification
1. Photograph the printed label.
2. Find the label quadrilateral and correct perspective (OpenCV).
3. OCR and decode the barcode.
4. Compare with the approved revision's known fields and payload (we know exactly what it should say, so this is a comparison, not retrieval).
5. Report mismatches with boxes, or ask for a clearer scan when blur, glare or low confidence is detected.
Metrics are reported per condition (clean print scan, phone photo, blur, glare).

## Guardrails
DRAFT watermark until approved. Change log with who, what, why, rules fired and evidence. UI always states: "Draft generated for review. Not a compliance determination."
