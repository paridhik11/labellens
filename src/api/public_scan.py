"""Public photo scan: find which reference medicine a pack photo shows, from the text printed on it.

Method (docs in reports/public_scan.md):
1. OCR every text line of the photo (no "product name field"), in a child process with a time budget.
2. Build candidate strings: single lines, adjacent line pairs and the whole text.
3. Match each candidate with the existing medicine matcher (unchanged, threshold 0.65) and keep the best.
4. The matcher decides: matched, needs_review (top 3 products, the person confirms) or no match (not identified,
   the person types the name). A product the matcher did not accept is never shown as the answer.

A cheap lexical prefilter only chooses which candidate strings are sent to the matcher (the matcher costs about
a second each); it never accepts or rejects a product. The settings live in ``public_scan_config.json``.
"""

from __future__ import annotations

import difflib
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

CONFIG_PATH = Path(__file__).with_name("public_scan_config.json")
REPO_ROOT = Path(__file__).resolve().parents[2]
# CV4b time budget (configuration c2): shrink to 1600 px, 55 s budget, quarter turn chosen on an 800 px copy.
MAX_SIDE, BUDGET_S, SEARCH_SIDE = 1600, 55.0, 800
CHILD_TIMEOUT_S = 50.0  # the OCR child is killed here, so matching still has time to finish
HARD_LIMIT_S = 57.0  # the whole identification (OCR plus matching) never runs past this
OUTCOME_RANK = {"matched": 2, "needs_review": 1, "no_reference_match": 0}
TOKEN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class ScanConfig:
    """How candidate strings are built and chosen. Frozen in a commit before the fresh photos are scored."""

    name: str = "A"
    max_candidates: int = 12  # strings sent to the matcher (the whole text counts as one)
    min_letters: int = 4  # a line needs this many letters to be a candidate
    min_conf: float = 0.0  # OCR lines below this confidence are not candidates
    pairs: bool = True  # adjacent line pairs
    full_text: bool = True  # the whole text as one candidate
    order: str = "score"  # "score": best cosine wins; "outcome": matched beats needs_review beats none
    max_chars: int = 300  # a candidate string is cut to this length
    name_evidence: bool = False  # candidate D: a distinctive name word must be visible in the OCR text (protocol v3)
    max_words: int = 5  # D: candidate strings have 1 to this many words
    other_ingredient_check: bool = False  # candidate E: another product's ingredient word in the text means review


def load_config(path: Path = CONFIG_PATH) -> ScanConfig:
    """The frozen configuration (defaults when the file is missing)."""
    if not path.exists():
        return ScanConfig()
    return ScanConfig(**json.loads(path.read_text(encoding="utf-8")))


@dataclass
class Candidate:
    """One string to match and the OCR lines (by index) it was built from."""

    text: str
    lines: tuple[int, ...]
    priority: float = 0.0


def tokens(text: str) -> list[str]:
    """Lower-case alphanumeric words."""
    return TOKEN.findall(text.lower())


def vocabulary(names: list[str]) -> set[str]:
    """Words (3+ letters or digits) of the product names and aliases."""
    return {t for name in names for t in tokens(name) if len(t) >= 3}


SIMILAR = 0.85  # normalized edit similarity (difflib ratio) for a word to count as visible
GENERIC_CHUNK_SHARE = 0.10  # a word in this share of the corpus chunks is generic
GENERIC_HEADING_PRODUCTS = 3  # a word in section headings of this many products is generic


def similar(a: str, b: str) -> bool:
    """True when two words are the same up to OCR slips (difflib ratio at least 0.85)."""
    return a == b or difflib.SequenceMatcher(None, a, b).ratio() >= SIMILAR


def corpus_generic(catalog: Any, headings: dict[str, set[str]]) -> set[str]:
    """Words generic by the corpus alone: in a dosage form, in 10% of the chunks, in headings of 3+ products."""
    def words(text: str) -> set[str]:
        return {w for w in re.findall(r"[a-z]+", text.lower()) if len(w) >= 4}

    forms = set().union(*(words(p.fields.get("dosage_form") or "") for p in catalog.products.values()))
    chunk_df: dict[str, int] = {}
    for chunk in catalog.chunks.values():
        for w in words(chunk.text):
            chunk_df[w] = chunk_df.get(w, 0) + 1
    heading_df: dict[str, int] = {}
    for ws in headings.values():
        for w in ws:
            heading_df[w] = heading_df.get(w, 0) + 1
    total = len(catalog.chunks)
    common = {w for w, n in chunk_df.items() if n / total >= GENERIC_CHUNK_SHARE}
    return forms | common | {w for w, n in heading_df.items() if n >= GENERIC_HEADING_PRODUCTS}


def derive_distinctive(catalog: Any, headings: dict[str, set[str]]) -> tuple[list[str], dict[str, tuple[str, ...]]]:
    """Generic words and the distinctive words of each product, both derived from the corpus (protocol v3).

    Source words are letters-only words of 4+ letters of the name, aliases and active substance. A word is generic
    when it is in 2+ products, in a dosage form, in 10% of the chunks or in the headings of 3+ products.
    ``headings`` maps product id to the words of its section titles.
    """
    def words(text: str) -> set[str]:
        return {w for w in re.findall(r"[a-z]+", text.lower()) if len(w) >= 4}

    source = {pid: words(" ".join([p.name, *p.aliases, p.fields.get("active_substance") or ""]))
              for pid, p in catalog.products.items()}
    product_df: dict[str, int] = {}
    for ws in source.values():
        for w in ws:
            product_df[w] = product_df.get(w, 0) + 1
    by_corpus = corpus_generic(catalog, headings)
    generic = {w for ws in source.values() for w in ws if product_df[w] >= 2 or w in by_corpus}
    return sorted(generic), {pid: tuple(sorted(ws - generic)) for pid, ws in source.items()}


NAMES_PATH = Path(__file__).with_name("public_scan_names.json")  # 70 extra products of the med100 list
EXTRA_SPREAD = 5  # a word in the label text of this many of the 30 products is generic for the E check
EXTRA_NAME_SHARE = 3  # a word in the names of this many of the 100 products is generic for the E check


def derive_ingredient_words(
    catalog: Any, headings: dict[str, set[str]], extra_ingredients: list[str],
) -> tuple[set[str], dict[str, set[str]]]:
    """Ingredient words of ANY corpus or med100-list product, derived (protocol v4), plus each product's own words.

    Ingredient names come from the sourced generic-medicine name of each of the 30 corpus products (the SPL
    genericMedicine element, kept in the metadata with its xpath) and the ingredient field of each of the 70 extra
    products. Words are letters-only, 4+ letters. Generic words (D's list and the corpus-generic ones), words in
    the generic names of 3 or more of the 100 products, and words in the label text of 5 or more of the 30 products
    are removed. ``own`` holds every name, alias and active substance word of a corpus product (never a foreign word).
    """
    from src.api import medicine

    def words(text: str) -> set[str]:
        return {w for w in re.findall(r"[a-z]+", text.lower()) if len(w) >= 4}

    generic, _ = derive_distinctive(catalog, headings)
    generic = sorted(set(generic) | corpus_generic(catalog, headings))
    metadata = medicine.load_medicine_metadata(medicine.MEDICINE_DIR)
    own = {pid: words(" ".join([p.name, *p.aliases, p.fields.get("active_substance") or ""]))
           for pid, p in catalog.products.items()}
    per_product = [words(" ".join(a["value"] for a in metadata.get(p.setid, {}).get("aliases", [])
                                  if "genericMedicine" in a["xpath"])) for p in catalog.products.values()]
    per_product += [words(n) for n in extra_ingredients]
    df: dict[str, int] = {}
    for ws in per_product:
        for w in ws:
            df[w] = df.get(w, 0) + 1
    spread: dict[str, int] = {}  # in how many of the 30 products' label texts a word occurs
    for p in catalog.products.values():
        seen: set[str] = set()
        for chunk_id in p.chunk_ids:
            seen |= words(catalog.chunks[chunk_id].text)
        for w in seen:
            spread[w] = spread.get(w, 0) + 1
    every = set().union(*per_product)
    other = {w for w in every if w not in set(generic) and df.get(w, 0) < EXTRA_NAME_SHARE
             and spread.get(w, 0) < EXTRA_SPREAD}
    return other, own


def heading_words(directory: Path) -> dict[str, set[str]]:
    """Words of the section titles of each product (``products.json``), keyed by product id."""
    rows = json.loads((directory / "products.json").read_text(encoding="utf-8"))
    return {f"med_{r['setid'][:8]}": {w for s in r["sections"] for w in re.findall(r"[a-z]+", s["title"].lower())
                                      if len(w) >= 4} for r in rows}


def visible_words(words: tuple[str, ...], ocr_tokens: list[str]) -> list[str]:
    """The distinctive words that appear in the OCR text (whole words, similarity at least 0.85)."""
    return [w for w in words if any(similar(w, t) for t in ocr_tokens if abs(len(t) - len(w)) <= 3)]


def apply_evidence(
    found: dict[str, Any], distinct: dict[str, tuple[str, ...]], ocr_tokens: list[str],
    other: tuple[set[str], dict[str, set[str]]] | None = None,
) -> dict[str, Any]:
    """Name-evidence check on the matcher's answer (the matcher itself is untouched). See protocol_v3.md."""
    shown = []
    for pid, score in found["candidates"]:
        seen = visible_words(distinct[pid], ocr_tokens)
        if seen:
            shown.append((pid, score, len(seen) == len(distinct[pid])))
    if found["outcome"] == "no_reference_match" or not shown:
        return {**found, "outcome": "no_reference_match", "candidates": []}
    shown.sort(key=lambda row: (not row[2], -row[1]))  # all words visible first, then by score
    keep = [(pid, score) for pid, score, _ in shown]
    complete = [row for row in shown if row[2]]
    outcome = found["outcome"]
    if outcome == "matched" and not (shown[0][0] == found["candidates"][0][0] and shown[0][2] and len(complete) == 1):
        outcome = "needs_review"
    if outcome == "matched" and other is not None:  # candidate E: an ingredient the product does not have is visible
        words, own = other
        mine = own[keep[0][0]]
        foreign = [w for w in visible_words(tuple(sorted(words)), ocr_tokens) if not any(similar(w, m) for m in mine)]
        if foreign:
            outcome = "needs_review"
    return {**found, "outcome": outcome, "candidates": keep}


def lexical_priority(text: str, vocab: set[str]) -> float:
    """How much of a string looks like a product name word (OCR slips tolerated). Orders candidates only."""
    words = [t for t in tokens(text) if len(t) >= 3]
    if not words:
        return 0.0
    hits = 0.0
    for word in words:
        if word in vocab:
            hits += 1.0
        elif len(word) >= 5 and difflib.get_close_matches(word, vocab, n=1, cutoff=0.85):
            hits += 0.8
    return hits / (len(words) ** 0.5)


def build_candidates(lines: list[dict[str, Any]], vocab: set[str], config: ScanConfig) -> list[Candidate]:
    """Single lines, adjacent pairs and the full text, deduplicated, best lexical priority first, cut to the limit."""
    usable = [i for i, ln in enumerate(lines)
              if ln.get("confidence", 1.0) >= config.min_conf and sum(c.isalpha() for c in ln["text"]) >= 1]
    if config.name_evidence:
        return evidence_candidates(lines, usable, vocab, config)
    found: dict[str, Candidate] = {}

    def add(indexes: tuple[int, ...]) -> None:
        text = " ".join(lines[i]["text"].strip() for i in indexes)[: config.max_chars].strip()
        if sum(c.isalpha() for c in text) < config.min_letters:
            return
        key = " ".join(tokens(text))
        if key and key not in found:
            found[key] = Candidate(text, indexes, lexical_priority(text, vocab))

    for i in usable:
        add((i,))
    if config.pairs:
        for a, b in zip(usable, usable[1:], strict=False):
            add((a, b))
    ranked = sorted(found.values(), key=lambda c: (-c.priority, len(c.lines)))
    chosen = ranked[: max(0, config.max_candidates - (1 if config.full_text else 0))]
    if config.full_text and usable:
        full = " ".join(lines[i]["text"].strip() for i in usable)[: config.max_chars].strip()
        if sum(ch.isalpha() for ch in full) >= config.min_letters:
            chosen.append(Candidate(full, tuple(usable), lexical_priority(full, vocab)))
    return chosen


def evidence_candidates(lines: list[dict[str, Any]], usable: list[int], vocab: set[str], config: ScanConfig,
                        ) -> list[Candidate]:
    """D: strings of 1 to ``max_words`` words that contain a distinctive word (``vocab`` holds those words)."""
    found: dict[str, Candidate] = {}
    for i in usable:
        words = lines[i]["text"].split()
        for at, word in enumerate(words):
            token = "".join(tokens(word))
            if len(token) < 4 or not any(similar(token, v) for v in vocab if abs(len(v) - len(token)) <= 3):
                continue
            for lo, hi in ((at, at + 1), (at, at + config.max_words), (max(0, at - config.max_words + 1), at + 1)):
                text = " ".join(words[lo:hi])[: config.max_chars].strip()
                key = " ".join(tokens(text))
                if key and key not in found:
                    found[key] = Candidate(text, (i,), 1.0 / (len(key.split()) ** 0.5))
    ranked = sorted(found.values(), key=lambda c: (-c.priority, c.text))
    return ranked[: config.max_candidates]


def identify(
    lines: list[dict[str, Any]], match: Callable[[str], dict[str, Any]], vocab: set[str], config: ScanConfig,
    *, start: float, hard_limit_s: float = HARD_LIMIT_S, cut_short: bool = False,
    distinct: dict[str, tuple[str, ...]] | None = None, other: tuple[set[str], dict[str, set[str]]] | None = None,
) -> dict[str, Any]:
    """Match the candidate strings and return ``{outcome, reason, best, tried, timed_out}`` (no HTTP, no database).

    ``match`` is the unchanged medicine matcher's ``match``. A time cut (OCR budget or matching limit) returns
    outcome ``no_reference_match`` with reason ``timeout``: a partly read photo is never identified.
    """
    candidates = build_candidates(lines, vocab, config)
    ocr_tokens = [t for ln in lines for t in tokens(ln["text"]) if len(t) >= 3]
    if not candidates:
        return {"outcome": "no_reference_match", "reason": "timeout" if cut_short else "no_text", "best": None,
                "tried": 0, "timed_out": cut_short}
    best: dict[str, Any] | None = None
    tried = 0
    for cand in candidates:
        if time.monotonic() - start > hard_limit_s:
            return {"outcome": "no_reference_match", "reason": "timeout", "best": None, "tried": tried,
                    "timed_out": True}
        found = match(cand.text)
        tried += 1
        if config.name_evidence:
            found = apply_evidence(found, distinct or {}, ocr_tokens, other)
        key = ((OUTCOME_RANK[found["outcome"]], found["score"]) if config.order == "outcome" or config.name_evidence
               else (found["score"],))
        if best is None or key > best["key"]:
            best = {"key": key, "found": found, "text": cand.text, "lines": cand.lines}
    assert best is not None
    if cut_short:
        return {"outcome": "no_reference_match", "reason": "timeout", "best": None, "tried": tried,
                "timed_out": True}
    outcome = best["found"]["outcome"]
    return {"outcome": outcome, "reason": None if outcome != "no_reference_match" else "no_match",
            "best": {k: best[k] for k in ("found", "text", "lines")}, "tried": tried, "timed_out": False}


@dataclass
class ScanInputs:
    """What identify needs besides the lines: candidate vocabulary, D's distinctive words, E's ingredient words."""

    vocab: set[str]
    distinct: dict[str, tuple[str, ...]] | None = None
    other: tuple[set[str], dict[str, set[str]]] | None = None


def scan_inputs(catalog: Any, config: ScanConfig) -> ScanInputs:
    """The inputs of one configuration (D and E derive their words from the corpus, protocol v3 and v4)."""
    if config.name_evidence:
        from src.api import medicine

        headings = heading_words(medicine.MEDICINE_DIR)
        _, distinct = derive_distinctive(catalog, headings)
        other = None
        if config.other_ingredient_check:
            extra = [r["ingredient"] for r in json.loads(NAMES_PATH.read_text(encoding="utf-8"))]
            other = derive_ingredient_words(catalog, headings, extra)
        return ScanInputs({w for ws in distinct.values() for w in ws}, distinct, other)
    names = [p.name for p in catalog.products.values()] + [a for p in catalog.products.values() for a in p.aliases]
    return ScanInputs(vocabulary(names))


def read_lines(path: Path, *, timeout_s: float = CHILD_TIMEOUT_S) -> dict[str, Any]:
    """OCR every line of a photo in a child process, killed at ``timeout_s``. ``complete`` False means a time cut."""
    command = [sys.executable, "-m", "src.api.public_scan_worker", str(path), str(MAX_SIDE), str(BUDGET_S),
               str(SEARCH_SIDE)]
    try:
        done = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return {"lines": [], "complete": False, "killed": True}
    for row in reversed(done.stdout.splitlines()):
        if row.startswith("{"):
            return {**json.loads(row), "killed": False}
    raise RuntimeError("the reader printed no result: " + done.stderr.strip()[-300:])


def memoise_queries(matcher: Any) -> None:
    """Make the matcher's dense model remember query encodings (same numbers, one encode per string, not four)."""
    matcher._load()
    model = getattr(matcher._dense, "_model", None)  # test stand-ins have no model
    if model is None or getattr(model, "_memoised", False):
        return
    original, cache = model.encode, {}

    def encode(sentences: Any, *args: Any, **kwargs: Any) -> Any:
        if isinstance(sentences, str):
            key = (sentences, repr(sorted(kwargs.items())))
            if key not in cache:
                cache[key] = original(sentences, *args, **kwargs)
            return cache[key]
        return original(sentences, *args, **kwargs)

    model.encode = encode
    model._memoised = True


@dataclass
class ScanOutcome:
    """The stored result of one public scan: the contract body plus the numbers the evaluation needs."""

    body: dict[str, Any]
    seconds: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)


def scan_photo(path: Path, service: Any, config: ScanConfig | None = None, *, read: Callable[..., dict[str, Any]]
               | None = None) -> ScanOutcome:
    """Photo in, contract ``PublicMatchResult`` out (``service`` is the app's MedicineService)."""
    from src.api import medicine

    config = config or load_config()
    start = time.monotonic()
    memoise_queries(service.matcher)
    reading = (read or read_lines)(path)
    lines = reading["lines"]
    catalog = service.catalog
    inputs = scan_inputs(catalog, config)
    result = identify(lines, service.matcher.match, inputs.vocab, config, start=start,
                      cut_short=not reading.get("complete", True), distinct=inputs.distinct, other=inputs.other)
    body = result_body(catalog, service.matcher, lines, result, medicine)
    extra = {"tried": result["tried"], "killed": reading.get("killed", False)}
    return ScanOutcome(body, time.monotonic() - start, extra)


def match_body(catalog: Any, found: dict[str, Any], text: str, medicine: Any) -> dict[str, Any]:
    """``medicine.match_result`` built from an answer already in hand (same fields, no second match)."""
    out: dict[str, Any] = {
        "banner": medicine.BANNER, "outcome": found["outcome"], "score_name": found["score_name"],
        "score": found["score"], "threshold": found["threshold"],
        "candidates": [medicine.candidate_json(catalog, pid, score, text) for pid, score in found["candidates"]]}
    best = found["candidates"][0][0]
    sections = medicine.reference_sections(catalog, best)
    out["sections"] = {k: sections[k] for k in ("summary", "ingredients", "warnings", "sources", "ingredients_note")}
    product = catalog.products[best]
    out["summary"] = f"{product.name}: reference label from DailyMed set {product.setid}."
    out["sources"] = sections["summary"][:1] or sections["ingredients"][:1]
    return out


def result_body(
    catalog: Any, matcher: Any, lines: list[dict[str, Any]], result: dict[str, Any], medicine: Any,
) -> dict[str, Any]:
    """The contract body (CR-27): PublicMatchResult plus ``read_lines``, ``matched_text`` and ``reason``."""
    best = result["best"]
    if result["outcome"] == "no_reference_match" or best is None:
        body: dict[str, Any] = {
            "banner": medicine.BANNER, "outcome": "no_reference_match", "candidates": [],
            "score_name": "bge_large_cosine", "score": round(best["found"]["score"], 4) if best else 0.0,
            "threshold": matcher.threshold, "reason": result["reason"] or "no_match",
            "message": {"timeout": "The photo took too long to read. Try a closer, steadier photo, or type the name.",
                        "no_text": "No readable text was found. Retake the photo closer, or type the name.",
                        }.get(result["reason"] or "", "This product is not one of the reference labels, so no "
                              "summary is shown. You can type the name instead.")}
        used: tuple[int, ...] = ()
        matched_text = ""
    else:
        body = match_body(catalog, best["found"], best["text"], medicine)
        used, matched_text = best["lines"], best["text"]
    body["matched_text"] = matched_text
    body["read_lines"] = [{"text": ln["text"], "confidence": ln["confidence"], "used": i in used}
                          for i, ln in enumerate(lines[:80])]
    return body


if __name__ == "__main__":
    if "--words" in sys.argv:
        from src.api import medicine

        catalog = medicine.MedicineCatalog()
        generic, distinct = derive_distinctive(catalog, heading_words(medicine.MEDICINE_DIR))
        extra = [r["ingredient"] for r in json.loads(NAMES_PATH.read_text(encoding="utf-8"))]
        other, _ = derive_ingredient_words(catalog, heading_words(medicine.MEDICINE_DIR), extra)
        listing = {"generic": generic, "ingredient_words_for_E": sorted(other),
                   "distinctive": {catalog.products[p].name: list(w) for p, w in distinct.items()}}
        print(json.dumps(listing, indent=1))
        target = REPO_ROOT / "results/public_scan/derived_words.json"
        target.write_text(json.dumps(listing, indent=1), encoding="utf-8")
