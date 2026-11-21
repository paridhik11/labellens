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


def identify(
    lines: list[dict[str, Any]], match: Callable[[str], dict[str, Any]], vocab: set[str], config: ScanConfig,
    *, start: float, hard_limit_s: float = HARD_LIMIT_S, cut_short: bool = False,
) -> dict[str, Any]:
    """Match the candidate strings and return ``{outcome, reason, best, tried, timed_out}`` (no HTTP, no database).

    ``match`` is the unchanged medicine matcher's ``match``. A time cut (OCR budget or matching limit) returns
    outcome ``no_reference_match`` with reason ``timeout``: a partly read photo is never identified.
    """
    candidates = build_candidates(lines, vocab, config)
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
        key = ((OUTCOME_RANK[found["outcome"]], found["score"]) if config.order == "outcome"
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
    vocab = vocabulary([p.name for p in catalog.products.values()] + [a for p in catalog.products.values()
                                                                       for a in p.aliases])
    result = identify(lines, service.matcher.match, vocab, config, start=start,
                      cut_short=not reading.get("complete", True))
    body = result_body(catalog, service.matcher, lines, result, medicine)
    extra = {"tried": result["tried"], "killed": reading.get("killed", False)}
    return ScanOutcome(body, time.monotonic() - start, extra)


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
        body = medicine.match_result(catalog, matcher, best["text"])
        used, matched_text = best["lines"], best["text"]
    body["matched_text"] = matched_text
    body["read_lines"] = [{"text": ln["text"], "confidence": ln["confidence"], "used": i in used}
                          for i, ln in enumerate(lines[:80])]
    return body
