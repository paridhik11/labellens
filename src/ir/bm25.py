"""Own inverted index with TF-IDF (cosine) and BM25 scoring. No IR libraries used here."""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

from src.common.schemas import Hit
from src.ir.tokenizer import tokenize


class InvertedIndex:
    def __init__(self, stem: bool = False, stopwords: bool = True):
        self.stem = stem
        self.stopwords = stopwords
        self.doc_ids: list[str] = []
        self.doc_len: list[int] = []
        self.texts: list[str] = []
        self.postings: dict[str, dict[int, int]] = defaultdict(dict)  # term -> {doc_idx: tf}
        self.avgdl = 0.0

    def tok(self, text: str) -> list[str]:
        return tokenize(text, stopwords=self.stopwords, stem=self.stem)

    def build(self, docs: list[tuple[str, str]]) -> "InvertedIndex":
        for doc_id, text in docs:
            idx = len(self.doc_ids)
            self.doc_ids.append(doc_id)
            self.texts.append(text)
            toks = self.tok(text)
            self.doc_len.append(len(toks))
            tf: dict[str, int] = defaultdict(int)
            for t in toks:
                tf[t] += 1
            for t, c in tf.items():
                self.postings[t][idx] = c
        self.avgdl = sum(self.doc_len) / max(len(self.doc_len), 1)
        return self

    @property
    def n_docs(self) -> int:
        return len(self.doc_ids)

    def df(self, term: str) -> int:
        return len(self.postings.get(term, {}))

    def save(self, path: str | Path) -> None:
        data = {
            "stem": self.stem, "stopwords": self.stopwords, "doc_ids": self.doc_ids,
            "doc_len": self.doc_len, "texts": self.texts, "postings": self.postings,
            "avgdl": self.avgdl,
        }
        Path(path).write_text(json.dumps(data))

    @classmethod
    def load(cls, path: str | Path) -> "InvertedIndex":
        d = json.loads(Path(path).read_text())
        ix = cls(stem=d["stem"], stopwords=d["stopwords"])
        ix.doc_ids, ix.doc_len, ix.texts, ix.avgdl = d["doc_ids"], d["doc_len"], d["texts"], d["avgdl"]
        ix.postings = defaultdict(dict, {t: {int(k): v for k, v in p.items()} for t, p in d["postings"].items()})
        return ix


def _top_k(scores: dict[int, float], ix: InvertedIndex, k: int) -> list[Hit]:
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
    return [
        Hit(doc_id=ix.doc_ids[i], score=s, rank=r + 1, text=ix.texts[i])
        for r, (i, s) in enumerate(ranked)
    ]


class BM25Retriever:
    name = "bm25"

    def __init__(self, index: InvertedIndex, k1: float = 1.5, b: float = 0.75):
        self.ix, self.k1, self.b = index, k1, b

    def idf(self, term: str) -> float:
        n, df = self.ix.n_docs, self.ix.df(term)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def search(self, query: str, k: int = 10) -> list[Hit]:
        scores: dict[int, float] = defaultdict(float)
        for term in set(self.ix.tok(query)):
            idf = self.idf(term)
            for doc, tf in self.ix.postings.get(term, {}).items():
                norm = tf + self.k1 * (1 - self.b + self.b * self.ix.doc_len[doc] / (self.ix.avgdl or 1))
                scores[doc] += idf * tf * (self.k1 + 1) / norm
        return _top_k(scores, self.ix, k)


class TfidfRetriever:
    name = "tfidf"

    def __init__(self, index: InvertedIndex):
        self.ix = index
        n = index.n_docs
        self.idf = {t: math.log(n / len(p)) for t, p in index.postings.items()}
        norms: dict[int, float] = defaultdict(float)
        for t, p in index.postings.items():
            for doc, tf in p.items():
                norms[doc] += ((1 + math.log(tf)) * self.idf[t]) ** 2
        self.norms = {d: math.sqrt(v) for d, v in norms.items()}

    def search(self, query: str, k: int = 10) -> list[Hit]:
        q_tf: dict[str, int] = defaultdict(int)
        for t in self.ix.tok(query):
            q_tf[t] += 1
        scores: dict[int, float] = defaultdict(float)
        q_norm = 0.0
        for t, c in q_tf.items():
            if t not in self.idf:
                continue
            wq = (1 + math.log(c)) * self.idf[t]
            q_norm += wq * wq
            for doc, tf in self.ix.postings[t].items():
                scores[doc] += wq * (1 + math.log(tf)) * self.idf[t]
        q_norm = math.sqrt(q_norm) or 1.0
        for d in list(scores):
            scores[d] /= q_norm * (self.norms.get(d) or 1.0)
        return _top_k(scores, self.ix, k)
