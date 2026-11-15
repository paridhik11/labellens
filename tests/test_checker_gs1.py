"""GS1 parser used by the checker, compared with the CV parser when the CV libraries exist."""
import pytest

from src.checker.gs1 import GROUP_SEPARATOR as GS
from src.checker.gs1 import check_digit_ok, parse_gs1

GOOD = "0100000000000000" + "17271231" + "10LOT1" + GS + "21SER1"


def test_check_digit() -> None:
    assert check_digit_ok("00000000000000")
    assert check_digit_ok("09506000134352")  # published GS1 example GTIN-14
    assert not check_digit_ok("09506000134353")
    assert not check_digit_ok("1234")


def test_parse_good_payload() -> None:
    assert parse_gs1(GOOD) == {"01": "00000000000000", "17": "271231", "10": "LOT1", "21": "SER1"}


@pytest.mark.parametrize("payload", [
    "", "0100000000000001", "0100000000000000" + "17271331", "99ABC",
    "0100000000000000" + "0100000000000000", "10" + "X" * 21,
])
def test_parse_rejects(payload: str) -> None:
    with pytest.raises(ValueError):
        parse_gs1(payload)


def test_agrees_with_cv_parser() -> None:
    pytest.importorskip("zxingcpp")
    from src.cv.barcode import parse_gs1 as cv_parse

    for payload in [GOOD, "", "0100000000000001", "99ABC", "17271231", "10ABC"]:
        try:
            expected = cv_parse(payload)
        except ValueError:
            with pytest.raises(ValueError):
                parse_gs1(payload)
        else:
            assert parse_gs1(payload) == expected
