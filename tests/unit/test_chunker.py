import pytest

from hb_align.audio.chunker import (
    ChunkAlignment,
    ChunkWindow,
    WordSegment,
    chunk_map_to_dict,
    plan_chunks,
    stitch_chunk_alignments,
)


def test_plan_chunks_generates_expected_windows():
    chunks = plan_chunks(duration_ms=120_000, chunk_size_sec=40, overlap_sec=5)
    assert len(chunks) == 4
    assert chunks[0].start_ms == 0
    assert chunks[1].start_ms == chunks[0].end_ms - 5000
    assert chunks[-1].end_ms == 120_000


def test_plan_chunks_validates_bounds():
    with pytest.raises(ValueError):
        plan_chunks(10_000, chunk_size_sec=55)
    with pytest.raises(ValueError):
        plan_chunks(10_000, overlap_sec=6)
    with pytest.raises(ValueError):
        plan_chunks(10_000, overlap_sec=10, chunk_size_sec=12)


def test_chunk_map_to_dict_serializes_duration():
    chunks = plan_chunks(duration_ms=30_000, chunk_size_sec=20, overlap_sec=5)
    data = chunk_map_to_dict(chunks)
    assert data[0]["duration_ms"] == chunks[0].duration_ms
    assert all(key in data[0] for key in {"chunk_id", "start_ms", "end_ms", "overlap_ms"})


def test_stitch_chunk_alignments_prefers_higher_confidence():
    first_chunk = ChunkWindow(chunk_id="chunk-001", start_ms=0, end_ms=1500, overlap_ms=0)
    second_chunk = ChunkWindow(chunk_id="chunk-002", start_ms=1200, end_ms=2700, overlap_ms=300)
    first = ChunkAlignment(
        chunk=first_chunk,
        words=[
            WordSegment(text="a", start_ms=0, end_ms=400, confidence=0.8),
            WordSegment(text="b", start_ms=800, end_ms=1300, confidence=0.7),
        ],
    )
    second = ChunkAlignment(
        chunk=second_chunk,
        words=[
            WordSegment(text="b", start_ms=0, end_ms=450, confidence=0.9),
            WordSegment(text="c", start_ms=600, end_ms=1100, confidence=0.95),
        ],
    )

    merged = stitch_chunk_alignments([first, second], overlap_tolerance_ms=600)
    texts = [word.text for word in merged]
    assert texts == ["a", "b", "c"]
    assert merged[1].confidence == pytest.approx(0.9)


def test_stitch_chunk_alignments_handles_non_overlap():
    chunk = ChunkWindow(chunk_id="chunk-001", start_ms=0, end_ms=5000, overlap_ms=0)
    alignment = ChunkAlignment(
        chunk=chunk,
        words=[WordSegment(text="solo", start_ms=0, end_ms=1000, confidence=0.5)],
    )
    merged = stitch_chunk_alignments([alignment])
    assert len(merged) == 1
    result = merged[0]
    assert result.text == "solo"
    assert result.start_ms == 0
    assert result.end_ms == 1000