from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict

import pytest
from typer.testing import CliRunner

from hb_align.cli import app as cli_app
from hb_align.cli import process as process_module

RUNNER = CliRunner(mix_stderr=False)
SAMPLE_AUDIO = Path("samples/genesis-001.mp3")


@pytest.fixture(scope="module")
def sample_audio_path() -> Path:
    if not SAMPLE_AUDIO.exists():
        pytest.skip("Sample audio placeholder missing; ensure T012 assets are seeded.")
    return SAMPLE_AUDIO


def _write_alignment_csv(path: Path) -> None:
    rows = [
        {
            "book": "Genesis",
            "chapter": 1,
            "verse": "1:1",
            "word_index": 0,
            "word_text": "בראשית",
            "start_ms": 0,
            "end_ms": 420,
            "confidence": 0.99,
        }
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_alignment_json(path: Path) -> None:
    payload = [
        {
            "book": "Genesis",
            "chapter": 1,
            "verse": "1:1",
            "word_index": 0,
            "word_text": "בראשית",
            "start_ms": 0,
            "end_ms": 420,
            "confidence": 0.99,
        }
    ]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_cli(args: list[str]) -> Any:
    return RUNNER.invoke(cli_app, args)


def test_process_cli_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sample_audio_path: Path) -> None:
    artifact_dir = tmp_path / "output"
    summary_payload = {
        "book": "Genesis",
        "chapter": 1,
        "expected_words": 434,
        "aligned_words": 426,
        "coverage_pct": 98.15,
        "avg_confidence": 0.91,
        "min_confidence": 0.72,
    }

    def fake_pipeline(**kwargs: Dict[str, Any]) -> Dict[str, Any]:
        assert kwargs["book"] == "Genesis"
        assert kwargs["chapter"] == 1
        assert kwargs["tradition"] == "modern"
        assert kwargs["input_path"] == sample_audio_path
        chapter_dir = artifact_dir / "genesis" / "001"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        csv_path = chapter_dir / "alignments.csv"
        json_path = chapter_dir / "alignments.json"
        summary_path = chapter_dir / "summary.json"
        chunk_map_path = chapter_dir / "chunk-map.json"
        log_path = chapter_dir / "log.txt"
        _write_alignment_csv(csv_path)
        _write_alignment_json(json_path)
        summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
        chunk_map_path.write_text(json.dumps({"chunks": []}, indent=2), encoding="utf-8")
        log_path.write_text("alignment completed", encoding="utf-8")
        return {
            "exit_code": 0,
            "artifacts": {
                "alignments_csv": csv_path,
                "alignments_json": json_path,
                "summary_json": summary_path,
                "chunk_map": chunk_map_path,
                "log_path": log_path,
            },
            "metrics": summary_payload,
        }

    monkeypatch.setattr(process_module, "_run_process_pipeline", fake_pipeline, raising=False)

    result = _run_cli(
        [
            "process",
            str(sample_audio_path),
            "--book",
            "Genesis",
            "--chapter",
            "1",
            "--tradition",
            "modern",
            "--output-dir",
            str(artifact_dir),
        ]
    )

    assert result.exit_code == 0
    chapter_dir = artifact_dir / "genesis" / "001"
    assert (chapter_dir / "alignments.csv").exists()
    assert (chapter_dir / "alignments.json").exists()
    payload = json.loads((chapter_dir / "summary.json").read_text(encoding="utf-8"))
    assert pytest.approx(payload["coverage_pct"], rel=1e-3) == 98.15
    assert payload["expected_words"] == 434


def test_process_cli_coverage_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sample_audio_path: Path
) -> None:
    artifact_dir = tmp_path / "output"

    def fake_pipeline(**kwargs: Dict[str, Any]) -> Dict[str, Any]:
        chapter_dir = artifact_dir / "genesis" / "001"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        summary_path = chapter_dir / "summary.json"
        summary_path.write_text(
            json.dumps({"coverage_pct": 92.7, "expected_words": 434, "aligned_words": 402}, indent=2),
            encoding="utf-8",
        )
        return {
            "exit_code": 2,
            "artifacts": {"summary_json": summary_path},
            "metrics": {"coverage_pct": 92.7},
        }

    monkeypatch.setattr(process_module, "_run_process_pipeline", fake_pipeline, raising=False)

    result = _run_cli(
        [
            "process",
            str(sample_audio_path),
            "--book",
            "Genesis",
            "--chapter",
            "1",
            "--output-dir",
            str(artifact_dir),
        ]
    )

    assert result.exit_code == 2
    summary_path = artifact_dir / "genesis" / "001" / "summary.json"
    assert summary_path.exists()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["coverage_pct"] == 92.7


def test_process_cli_fatal_error(monkeypatch: pytest.MonkeyPatch, sample_audio_path: Path) -> None:
    def fake_pipeline(**kwargs: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - error path
        raise RuntimeError("MFA_NOT_AVAILABLE")

    monkeypatch.setattr(process_module, "_run_process_pipeline", fake_pipeline, raising=False)

    result = _run_cli(["process", str(sample_audio_path)])

    assert result.exit_code == 3
    assert "MFA_NOT_AVAILABLE" in result.stderr