# Label checker spec (Step 21a)

Status: approved, implemented in `src/checker/` (21b) and `src/api/` (21c). Section 9 records the decisions taken after review.

The checker takes one label extraction (from CV), one product record and the regulation corpus, and returns `Flag` objects (`src/common/schemas.py`, locked) with citations. **Rules decide, retrieval cites.** No LLM is involved: every verdict is computed by a deterministic rule, and retrieval only finds the regulation text to show beside it. The checker never says a label is compliant. A label with no flags means "no rule found a problem", and the coverage list (below) says which rules actually ran.

## 1. Inputs and outputs

| Item | Source | Notes |
|---|---|---|
| `LabelExtraction` | `src/cv/extract.py` (`extract_label`), fields as read (post-correction off) | Text fields: `product_name`, `manufacturer`, `manufacturer_address`, `model`, `lot`, `expiry`. Keyed fields carry their printed key, for example `REF: TEST-M001`, `EXP: 2027-05-01`. Strip with `src.cv.fields.split_key_value`. |
| `ProductRecord` | `src/common/schemas.py`, the version the label was made against (`LabelVersion.product_version`) | `name`, `model`, `manufacturer`, `manufacturer_address`, `udi_di`, `extra`. |
| Corpus | `data/processed/regs.jsonl`, `module == "device"` only | A device check never touches medicine chunks. |
| Output | `CheckerResult`: `flags: list[Flag]`, `coverage: list[RuleOutcome]`, `retrieval_config` echo | `Flag` is the shared schema. Citation details (section, title, url, quote) go in the contract `Finding.citations`, built from the chunk (DATA_MODEL.md, Citation). |

`RuleOutcome` is internal to `src/checker/`: `rule_id`, `outcome` (`pass`, `fail`, `needs_human`, `not_applicable`, `not_checked`), `reason`. It exists so that an absent flag is never mistaken for "checked and fine".

## 2. Verdict vocabulary

- **fail**: the rule is deterministic, the inputs are trustworthy, a flag is raised. Severity `critical` when the problem is a hard mismatch or a violated explicit requirement, `review` otherwise.
- **needs_human**: the inputs are not trustworthy enough, or the rule cannot be decided from the extraction. A flag is raised with `needs_human=True`, severity `review`, never `critical`, and the message says why. There is no confident pass or fail on this path.
- **pass**: no flag.
- **not_applicable** / **not_checked**: no flag, listed in `coverage` with a reason (for example the product record has no `udi_di`).

`Flag.needs_human` is `True` whenever any of these holds: the OCR reading behind the verdict is below the confidence threshold, the rule needs a symbol detection while the detector is untrusted, no supporting citation was retrieved for a rule that requires one, or the rule is of the needs_human kind. It is `False` only for a confident, deterministic verdict that has its citation (or a rule marked `cite = none`).

Shared thresholds (one place, `src/checker/settings.py`):

| Setting | Default | Meaning |
|---|---|---|
| `min_ocr_confidence` | 0.8 | Same value as `consistency.DEFAULT_MIN_OCR_CONFIDENCE`, chosen before measuring. A field reading below it is "uncertain". |
| `symbol_detector_trusted` | `False` | The symbol detector in `src/cv/symbols.py` is template matching for two synthetic pictograms, and finds 0 of 204 independently drawn versions (`docs/CV_STATUS.md`). It stays untrusted until the cv-symbols work is merged and evaluated. Flip this one constant then. |
| `RETRIEVAL` | see section 5 | The only retrieval setting. |

## 3. Rule table

Severity shows the severity of a **fail**; every needs_human outcome is `review`. Citation strength: **direct** (the passage states the requirement), **indirect** (the passage is the nearest regulation text but does not state this exact rule), **none** (an internal consistency rule, no regulation applies, `evidence_chunk_ids` stays empty and the message says so).

Rules are grouped. A rule id appears in `Flag.flag_id` as `<label_id>:<rule_id>[:<field>]`, and in `Flag.kind` as the kind column.

### Group X: is the extraction usable at all

| id | kind | Checks | Inputs | Sev | needs_human instead of a verdict when |
|---|---|---|---|---|---|
| X-HEALTH | `extraction_unreliable` | The extraction has OCR text and a located label. | `warnings` | review | Any warning starting `LABEL_NOT_FOUND`, `OCR_NOT_RUN`, `OCR_FAILED`, `OCR_NO_TEXT`, `FIELD_MAPPING_SKIPPED`. This rule always yields needs_human on failure. All text rules in groups P, D, R become `not_checked` (one flag instead of a pile). Barcode rules still run, because the barcode needs no OCR. |

### Group P: extracted fields against the product record

A field comparison collapses whitespace and case, strips the printed key (`REF:`), and compares the rest as exact text. No fuzzy matching: a one-character misprint must stay visible. Confidence is the OCR confidence of the line that produced the field (`consistency.field_confidence`).

| id | kind | Checks | Inputs | Sev | needs_human instead of a verdict when | Citation query (section) |
|---|---|---|---|---|---|---|
| P-NAME | `field_mismatch` | `fields["product_name"]` equals `record.name`. | extraction, record | critical | Field absent (cannot tell "not printed" from "not read"), or field confidence unknown or below 0.8. | none |
| P-REF | `field_mismatch` | `fields["model"]` (after the key) equals `record.model`, or `record.extra["ref"]` when `model` is empty. | extraction, record | critical | Same as P-NAME. `not_applicable` when the record has neither. | none |
| P-MFR | `field_mismatch` | `fields["manufacturer"]` equals `record.manufacturer`. | extraction, record | critical | Same as P-NAME. `not_applicable` when the record has none. | "name and place of business of the manufacturer, packer or distributor on the label" (801.1), **direct** for the manufacturer name |
| P-ADDR | `field_mismatch` | `fields["manufacturer_address"]` equals `record.manufacturer_address`. | extraction, record | critical | Same as P-NAME. `not_applicable` when the record has none. | same as P-MFR, **direct** |
| P-UDI | `field_mismatch` | GTIN in the barcode (AI 01) equals `record.udi_di`. Both are padded with leading zeros to 14 digits when digits only and at most 14 long. | `barcodes[0].parsed["01"]`, record | critical | Record `udi_di` is empty (never guess, never fill it in), zero or several barcodes, or AI 01 absent. | "unique device identifier on the label of every medical device" (801.20), **indirect**: 801.20 requires a UDI, not that it equals the record |

### Group B: barcode

| id | kind | Checks | Inputs | Sev | needs_human instead of a verdict when | Citation query (section) |
|---|---|---|---|---|---|---|
| B-READ | `barcode_unreadable` | Exactly one barcode decoded and parsed. | `barcodes`, `warnings` | review | Always needs_human on failure: a decoder miss does not prove the barcode is absent. Includes `MULTIPLE_BARCODES`. Wraps `consistency.check_extraction`. | "UDI automatic identification and data capture AIDC technology plain-text" (801.40), **indirect** |
| B-GS1 | `gs1_invalid` | The raw payload parses as GS1 and the AI 01 check digit is correct (the GS1 mod 10 rule). AI 17 is a real YYMMDD date. | `barcodes[0].raw` | critical | No raw payload, or more than one barcode. A parse error from a decoded 2D symbol is a fail, because DataMatrix error correction makes a silent misdecode very unlikely. | "UDI must conform to ISO/IEC 15459 issuing agency standards" (830.20), **indirect**: the GS1 check digit rule is in the GS1 General Specifications, which are not in the corpus. The message says so. |
| B-LOT | `barcode_mismatch` | Printed lot equals AI 10. | `fields["lot"]`, `parsed["10"]` | critical | Printed lot missing, or OCR confidence unknown or below 0.8 (existing behaviour of `consistency.check_extraction`). | "UDI production identifier segment lot or batch number expiration date" (801.40), **direct** |
| B-EXP | `barcode_mismatch` | Printed expiry equals AI 17 read as `20YY-MM-DD`. | `fields["expiry"]`, `parsed["17"]` | critical | Same as B-LOT. **Skipped (not_checked) when D-FMT fails**: a wrongly formatted date cannot be compared by text, and one injected error must not raise two flags. | same as B-LOT, **direct** |

Known blind spot, inherited from `consistency.py`: characters OCR confuses (0/O, 1/I, 5/S, 8/B) compare equal, so a genuine 0 versus O misprint in lot or expiry is invisible. The 21b report lists it and the injected-error tests avoid those characters on purpose, with one separate case showing the blind spot.

### Group D: dates

| id | kind | Checks | Inputs | Sev | needs_human instead of a verdict when | Citation query (section) |
|---|---|---|---|---|---|---|
| D-FMT | `date_format` | The printed expiry value (after the key) matches `YYYY-MM-DD` and is a real calendar date. | `fields["expiry"]` | critical | Field absent, or OCR confidence below 0.8 (an unreadable digit is not a format error). | "format of dates on a medical device label year month day hyphens expiration date" (801.18), **direct** |

### Group R: required elements present

Absence is never a confident verdict, because OCR cannot tell "not printed" from "not read" yet. Every R rule therefore yields needs_human with severity `review` when the element is not found. Upgrading to a critical verdict needs per-slot emptiness from CV and is out of scope here.

| id | kind | Checks | Inputs | Sev | needs_human instead of a verdict when | Citation query (section) |
|---|---|---|---|---|---|---|
| R-UDI | `missing_element` | A machine-readable UDI is on the label: a decoded barcode with AI 01. | `barcodes` | critical | A missing or undecodable barcode is B-READ's needs_human, not R-UDI. R-UDI is raised only when exactly one barcode was decoded and parsed but AI 01 is absent, which is a fail. | "label of every medical device shall bear a unique device identifier" (801.20), **direct** |
| R-NAMEPLACE | `missing_element` | `manufacturer` and `manufacturer_address` fields are both present and non-empty. | extraction | review | Always needs_human when absent. Address completeness (street, city, State, ZIP, 801.1(d)) is **not checked**: the synthetic labels carry a street line only, so the rule would fire on every clean label. Listed under limitations. | "name and place of business of the manufacturer, packer or distributor on the label" (801.1), **direct** |
| R-RX | `missing_element` | When `record.extra.get("rx_only") == "true"`, an OCR line (confidence at least 0.8) contains `Rx only` or `Caution: Federal law restricts this device to sale by or on the order of`, ignoring case and spacing. | `ocr_blocks`, record | review | Absent statement is needs_human (the glyph for the Rx symbol is not reliably OCR-readable). `not_applicable` when the record does not mark the device prescription-only. | "prescription device label bears Rx only statement caution federal law restricts" (801.109), **direct** |

### Group S: symbols

The required set comes from the template, not from the CFR: the current template has a `manufacturer` and an `expiry` symbol slot (`consistency.EXPECTED_SYMBOLS`). 801.15 sets the conditions under which a symbol may be used without adjacent text, it does not make a particular symbol mandatory. The citation is therefore **indirect** and the message must not say a symbol is required by regulation.

| id | kind | Checks | Inputs | Sev | needs_human instead of a verdict when | Citation query (section) |
|---|---|---|---|---|---|---|
| S-MFR, S-EXP | `missing_symbol` | The expected symbol is among `extraction.symbols`. | `symbols`, template | review | **Always needs_human while `symbol_detector_trusted` is `False`, in both directions.** A detection is not confirmed as a pass (outcome `needs_human` in coverage, no flag), and a non-detection raises a `needs_human` flag, never a fail. When the constant becomes `True`, a confident non-detection becomes a fail (review). | "symbols in labeling used without adjacent explanatory text, symbols glossary" (801.15), **indirect** |

## 4. Precedence and de-duplication

1. X-HEALTH failing turns off groups P, D, R (`not_checked`). Groups B and S still run.
2. D-FMT failing turns off B-EXP. P-UDI turns off when B-READ fails.
3. One injected error should produce one flag of its own kind. Two flags about the same field are allowed only when they are different rules (for example P-NAME and a barcode rule never overlap).
4. Flag order: critical first, then review, by rule id.

## 5. Citations and retrieval

**Citation = real chunk id, section, verbatim quote copied from the chunk, never invented.**

Procedure, per rule that has a citation query:

1. The query is a fixed string in the rule table. It does not contain label content, so retrieval does not depend on what the label says and results can be cached for the process lifetime.
2. Search the device corpus with the configured retriever, `k = 10`.
3. Each rule also names `accepted_sections` (the section column above, for example `801.18`). Take the highest ranked hit whose `Chunk.section` is in that set. If none of the ten hits is accepted, the flag has **no citation**, `needs_human=True`, and the message says "no supporting regulation was retrieved". A section outside the accepted set is never attached, because a plausible-looking wrong citation is worse than none. The rank of the accepted hit (or its absence) is recorded, so 21b can report **citation hit@10 per rule**.
4. Quote: split the chunk text at paragraph breaks and sentence ends, score each segment by overlap with the query terms, return the best segment (at most about 300 characters), copied character for character. The code asserts `quote in chunk.text` and fails loudly otherwise.
5. `Flag.evidence_chunk_ids` gets the chunk id. The contract `Finding.citations[0]` gets `source_type="cfr"`, `chunk_id`, `source`, `section`, `title`, `url`, `quote`, all read from the `Chunk`.

Retrieval config comes from one setting only:

```python
@dataclass(frozen=True)
class RetrievalSettings:
    method: str = "hybrid_rrf"   # bm25 | tfidf | dense | hybrid_rrf
    module: str = "device"
    k: int = 10
    rrf_k: int = 60
    stem: bool = False
    prefix: bool = False
RETRIEVAL = RetrievalSettings()
```

This is plain hybrid RRF today. The frozen best configuration from Session B will replace the default by editing this one object. `inspectLabel` accepts an optional `retrieval` override (the contract allows it), and the response echoes the configuration used. There is no single public retrieval entry point in `src/ir` today. 21b adds a thin wrapper in `src/checker/retrieval.py` that loads chunks with `src.ir.search.load_chunks` and builds systems with `src.ir.eval.build_systems`. It does not edit `src/ir`.

Dense retrieval needs sentence-transformers and the cached embeddings. Unit tests use a stub retriever or BM25. One test marked `slow` runs the real hybrid retriever.

## 6. Corpus check done for this spec

Checked in `data/processed/regs.jsonl` (903 chunks, 435 device). Chunk ids that exist and carry the text the rules need:

| Rule(s) | Chunk id | Section |
|---|---|---|
| D-FMT | `fda_21cfr801_s801.18` | 801.18 |
| R-UDI, P-UDI | `fda_21cfr801_s801.20` | 801.20 |
| B-LOT, B-EXP, B-READ | `fda_21cfr801_s801.40` | 801.40 |
| B-GS1 | `fda_21cfr830_s830.20` | 830.20 |
| P-MFR, P-ADDR, R-NAMEPLACE | `fda_21cfr801_s801.1_c1`, `fda_21cfr801_s801.1_c2` | 801.1 |
| R-RX | `fda_21cfr801_s801.109_c1` | 801.109 |
| S-MFR, S-EXP | `fda_21cfr801_s801.15_c1` to `_c7` | 801.15 |

Retrieval has not been run for these queries yet. Whether each query ranks its expected section in the top 10 is what 21b measures, on the dev seeds, and the queries are written now, before that.

## 7. Evaluation plan (21b)

**Two layers**, so checker errors are not confused with CV errors:

- **Oracle layer:** build the `LabelExtraction` directly from the generator's ground truth (perfect OCR, confidence 1.0). Measures the rule logic only. Fast, runs in CI without CV libraries.
- **End-to-end layer:** render with `src.gen.smoke_label.build_label`, run `extract_label` (blind and template mode), then the checker. Needs the CV libraries, so these tests skip when `cv2`, `zxingcpp` or `rapidocr_onnxruntime` are missing. Reported per photo condition (clean, moderate, hard), never blended.

`src/cv/barcode.py` imports `cv2` and `zxingcpp` at module level, which CI does not install. The checker therefore has its own small `src/checker/gs1.py` (AI set 01, 17, 10, 21, mod 10 check digit, YYMMDD validity). A test compares it with `parse_gs1` on a set of payloads and is skipped when the CV libraries are absent.

**Injected errors**, made with the existing generator hooks (`build_label` options `field_values`, `symbol_overrides`, `allow_print_barcode_mismatch`), with no edit to `src/gen` or `src/cv`:

| Injection | Expected flag |
|---|---|
| Printed expiry in another format (for example `30/04/2028`) | D-FMT on `expiry`, and no B-EXP flag |
| Printed lot or expiry differs from the barcode, ISO format kept | B-LOT or B-EXP |
| Expected symbol removed | S-MFR or S-EXP (needs_human) |
| Product name text changed, record keeps the true name | P-NAME |
| Record `udi_di` changed (extra case, record side) | P-UDI |
| Record marked `rx_only`, label has no statement | R-RX (needs_human) |

**Metrics**, per injection kind and per condition, each with a Wilson 95% interval and n in every cell:

- Recall: injected labels that received a flag of the expected kind on the expected field. Reported twice: **flagged** (any flag) and **confident** (`needs_human=False`).
- Precision: flags of a kind that sit on a label with that injection, over all flags of that kind on injected and clean labels.
- False alarm rate: share of **clean** labels with at least one `review` or `critical` flag, overall and per rule.
- Citation: share of flags whose citation passes (chunk id exists, `quote in chunk.text`), and citation hit@10 per rule.

**Seeds:** development on seeds 200 and 201, final evaluation once on seeds 300, 301, 302. I will check with `git grep` that none of these seeds was used elsewhere before generating. Rule thresholds and retrieval queries are fixed before the final run, and the final run happens once.

**Caveats the report must state:** one synthetic template family; synthetic injected errors are easier than real ones; the symbol detector is in-distribution on these images and fails on independent drawings, so symbol results here do not predict real use; address text on synthetic labels is a single street line.

## 8. What 21c needs and the current gaps

Findings from reading `src/api` and the contract. These are decisions for you, not things I will change silently.

1. **No stored extraction.** The API has no extraction table and `uploadScan`, `getScan` and `getExtraction` are mocks. A real `inspectLabel` has nothing to read. Proposal: run `extract_label` on `LabelVersion.artwork_file` inside the inspect job, and store the resulting extraction in a new append-only `extractions` table (a database change in `src/api`, not a `schemas.py` change).
2. **No job store.** `getJob` is a mock. A real 202 envelope needs a small `jobs` table. Proposal: one row per state change (queued, processing, done, failed), so tables stay append-only.
3. **`recheckLabel` needs real generated artwork**, and `generateArtwork` is a mock. Proposal: recheck renders nothing. It runs the same extraction and checker on `LabelVersion.artwork_file` (the rendered preview PNG) and writes a `self_check` CheckResult with `artifact_sha256` copied from the version. Until generation is real it can only be tested on versions created by a test.
4. **`passed` means zero critical findings** (DATA_MODEL.md). A label with an unreadable barcode and a missing symbol only has `review` findings, so `passed` would be `true`. See open question 1.

## 9. Decisions (approved after review of 21a)

1. `passed` stays "zero critical findings". `CheckResult` gains `needs_human_count` and `coverage` (`rule_id`, `outcome`, `reason`), added to `openapi.yaml`, the mocks, the contract tests and DATA_MODEL (CR-17). `schemas.py` is untouched.
2. `findings` contain only problems. Passed rules appear only in `coverage`.
3. `ProductRecord.extra["rx_only"] == "true"` marks a prescription-only device. It is documented as a product registration field in DATA_MODEL and `openapi.yaml` so the UI can collect it.
4. Seeds 200 and 201 are development seeds. Seeds 300 to 302 are the final evaluation, run once, after the thresholds and queries in this document are frozen (committed).
5. The gaps in section 8 are accepted: append-only `extractions` and `jobs` tables, and `recheckArtwork` runs on the version's artwork file and copies its `artifact_sha256`.

Also required: `src/api` must import without cv2, zxingcpp or rapidocr (the extractor imports them lazily inside the job), and API tests stub the extraction.

## 10. Assumptions and known limits

- A GTIN equals the UDI-DI for GS1-issued identifiers, so P-UDI compares AI 01 with `record.udi_di`. Other issuing agencies are not handled.
- `Flag.confidence` is the OCR line confidence for text rules. For barcode rules it is 1.0 and means only "the decoder returned a payload and the rule is arithmetic on it", not a calibrated probability.
- The corpus has no GS1 General Specifications, no ISO 15223-1 and no non-US sources, so B-GS1 and S-* citations are indirect. Symbol requirements by ISO 15223-1 cannot be cited.
- US only, 21 CFR Part 801 and 830.
- The synthetic labels have no plain-text UDI line, so the plain-text half of 801.40(a) is not checked and appears in `coverage` as `not_checked`.
- Rules were written for one synthetic template family. Field names assume the extractor's naming.
- The checker reads the extraction as given. Corrections the user confirms in the UI would go through the same path.
