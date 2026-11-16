"""Frozen-input and exact-score protocol tests without photo/model dependencies."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.cv_experiments import eval_photo_protocol as protocol


def test_fixed_inputs_and_failure_denominator(tmp_path: Path) -> None:
    """Changed bytes fail before OCR and extraction exceptions remain field misses."""
    (tmp_path / 'one.jpg').write_bytes(b'synthetic test bytes')
    (tmp_path / 'transcriptions.csv').write_text('filename,product_name,lot,expiry\none.jpg,INVENTED,Z9,2033-01\n')
    frozen = {'cohort': [{'filename': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                         for p in sorted(tmp_path.iterdir())]}
    protocol.validate_inputs(tmp_path, frozen)

    def fail(*args: object, **kwargs: object) -> object:
        """Simulate an OCR failure without consulting any reference."""
        raise RuntimeError('synthetic failure')

    result = protocol.run_evaluation(tmp_path, frozen, fail)
    assert result['totals']['lot']['photos'] == 1 and result['totals']['lot']['exact'] == 0
    assert 'failure' in result['rows'][0]['error']
    extraction = SimpleNamespace(model_dump=lambda: {'fields': {'product_name': 'INVENTED',
                                                               'lot': 'LOT: Z9', 'expiry': 'EXP: 2033-01'}})
    after = protocol.run_evaluation(tmp_path, frozen, lambda *args, **kwargs: extraction)
    report = protocol.render_comparison(result, after)
    assert '| lot | 0/1 | 1/1 |' in report
    assert 'not an unseen holdout' in report and 'unmeasured' in report
    before_path, after_path = tmp_path / 'before.json', tmp_path / 'after.json'
    before_path.write_text(json.dumps(result))
    after_path.write_text(json.dumps(after))
    assert protocol.main(['--before', str(before_path), '--after', str(after_path),
                          '--output', str(tmp_path / 'report.md')]) == 0
    with pytest.raises(ValueError):
        protocol.render_comparison(result, {**after, 'protocol': {}})
    (tmp_path / 'one.jpg').write_bytes(b'changed')
    with pytest.raises(ValueError, match='fingerprint'):
        protocol.validate_inputs(tmp_path, frozen)
    (tmp_path / 'extra.jpg').write_bytes(b'extra')
    with pytest.raises(ValueError, match='cohort'):
        protocol.validate_inputs(tmp_path, frozen)
