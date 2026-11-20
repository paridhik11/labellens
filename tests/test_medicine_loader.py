"""Medicine loader contract, isolation and fingerprint validation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.common.schemas import Chunk
from src.gen.medicine import load_medicine_corpus


def test_chunk_loader(tmp_path: Path) -> None:
    """Load the exact shared shape, reject mixed/changed/duplicate and empty inputs."""
    text = 'A sourced test passage with no medical advice.'
    row = Chunk(chunk_id='test', source='DailyMed', module='medicine', text=text,
                hash=hashlib.sha256(text.encode()).hexdigest()[:16]).model_dump()
    path = tmp_path / 'corpus.jsonl'
    path.write_text(json.dumps(row)+'\n')
    assert load_medicine_corpus(path)[0].model_dump() == row
    for change in ({'module': 'device'}, {'hash': 'bad'}, {'text': ''}, {'unknown': 'extra'}):
        path.write_text(json.dumps({**row, **change}))
        with pytest.raises(ValueError):
            load_medicine_corpus(path)
    path.write_text((json.dumps(row)+'\n')*2)
    with pytest.raises(ValueError, match='Duplicate'):
        load_medicine_corpus(path)
    path.write_text('')
    with pytest.raises(ValueError, match='empty'):
        load_medicine_corpus(path)


def test_repository_corpus() -> None:
    """All committed medicine chunks are indexable without changing retrieval."""
    rows = load_medicine_corpus()
    assert len(rows) == 618 and {r.module for r in rows} == {'medicine'}
