"""Audio chunking and stitching utilities (T009).

These helpers keep chunk size/overlap constraints consistent with the design
spec so all pipelines share the same behaviour. They operate purely on timing
metadata to keep them testable without heavy audio dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

MAX_CHUNK_SECONDS = 50
MAX_OVERLAP_SECONDS = 5
DEFAULT_OVERLAP_TOLERANCE_MS = 750


@dataclass(frozen=True)
class ChunkWindow:
    chunk_id: str
    start_ms: int
    end_ms: int
    overlap_ms: int

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


@dataclass(frozen=True)
class WordSegment:
    text: str
    start_ms: int
    end_ms: int
    confidence: float = 0.0


@dataclass(frozen=True)
class ChunkAlignment:
    chunk: ChunkWindow
    words: Sequence[WordSegment]


@dataclass(frozen=True)
class AlignedWord:
    text: str
    start_ms: int
    end_ms: int
    confidence: float
    chunk_id: str


def plan_chunks(
    duration_ms: int,
    *,
    chunk_size_sec: int = MAX_CHUNK_SECONDS,
    overlap_sec: int = MAX_OVERLAP_SECONDS,
) -> List[ChunkWindow]:
    """Generate chunk windows covering the supplied duration."""

    if duration_ms <= 0:
        raise ValueError("Duration must be positive")
    if chunk_size_sec <= 0 or chunk_size_sec > MAX_CHUNK_SECONDS:
        raise ValueError("Chunk size must be between 1 and 50 seconds")
    if overlap_sec < 0 or overlap_sec > MAX_OVERLAP_SECONDS:
        raise ValueError("Overlap must be between 0 and 5 seconds")
    if overlap_sec >= chunk_size_sec:
        raise ValueError("Overlap must be smaller than chunk size")

    chunk_size_ms = chunk_size_sec * 1000
    overlap_ms = overlap_sec * 1000
    windows: List[ChunkWindow] = []
    start = 0
    index = 1
    while start < duration_ms:
        end = min(start + chunk_size_ms, duration_ms)
        overlap = 0 if index == 1 else overlap_ms
        windows.append(
            ChunkWindow(
                chunk_id=f"chunk-{index:03}",
                start_ms=start,
                end_ms=end,
                overlap_ms=overlap,
            )
        )
        if end >= duration_ms:
            break
        start = end - overlap_ms
        index += 1
    return windows


def chunk_map_to_dict(chunks: Sequence[ChunkWindow]) -> List[dict]:
    """Serialize chunk windows for JSON diagnostics."""

    return [
        {
            "chunk_id": chunk.chunk_id,
            "start_ms": chunk.start_ms,
            "end_ms": chunk.end_ms,
            "duration_ms": chunk.duration_ms,
            "overlap_ms": chunk.overlap_ms,
        }
        for chunk in chunks
    ]


def stitch_chunk_alignments(
    chunks: Iterable[ChunkAlignment],
    *,
    overlap_tolerance_ms: int = DEFAULT_OVERLAP_TOLERANCE_MS,
) -> List[AlignedWord]:
    """Merge chunk-scoped word timings into a continuous timeline."""

    merged: List[AlignedWord] = []
    sorted_chunks = sorted(chunks, key=lambda c: c.chunk.start_ms)
    for chunk_alignment in sorted_chunks:
        offset = chunk_alignment.chunk.start_ms
        for word in chunk_alignment.words:
            absolute = AlignedWord(
                text=word.text,
                start_ms=offset + word.start_ms,
                end_ms=offset + word.end_ms,
                confidence=word.confidence,
                chunk_id=chunk_alignment.chunk.chunk_id,
            )
            if merged:
                prev = merged[-1]
                overlap = prev.end_ms - absolute.start_ms
                if overlap >= 0 and overlap <= overlap_tolerance_ms:
                    if absolute.confidence > prev.confidence:
                        merged[-1] = absolute
                    continue
            merged.append(absolute)
    return merged


__all__ = [
    "ChunkWindow",
    "WordSegment",
    "ChunkAlignment",
    "AlignedWord",
    "plan_chunks",
    "chunk_map_to_dict",
    "stitch_chunk_alignments",
]
