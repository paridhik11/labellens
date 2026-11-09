import pytest
from pydantic import ValidationError

from src.common.schemas import Chunk, Flag, IdentifierRequired, LabelExtraction


def test_chunk_defaults():
    c = Chunk(chunk_id="c1", source="x", text="hello")
    assert c.module == "device"


def test_label_extraction_defaults():
    assert LabelExtraction(label_id="l1").version == 1


def test_flag_severity_validation():
    with pytest.raises(ValidationError):
        Flag(flag_id="f", kind="k", message="m", severity="bad")


def test_identifier_required_is_exception():
    with pytest.raises(IdentifierRequired):
        raise IdentifierRequired("new UDI-DI needed")
