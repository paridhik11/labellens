# Template spec (contract, Step 19b)

A label template describes one existing label artwork so LabelLens can refill it with updated product values without redrawing anything else. This document fixes the JSON shape, the physical units, the named SVG groups the renderer must emit, and the GS1 barcode rule. It extends `docs/GENERATION.md` and matches the template on Parth's branch (`cv-fixes:src/gen/templates/test_device.json`). The entity is `LabelTemplate` in `DATA_MODEL.md` (CR-2).

Artwork is filled from this template only. It is never produced by an image generation model.

## 1. Units and coordinates

| Quantity | Unit | Rule |
|---|---|---|
| Label size `size_mm` | millimetres | `{w, h}`, both greater than 0. The printed PDF page is exactly this size. |
| Slot box `bbox_mm` | millimetres | `[x, y, w, h]`. Origin is the top left corner of the label, x to the right, y downwards. |
| Font size `size_pt` | typographic points | 1 pt = 1/72 inch = 25.4/72 mm (about 0.3528 mm). |
| PDF | points | Page width = `w * 72 / 25.4` pt, height = `h * 72 / 25.4` pt. PDF y runs upwards, so the renderer flips: `pdf_y = h - y - box_h`. |
| SVG | millimetres | Root element `width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}"`, so one SVG user unit is one millimetre and `bbox_mm` can be used directly. |
| Image coordinates (OCR, symbol boxes) | pixels | Stay in the original image's pixels (as `OcrBlock.bbox` does). To compare with a slot, scale by `(image_width - 1) / w` and `(image_height - 1) / h` after perspective correction, as `src/cv/extract.py` on Parth's branch does. |

Worked example: a 100 x 60 mm label gives a PDF page of 283.46 x 170.08 pt. A slot at `[5, 40, 60, 12]` sits 5 mm from the left and 40 mm from the top. In the PDF its bottom left corner is at (14.17 pt, 22.68 pt), because 60 - 40 - 12 = 8 mm.

## 2. Template JSON

```json
{
  "template_id": "tpl_exampledevice_carton",
  "version": 1,
  "product_id": "prd_exampledevice",
  "size_mm": {"w": 100, "h": 60},
  "background": "artwork/base.svg",
  "slots": [
    {"id": "name", "type": "text", "field": "name",
     "bbox_mm": [5, 12, 60, 6], "font": "Helvetica", "size_pt": 12, "align": "left", "max_lines": 1},
    {"id": "mfr_address", "type": "text", "field": "manufacturer_address",
     "bbox_mm": [5, 26, 60, 10], "font": "Helvetica", "size_pt": 7, "align": "left", "max_lines": 3},
    {"id": "sterile_symbol", "type": "symbol", "field": "sterilization", "symbol_name": "sterile_eo",
     "bbox_mm": [70, 5, 10, 10]},
    {"id": "udi_barcode", "type": "barcode", "field": "udi", "symbology": "GS1_DataMatrix",
     "bbox_mm": [70, 20, 25, 25]}
  ]
}
```

### Top level

| Key | Type | Req | Rule |
|---|---|---|---|
| `template_id` | string | req | Stable across versions. |
| `version` | integer >= 1 | req | Any edit (moved slot, new font) makes a new version. Old versions are immutable. |
| `product_id` | string | req in the API | Parth's test template has no `product_id` because it is a fixture. |
| `size_mm` | `{w, h}` numbers | req | |
| `background` | string or null | req | Path of the fixed artwork (logos, borders, fixed text). `null` means a blank background, as in Parth's test template. |
| `slots` | array of Slot | req | At least one slot. |
| `min_font_pt` | number | opt | Minimum readable font size for the layout checks. Default 6. |

### Slot

| Key | Applies to | Req | Rule |
|---|---|---|---|
| `id` | all | req | Unique in the template. Letters, digits, `_` and `-`, starting with a letter, so it is a valid SVG id. |
| `type` | all | req | `text`, `symbol` or `barcode`. |
| `field` | all | req | Product field the slot shows. A `ProductRecord` field name (`name`, `model`, `manufacturer`, `manufacturer_address`, `udi_di`, `sterilization`, `storage`), a key of `ProductRecord.extra` (for example `lot`, `expiry`, `serial`, `ref`), or the reserved name `udi` for the GS1 barcode payload. Parth's test template uses `product_name` for the name slot; the API accepts it as an alias of `name`. |
| `bbox_mm` | all | req | Fully inside `size_mm`. |
| `font` | text | opt | Default `Helvetica`. Must be one of the fonts installed for the renderer. |
| `size_pt` | text | req | At least the minimum readable size (`min_font_pt`, default 6). |
| `align` | text | opt | `left` (default), `center`, `right`. |
| `max_lines` | text | opt | Default 1. Wrapped text past this is a `text_overflow` finding, never silently shrunk. |
| `symbol_name` | symbol | req | Name of the reference symbol drawn in the slot, for example `manufacturer`, `expiry`. |
| `symbology` | barcode | req | `GS1_DataMatrix` or `GS1-128`. |
| `min_size_mm` | symbol, barcode | opt | Minimum printed size checked by the layout checks. |

### Validation rules (become layout findings when broken)

| Rule | Finding kind | Severity |
|---|---|---|
| Slot box outside the label | `slot_out_of_bounds` | critical |
| Two slots overlap | `slot_overlap` | review |
| Slot overlaps the reserved DRAFT band (top 6 mm, full width) | `watermark_overlap` | critical |
| Text wraps past `max_lines` or past the box | `text_overflow` | critical |
| Font below `min_font_pt` | `font_too_small` | critical |
| Symbol or barcode below `min_size_mm` | `symbol_too_small`, `barcode_too_small` | critical |
| Barcode quiet zone not clear | `barcode_quiet_zone` | critical |
| Required field empty | `required_field_empty` | critical |

## 3. Named SVG groups

The rendered SVG is the editable template output. It must contain these groups so the editor, the side-by-side diff and the self-check can find each part without guessing.

```
<svg width="100mm" height="60mm" viewBox="0 0 100 60" data-template-id="..." data-template-version="1">
  <g id="layer-background">      fixed artwork from `background`, never edited by LabelLens
  <g id="layer-slots">
    <g id="slot-{id}" data-slot-type="text|symbol|barcode" data-field="{field}"
       data-bbox-mm="x y w h">     one group per slot, in template order
  <g id="layer-watermark">       the DRAFT mark (and "TEST DATA" when test data is used)
  <g id="layer-review">          optional change highlights for the review screen
</svg>
```

Rules:
1. Group ids are exactly `layer-background`, `layer-slots`, `slot-{id}`, `layer-watermark`, `layer-review`. Clients find slots by id, never by position.
2. `layer-watermark` is present on every draft. It is removed only in the approved export, and only when a valid approval record exists (`DATA_MODEL.md`, Review).
3. `layer-review` is never printed. The physical-size PDF export leaves it out.
4. A barcode slot group holds the barcode as vector rectangles, plus `data-payload` with the human-readable GS1 string, for example `(01)00000000000000(17)281231(10)LOT001(21)SN001`.

## 4. GS1 barcode rule

### Payload

Build the GS1 element string from application identifiers (AIs), in this order:

| AI | Meaning | Source | Format |
|---|---|---|---|
| (01) | GTIN or UDI-DI | `ProductRecord.udi_di` | `N2+N14`: exactly 14 digits, valid GS1 mod-10 check digit, fixed length (no separator needed) |
| (17) | Expiry date | `extra.expiry` (ISO date) | `N2+N6`: YYMMDD, fixed length. GS1 allows DD = 00 (meaning the last day of the month), but LabelLens always writes the real day from the ISO date. |
| (10) | Lot | `extra.lot` | `N2+X..20`: 1 to 20 characters from the GS1 AI encodable character set, variable length, FNC1 or group separator required when another AI follows |
| (21) | Serial | `extra.serial`, where used | `N2+X..20`: 1 to 20 characters, same character set, variable length, separator required when another AI follows |

Formats were checked on 2026-11-15 against GS1's machine-readable Application Identifier list (`https://ref.gs1.org/ai/GS1_Application_Identifiers.jsonld`). It gives `N2+N14` for (01), `N2+N6` for (17), and `N2+X..20` with separator required for both (10) and (21).

### Decision

Compare the payload built from the confirmed new record with the payload of the current approved label.

| Decision | When | What happens |
|---|---|---|
| `KEEP` | New payload equals the existing payload and the symbology is unchanged. | Reuse the existing barcode exactly (the same module matrix). No new barcode is drawn. |
| `REGENERATE` | The payload differs and every changed encoded value was confirmed by the user. All identifiers are present. | Draw a new barcode in the slot's symbology. Validate the check digit, lengths and date format, then decode the drawn barcode and compare it with the intended payload before saving. |
| `NEEDS_INPUT` | Anything else: an identifier is missing, a change needs a new GTIN or UDI-DI that nobody has entered, or an encoded change is not yet confirmed. | No barcode is drawn and no artwork is finalised. The server raises `IdentifierRequired` (from `schemas.py`) for a missing identifier and creates the task "enter allocated identifier". The API returns `required_identifier`, for example `udi_di`. |

Never invent identifiers. GTIN and UDI-DI values come only from the product record or an authorized user. The only allowed stand-in is the test placeholder `00000000000000`, and only when the request is explicitly marked as test data. The draft then prints "TEST DATA | DRAFT", following the renderer on Parth's branch.

Mapping to Parth's renderer: its manifest field `barcode_action` is `reused` (= `KEEP`) or `generated` (= `REGENERATE`). It raises `IdentifierRequired` or refuses an unconfirmed encoded change, which together correspond to `NEEDS_INPUT`.

### Worked examples

| Change | Old payload | New payload | Decision |
|---|---|---|---|
| New manufacturer address | `(01)00000000000000(17)281231(10)LOT001(21)SN001` | same | `KEEP`. The address is printed text only. |
| Sterilization method EO to gamma | same as above | same | `KEEP`. The text and symbol slots change, the barcode does not. |
| Confirmed new lot `LOT002` | `...(10)LOT001...` | `...(10)LOT002...` | `REGENERATE` |
| New model that needs a new UDI-DI, none entered | `(01)00000000000000...` | cannot be built | `NEEDS_INPUT`, `required_identifier = udi_di` |
| Expiry changed in the change text but not confirmed | `...(17)281231...` | `...(17)291231...` | `NEEDS_INPUT` until confirmed |

## 5. Fonts and limits

The user picks fonts from the installed list. LabelLens cannot recover an unknown font from a scanned image. This is a stated limitation, not something the system guesses.

## Assumptions

1. Millimetres from the top left, y downwards, matches both `docs/GENERATION.md` and the code on Parth's branch, which scales `bbox_mm` with `(width - 1) / w`.
2. `GS1-128` (with a hyphen) is the symbology string, because Parth's renderer accepts `GS1_DataMatrix` and `GS1-128`. `GENERATION.md` only names it in prose.
3. The named SVG groups are a contract for the renderer. The current renderer on Parth's branch writes the SVG through ReportLab and does not yet emit these group ids. That is a gap for Parth, not something this step changes.
4. The 6 mm DRAFT band and the 6 pt minimum font size are defaults chosen for the contract. They are not regulatory values, and a product setup may change them.
5. `product_name` is accepted as an alias of `name` so Parth's fixture validates unchanged.
6. The lot and serial limits (20 characters, `N2+X..20`) were confirmed on 2026-11-15 against GS1's published AI list (ref.gs1.org). That list is the machine-readable form of the GS1 General Specifications AI table. I did not read the full General Specifications PDF.
7. The serial (21) is included only where the product uses serialisation. The payload order (01), (17), (10), (21) follows `GENERATION.md` and Parth's renderer.
8. The older example in `docs/GENERATION.md` has a symbol slot without `symbol_name`, so it does not pass this spec. I left `GENERATION.md` unchanged because it is outside this step. This spec is the newer contract.
