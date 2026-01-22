from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

import pytest

from hb_align.aligner import pipeline
from hb_align.audio import chunker
from hb_align.text.wlc_loader import TextChapter, VerseTokens, WordToken


def _build_text_chapter(words: Sequence[str]) -> TextChapter:
    tokens = [
        WordToken(
            index=i,
            hebrew=word,
            translit=f"t{i}",
            ipa_modern=f"ipa{i}",
            ipa_ashkenazi=f"ipa{i}",
            ipa_sephardi=f"ipa{i}",
        )
        for i, word in enumerate(words)
    ]
    verses = (VerseTokens(verse="1:1", tokens=tuple(tokens)),)
    return TextChapter(book="Genesis", chapter=1, verses=verses)


def _make_chunk_windows() -> List[chunker.ChunkWindow]:
    return [
        chunker.ChunkWindow(chunk_id="chunk-001", start_ms=0, end_ms=4500, overlap_ms=0),
        chunker.ChunkWindow(chunk_id="chunk-002", start_ms=4000, end_ms=9000, overlap_ms=1000),
    ]


def _make_chunk_alignment(window: chunker.ChunkWindow, tokens: Sequence[str]) -> chunker.ChunkAlignment:
    segments = tuple(
        chunker.WordSegment(text=token, start_ms=i * 100, end_ms=i * 100 + 80, confidence=0.9)
        for i, token in enumerate(tokens)
    )
    return chunker.ChunkAlignment(chunk=window, words=segments)


def test_alignment_pipeline_reports_full_coverage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    chapter = _build_text_chapter(["בראשית", "ברא", "אלוהים", "את"])
    fake_windows = _make_chunk_windows()
    monkeypatch.setattr(
        pipeline.chunker,
        "plan_chunks",
        lambda duration_ms, *, chunk_size_sec, overlap_sec: fake_windows,
    )

    chunk_alignments = [
        _make_chunk_alignment(fake_windows[0], ["בראשית", "ברא"]),
        _make_chunk_alignment(fake_windows[1], ["אלוהים", "את"]),
    ]
    call_counter = {"idx": 0}

    def fake_run_mfa(**kwargs):
        idx = call_counter["idx"]
        call_counter["idx"] += 1
        return chunk_alignments[idx]

    monkeypatch.setattr(pipeline, "_run_mfa_for_chunk", fake_run_mfa, raising=False)

    stitched_words = [
        chunker.AlignedWord(text="בראשית", start_ms=0, end_ms=80, confidence=0.93, chunk_id="chunk-001"),
        chunker.AlignedWord(text="ברא", start_ms=180, end_ms=260, confidence=0.91, chunk_id="chunk-001"),
        chunker.AlignedWord(text="אלוהים", start_ms=4200, end_ms=4280, confidence=0.9, chunk_id="chunk-002"),
        chunker.AlignedWord(text="את", start_ms=4500, end_ms=4580, confidence=0.95, chunk_id="chunk-002"),
    ]
    monkeypatch.setattr(
        pipeline.chunker,
        "stitch_chunk_alignments",
        lambda alignments, **kwargs: stitched_words,
    )

    chunk_map = chunker.chunk_map_to_dict(fake_windows)
    monkeypatch.setattr(pipeline.chunker, "chunk_map_to_dict", lambda windows: chunk_map)

    result = pipeline.run_alignment_pipeline(
        text_chapter=chapter,
        audio_duration_ms=9000,
        chunk_size_sec=5,
        chunk_overlap_sec=1,
        profile="modern",
        mfa_runner=None,
        cache_manager=None,
        working_dir=tmp_path,
    )

    summary = result["summary"]
    assert summary["expected_words"] == chapter.word_count == 4
    assert summary["aligned_words"] == len(stitched_words) == 4
    assert summary["coverage_pct"] == pytest.approx(100.0)
    assert result["aligned_words"] == stitched_words
    assert result["chunk_map"] == chunk_map


def test_alignment_pipeline_detects_low_coverage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    chapter = _build_text_chapter(["בראשית", "ברא", "אלוהים", "את"])
    fake_windows = _make_chunk_windows()
    monkeypatch.setattr(
        pipeline.chunker,
        "plan_chunks",
        lambda duration_ms, *, chunk_size_sec, overlap_sec: fake_windows,
    )

    chunk_alignments = [
        _make_chunk_alignment(fake_windows[0], ["בראשית"]),
        _make_chunk_alignment(fake_windows[1], ["אלוהים"]),
    ]
    call_counter = {"idx": 0}

    def fake_run_mfa(**kwargs):
        idx = call_counter["idx"]
        call_counter["idx"] += 1
        return chunk_alignments[idx]

    monkeypatch.setattr(pipeline, "_run_mfa_for_chunk", fake_run_mfa, raising=False)

    stitched_words = [
        chunker.AlignedWord(text="בראשית", start_ms=0, end_ms=80, confidence=0.93, chunk_id="chunk-001"),
        chunker.AlignedWord(text="אלוהים", start_ms=4200, end_ms=4280, confidence=0.9, chunk_id="chunk-002"),
    ]
    monkeypatch.setattr(
        pipeline.chunker,
        "stitch_chunk_alignments",
        lambda alignments, **kwargs: stitched_words,
    )

    chunk_map = chunker.chunk_map_to_dict(fake_windows)
    monkeypatch.setattr(pipeline.chunker, "chunk_map_to_dict", lambda windows: chunk_map)

    result = pipeline.run_alignment_pipeline(
        text_chapter=chapter,
        audio_duration_ms=9000,
        chunk_size_sec=5,
        chunk_overlap_sec=1,
        profile="modern",
        mfa_runner=None,
        cache_manager=None,
        working_dir=tmp_path,
    )

    summary = result["summary"]
    assert summary["expected_words"] == chapter.word_count == 4
    assert summary["aligned_words"] == len(stitched_words) == 2
    assert summary["coverage_pct"] == pytest.approx(50.0)
    assert result["chunk_map"] == chunk_map
