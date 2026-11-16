"""Tests for src.ir.step17_config."""
from __future__ import annotations

import copy

import pytest

from src.ir.step17_config import (
    BEST_COMBO,
    VARIANTS,
    build_config,
    check_config,
    file_sha256,
    record,
    settings_hash,
    spec_from_dict,
    spec_to_dict,
)


def test_spec_round_trip_and_unique_names():
    for spec, *_ in VARIANTS:
        assert spec_from_dict(spec_to_dict(spec)) == spec
    names = [s.name for s, *_ in VARIANTS]
    assert len(names) == len(set(names))


def test_primaries_are_the_three_declared_ones():
    cfg = build_config()
    prim = {v["id"]: (v["name"], v["vs"]) for v in cfg["variants"] if v["role"] == "primary"}
    assert prim == {
        "P1": ("bm25+exp(w=0.5,all)", "bm25"),
        "P2": (BEST_COMBO.name, "hybrid"),
        "P3": ("hybrid+stem+prefix", "hybrid"),
    }
    assert cfg["params"]["holm_family"] == ["P1", "P2", "P3"]
    for v in cfg["variants"]:
        assert v["vs"] is None or v["vs"] in {w["name"] for w in cfg["variants"]}


def test_record_fills_commit_and_qrels_without_touching_settings(tmp_path):
    qrels = tmp_path / "qrels.tsv"
    qrels.write_text("q01 0 a 1\nq01 0 b 0\n", encoding="utf-8")
    cfg = build_config()
    out = record(cfg, "abc123", qrels)
    assert out["main_commit"] == "abc123" and out["qrels"]["rows"] == 2
    assert out["qrels"]["sha256"] == file_sha256(qrels)
    assert settings_hash(out) == cfg["settings_sha256"] == out["settings_sha256"]
    assert cfg["main_commit"] is None  # the input was not modified


def test_check_detects_a_changed_setting():
    cfg = build_config()
    assert check_config(cfg) == []
    bad = copy.deepcopy(cfg)
    bad["variants"][3]["spec"]["exp"][0] = 0.9
    assert any("settings_sha256" in p for p in check_config(bad))


def test_sha_ignores_crlf(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.write_bytes(b"x\ny\n")
    b.write_bytes(b"x\r\ny\r\n")
    assert file_sha256(a) == file_sha256(b)


def test_record_refuses_when_qrels_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        record(build_config(), "abc", tmp_path / "nope.tsv")
