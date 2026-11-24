"""Live labels: the chunking version is part of the cache key, Adverse Reactions is chunked, side-effect rewrite."""
from __future__ import annotations

import json

from src.api.live_dailymed import CHUNK_VERSION, PARSER_VERSION
from src.rag.query_rewrite import expand_side_effects, rewrite_for_retrieval
from tests.live_helpers import LABEL, XML, FakeHttp, live_service

ADVERSE_TEXT = "The most common adverse reactions are tiredness, dizziness and a slow heart rate."
ADVERSE = (b'<component><section><code code="34084-4" codeSystem="2.16.840.1.113883.6.1"/>'
           b"<title>6 ADVERSE REACTIONS</title><text>" + ADVERSE_TEXT.encode() + b"</text></section></component>")


def _with_adverse(xml: bytes) -> bytes:
    return xml.replace(b"</structuredBody>", ADVERSE + b"</structuredBody>", 1)


def test_cache_file_name_carries_the_chunk_version(tmp_path) -> None:
    service = live_service(tmp_path, FakeHttp(xml=XML))
    label = service.fetch(LABEL["setid"], LABEL["version"])
    path = service._path(label.product_id)
    assert path.name == f"{label.product_id}.c{CHUNK_VERSION}.json" and path.exists()
    assert json.loads(path.read_text(encoding="utf-8"))["parser_version"] == PARSER_VERSION


def test_old_unversioned_cache_file_is_ignored_and_refetched(tmp_path) -> None:
    http = FakeHttp(xml=XML)
    service = live_service(tmp_path, http)
    label = service.fetch(LABEL["setid"], LABEL["version"])
    new_path = service._path(label.product_id)
    old_path = new_path.with_name(f"{label.product_id}.json")  # how a cache file was named before
    new_path.rename(old_path)
    assert not service.knows(label.product_id)
    service.fetch(LABEL["setid"], LABEL["version"])
    assert len([u for u in http.calls if "getFile" in u]) == 2 and new_path.exists()


def test_adverse_reactions_section_is_chunked(tmp_path) -> None:
    service = live_service(tmp_path, FakeHttp(xml=_with_adverse(XML)))
    label = service.fetch(LABEL["setid"], LABEL["version"])
    adverse = [c for c in label.chunks if c.section.startswith("adverse/34084-4/")]
    assert adverse and ADVERSE_TEXT in adverse[0].text and adverse[0].title.endswith("6 ADVERSE REACTIONS")


def test_side_effect_rewrite() -> None:
    assert expand_side_effects("side effects") == "side effects adverse reactions"
    assert expand_side_effects("what are the adverse reactions") == "what are the adverse reactions"
    assert expand_side_effects("what is the dose") == "what is the dose"
    expected = "what are Aspirin's side effects adverse reactions"
    assert rewrite_for_retrieval("what are its side effects", "Aspirin") == expected
