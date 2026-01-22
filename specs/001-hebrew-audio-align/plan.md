# Implementation Plan: Hebrew Bible Audio/Text Alignment

**Branch**: `001-hebrew-audio-align` | **Date**: 2025-11-30 | **Spec**: specs/001-hebrew-audio-align/spec.md  
**Input**: Feature specification derived from the user request plus clarifications logged on 2025-11-30.

## Summary

Deliver a Python-based CLI (`hb-align`) that aligns Hebrew Bible chapter recordings to canonical text, powered by Montreal Forced Aligner (MFA). Work proceeds in independent slices mapped to the three user stories:

1. **P1 – Single-Chapter Alignment**: Build ingestion, text normalization + transliteration, MFA alignment, and CSV/JSON export with ≥95% coverage at ≥0.85 confidence. Includes intermediate cache management, CLI UX, and structured logging.
2. **P2 – Review & Flagging**: Layer a reviewer workflow that filters low-confidence rows, summarizes stats, and exports QA reports without rerunning alignment. Relies on the P1 schema.
3. **P3 – Batch Processing**: Add batch orchestration to process multiple chapters with manifests, resumable execution, and failure isolation while reusing caches/logging.

Phase 0 research focuses on (a) training/using MFA with Hebrew pronunciations (Ashkenazi/Sephardi/Modern), (b) reliable transliteration pipeline (ISO 259-based) that feeds MFA lexicons, (c) chunking strategies for very long chapters (e.g., Psalms 119) without losing context, and (d) packaging the Westminster Leningrad Codex data bundle plus pronunciation dictionaries locally so the tool works offline.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Montreal Forced Aligner (MFA 3.x), librosa/pydub/soundfile for audio handling, NumPy/Pandas for data transforms, Typer (CLI), Rich (logging/output), PyYAML for configs.  
**Storage**: Local filesystem (output directories, cached MFA corpora/lexicons, manifests).  
**Testing**: pytest + pytest-benchmark; golden CSV fixtures for contract tests; soundfile-based integration tests.  
**Target Platform**: Cross-platform CLI (Windows, macOS, Linux) with MFA binaries available; CI focus on Linux.  
**Project Type**: Single CLI project with `src/hb_align` package and `tests/`.  
**Performance Goals**: Meet SC-001 (≥95% coverage @ ≥0.85 confidence) and SC-003 (10 chapters ≈45 min audio processed in <30 min on baseline 8-core box).  
**Constraints**: Must fail runs <95% coverage (exit code 2); operate fully offline with bundled WLC text; chunk processing windows <60s for long chapters; keep CPU <80% avg in batch mode (observability).  
**Scale/Scope**: Entire Tanakh (~929 chapters) over time; initial milestone focuses on a single book but architecture must scale across books with pronunciation profiles.

## Constitution Check

- [x] **Principle I – Independent Value Slices**: Each user story in the spec is deliverable/testable independently; plan keeps work scoped per story with shared prerequisites confined to Foundational steps.
- [x] **Principle II – Constitution Gate**: Problem statement, measurable outcomes (SC-001..004), and clarifications (bundled text + 95% threshold) are captured; remaining unknowns noted under Phase 0 research tasks.
- [x] **Principle III – Evidence First**: Acceptance tests, CSV schema, exit codes, and success metrics are referenced; tests will precede implementation (contract fixtures + audio samples).
- [x] **Principle IV – Text-First Interfaces**: CLI contracts (`process`, `review`, `batch`) defined in spec; outputs/logs are CSV/JSON/Markdown.
- [x] **Principle V – Traceable Changes**: Plan references spec paths, research items, and will feed tasks.md; no cross-artifact drift introduced.

## Project Structure

```text
src/
└── hb_align/
    ├── cli/              # Typer commands: process, review, batch
    ├── audio/            # I/O, format normalization, chunking
    ├── text/             # WLC loader, normalization, transliteration, lexicon export
    ├── aligner/          # MFA orchestration, pronunciation profiles, caching
    ├── review/           # Confidence analysis, reporting utilities
    ├── batch/            # Job planner, manifest writer, resumable orchestration
    └── utils/            # Logging, config, dependency checks

resources/
└── wlc/                  # Bundled Westminster Leningrad Codex text + metadata

outputs/
└── (generated)           # alignments/, manifests/, logs/ per run

tests/
├── unit/
├── integration/
└── contract/             # Golden CSV/JSON comparison per CLI command

specs/001-hebrew-audio-align/
├── contracts/
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md
```

**Structure Decision**: Single Python package (`src/hb_align`) keeps CLI + services cohesive, mirroring Constitution expectations for text-first tooling. Separate submodules isolate audio, text, alignment, review, and batch orchestration so user stories can be worked independently; shared assets (WLC bundle, configs) live under `resources/`.

## Implementation Strategy

### Foundational (shared prerequisites)
- Ship/validate bundled Westminster Leningrad Codex dataset plus pronunciation dictionaries (Modern, Ashkenazi, Sephardi) and expose configuration hooks.
- Create transliteration + lexicon generator feeding MFA (Phase 0 research deliverable) and persist caches under `outputs/cache/`.
- Wrap MFA binaries via Python subprocess with health checks, download/install automation, and deterministic configs (sample rate, beam widths, scoring thresholds).
- Build observability scaffolding: structured logging (JSON + text), run manifests, metric aggregation (coverage %, average confidence, processing durations).

### User Story 1 – Single-Chapter Alignment (P1)
- CLI `process` command orchestrates ingestion → normalization → transliteration → MFA alignment → CSV/JSON export.
- Implement chunking/windowing for long chapters, ensuring overlaps merge cleanly; store intermediate `.TextGrid` or MFA JSON, convert to canonical schema.
- Implement coverage validator enforcing ≥95% aligned words; exit codes and summary messages follow spec.
- Provide smoke tests with short sample chapter audio + expected CSV fixture; contract tests ensure schema stability.

### User Story 2 – Review & Flagging (P2)
- Add review module reading alignment CSV/JSON, computing stats per verse/word, applying configurable thresholds, and outputting filtered tables + Markdown summary.
- Extend CLI with `review` command (Typer) to support `--threshold`, `--format`, `--output` options; integrate Rich tables for console view.
- Provide QA report template + tests ensuring deterministic ordering/grouping; add unit tests for aggregator edge cases (ties, missing verses).

### User Story 3 – Batch Chapters & Metadata Audit (P3)
- Build batch planner to walk directories, parse filenames, and queue `process` runs (sequential or parallel). Support resumable manifests with statuses (pending/running/success/failure).
- Add manifest writer summarizing runtime, coverage, confidence stats, failure reasons per file; CLI exit code 5 if any chapter fails while preserving successful outputs.
- Implement concurrency controls (max parallel alignments) plus resource guards (CPU threshold) referencing SC-003; tests simulate mixed success/failure batch runs using stub audio files.

## Phase 0 Research Focus
-
1. **MFA Hebrew Pipeline**: Determine best practice for generating grapheme-to-phoneme lexicons from WLC for each pronunciation profile; evaluate need for additional acoustic models or training.
2. **Transliteration & Normalization**: Validate ISO-259-like transliteration accuracy for consonant/vowel handling, especially for niqqud-less text; confirm reversibility or need for custom heuristics.
3. **Chunking Strategy for Long Chapters**: Experiment with sliding windows (<60s) + overlap merging to ensure timestamp continuity without overwhelming MFA.
4. **Performance Benchmarks**: Measure throughput on baseline hardware (8-core, 32 GB RAM) to ensure SC-003 feasibility; identify hotspots (audio preprocessing vs MFA runtime).
5. **Confidence Calibration**: Understand MFA scoring to translate log probabilities into user-facing confidence percentages; confirm threshold mapping for exit codes + review tool.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|---------------------------------------|
| _None_ | | |
