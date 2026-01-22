"""Cache manager for MFA artifacts (T010).

The cache groups artifacts by a deterministic key derived from
(audio checksum, text version, pronunciation tradition, and chunking config).
It stores each key in its own directory so command invocations can quickly
reuse normalized audio, dictionaries, or prior alignment outputs.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping

from hb_align.utils.config import AppConfig

_METADATA_FILENAME = "metadata.json"


@dataclass(frozen=True)
class CacheEntry:
    key: str
    path: Path
    metadata_path: Path

    def artifact_path(self, relative_name: str) -> Path:
        return self.path / relative_name


def build_cache_key(
    *,
    audio_checksum: str,
    text_version: str,
    tradition: str,
    chunk_size_sec: int,
    chunk_overlap_sec: int,
    extra: Mapping[str, str] | None = None,
) -> str:
    """Derive a deterministic cache key from the provided attributes."""

    parts = [
        audio_checksum.lower(),
        text_version,
        tradition,
        str(chunk_size_sec),
        str(chunk_overlap_sec),
    ]
    if extra:
        for key in sorted(extra):
            parts.append(f"{key}={extra[key]}")
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest


class CacheManager:
    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_config(cls, config: AppConfig) -> "CacheManager":
        return cls(config.cache_dir)

    @property
    def root(self) -> Path:
        return self._root

    def ensure_entry(self, key: str) -> CacheEntry:
        path = self._root / key
        path.mkdir(parents=True, exist_ok=True)
        return CacheEntry(key=key, path=path, metadata_path=path / _METADATA_FILENAME)

    def entry_exists(self, key: str) -> bool:
        return (self._root / key).exists()

    def artifact_path(self, key: str, relative_name: str, ensure: bool = False) -> Path:
        if ensure:
            entry = self.ensure_entry(key)
            return entry.artifact_path(relative_name)
        return (self._root / key) / relative_name

    def read_metadata(self, key: str) -> MutableMapping[str, object] | None:
        path = (self._root / key) / _METADATA_FILENAME
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def write_metadata(self, key: str, payload: Mapping[str, object]) -> Path:
        entry = self.ensure_entry(key)
        entry.metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return entry.metadata_path

    def purge_older_than(self, days: int) -> list[str]:
        """Delete cache entries whose directories are older than the threshold."""

        if days <= 0:
            raise ValueError("days must be positive")
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        removed: list[str] = []
        for candidate in self._root.iterdir():
            if not candidate.is_dir():
                continue
            modified = datetime.fromtimestamp(candidate.stat().st_mtime, timezone.utc)
            if modified < cutoff:
                shutil.rmtree(candidate)
                removed.append(candidate.name)
        return removed


__all__ = ["CacheEntry", "CacheManager", "build_cache_key"]
