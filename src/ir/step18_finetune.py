"""Step 18d: fine-tune bge-reranker-base on synthetic in-domain queries.

DATA (no evaluation query is ever used)
  data/eval/synth_train_queries.csv has 150 queries written from corpus chunks outside
  data/eval/finetune_exclusions.json. For each query the positive is its source chunk, and
  the hard negatives come from bm25 and dense top 20: the lists are interleaved, the
  positive, every chunk of the positive's section (likely relevant too) and every excluded
  chunk are removed, and the first N_NEG left are kept. A group is [positive, negative x 3].

LOSS
  Listwise softmax cross-entropy over a group: the model scores all 4 (query, chunk) pairs and
  is trained to give the positive the highest score. Training is plain PyTorch on CPU.

VALIDATION
  Queries are split by the section of their source chunk (a section never appears on both
  sides), 80% train and 20% validation. Validation reports how often the positive ranks first
  in its group; the best epoch is kept. The 57 evaluation queries and the fresh set are not
  touched by training or by choosing the epoch.

Commands:
  python -m src.ir.step18_finetune data     writes data/processed/ft_groups.json
  python -m src.ir.step18_finetune time     times a few real training steps and projects the cost
  python -m src.ir.step18_finetune train    trains and saves the best epoch
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

from src.ir.base import Retriever
from src.ir.eval import load_chunks

SEED = 42
N_NEG = 3
DEPTH = 20
VAL_FRAC = 0.2
GROUPS_PATH = Path("data/processed/ft_groups.json")
TRAIN_CSV = Path("data/eval/synth_train_queries.csv")
EXCLUSIONS = Path("data/eval/finetune_exclusions.json")
BASE_MODEL = "BAAI/bge-reranker-base"


def hard_negatives(query: str, positive: str, section: str, bm25: Retriever, dense: Retriever,
                   section_of: dict[str, str], excluded: set[str], n: int = N_NEG,
                   depth: int = DEPTH) -> list[str]:
    """First n chunks from the interleaved bm25 and dense top-`depth` that are safe negatives.

    Not safe: the positive itself, any chunk of the positive's section, any excluded chunk.
    """
    lists = [[h.doc_id for h in bm25.search(query, k=depth)], [h.doc_id for h in dense.search(query, k=depth)]]
    out: list[str] = []
    for i in range(depth):
        for lst in lists:
            if i >= len(lst):
                continue
            cid = lst[i]
            if (cid != positive and section_of.get(cid) != section and cid not in excluded
                    and cid not in out):
                out.append(cid)
            if len(out) == n:
                return out
    return out


def build_groups(rows: list[dict[str, str]], retrievers: dict[str, tuple[Retriever, Retriever]],
                 section_of: dict[str, str], excluded: set[str], n_neg: int = N_NEG) -> list[dict]:
    """Training groups: one per synthetic query, with its positive and hard negatives."""
    groups = []
    for r in rows:
        if r["source_chunk"] in excluded:
            raise ValueError(f"{r['qid']}: source chunk is in the fine-tuning exclusion list")
        bm25, dense = retrievers[r["module"]]
        negs = hard_negatives(r["query"], r["source_chunk"], r["source_section"], bm25, dense, section_of,
                              excluded, n_neg)
        groups.append({"qid": r["qid"], "query": r["query"], "module": r["module"], "pos": r["source_chunk"],
                       "section": r["source_section"], "negs": negs})
    return groups


def split_by_section(groups: list[dict], frac: float = VAL_FRAC, seed: int = SEED) -> tuple[list[dict], list[dict]]:
    """Train/validation split in which no section appears on both sides."""
    sections = sorted({g["section"] for g in groups})
    random.Random(seed).shuffle(sections)
    target = frac * len(groups)
    val_sections: set[str] = set()
    n_val = 0
    for s in sections:
        if n_val >= target:
            break
        val_sections.add(s)
        n_val += sum(g["section"] == s for g in groups)
    return ([g for g in groups if g["section"] not in val_sections],
            [g for g in groups if g["section"] in val_sections])


def group_pairs(group: dict, texts: dict[str, str]) -> list[tuple[str, str]]:
    """The (query, chunk text) pairs of a group, positive first."""
    return [(group["query"], texts[c]) for c in [group["pos"], *group["negs"]]]


def load_rows(path: str | Path = TRAIN_CSV) -> list[dict[str, str]]:
    """Reads the validated synthetic queries."""
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- training (PyTorch, CPU)

def _load(model_name: str, threads: int):
    import os

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    torch.set_num_threads(threads)
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=1)
    return torch, tok, model


def _scores(torch, tok, model, pairs: list[tuple[str, str]], max_length: int):
    enc = tok([q for q, _ in pairs], [t for _, t in pairs], truncation="only_second", padding=True,
              max_length=max_length, return_tensors="pt")
    return model(**enc).logits.squeeze(-1)


def validate(torch, tok, model, groups: list[dict], texts: dict[str, str], max_length: int) -> dict[str, float]:
    """Share of validation groups whose positive scores highest, and the mean group loss."""
    model.eval()
    hits, loss = 0, 0.0
    with torch.no_grad():
        for g in groups:
            s = _scores(torch, tok, model, group_pairs(g, texts), max_length)
            hits += int(torch.argmax(s).item() == 0)
            loss += float(torch.nn.functional.cross_entropy(s.unsqueeze(0), torch.zeros(1, dtype=torch.long)))
    return {"top1": hits / len(groups), "loss": loss / len(groups)}


def train(groups_train: list[dict], groups_val: list[dict], texts: dict[str, str], out_dir: str | Path,
          model_name: str = BASE_MODEL, epochs: int = 2, lr: float = 2e-5, groups_per_step: int = 2,
          max_length: int = 384, threads: int = 6, max_steps: int | None = None, save: bool = True,
          freeze_embeddings: bool = True, log=print) -> dict:
    """Trains with the listwise loss; returns timing and per-epoch validation results.

    freeze_embeddings keeps the word-embedding matrix fixed (about 192M of the 278M parameters in
    XLM-R base): it makes each step much cheaper and is the usual choice for a small training set.
    """
    torch, tok, model = _load(model_name, threads)
    rng = random.Random(SEED)
    if freeze_embeddings:
        for p in model.roberta.embeddings.word_embeddings.parameters():
            p.requires_grad = False
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=lr, weight_decay=0.01)
    steps_per_epoch = (len(groups_train) + groups_per_step - 1) // groups_per_step
    total = steps_per_epoch * epochs
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min((s + 1) / max(1, int(0.1 * total)), max(0.0, (total - s) / max(1, total))))
    history: list[dict] = []
    base = validate(torch, tok, model, groups_val, texts, max_length) if groups_val and max_steps is None else None
    if base:
        log(f"[val] before training: top1 {base['top1']:.3f} loss {base['loss']:.3f}")
    best = (-1.0, None)
    step, t0 = 0, time.time()
    for epoch in range(1, epochs + 1):
        order = groups_train[:]
        rng.shuffle(order)
        model.train()
        for i in range(0, len(order), groups_per_step):
            batch = order[i:i + groups_per_step]
            pairs = [p for g in batch for p in group_pairs(g, texts)]
            s = _scores(torch, tok, model, pairs, max_length).view(len(batch), -1)
            loss = torch.nn.functional.cross_entropy(s, torch.zeros(len(batch), dtype=torch.long))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
            step += 1
            if step % 5 == 0 or max_steps:
                log(f"[train] epoch {epoch} step {step}/{total} loss {float(loss.detach()):.3f} "
                    f"{(time.time() - t0) / step:.1f} s/step, wall {(time.time() - t0) / 60:.1f} min")
            if max_steps and step >= max_steps:
                return {"sec_per_step": (time.time() - t0) / step, "steps_per_epoch": steps_per_epoch,
                        "pairs_per_step": len(pairs)}
        val = validate(torch, tok, model, groups_val, texts, max_length) if groups_val else {"top1": 0.0, "loss": 0.0}
        history.append({"epoch": epoch, **val})
        log(f"[val] epoch {epoch}: top1 {val['top1']:.3f} loss {val['loss']:.3f}")
        if save and val["top1"] > best[0]:
            best = (val["top1"], epoch)
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            model.save_pretrained(out_dir)
            tok.save_pretrained(out_dir)
            log(f"[save] best epoch so far: {epoch} (val top1 {val['top1']:.3f}) -> {out_dir}")
    return {"history": history, "best_epoch": best[1], "wall_min": (time.time() - t0) / 60,
            "val_before": base}


def prepare(corpus: str = "data/processed/regs.jsonl") -> tuple[list[dict], dict[str, str]]:
    """Builds the groups from the corpus (bm25 plain and bge-small with the query prefix per module)."""
    from src.ir.bm25 import BM25Retriever, InvertedIndex
    from src.ir.dense import BGE_QUERY_PREFIX, DenseRetriever

    chunks = load_chunks(corpus)
    texts = {c.chunk_id: c.text for c in chunks}
    section_of = {c.chunk_id: c.section for c in chunks}
    excluded = set(json.loads(EXCLUSIONS.read_text(encoding="utf-8"))["excluded_chunk_ids"])
    rets = {}
    for m in ("device", "medicine"):
        mc = [c for c in chunks if c.module == m]
        bm25 = BM25Retriever(InvertedIndex().build([(c.chunk_id, c.text) for c in mc]))
        rets[m] = (bm25, DenseRetriever.from_chunks(mc, query_prefix=BGE_QUERY_PREFIX))
    return build_groups(load_rows(), rets, section_of, excluded), texts


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Step 18d fine-tuning.")
    ap.add_argument("action", choices=["data", "time", "train"])
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--max-length", type=int, default=384)
    ap.add_argument("--steps", type=int, default=3, help="steps to time in 'time' mode")
    ap.add_argument("--out", default="data/processed/ft_reranker_bge")
    ap.add_argument("--train-embeddings", action="store_true", help="also train the word embeddings (slow)")
    a = ap.parse_args()
    groups, texts = prepare()
    GROUPS_PATH.parent.mkdir(parents=True, exist_ok=True)
    GROUPS_PATH.write_text(json.dumps(groups, indent=1), encoding="utf-8")
    tr, va = split_by_section(groups)
    n_pairs = sum(1 + len(g["negs"]) for g in tr)
    print(f"{len(groups)} groups ({sum(len(g['negs']) for g in groups)} hard negatives), train {len(tr)}, "
          f"validation {len(va)} (no shared sections); {n_pairs} training pairs per epoch")
    if a.action == "data":
        return
    if a.action == "time":
        t = train(tr, va, texts, a.out, epochs=a.epochs, lr=a.lr, max_length=a.max_length, threads=a.threads,
                  max_steps=a.steps, save=False, freeze_embeddings=not a.train_embeddings)
        total_steps = t["steps_per_epoch"] * a.epochs
        print(f"measured {t['sec_per_step']:.1f} s/step ({t['pairs_per_step']} pairs/step); "
              f"{a.epochs} epochs = {total_steps} steps = about {total_steps * t['sec_per_step'] / 60:.0f} min "
              "of training, plus validation passes")
        return
    res = train(tr, va, texts, a.out, epochs=a.epochs, lr=a.lr, max_length=a.max_length, threads=a.threads,
                freeze_embeddings=not a.train_embeddings)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
