import os
import time
from pathlib import Path

import pytest

from hb_align.utils.cache import CacheManager, build_cache_key
from hb_align.utils.config import AppConfig


def _config(tmp_path: Path) -> AppConfig:
    cfg = AppConfig(
        project_root=tmp_path,
        wlc_root=tmp_path / "wlc",
        cache_dir=tmp_path / "cache",
        output_root=tmp_path / "out",
        logs_dir=tmp_path / "logs",
        mfa_executable="mfa",
        log_format="text",
    )
    cfg.ensure_directories()
    return cfg


def test_build_cache_key_is_stable():
    base_kwargs = dict(
        audio_checksum="abc123",
        text_version="wlc-2023.09",
        tradition="modern",
        chunk_size_sec=50,
        chunk_overlap_sec=5,
        extra={"chunker": "default"},
    )
    key1 = build_cache_key(**base_kwargs)
    key2 = build_cache_key(**base_kwargs)
    assert key1 == key2
    key3 = build_cache_key(**{**base_kwargs, "tradition": "ashkenazi"})
    assert key3 != key1


def test_metadata_round_trip(tmp_path):
    manager = CacheManager.from_config(_config(tmp_path))
    key = build_cache_key(
        audio_checksum="foo",
        text_version="bar",
        tradition="modern",
        chunk_size_sec=40,
        chunk_overlap_sec=5,
    )
    manager.write_metadata(key, {"status": "ok", "words": 123})
    metadata = manager.read_metadata(key)
    assert metadata == {"status": "ok", "words": 123}
    artifact = manager.artifact_path(key, "alignments.json", ensure=True)
    assert artifact.parent.exists()


def test_purge_older_than(tmp_path):
    manager = CacheManager.from_config(_config(tmp_path))
    fresh_key = "fresh"
    old_key = "old"
    manager.ensure_entry(fresh_key)
    old_entry = manager.ensure_entry(old_key)
    past = time.time() - (3 * 86400)
    os.utime(old_entry.path, (past, past))
    removed = manager.purge_older_than(2)
    assert old_key in removed
    assert not manager.entry_exists(old_key)
    assert manager.entry_exists(fresh_key)


def test_purge_older_than_rejects_invalid(tmp_path):
    manager = CacheManager.from_config(_config(tmp_path))
    with pytest.raises(ValueError):
        manager.purge_older_than(0)
