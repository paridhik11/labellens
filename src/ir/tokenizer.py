"""Simple tokenizer: lowercase, alphanumeric tokens, optional stopwords and light stemming."""
import re

STOPWORDS = frozenset(
    "a an and are as at be by for from has have in is it its of on or that the this to was were will with".split()
)
_TOKEN = re.compile(r"[a-z0-9]+(?:[.\-/][a-z0-9]+)*")


def light_stem(tok: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if tok.endswith(suf) and len(tok) - len(suf) >= 3:
            return tok[: -len(suf)]
    return tok


def tokenize(text: str, stopwords: bool = True, stem: bool = False) -> list[str]:
    toks = _TOKEN.findall(text.lower())
    if stopwords:
        toks = [t for t in toks if t not in STOPWORDS]
    if stem:
        toks = [light_stem(t) for t in toks]
    return toks
