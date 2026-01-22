"""Structured logging + summary writer utilities (T011)."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Mapping, MutableMapping, Optional

from rich.console import Console
from rich.text import Text

DEFAULT_LOG_FORMAT = "text"


class StructuredLogger:
    """Small wrapper that emits either text or JSON logs."""

    def __init__(
        self,
        *,
        log_format: str = DEFAULT_LOG_FORMAT,
        console: Console | None = None,
        json_stream=None,
    ) -> None:
        self._format = log_format
        self._console = console or Console()
        self._json_stream = json_stream

    def info(self, message: str, **fields) -> None:
        self._emit("info", message, fields)

    def warning(self, message: str, **fields) -> None:
        self._emit("warning", message, fields)

    def error(self, message: str, **fields) -> None:
        self._emit("error", message, fields)

    def debug(self, message: str, **fields) -> None:
        self._emit("debug", message, fields)

    def _emit(self, level: str, message: str, fields: Mapping[str, object]) -> None:
        payload = {
            "level": level,
            "message": message,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        payload.update(fields)
        if self._format == "json":
            stream = self._json_stream or self._console.file
            stream.write(json.dumps(payload) + "\n")
            stream.flush()
        else:
            text = Text(f"[{level.upper()}] {message}")
            if fields:
                text.append(f" {fields}")
            self._console.print(text)


@dataclass
class SummaryMetrics:
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    book: Optional[str] = None
    chapter: Optional[int] = None
    expected_words: int = 0
    aligned_words: int = 0
    coverage_pct: float = 0.0
    avg_confidence: float = 0.0
    min_confidence: float = 0.0
    chunk_count: int = 0
    durations_ms: MutableMapping[str, int] = field(default_factory=dict)
    cache_status: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "run_id": self.run_id,
            "book": self.book,
            "chapter": self.chapter,
            "expected_words": self.expected_words,
            "aligned_words": self.aligned_words,
            "coverage_pct": round(self.coverage_pct, 3),
            "avg_confidence": round(self.avg_confidence, 3),
            "min_confidence": round(self.min_confidence, 3),
            "chunk_count": self.chunk_count,
            "durations_ms": dict(self.durations_ms),
            "cache_status": self.cache_status,
            "created_at": self.created_at,
            "notes": list(self.notes),
        }


class SummaryWriter:
    def __init__(self, *, metrics: SummaryMetrics | None = None) -> None:
        self._metrics = metrics or SummaryMetrics()

    @property
    def metrics(self) -> SummaryMetrics:
        return self._metrics

    def set_alignment_counts(self, *, aligned: int, expected: int) -> None:
        self._metrics.aligned_words = aligned
        self._metrics.expected_words = expected
        self._metrics.coverage_pct = (aligned / expected) * 100 if expected else 0.0

    def set_confidence(self, *, avg: float, minimum: float) -> None:
        self._metrics.avg_confidence = avg
        self._metrics.min_confidence = minimum

    def set_reference(self, *, book: str, chapter: int) -> None:
        self._metrics.book = book
        self._metrics.chapter = chapter

    def set_chunk_count(self, count: int) -> None:
        self._metrics.chunk_count = count

    def record_duration(self, stage: str, duration_ms: int) -> None:
        self._metrics.durations_ms[stage] = duration_ms

    def set_cache_status(self, status: str) -> None:
        self._metrics.cache_status = status

    def add_note(self, note: str) -> None:
        self._metrics.notes.append(note)

    def write(self, path: Path | str) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self._metrics.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return target


__all__ = [
    "StructuredLogger",
    "SummaryWriter",
    "SummaryMetrics",
]
