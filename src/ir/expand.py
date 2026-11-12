"""Query expansion with a general regulatory synonym list (Step 17b).

THE IDEA
Users say "over the counter" and "maker"; the CFR says "OTC" and "manufacturer".
BM25 only matches identical words, so those queries miss the right chunks
(the vocabulary mismatch problem). Query expansion adds the known synonyms to
the query before searching.

Worked example, with the group {manufacturer, maker, labeler}:
  query            "address of the maker on the box"
  group fires      because "maker" is in the query
  terms added      "manufacturer", "labeler"   (and "package", "carton" from
                   the box group)
  BM25 then scores the original words at weight 1.0 and the added words at a
  lower weight (for example 0.5), so a synonym can help a chunk but cannot
  outvote the user's own words.

The lexicon is data/eval/synonyms.json. Matching is on whole words or word
sequences, case-insensitive, with hyphens and punctuation treated as spaces. There
is no stemming, so "relabeling" and "relabel" are listed separately.

Run the lexicon check:  python -m src.ir.expand --check
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from src.common.schemas import Hit
from src.ir.base import Retriever
from src.ir.bm25 import BM25Retriever, InvertedIndex, _top_k
from src.ir.tokenizer import tokenize

SYNONYMS_PATH = Path("data/eval/synonyms.json")
_WORD = re.compile(r"[a-z0-9]+")


def words(text: str) -> list[str]:
    """Lowercase alphanumeric words; hyphens and punctuation split words."""
    return _WORD.findall(text.lower())


def contains_phrase(tokens: list[str], phrase: list[str]) -> bool:
    """True if phrase occurs as a contiguous run inside tokens."""
    n = len(phrase)
    return n > 0 and any(tokens[i:i + n] == phrase for i in range(len(tokens) - n + 1))


@dataclass(frozen=True)
class Expansion:
    """Result of expanding one query."""

    added: tuple[str, ...] = ()
    groups: tuple[str, ...] = ()


@dataclass
class SynonymExpander:
    """Expands queries using synonym groups.

    Args:
        groups: list of group dicts (id, source, terms, ...).
        sources: if given, only groups whose source is in this set are used
            (for example {"cfr_definition"} for the "without failure-derived"
            ablation).
    """

    groups: list[dict]
    sources: frozenset[str] | None = None
    _active: list[dict] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._active = [g for g in self.groups if self.sources is None or g["source"] in self.sources]

    @classmethod
    def from_file(cls, path: str | Path = SYNONYMS_PATH,
                  sources: set[str] | None = None) -> "SynonymExpander":
        """Loads groups from the synonyms JSON file."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data["groups"], frozenset(sources) if sources else None)

    def expand(self, query: str) -> Expansion:
        """Returns the synonyms to add for this query.

        A group fires when any of its terms occurs in the query. Every other term
        of the group is added unless the query already contains all of its index
        tokens (so adding it would change nothing).
        """
        qwords = words(query)
        qindex = set(tokenize(query))
        added: list[str] = []
        fired: list[str] = []
        for g in self._active:
            if not any(contains_phrase(qwords, words(t)) for t in g["terms"]):
                continue
            fired.append(g["id"])
            for t in g["terms"]:
                # Skip a term only if the index already sees all its tokens in the
                # query. "over-the-counter" is ONE index token while "over the counter"
                # is two, so a query using one form still gets the other added.
                if set(tokenize(t)) <= qindex or t in added:
                    continue
                added.append(t)
        return Expansion(tuple(added), tuple(fired))


class ExpandedBM25Retriever(BM25Retriever):
    """BM25 where expansion terms count with a lower weight than query terms.

    Scoring is the same as BM25Retriever.search except that each term's
    contribution is multiplied by its weight: 1.0 for words in the query, and
    `weight` for words that only come from expansion.
    """

    def __init__(self, index: InvertedIndex, expander: SynonymExpander,
                 weight: float = 0.5, name: str = "bm25_exp",
                 k1: float = 1.5, b: float = 0.75) -> None:
        super().__init__(index, k1=k1, b=b)
        self.expander = expander
        self.weight = weight
        self.name = name

    def term_weights(self, query: str) -> dict[str, float]:
        """Maps each index token to its weight (query tokens 1.0, expansion tokens w)."""
        weights = {t: 1.0 for t in set(self.ix.tok(query))}
        for term in self.expander.expand(query).added:
            for tok in self.ix.tok(term):
                weights.setdefault(tok, self.weight)
        return weights

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Top-k chunks by weighted BM25."""
        scores: dict[int, float] = defaultdict(float)
        for term, w in self.term_weights(query).items():
            idf = self.idf(term)
            for doc, tf in self.ix.postings.get(term, {}).items():
                norm = tf + self.k1 * (1 - self.b + self.b * self.ix.doc_len[doc] / (self.ix.avgdl or 1))
                scores[doc] += w * idf * tf * (self.k1 + 1) / norm
        return _top_k(scores, self.ix, k)


class AppendExpansionRetriever:
    """Wraps any retriever (for example dense) and appends the synonyms to the query text."""

    def __init__(self, base: Retriever, expander: SynonymExpander, name: str) -> None:
        self.base = base
        self.expander = expander
        self.name = name

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Searches the base retriever with the expanded query string."""
        extra = self.expander.expand(query).added
        return self.base.search(" ".join([query, *extra]), k=k)


def check_lexicon(groups: list[dict], chunks: list[dict]) -> tuple[list[str], bool]:
    """Checks every group against the corpus; returns (report lines, all_ok).

    For cfr_definition groups the check fails unless some evidence section has
    at least two of the group's terms in its text. For every term it reports how
    many chunks contain it, so terms that appear nowhere (useless as expansion
    targets) are visible.
    """
    by_section: dict[str, list[str]] = defaultdict(list)
    chunk_words = []
    for c in chunks:
        w = words(c["text"])
        by_section[c["section"]].extend(w)
        chunk_words.append(w)
    lines: list[str] = []
    ok = True
    for g in groups:
        counts = {t: sum(contains_phrase(w, words(t)) for w in chunk_words) for t in g["terms"]}
        best = 0
        for sec in g.get("evidence", []):
            best = max(best, sum(contains_phrase(by_section.get(sec, []), words(t)) for t in g["terms"]))
        status = "ok" if best >= 2 else "no co-occurrence"
        if g["source"] == "cfr_definition" and best < 2:
            ok = False
            status = "FAIL"
        lines.append(f"{g['id']:14s} {g['source']:15s} evidence_terms={best} {status:17s} "
                     + ", ".join(f"{t}={n}" for t, n in counts.items()))
    return lines, ok


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Check or try the synonym lexicon.")
    ap.add_argument("--check", action="store_true", help="verify groups against the corpus")
    ap.add_argument("--corpus", default="data/processed/regs.jsonl")
    ap.add_argument("--synonyms", default=str(SYNONYMS_PATH))
    ap.add_argument("--try", dest="try_query", help="show the expansion of one query")
    args = ap.parse_args()
    exp = SynonymExpander.from_file(args.synonyms)
    if args.try_query:
        print(exp.expand(args.try_query))
    if args.check:
        chunks = [json.loads(line) for line in Path(args.corpus).read_text(encoding="utf-8").splitlines()
                  if line.strip()]
        lines, ok = check_lexicon(exp.groups, chunks)
        print("\n".join(lines))
        print("lexicon check:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
