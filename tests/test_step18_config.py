"""Tests for src.ir.step18_config (no model is loaded)."""
from __future__ import annotations

import copy

from src.common.schemas import Chunk
from src.ir.step18_config import (
    ENRICHMENT_TEMPLATE,
    SELECTED_ID,
    build_config,
    cache_files,
    check_config,
    e5b,
    settings_hash,
    system_to_dict,
)
from src.ir.step18_systems import enrich_chunk


def test_selected_system_is_the_e5b_definition():
    s = e5b()
    assert SELECTED_ID == "E5b" and s.name == "rrf[bm25+stem, large+prefix+head]"
    d = system_to_dict(s)
    assert d["bm25"] == {"stem": True, "heading_prepended": False}
    assert d["dense"][0]["model"] == "BAAI/bge-large-en-v1.5" and d["dense"][0]["heading_prepended"] is True
    assert d["dense"][0]["query_prefix"].startswith("Represent this sentence") and d["medcpt"] is False


def test_enrichment_template_matches_the_code():
    c = Chunk(chunk_id="fda_21cfr801_s801.109_c1", source="F", section="801.109", title="Prescription devices",
              text="body text", hash="h")
    assert enrich_chunk(c).text == ENRICHMENT_TEMPLATE.format(part="801", section="801.109",
                                                              title="Prescription devices", text="body text")


def test_cache_names_depend_on_chunk_content_and_check_catches_changes():
    a = [Chunk(chunk_id="c1", source="F", section="1.1", title="t", text="x", hash="h1", module="device")]
    b = [a[0].model_copy(update={"text": "y"})]  # the cache key follows the enriched text
    names_a, names_b = cache_files({"device": a}), cache_files({"device": b})
    assert names_a != names_b and cache_files({"device": a}) == names_a
    cfg = build_config()
    assert check_config(cfg) == [] and settings_hash(cfg) == cfg["settings_sha256"]
    bad = copy.deepcopy(cfg)
    bad["parameters"]["fusion"]["k"] = 30
    assert any("settings_sha256" in p for p in check_config(bad))
    rows = cfg["selected_on"]["cv_rows"]
    assert {r["base"] for r in rows} >= {"hybrid", "hybrid+stem+prefix"} and all(r["exp_id"] == "E5b" for r in rows)
