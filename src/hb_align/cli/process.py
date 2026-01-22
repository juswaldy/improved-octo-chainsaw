"""`hb-align process` command implementation (T015)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typer

from hb_align.aligner import pipeline, validators
from hb_align.text import wlc_loader
from hb_align.text.wlc_loader import TextChapter
from hb_align.utils import load_config

DEFAULT_CHUNK_SIZE = 50
DEFAULT_CHUNK_OVERLAP = 5
DEFAULT_COVERAGE_THRESHOLD = 95.0


def register(app: typer.Typer) -> None:
    @app.command("process", context_settings={"allow_interspersed_args": True})
    def process_command(
        input_path: Path = typer.Argument(..., help="Path to the book-chapter audio file."),
        book: Optional[str] = typer.Option(None, "--book", help="Override detected book name."),
        chapter: Optional[int] = typer.Option(
            None, "--chapter", min=1, help="Override detected chapter number."
        ),
        tradition: str = typer.Option(
            "modern",
            "--tradition",
            help="Pronunciation profile (modern|ashkenazi|sephardi).",
        ),
        output_dir: Path = typer.Option(
            Path("./output"), "--output-dir", help="Directory root for artifacts."
        ),
        chunk_size: int = typer.Option(
            DEFAULT_CHUNK_SIZE,
            "--chunk-size",
            min=10,
            max=60,
            help="Chunk size in seconds (<=60).",
        ),
        chunk_overlap: int = typer.Option(
            DEFAULT_CHUNK_OVERLAP,
            "--chunk-overlap",
            min=0,
            max=10,
            help="Chunk overlap in seconds (< chunk-size).",
        ),
        coverage_threshold: float = typer.Option(
            DEFAULT_COVERAGE_THRESHOLD,
            "--coverage-threshold",
            min=50.0,
            max=99.0,
            help="Coverage % required for success (default 95).",
        ),
        dry_run: bool = typer.Option(False, "--dry-run", help="Validate inputs without MFA."),
    ) -> None:
        """Align a single chapter recording to the canonical WLC text."""

        load_config()  # Ensures .env + config validation happens before work begins.

        if chunk_overlap >= chunk_size:
            typer.secho(
                "--chunk-overlap must be smaller than --chunk-size",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=3)

        try:
            resolved_book, resolved_chapter = _resolve_reference(input_path, book, chapter)
        except ValueError as exc:  # pragma: no cover - simple validation guard
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(code=3)

        try:
            run_result = _run_process_pipeline(
                input_path=input_path,
                book=resolved_book,
                chapter=resolved_chapter,
                tradition=tradition,
                output_dir=output_dir,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                coverage_threshold=coverage_threshold,
                dry_run=dry_run,
            )
        except FileNotFoundError as exc:
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(code=3)
        except Exception as exc:  # pragma: no cover - defensive
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(code=3)

        summary = run_result.get("summary") or run_result.get("metrics") or {}
        _echo_summary(summary, run_result.get("exit_code", 0))

        artifacts = run_result.get("artifacts", {})
        if artifacts:
            typer.secho("Artifacts:", fg=typer.colors.BLUE)
            for name, path in artifacts.items():
                typer.secho(f"  {name}: {path}")

        raise typer.Exit(code=run_result.get("exit_code", 0))


def _run_process_pipeline(
    *,
    input_path: Path,
    book: str,
    chapter: int,
    tradition: str,
    output_dir: Path,
    chunk_size: int,
    chunk_overlap: int,
    coverage_threshold: float,
    dry_run: bool,
) -> Dict[str, object]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {input_path}")

    text_chapter = wlc_loader.load_chapter(book, chapter)
    chapter_dir = _chapter_output_dir(output_dir, book, chapter)
    chapter_dir.mkdir(parents=True, exist_ok=True)

    if dry_run:
        summary = {
            "book": book,
            "chapter": chapter,
            "expected_words": text_chapter.word_count,
            "aligned_words": 0,
            "coverage_pct": 0.0,
            "dry_run": True,
        }
        return {"exit_code": 0, "summary": summary, "artifacts": {}}

    audio_duration_ms = _estimate_audio_duration(input_path, text_chapter)
    pipeline_result = pipeline.run_alignment_pipeline(
        text_chapter=text_chapter,
        audio_duration_ms=audio_duration_ms,
        chunk_size_sec=chunk_size,
        chunk_overlap_sec=chunk_overlap,
        profile=tradition,
        mfa_runner=None,
        cache_manager=None,
        working_dir=chapter_dir,
    )

    summary = dict(pipeline_result.get("summary", {}))
    coverage_status = validators.evaluate_coverage(
        expected_words=summary.get("expected_words", text_chapter.word_count),
        aligned_words=summary.get("aligned_words", 0),
        threshold=coverage_threshold,
    )
    summary["coverage_pct"] = coverage_status.coverage_pct
    summary["coverage_threshold"] = coverage_threshold
    summary["coverage_passed"] = coverage_status.passed

    artifacts = _write_artifacts(chapter_dir, summary, pipeline_result.get("chunk_map", []))
    exit_code = validators.determine_exit_code(coverage_status)

    return {
        "exit_code": exit_code,
        "summary": summary,
        "artifacts": artifacts,
    }


def _write_artifacts(
    chapter_dir: Path,
    summary: Dict[str, object],
    chunk_map: List[Dict[str, Any]],
) -> Dict[str, Path]:
    summary_path = chapter_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    chunk_map_path = chapter_dir / "chunk-map.json"
    chunk_map_path.write_text(json.dumps(chunk_map, indent=2, ensure_ascii=False), encoding="utf-8")

    log_path = chapter_dir / "log.txt"
    log_path.write_text("Alignment pipeline execution log placeholder\n", encoding="utf-8")

    return {
        "summary_json": summary_path,
        "chunk_map": chunk_map_path,
        "log_path": log_path,
    }


def _resolve_reference(input_path: Path, book: Optional[str], chapter: Optional[int]) -> Tuple[str, int]:
    inferred_book, inferred_chapter = _infer_reference_from_filename(input_path)
    resolved_book = book or inferred_book
    resolved_chapter = chapter or inferred_chapter
    if not resolved_book or resolved_chapter is None:
        raise ValueError(
            "Unable to determine book/chapter. Use --book/--chapter or follow <book>-<chapter>.mp3 naming."
        )
    return resolved_book, resolved_chapter


def _infer_reference_from_filename(path: Path) -> Tuple[Optional[str], Optional[int]]:
    stem = path.stem
    if "-" not in stem:
        return None, None
    book_slug, chapter_str = stem.rsplit("-", 1)
    try:
        chapter = int(chapter_str)
    except ValueError:
        return None, None
    book = book_slug.replace("_", " ").replace("-", " ").title()
    return book, chapter


def _chapter_output_dir(root: Path, book: str, chapter: int) -> Path:
    slug = book.lower().replace(" ", "-")
    return root / slug / f"{chapter:03d}"


def _estimate_audio_duration(input_path: Path, text_chapter: TextChapter) -> int:
    """Fallback heuristic until real audio probing (T018/T019)."""

    words = max(text_chapter.word_count, 1)
    base_estimate = words * 500  # ≈0.5s per word
    min_duration = 60_000  # 60 seconds safety net
    try:
        size_bytes = input_path.stat().st_size
        # Assume ~32 KB per minute @128 kbps. Convert bytes to ms heuristically.
        approx_from_size = int((size_bytes / 4096) * 1000)
    except OSError:
        approx_from_size = 0
    return max(base_estimate, approx_from_size, min_duration)


def _echo_summary(summary: Dict[str, object], exit_code: int) -> None:
    if not summary:
        return
    coverage_pct = summary.get("coverage_pct", 0.0)
    expected = summary.get("expected_words", 0)
    aligned = summary.get("aligned_words", 0)
    book = summary.get("book", "?")
    chapter = summary.get("chapter", "?")
    fg = typer.colors.GREEN if exit_code == 0 else typer.colors.YELLOW
    typer.secho(
        f"{book} {chapter}: coverage {coverage_pct:.2f}% ({aligned}/{expected} words aligned)",
        fg=fg,
    )


__all__ = ["register", "_run_process_pipeline"]
