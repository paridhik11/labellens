"""Invented development examples, never values from the ten scoring photographs."""
from __future__ import annotations

import pytest

from src.common.schemas import OcrBlock
from src.cv.photo_fields import field_key, map_photo_fields, visible_date


def block(text: str, x: float, y: float, w: float = 100, h: float = 20, conf: float = 0.99) -> OcrBlock:
    """Build a synthetic text observation with configurable geometry."""
    return OcrBlock(text=text, bbox=(x, y, w, h), conf=conf)


@pytest.mark.parametrize('text,expected', [
    ('2033-06-15', '2033-06-15'), ('2033/06', '2033/06'), ('04/2031', '04/2031'),
    ('EXP 15.06.2033', '15.06.2033'), ('USE BY OCT-2032', 'OCT-2032'),
    ('MFG 2033-06-15', None), ('2033-02-30', None), ('no date', None),
    ('2032-01-01 2033-01-01', None), ('EXP 2033-13-01', None),
])
def test_printed_dates(text: str, expected: str | None) -> None:
    """Keep visible formats, reject invalid dates and do not relabel manufacture dates."""
    assert visible_date(text) == expected


@pytest.mark.parametrize('text,expected', [
    ('[LOT] A784', ('lot', 'A784')), ('LOTZ981', ('lot', 'Z981')),
    ('LOTUS', (None, 'LOTUS')), ('BATCH', ('lot', '')), ('REF M-95', ('model', 'M-95')),
])
def test_printed_keys(text: str, expected: tuple[str | None, str]) -> None:
    """Read split/boxed/attached keys without promoting ordinary alphabetic words."""
    assert field_key(text) == expected


def test_split_key_date_and_product() -> None:
    """Resolve separate lot key/value, bare expiry and typography without a template."""
    fields, _ = map_photo_fields([block('NOVA DEVICE', 10, 10, 300, 40),
                                  block('STERILE', 400, 10, 150, 20), block('LOT', 20, 100, 40),
                                  block('Z981', 75, 100), block('2033-06-15', 20, 160, 160)])
    assert fields['lot'] == 'LOT: Z981'
    assert fields['expiry'] == 'EXP: 2033-06-15'
    assert fields['product_name'] == 'NOVA DEVICE'


def test_ambiguous_dates_and_lots() -> None:
    """Abstain on conflicting observed values and multiple unkeyed dates."""
    fields, warnings = map_photo_fields([block('LOT: A72', 0, 0), block('LOT: B49', 0, 40),
                                        block('2033-01-01', 0, 80), block('2034-01-01', 0, 120)])
    assert 'lot' not in fields and 'expiry' not in fields
    assert any('conflicting' in value for value in warnings)
    assert any('multiple unkeyed dates' in value for value in warnings)


def test_low_confidence_and_unlabelled_number() -> None:
    """Do not infer a batch from a reference number or promote regulatory text to a name."""
    fields, _ = map_photo_fields([block('A12349', 0, 0), block('CE', 0, 30),
                                  block('STERILE', 0, 60), block('LOT: Q5', 0, 100, conf=0.1)])
    assert 'product_name' not in fields and 'lot' not in fields
