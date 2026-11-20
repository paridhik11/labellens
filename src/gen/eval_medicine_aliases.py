"""Once-only evaluation of 60 committed names at the unchanged medicine threshold."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Treat any surfaced decoy candidate, including review candidates, as failing the strict gate."""
    decoys = [r for r in rows if r['kind'] == 'decoy']
    positives = [r for r in rows if r['kind'] != 'decoy']
    wrong = sum(bool(r['result']['candidates']) for r in decoys)
    return {'decoys': len(decoys), 'wrong_decoy_candidates': wrong, 'gate_passed': wrong == 0,
            'decoy_matched': sum(r['result']['outcome'] == 'matched' for r in decoys),
            'positive_matched_correct': sum(r['result']['outcome'] == 'matched' and
                                          r['predicted'] == r['expected'] for r in positives),
            'positive_matched_wrong': sum(r['result']['outcome'] == 'matched' and
                                        r['predicted'] != r['expected'] for r in positives),
            'positive_review': sum(r['result']['outcome'] == 'needs_review' for r in positives),
            'positive_no_match': sum(r['result']['outcome'] == 'no_reference_match' for r in positives)}


def main() -> None:
    """Run the real E5b matcher after preloading; persist every query once without altering it."""
    from src.api.medicine import MATCH_THRESHOLD, MedicineCatalog, ProductMatcher

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Scoring output is immutable')
    assert MATCH_THRESHOLD == 0.65
    with Path('src/gen/medicine_match_fresh.tsv').open() as handle:
        queries = list(csv.DictReader(handle, delimiter='\t'))
    assert len(queries) == 60 and sum(q['kind'] == 'decoy' for q in queries) == 15
    catalog = MedicineCatalog()
    matcher = ProductMatcher(catalog)
    matcher._load()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with args.output.open('x') as handle:
        for query in queries:
            result = matcher.match(query['query'])
            predicted = catalog.products[result['candidates'][0][0]].name if result['candidates'] else ''
            row = {**query, 'predicted': predicted, 'result': result}
            rows.append(row)
            handle.write(json.dumps(row)+'\n')
            handle.flush()
            print(len(rows), query['kind'], result['outcome'], flush=True)
    print(json.dumps(summarize(rows)), flush=True)


if __name__ == '__main__':
    main()
