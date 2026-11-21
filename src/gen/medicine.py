"""Load the separate medicine corpus without importing vision or retrieval libraries."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.common.schemas import Chunk

DEFAULT_CORPUS = Path(__file__).resolve().parents[2] / 'data/medicine/corpus.jsonl'


def load_medicine_metadata(directory: Path) -> dict[str, dict]:
    """Load sourced SPL aliases/labelers bound to the matching pinned product fingerprint."""
    path = directory/'metadata.json'
    if not path.exists():
        return {}
    products = {r['setid']: r for r in json.loads((directory/'products.json').read_text())}
    result = {}
    for row in json.loads(path.read_text()):
        source = products[row['setid']]
        if row['version'] != source['version'] or row['setid'] in result:
            raise ValueError('Metadata identity/version mismatch')
        for value in row['aliases']+row['labelers']+row['titles']:
            if (value['xml_sha256'] != source['xml_sha256'] or value['url'] != source['url']
                    or value['effective_date'] != source['effective_date'] or not value['value']):
                raise ValueError('Metadata source mismatch')
        result[row['setid']] = row
    return result


def load_medicine_corpus(path: str | Path = DEFAULT_CORPUS) -> list[Chunk]:
    """Validate all medicine Chunk rows before returning indexable passages.

    No retrieval index is created. Reject mixed modules, duplicate identities,
    unknown/missing keys and altered content hashes rather than partly indexing
    an invalid corpus. Product effective dates live in adjacent products.json.
    """
    chunks = []
    seen = set()
    with Path(path).open(encoding='utf-8') as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or set(row) != set(Chunk.model_fields):
                raise ValueError(f'Invalid Chunk keys on line {line_number}')
            chunk = Chunk.model_validate(row)
            if chunk.module != 'medicine' or not chunk.text.strip() or not chunk.chunk_id:
                raise ValueError(f'Expected a nonempty medicine passage on line {line_number}')
            if chunk.chunk_id in seen:
                raise ValueError(f'Duplicate medicine chunk: {chunk.chunk_id}')
            if chunk.hash != hashlib.sha256(chunk.text.encode()).hexdigest()[:16]:
                raise ValueError(f'Content fingerprint mismatch: {chunk.chunk_id}')
            seen.add(chunk.chunk_id)
            chunks.append(chunk)
    if not chunks:
        raise ValueError('Medicine corpus is empty')
    return chunks
