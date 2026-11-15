"""A small CPU-only CNN that classifies a candidate crop as manufacturer, expiry or other.

Input is two 48 by 48 channels computed from the candidate's ink map (so lighting and polarity of the photo do not
matter): the ink itself and its hole-filled silhouette. Training data are procedurally drawn pictograms from the
*seen* geometry families (``src.gen.symbol_procedural``) pushed through the same candidate finder as real photos,
plus candidate crops mined from the train split of the styled label set. Dev and held-out styles are never read here.

    python -m src.cv.symbols_v2.cnn train --out data/models/symbols_cnn.npz

At most 4 torch threads are used. Weights are stored as plain arrays in an ``.npz`` file.
"""

from __future__ import annotations

import argparse
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np

from src.cv.symbols_v2.candidates import Candidate, propose
from src.cv.symbols_v2.refs import silhouette

CLASSES = ("manufacturer", "expiry", "other")
SIDE = 48
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WEIGHTS = ROOT / "data" / "models" / "symbols_cnn.npz"
torch = None  # imported lazily so the rest of the package works without torch


def encode(ink: np.ndarray) -> np.ndarray:
    """Turn a 0/1 ink crop into the (2, SIDE, SIDE) float input."""
    ink = ink.astype(np.uint8)
    plain = cv2.resize(ink.astype(np.float32), (SIDE, SIDE), interpolation=cv2.INTER_AREA)
    filled = cv2.resize(silhouette(ink).astype(np.float32), (SIDE, SIDE), interpolation=cv2.INTER_AREA)
    return np.stack([plain, filled]).astype(np.float32)


def _load_torch():
    """Import torch on first use and cap its threads."""
    global torch
    if torch is None:
        import torch as _torch

        _torch.set_num_threads(int(os.environ.get("SYMBOLS_TORCH_THREADS", "4")))
        torch = _torch
    return torch


def build_model():
    """The classifier: three conv blocks and a small dense head (about 60 thousand weights)."""
    t = _load_torch()
    nn = t.nn

    def block(cin: int, cout: int):
        return nn.Sequential(nn.Conv2d(cin, cout, 3, padding=1), nn.BatchNorm2d(cout), nn.ReLU(), nn.MaxPool2d(2))

    return nn.Sequential(
        block(2, 16), block(16, 32), block(32, 48), nn.Flatten(), nn.Dropout(0.3),
        nn.Linear(48 * 6 * 6, 48), nn.ReLU(), nn.Linear(48, len(CLASSES)),
    )


def _patch_worker(job: tuple[int, int, int]) -> tuple[np.ndarray, np.ndarray]:
    """Make ``count`` training crops of every class from one seed (worker for the process pool)."""
    from src.cv.symbols_v2.train_data import make_samples

    seed, count, _ = job
    return make_samples(seed, count)


def build_training_set(per_class: int, workers: int = 4, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Procedural crops: arrays of shape (n, 2, SIDE, SIDE) and integer labels."""
    chunk = 250
    jobs = [(seed * 1000 + index, chunk, 0) for index in range(max(1, per_class // chunk))]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        parts = list(pool.map(_patch_worker, jobs))
    return np.concatenate([p[0] for p in parts]), np.concatenate([p[1] for p in parts])


def train(
    inputs: np.ndarray, labels: np.ndarray, *, epochs: int = 25, seed: int = 0, batch: int = 128
) -> dict[str, np.ndarray]:
    """Train the model and return its weights (state dict as numpy arrays)."""
    t = _load_torch()
    t.manual_seed(seed)
    rng = np.random.default_rng(seed)
    model = build_model()
    optimiser = t.optim.Adam(model.parameters(), lr=2e-3, weight_decay=1e-4)
    schedule = t.optim.lr_scheduler.CosineAnnealingLR(optimiser, epochs)
    x, y = t.from_numpy(inputs), t.from_numpy(labels.astype(np.int64))
    for epoch in range(epochs):
        model.train()
        order = rng.permutation(len(x))
        total = 0.0
        for start in range(0, len(order), batch):
            index = t.from_numpy(order[start:start + batch])
            optimiser.zero_grad()
            loss = t.nn.functional.cross_entropy(model(x[index]), y[index], label_smoothing=0.05)
            loss.backward()
            optimiser.step()
            total += loss.item() * len(index)
        schedule.step()
        if epoch % 5 == 4 or epoch == epochs - 1:
            print(f"epoch {epoch + 1}/{epochs} loss {total / len(x):.4f}", flush=True)
    return {key: value.detach().numpy() for key, value in model.state_dict().items()}


class Classifier:
    """Loaded weights plus a batch scorer (probabilities per class)."""

    def __init__(self, weights: Path | None = None) -> None:
        t = _load_torch()
        self.model = build_model()
        data = np.load(weights or DEFAULT_WEIGHTS)
        self.model.load_state_dict({key: t.from_numpy(data[key]) for key in data.files})
        self.model.eval()

    def probabilities(self, inks: list[np.ndarray]) -> np.ndarray:
        """Class probabilities (n, 3) for a list of ink crops."""
        t = _load_torch()
        if not inks:
            return np.zeros((0, len(CLASSES)), np.float32)
        batch = t.from_numpy(np.stack([encode(ink) for ink in inks]))
        with t.no_grad():
            return t.softmax(self.model(batch), dim=1).numpy()


_CLASSIFIERS: dict[str, Classifier] = {}


def cnn_featurizer(weights: str | None = None):
    """Return a featurizer for ``detector.featurize``: candidate crop to per-class probabilities."""
    key = str(weights)
    if key not in _CLASSIFIERS:
        _CLASSIFIERS[key] = Classifier(Path(weights) if weights else None)
    classifier = _CLASSIFIERS[key]

    def featurizer(candidate: Candidate, gray: np.ndarray) -> dict[str, float]:
        probs = classifier.probabilities([candidate.ink])[0]
        return {name: float(p) for name, p in zip(CLASSES, probs, strict=True)}

    return featurizer


def main(argv: list[str] | None = None) -> int:
    """Train from the command line and write the weights."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["train"])
    parser.add_argument("--out", type=Path, default=DEFAULT_WEIGHTS)
    parser.add_argument("--per-class", type=int, default=3000)
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--mined", type=Path, nargs="*", default=[], help="Train-split label sets to mine crops from")
    args = parser.parse_args(argv)
    started = time.time()
    inputs, labels = build_training_set(args.per_class, seed=args.seed)
    if args.mined:
        from src.cv.symbols_v2.train_data import mine_crops

        extra_x, extra_y = mine_crops(args.mined)
        inputs, labels = np.concatenate([inputs, extra_x]), np.concatenate([labels, extra_y])
    counts = {name: int((labels == i).sum()) for i, name in enumerate(CLASSES)}
    print("training crops", counts, f"({time.time() - started:.0f}s to make)", flush=True)
    weights = train(inputs, labels, epochs=args.epochs, seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(args.out, **weights)
    print(f"saved {args.out} ({time.time() - started:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["CLASSES", "Classifier", "build_model", "cnn_featurizer", "encode", "propose"]
