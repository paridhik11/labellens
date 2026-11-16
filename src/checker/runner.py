"""Runs the rules of docs/CHECKER_SPEC.md on one extraction and one product record."""
from __future__ import annotations

import re
from datetime import date

from src.checker import gs1
from src.checker.citations import CITATION_SPECS, Citation, find_citation
from src.checker.models import CheckerResult, Finding, RuleOutcome
from src.checker.retrieval import default_retriever, module_chunks
from src.checker.settings import CheckerSettings
from src.common.schemas import Chunk, LabelExtraction, ProductRecord
from src.cv.consistency import check_extraction, field_confidence
from src.cv.fields import CONFUSABLE_TO_DIGIT, split_key_value
from src.ir.base import Retriever

UNRELIABLE_PREFIXES = ("LABEL_NOT_FOUND", "OCR_NOT_RUN", "OCR_FAILED", "OCR_NO_TEXT", "FIELD_MAPPING_SKIPPED")
RX_PHRASES = ("rxonly", "cautionfederallawrestrictsthisdevicetosalebyoronthe" + "orderof")
KEYED_FIELDS = ("model", "lot", "expiry", "serial")
_CITATION_CACHE: dict[tuple[int, int, str, int], Citation | None] = {}
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _same(a: str, b: str) -> bool:
    """Exact comparison after collapsing whitespace and case. No fuzzy matching, so a misprint stays visible."""
    return re.sub(r"\s+", " ", a).strip().casefold() == re.sub(r"\s+", " ", b).strip().casefold()


def _value(extraction: LabelExtraction, field: str) -> str | None:
    """Field text without its printed key (REF:, LOT:, EXP:), or None when the field was not read."""
    text = extraction.fields.get(field)
    if text is None or not text.strip():
        return None
    return split_key_value(text)[2].strip() if field in KEYED_FIELDS else text.strip()


def _valid_date(text: str) -> bool:
    """True for a real calendar date written YYYY-MM-DD."""
    if not _ISO.match(text):
        return False
    try:
        date(int(text[:4]), int(text[5:7]), int(text[8:]))
    except ValueError:
        return False
    return True


class _Run:
    """Collects findings and coverage for one check, and attaches citations from one retriever."""

    def __init__(self, extraction: LabelExtraction, settings: CheckerSettings, retriever: Retriever,
                 chunks: dict[str, Chunk]) -> None:
        self.x = extraction
        self.s = settings
        self.retriever = retriever
        self.chunks = chunks
        self.findings: list[Finding] = []
        self.coverage: list[RuleOutcome] = []

    def citation(self, rule_id: str) -> Citation | None:
        """Citation for a rule, looked up once per retriever (the rule queries are fixed)."""
        spec = CITATION_SPECS.get(rule_id)
        if spec is None:
            return None
        key = (id(self.retriever), id(self.chunks), rule_id, self.s.retrieval.k)
        if key not in _CITATION_CACHE:  # the queries are fixed, so one lookup per retriever and rule is enough
            _CITATION_CACHE[key] = find_citation(spec, self.retriever, self.chunks, self.s.retrieval.k)
        return _CITATION_CACHE[key]

    def done(self, rule_id: str, outcome: str, reason: str = "") -> None:
        """Record a rule outcome with no finding."""
        self.coverage.append(RuleOutcome(rule_id=rule_id, outcome=outcome, reason=reason))  # type: ignore[arg-type]

    def flag(self, rule_id: str, kind: str, severity: str, message: str, *, field: str = "", observed: str = "",
             expected: str = "", confidence: float = 0.0, human: bool = False) -> None:
        """Raise a finding. A cited rule with no retrieved passage is forced to needs_human and review severity."""
        cite = self.citation(rule_id)
        if rule_id in CITATION_SPECS and cite is None:
            human = True
            message += " No supporting regulation passage was retrieved."
        if human:
            severity = "review"
        self.findings.append(Finding(
            flag_id=f"{self.x.label_id}:{rule_id}", kind=kind, severity=severity,  # type: ignore[arg-type]
            message=message, observed=observed, expected=expected, confidence=confidence, needs_human=human,
            rule_id=rule_id, field=field, evidence_chunk_ids=[cite.chunk_id] if cite else [],
            citations=[cite] if cite else [],
        ))
        self.done(rule_id, "needs_human" if human else "fail", message)


def _field_rule(run: _Run, rule_id: str, field: str, expected: str, *, text_ok: bool, label: str) -> None:
    """Compare one extracted field with the product record (rules P-NAME, P-REF, P-MFR, P-ADDR)."""
    if not expected.strip():
        return run.done(rule_id, "not_applicable", f"product record has no {label}")
    if not text_ok:
        return run.done(rule_id, "not_checked", "extraction unreliable (X-HEALTH)")
    observed = _value(run.x, field)
    if observed is None:
        return run.flag(rule_id, "field_mismatch", "review", f"The {label} was not read; compare by eye.",
                        field=field, expected=expected, human=True)
    if _same(observed, expected):
        return run.done(rule_id, "pass")
    conf = field_confidence(run.x, field)
    sure = conf is not None and conf >= run.s.min_ocr_confidence
    msg = f"Printed {label} differs from the product record."
    if not sure:
        shown = "unknown" if conf is None else f"{conf:.2f}"
        msg += f" The OCR reading is uncertain (confidence {shown})."
    run.flag(rule_id, "field_mismatch", "critical", msg, field=field, observed=observed, expected=expected,
             confidence=conf or 0.0, human=not sure)


def _check_date_format(run: _Run, text_ok: bool) -> bool:
    """Rule D-FMT. Returns False when the expiry is unread or wrongly formatted (B-EXP is then skipped)."""
    x = run.x
    exp_text = _value(x, "expiry") if text_ok else None
    if not text_ok:
        run.done("D-FMT", "not_checked", "extraction unreliable (X-HEALTH)")
        return True
    if exp_text is None:
        run.flag("D-FMT", "date_format", "review", "The expiry date was not read from the label.", field="expiry",
                 expected="YYYY-MM-DD", human=True)
        return False
    if _valid_date(exp_text):
        run.done("D-FMT", "pass")
        return True
    conf = field_confidence(x, "expiry")
    sure = conf is not None and conf >= run.s.min_ocr_confidence
    confusion = _valid_date(exp_text.replace(" ", "").translate(CONFUSABLE_TO_DIGIT))
    if confusion or not sure:
        run.flag("D-FMT", "date_format", "review",
                 "Printed expiry does not read as YYYY-MM-DD, but it may be an OCR confusion; check by eye.",
                 field="expiry", observed=exp_text, expected="YYYY-MM-DD", confidence=conf or 0.0, human=True)
    else:
        run.flag("D-FMT", "date_format", "critical", "Printed expiry is not in the YYYY-MM-DD format.",
                 field="expiry", observed=exp_text, expected="YYYY-MM-DD", confidence=conf or 0.0)
    return False


def _check_barcode_values(run: _Run, parsed: dict[str, str], record: ProductRecord, date_ok: bool) -> None:
    """Rules B-LOT, B-EXP (through the existing consistency checker), R-UDI and P-UDI."""
    x, s = run.x, run.s
    view = x.model_copy(update={"barcodes": [x.barcodes[0].model_copy(update={"parsed": parsed})]})
    raised: set[str] = set()
    for f in check_extraction(view, expected_symbols=(), min_ocr_confidence=s.min_ocr_confidence):
        field = f.flag_id.rsplit(":", 1)[-1]
        rid = {"lot": "B-LOT", "expiry": "B-EXP"}.get(field)
        if rid is None or (rid == "B-EXP" and not date_ok):
            continue
        raised.add(rid)
        sure = f.kind == "barcode_mismatch"
        run.flag(rid, "barcode_mismatch", "critical", f.message, field=field, observed=f.observed,
                 expected=f.expected, confidence=f.confidence, human=not sure)
    for rid, field, ai in (("B-LOT", "lot", "10"), ("B-EXP", "expiry", "17")):
        if rid in raised:
            continue
        if rid == "B-EXP" and not date_ok:
            run.done(rid, "not_checked", "date format failed or unread (D-FMT)")
        elif ai not in parsed:
            run.done(rid, "not_checked", f"AI {ai} is not in the barcode")
        elif _value(x, field) is None:
            run.done(rid, "not_checked", f"printed {field} was not read")
        else:
            run.done(rid, "pass")
    if "01" not in parsed:
        run.flag("R-UDI", "missing_element", "critical", "The barcode decodes but carries no GTIN (AI 01).",
                 confidence=1.0)
        return run.done("P-UDI", "not_checked", "no AI 01 (R-UDI)")
    run.done("R-UDI", "pass")
    want = record.udi_di.strip()
    if not want:
        return run.flag("P-UDI", "field_mismatch", "review",
                        "The product record has no UDI-DI yet, so the barcode GTIN cannot be compared. "
                        "It is never filled in automatically.", field="udi_di", observed=parsed["01"], human=True)
    norm = want.zfill(14) if want.isdigit() and len(want) <= 14 else want
    if norm == parsed["01"]:
        return run.done("P-UDI", "pass")
    run.flag("P-UDI", "field_mismatch", "critical", "Barcode GTIN differs from the UDI-DI in the product record.",
             field="udi_di", observed=parsed["01"], expected=norm, confidence=1.0)


def _check_required_text(run: _Run, record: ProductRecord, text_ok: bool) -> None:
    """Rules R-NAMEPLACE and R-RX."""
    x = run.x
    if not text_ok:
        run.done("R-NAMEPLACE", "not_checked", "extraction unreliable (X-HEALTH)")
    else:
        absent = [name for name, field in (("manufacturer name", "manufacturer"),
                                           ("manufacturer address", "manufacturer_address"))
                  if _value(x, field) is None]
        if absent:
            run.flag("R-NAMEPLACE", "missing_element", "review",
                     "Not read from the label: " + ", ".join(absent) + ". Name and place of business must appear "
                     "on the label; compare by eye.", observed=", ".join(absent), human=True)
        else:
            run.done("R-NAMEPLACE", "pass", "address completeness is not checked")
    if record.extra.get("rx_only") != "true":
        run.done("R-RX", "not_applicable", "product is not registered as prescription only (extra.rx_only)")
    elif not text_ok:
        run.done("R-RX", "not_checked", "extraction unreliable (X-HEALTH)")
    else:
        compact = [re.sub(r"[^a-z0-9]", "", b.text.casefold().replace("℞", "rx"))
                   for b in x.ocr_blocks if b.conf >= run.s.min_ocr_confidence]
        if any(p in c for c in compact for p in RX_PHRASES):
            run.done("R-RX", "pass")
        else:
            run.flag("R-RX", "missing_element", "review", "Prescription-only product, but no 'Rx only' or "
                     "'Caution: Federal law restricts' statement was read; compare by eye.", human=True)


def _check_symbols(run: _Run) -> None:
    """Rules S-MFR and S-EXP. While the detector is untrusted both directions need a human."""
    found = {s.name for s in run.x.symbols}
    trusted = run.s.symbol_detector_trusted
    for name in run.s.expected_symbols:
        rid = {"manufacturer": "S-MFR", "expiry": "S-EXP"}.get(name, f"S-{name.upper()}")
        if name in found and not trusted:
            run.done(rid, "needs_human", "detected, but the symbol detector is untrusted; a detection is not a pass")
        elif name in found:
            run.done(rid, "pass")
        else:
            note = "" if trusted else " (the symbol detector is untrusted, so this is not a verdict)"
            run.flag(rid, "missing_symbol", "review", f"Expected symbol '{name}' was not detected{note}.",
                     field=name, expected=name, human=not trusted)


def run_checks(
    extraction: LabelExtraction, record: ProductRecord, *, settings: CheckerSettings | None = None,
    retriever: Retriever | None = None, chunks: dict[str, Chunk] | None = None,
) -> CheckerResult:
    """Apply every rule and return findings (problems only), coverage and the retrieval config used."""
    settings = settings or CheckerSettings()
    chunks = chunks if chunks is not None else module_chunks(settings.retrieval.module)
    retriever = retriever if retriever is not None else default_retriever(settings.retrieval)
    run = _Run(extraction, settings, retriever, chunks)
    x = extraction

    bad = [w for w in x.warnings if w.startswith(UNRELIABLE_PREFIXES)]
    text_ok = not bad
    if bad:
        run.flag("X-HEALTH", "extraction_unreliable", "review",
                 "The label could not be read reliably, so text checks were skipped: " + "; ".join(bad[:3]),
                 observed=str(len(bad)), human=True)
    else:
        run.done("X-HEALTH", "pass")

    _field_rule(run, "P-NAME", "product_name", record.name, text_ok=text_ok, label="product name")
    _field_rule(run, "P-REF", "model", record.model or record.extra.get("ref", ""), text_ok=text_ok, label="REF")
    for rid, field, expected, label in (
        ("P-MFR", "manufacturer", record.manufacturer, "manufacturer"),
        ("P-ADDR", "manufacturer_address", record.manufacturer_address, "manufacturer address"),
    ):
        if text_ok and expected.strip() and _value(x, field) is None:
            run.done(rid, "not_checked", "not read; reported by R-NAMEPLACE")  # one flag per injected error
        else:
            _field_rule(run, rid, field, expected, text_ok=text_ok, label=label)

    parsed: dict[str, str] | None = None
    if len(x.barcodes) != 1 or not x.barcodes[0].raw:
        run.flag("B-READ", "barcode_unreadable", "review",
                 f"Expected one readable GS1 barcode, decoded {len(x.barcodes)}; a decoder miss does not prove "
                 "it is absent.", observed=str(len(x.barcodes)), expected="1", human=True)
        for rid in ("B-GS1", "B-LOT", "B-EXP", "P-UDI", "R-UDI"):
            run.done(rid, "not_checked", "no single barcode payload (B-READ)")
        date_ok = _check_date_format(run, text_ok)
    else:
        run.done("B-READ", "pass")
        try:
            parsed = gs1.parse_gs1(x.barcodes[0].raw)
            run.done("B-GS1", "pass")
        except ValueError as error:
            run.flag("B-GS1", "gs1_invalid", "critical", f"Barcode payload is not valid GS1: {error}.",
                     observed=x.barcodes[0].raw.replace("\x1d", "<GS>"), confidence=1.0)
            for rid in ("B-LOT", "B-EXP", "P-UDI", "R-UDI"):
                run.done(rid, "not_checked", "barcode payload invalid (B-GS1)")
        date_ok = _check_date_format(run, text_ok)
        if parsed is not None:
            _check_barcode_values(run, parsed, record, date_ok)

    _check_required_text(run, record, text_ok)
    _check_symbols(run)
    order = {"critical": 0, "review": 1, "info": 2}
    run.findings.sort(key=lambda f: (order[f.severity], f.rule_id))
    return CheckerResult(findings=run.findings, coverage=run.coverage, retrieval_config=settings.retrieval.echo())
