"""Exact section-number lookup for citation-style queries (Step 18, deterministic feature).

A user who types "801.109" or "21 CFR 801.109(b)" wants that section, not a ranked guess.
This module finds such citations in a query with regular expressions and returns the
chunks of the cited section directly. It is NOT a ranking experiment: it is not wired into
the CV or the fresh-set evaluation, because the project's queries contain no citations.

Patterns recognised (case-insensitive):
  801.109                     a bare section number
  21 CFR 801.109, 21 C.F.R. 801.109, 21 CFR § 801.109, § 801.109, sec. 801.109, section 801.109
  801.109(b)(2)               paragraph marks are parsed and returned, but lookup is by section
A citation counts only if its part is a known CFR part AND the section exists in the corpus
chunks given to the lookup, so numbers like "510(k)" or "13485" never match. A bare number
followed by a unit (mg, ml, %, mm, cm, kg, g) is skipped ("201.5 mg" is a dose, not a section).

Module separation: build one SectionLookup per module (device or medicine) from that module's
chunks, so a device query never returns a medicine section.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from src.common.schemas import Chunk, Hit

PARTS = frozenset({201, 208, 211, 801, 803, 806, 807, 809, 812, 820, 830})

_CITE = re.compile(
    r"""(?ix)
    (?:(?:21\s*c\.?\s*f\.?\s*r\.?\s*(?:part\s*)?|§+\s*|\bsec(?:tion|\.)?\s*)\s*)?   # optional cue
    (?<![\d.])(?P<part>\d{3})\.(?P<sec>\d{1,4})(?![\d.]*\d)                         # 801.109
    (?P<para>(?:\([a-z0-9]{1,3}\))*)                                                # (b)(2)
    (?P<unit>\s*(?:mg|ml|mm|cm|kg|mcg|g|%)\b)?                                      # dose guard
    """
)
_CUE = re.compile(r"(?i)(21\s*c\.?\s*f\.?\s*r|§|\bsec(?:tion|\.))")


@dataclass(frozen=True)
class Citation:
    """One section citation found in a query."""

    part: int
    section: str  # "801.109"
    paragraph: str  # "(b)(2)" or ""
    cued: bool  # True if introduced by 21 CFR, section, sec. or the section sign


def parse_citations(query: str) -> list[Citation]:
    """Finds section citations in a query, in order, without checking the corpus.

    A bare number followed by a unit is skipped unless a cue such as "21 CFR" or "§"
    introduces it.
    """
    out: list[Citation] = []
    for m in _CITE.finditer(query):
        part = int(m.group("part"))
        if part not in PARTS:
            continue
        cued = bool(_CUE.search(m.group(0)))
        if m.group("unit") and not cued:
            continue
        out.append(Citation(part, f"{m.group('part')}.{m.group('sec')}", m.group("para") or "", cued))
    return out


class SectionLookup:
    """Maps section numbers to chunk ids for one module and answers citation queries."""

    name = "section_lookup"

    def __init__(self, chunks: list[Chunk]) -> None:
        """Args:
            chunks: the chunks of ONE module (so lookups cannot cross modules).
        """
        self._by_section: dict[str, list[Chunk]] = defaultdict(list)
        for c in chunks:
            if c.section:
                self._by_section[c.section].append(c)
        for lst in self._by_section.values():
            lst.sort(key=lambda c: _chunk_order(c.chunk_id))

    def sections(self) -> set[str]:
        """All section numbers known to this lookup."""
        return set(self._by_section)

    def citations(self, query: str) -> list[Citation]:
        """The citations in the query whose section exists in this module's chunks."""
        seen: set[str] = set()
        out = []
        for c in parse_citations(query):
            if c.section in self._by_section and c.section not in seen:
                seen.add(c.section)
                out.append(c)
        return out

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Chunks of every cited section, in citation order then chunk order; [] if none cited.

        Scores are all 1.0 (exact match), so this is a lookup, not a relevance ranking.
        """
        hits: list[Hit] = []
        for cit in self.citations(query):
            for ch in self._by_section[cit.section]:
                hits.append(Hit(doc_id=ch.chunk_id, score=1.0, rank=len(hits) + 1, text=ch.text))
        return hits[:k]


def _chunk_order(chunk_id: str) -> int:
    """Chunk number inside its section: ..._c3 -> 3, a single-chunk section -> 0."""
    m = re.search(r"_c(\d+)$", chunk_id)
    return int(m.group(1)) if m else 0
