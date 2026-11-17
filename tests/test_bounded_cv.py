"""Native-stall isolation, durable resume and rejection of changed scoring protocols."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from scripts.cv_experiments.bounded import run_bounded


def toy_prediction(task: tuple[str, str, str]) -> dict[str, Any]:
    """Simulate an image-dependent native stall without loading any CV package."""
    if task[0] == 'stall':
        time.sleep(5)
    return {'fields': {'lot': task[0]}}


def test_timeout_restart_resume(tmp_path: Path) -> None:
    """A stalled image is a permanent miss, other images finish, and resume never repeats them."""
    tasks = [(value, '.', 'baseline') for value in ['first', 'stall', 'last']]
    journal = tmp_path/'predictions.jsonl'
    args = {'workers': 1, 'timeout': 0.2, 'journal': journal, 'fingerprint': 'fixed', 'predict': toy_prediction}
    results = run_bounded(tasks, **args)
    assert results[0]['fields']['lot'] == 'first' and results[2]['fields']['lot'] == 'last'
    assert 'EvaluationTimeout' in results[1]['error'] and results[1]['fields'] == {}
    original = journal.read_bytes()
    assert run_bounded(tasks, **args) == results and journal.read_bytes() == original
    assert len([json.loads(line) for line in journal.read_text().splitlines()]) == 4
    with pytest.raises(ValueError, match='protocol differs'):
        run_bounded(tasks, **{**args, 'fingerprint': 'changed'})
    with pytest.raises(ValueError, match='Positive'):
        run_bounded(tasks, **{**args, 'timeout': 0})
