from __future__ import annotations

import io
import json
from pathlib import Path

from hb_align.utils.logging import StructuredLogger, SummaryWriter
from rich.console import Console


def test_structured_logger_json_mode(tmp_path: Path) -> None:
    buffer = tmp_path / "log.jsonl"
    with buffer.open("w", encoding="utf-8") as handle:
        logger = StructuredLogger(log_format="json", json_stream=handle)
        logger.info("chunk-built", chunk=3, duration_ms=1250)
        logger.error("align-failed", stage="align", chunk=4)

    lines = buffer.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["message"] == "chunk-built"
    assert first["chunk"] == 3
    assert first["duration_ms"] == 1250


def test_structured_logger_text_mode() -> None:
    sink = io.StringIO()
    logger = StructuredLogger(log_format="text", console=Console(file=sink))
    logger.info("chunk-built", chunk=2)
    output = sink.getvalue()
    assert "chunk-built" in output


def test_summary_writer(tmp_path: Path) -> None:
    writer = SummaryWriter()
    writer.set_reference(book="Genesis", chapter=1)
    writer.set_alignment_counts(aligned=950, expected=1200)
    writer.set_confidence(avg=0.89, minimum=0.67)
    writer.set_chunk_count(15)
    writer.record_duration("chunk", 5132)
    writer.record_duration("align", 15320)
    writer.set_cache_status("miss")
    writer.add_note("alignment completed")
    output = writer.write(tmp_path / "summary.json")

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["book"] == "Genesis"
    assert payload["chapter"] == 1
    assert payload["chunk_count"] == 15
    assert payload["coverage_pct"] == round((950 / 1200) * 100, 3)
    assert payload["durations_ms"]["align"] == 15320
    assert payload["cache_status"] == "miss"
