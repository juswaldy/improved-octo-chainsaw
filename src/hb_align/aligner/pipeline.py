"""Chunking → MFA → stitching pipeline orchestrator (T014/T015)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from hb_align.audio import chunker
from hb_align.text.wlc_loader import TextChapter


def run_alignment_pipeline(
    *,
    text_chapter: TextChapter,
    audio_duration_ms: int,
    chunk_size_sec: int,
    chunk_overlap_sec: int,
    profile: str,
    mfa_runner: Any,
    cache_manager: Any,
    working_dir: Path,
    logger: Any | None = None,
) -> Dict[str, Any]:
    """Execute the core alignment pipeline.

    The pipeline performs three high-level steps:

    1. Plan chunk windows across the normalized audio duration.
    2. Invoke MFA for each chunk (delegated to ``_run_mfa_for_chunk``).
    3. Stitch chunk alignments back into a chapter-wide list of aligned words.

    Integration tests stub MFA execution, so this implementation focuses on the
    orchestration glue and summary calculation. Real MFA invocation will be
    handled in `_run_mfa_for_chunk` during later tasks.
    """

    chunk_windows = chunker.plan_chunks(
        audio_duration_ms,
        chunk_size_sec=chunk_size_sec,
        overlap_sec=chunk_overlap_sec,
    )

    chunk_alignments: List[chunker.ChunkAlignment] = []
    for index, window in enumerate(chunk_windows):
        alignment = _run_mfa_for_chunk(
            chunk_window=window,
            chunk_index=index,
            text_chapter=text_chapter,
            profile=profile,
            mfa_runner=mfa_runner,
            cache_manager=cache_manager,
            working_dir=working_dir,
            logger=logger,
        )
        chunk_alignments.append(alignment)

    stitched_words = chunker.stitch_chunk_alignments(chunk_alignments)
    chunk_map = chunker.chunk_map_to_dict(chunk_windows)

    expected_words = text_chapter.word_count
    aligned_word_count = len(stitched_words)
    coverage_pct = (aligned_word_count / expected_words) * 100 if expected_words else 0.0

    summary = {
        "book": text_chapter.book,
        "chapter": text_chapter.chapter,
        "expected_words": expected_words,
        "aligned_words": aligned_word_count,
        "coverage_pct": round(coverage_pct, 3),
        "profile": profile,
    }

    return {
        "chunks": chunk_windows,
        "chunk_alignments": chunk_alignments,
        "aligned_words": stitched_words,
        "chunk_map": chunk_map,
        "summary": summary,
    }


def _run_mfa_for_chunk(*_, **__) -> chunker.ChunkAlignment:  # pragma: no cover - stub
    """Placeholder helper for MFA execution (stubbed in tests)."""

    raise NotImplementedError("Chunk alignment helper not implemented yet")


__all__ = ["run_alignment_pipeline"]
