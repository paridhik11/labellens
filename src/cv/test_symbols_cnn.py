"""Checks for the procedural training data and the small CNN (skipped without torch)."""

import pytest

for _module in ("cv2", "PIL", "zxingcpp", "reportlab", "pypdf", "torch"):
    pytest.importorskip(_module)

import numpy as np

from src.cv.symbols_v2 import cnn
from src.cv.symbols_v2.train_data import make_samples
from src.gen.symbol_procedural import random_sample
from src.gen.symbol_styles import STYLES


def test_procedural_samples_have_ink_and_vary() -> None:
    """Each class renders ink, and two draws differ."""
    rng = np.random.default_rng(0)
    for label in ("manufacturer", "expiry", "other"):
        first, second = random_sample(label, rng, 64), random_sample(label, rng, 64)
        assert (np.asarray(first) < 128).mean() > 0.02
        assert not np.array_equal(np.asarray(first), np.asarray(second))
    assert {s.mode for s in STYLES if s.split == "train"} <= {"outline", "filled", "duo"}


def test_training_crops_have_expected_shape_and_labels() -> None:
    """The crop maker returns encoded crops with labels 0, 1 and 2, reproducibly."""
    inputs, labels = make_samples(1, 3)
    again, _ = make_samples(1, 3)
    assert inputs.shape[1:] == (2, cnn.SIDE, cnn.SIDE) and set(labels) == {0, 1, 2}
    assert np.array_equal(inputs, again)


def test_cnn_learns_a_trivial_split_and_round_trips(tmp_path, monkeypatch) -> None:
    """A tiny training run separates two obviously different crops, and saved weights reload to the same output."""
    monkeypatch.setenv("SYMBOLS_TORCH_THREADS", "1")
    solid = np.ones((30, 30), np.uint8)
    ring = np.zeros((30, 30), np.uint8)
    ring[:3], ring[-3:], ring[:, :3], ring[:, -3:] = 1, 1, 1, 1
    x = np.stack([cnn.encode(solid if i % 2 else ring) for i in range(60)])
    y = np.array([i % 2 for i in range(60)], np.int64)
    weights = cnn.train(x, y, epochs=8, seed=0, batch=16)
    path = tmp_path / "w.npz"
    np.savez(path, **weights)
    classifier = cnn.Classifier(path)
    probs = classifier.probabilities([ring, solid])
    assert probs.shape == (2, 3) and np.allclose(probs.sum(axis=1), 1, atol=1e-5)
    assert probs[0].argmax() == 0 and probs[1].argmax() == 1
