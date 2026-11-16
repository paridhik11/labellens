"""Structured edit validation and the rules text parser (docs/CHANGE_SPEC.md sections 2 and 3).

Deterministic and English only. A request is parsed only when every clause gives exactly one supported field and
exactly one new value. Anything else is reported, never guessed. The optional provider path runs only after the
rules failed, and every proposal goes through the same checks plus a verbatim check against the typed text.
"""
from __future__ import annotations

import re
from collections.abc import Mapping

from src.change.fields import ALIAS_TO_FIELD, FIELDS, InvalidValue, check_edit_set, normalise_value, resolve_field
from src.change.models import ChangeError, Edit, EditProvider, EditResult, ParseResult, Unassessed

_ALIASES = sorted(ALIAS_TO_FIELD, key=len, reverse=True)
_ALIAS_ALT = "|".join(re.escape(a).replace(r"\ ", r"[\s_-]+") for a in _ALIASES)
MENTION = re.compile(rf"\b({_ALIAS_ALT})\b", re.IGNORECASE)
SPLIT_AND = re.compile(rf"\s+and\s+(?=(?:the\s+)?(?:{_ALIAS_ALT})\b)", re.IGNORECASE)
NEGATION = re.compile(r"\b(do not|don't|dont|not change|no change|never)\b", re.IGNORECASE)
FROM_TO = re.compile(r"\bfrom\s+(?P<old>.+?)\s+to\s+(?P<new>.+)$", re.IGNORECASE)
ARROW = re.compile(r"^\W*(?P<old>.+?)\s*(?:->|=>|→)\s*(?P<new>.+)$")
VERB_TO = re.compile(r"\bto\s+(?P<new>.+)$", re.IGNORECASE)
IS_NOW = re.compile(r"^\s*(?:is\s+now|is|should\s+be|:)\s*(?P<new>.+)$", re.IGNORECASE)
NEW_FIELD = re.compile(r"\bnew\s*$", re.IGNORECASE)
VERBS = re.compile(r"\b(change|update|set|replace|switch|correct)\b", re.IGNORECASE)
SUPPORTED = tuple(FIELDS)


def _clean(value: str) -> str:
    """Strip surrounding quotes, whitespace and a trailing full stop."""
    text = value.strip().strip("\"'“”‘’").strip()
    return text[:-1].rstrip() if text.endswith(".") else text


def validate_edits(raw_edits: list[dict[str, str | None]], current: Mapping[str, str]) -> EditResult:
    """Check structured edits against the current record values.

    Unknown fields and invalid values are returned as `unassessed`, not raised. A duplicate field, or an edit whose
    new value equals the current value, raises ChangeError (the whole request is refused). A given old_value that
    differs from the record gives a warning, and the record's value is used.
    """
    result = EditResult()
    resolved: list[tuple[str, dict[str, str | None]]] = []
    for raw in raw_edits:
        name = resolve_field(raw["field"] or "")
        if name is None:
            result.unassessed.append(Unassessed(
                raw["field"] or "", "unknown_field",
                f"Unknown field {raw['field']!r}. Supported fields: {', '.join(SUPPORTED)}.",
            ))
            continue
        resolved.append((name, raw))
    check_edit_set([name for name, _ in resolved])
    for name, raw in resolved:
        try:
            new_value = normalise_value(name, raw["new_value"] or "")
        except InvalidValue as error:
            result.unassessed.append(Unassessed(name, error.code, error.message))
            continue
        old_value = current.get(name, "")
        if new_value == old_value:
            raise ChangeError("no_change", f"{name} already has this value ({old_value!r}); nothing to change.")
        given = raw.get("old_value")
        if given is not None and re.sub(r"\s+", " ", given).strip() != old_value:
            result.warnings.append(
                f"old_value_mismatch: the {name} you gave as old ({given!r}) is not the record's value "
                f"({old_value!r}). The record's value is used."
            )
        result.edits.append(Edit(name, old_value, new_value))
    return result


def _parse_clause(clause: str, verb_seen: bool) -> tuple[dict[str, str] | None, str | None]:
    """One clause to an edit dict, or (None, issue). `verb_seen`: the request has a verb like change or set."""
    if NEGATION.search(clause):
        return None, f"ambiguous: a negation in {clause!r}"
    mentions = list(MENTION.finditer(clause))
    names = {ALIAS_TO_FIELD[re.sub(r"[\s_-]+", " ", m.group(1).lower())] for m in mentions}
    if not names:
        return None, f"unknown: no supported field named in {clause!r}"
    if len(names) > 1:
        return None, f"ambiguous: {sorted(names)} are named in {clause!r}; give one field per clause"
    name = next(iter(names))
    last = mentions[-1]
    before, after = clause[: mentions[0].start()], clause[last.end():]
    old: str | None = None
    new: str | None = None
    if (m := FROM_TO.search(after)):
        old, new = m.group("old"), m.group("new")
    elif (m := ARROW.match(after)):
        old, new = m.group("old"), m.group("new")
    elif (verb_seen or VERBS.search(before)) and (m := VERB_TO.search(after)):
        new = m.group("new")
    elif (m := IS_NOW.match(after)):
        new = m.group("new")
    elif NEW_FIELD.search(before) and after.strip():
        new = after
    if new is None or not _clean(new):
        return None, f"ambiguous: no new value found for {name} in {clause!r}"
    edit = {"field": name, "new_value": _clean(new)}
    if old is not None and _clean(old):
        edit["old_value"] = _clean(old)
    try:
        normalise_value(name, edit["new_value"])
    except InvalidValue as error:
        kind = "ambiguous" if error.code == "ambiguous_date" else "invalid_value"
        return None, f"{kind}: {error.message}"
    return edit, None


def parse_rules(raw_text: str) -> ParseResult:
    """The rules path. All clauses must parse, otherwise nothing is returned."""
    text = (raw_text or "").strip()
    if not text:
        return ParseResult("empty", issues=["The request is empty."])
    clauses = [c.strip() for piece in re.split(r"[\n;]+", text) for c in SPLIT_AND.split(piece) if c.strip()]
    edits: list[dict[str, str]] = []
    issues: list[str] = []
    verb_seen = bool(VERBS.search(text))
    for clause in clauses:
        edit, issue = _parse_clause(clause, verb_seen)
        if edit:
            edits.append(edit)
        if issue:
            issues.append(issue)
    if issues:
        status = "unknown" if all(i.startswith("unknown") for i in issues) and not edits else "ambiguous"
        return ParseResult(status, issues=issues)
    return ParseResult("parsed", edits=edits)


def _verbatim(value: str, raw_text: str) -> bool:
    """True when `value` appears in the typed text (case-insensitive, whitespace collapsed)."""
    collapse = lambda s: re.sub(r"\s+", " ", s).strip().casefold()  # noqa: E731
    return bool(collapse(value)) and collapse(value) in collapse(raw_text)


def parse_request(raw_text: str, provider: EditProvider | None = None) -> ParseResult:
    """Rules first. Only when they fail and a provider is set, ask it, then validate every proposal."""
    result = parse_rules(raw_text)
    if result.status == "parsed" or provider is None or result.status == "empty":
        return result
    try:
        proposals = provider.propose_edits(raw_text, SUPPORTED)
    except Exception:  # a provider failure must never reach the client
        return result
    edits: list[dict[str, str]] = []
    seen: set[str] = set()
    for proposal in proposals or []:
        name = resolve_field(str(proposal.get("field", "")))
        new = str(proposal.get("new_value", ""))
        old = proposal.get("old_value")
        if name is None or name in seen or not _verbatim(new, raw_text) or (old and not _verbatim(str(old), raw_text)):
            continue
        try:
            normalise_value(name, new)
        except InvalidValue:
            continue
        seen.add(name)
        edit = {"field": name, "new_value": re.sub(r"\s+", " ", new).strip()}
        if old:
            edit["old_value"] = re.sub(r"\s+", " ", str(old)).strip()
        edits.append(edit)
    if not edits:
        return result
    return ParseResult("parsed", edits=edits, issues=result.issues, source="llm")
