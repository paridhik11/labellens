"""Shared index store: copy missing files in and out, never overwrite, never need a model."""
from __future__ import annotations

from pathlib import Path

from src.rag import indexes


def test_pull_and_push_copy_missing_files_only(tmp_path: Path) -> None:
    local, store = tmp_path / "local", tmp_path / "store"
    files = [local / "dense_cache_m_abc.npy", local / "dense_cache_m_abc.json"]
    local.mkdir()
    files[0].write_bytes(b"vectors")
    files[1].write_text("{}")
    assert indexes.missing(files) == []
    assert indexes.push(files, store) == files and (store / files[0].name).read_bytes() == b"vectors"
    assert indexes.push(files, store) == []  # already there
    (store / files[0].name).write_bytes(b"newer")
    assert indexes.push(files, store) == []  # never overwritten
    for f in files:
        f.unlink()
    assert indexes.missing(files) == files
    assert indexes.pull(files, store) == files and files[0].read_bytes() == b"newer"
    assert indexes.pull(files, store) == []  # present locally, not copied again


def test_shared_dir_honours_the_environment(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LABELLENS_INDEX_DIR", str(tmp_path / "x"))
    assert indexes.shared_dir() == tmp_path / "x"
    monkeypatch.delenv("LABELLENS_INDEX_DIR")
    assert indexes.shared_dir().parts[-3:] == ("data", "cache", "indexes")


def test_required_files_name_both_models_for_both_modules() -> None:
    names = [p.name for p in indexes.required_files()]
    assert sum("bge-large" in n for n in names) == 4 and sum("bge-small" in n for n in names) == 4
    assert all(n.startswith("dense_cache_") for n in names)
