# Feature Specification: Hebrew Bible Audio/Text Alignment

**Feature Branch**: `001-hebrew-audio-align`  
**Created**: 2025-11-30  
**Status**: Draft  
**Input**: User description: "develop an audio splitting app that matches an audio recording of the hebrew bible with the hebrew text being read. the input is one chapter of speech recording, and the book/chapter reference is specified by the file name eg genesis-001.mp3. figure out intermediate representations or encodings if needed, eg english transliteration etc. the output should be a book/chapter/verse/word--timestamp table with percent confidence"

> **Constitution Alignment**: Document each user story so it can be implemented and tested independently (Principle I). Define measurable success criteria and evidence before any build work (Principle III).

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Single-Chapter Alignment (Priority: P1)

An audio archivist drops a `book-chapter.mp3` file (e.g., `genesis-001.mp3`) into the CLI tool and receives a CSV/JSON table listing every word in Genesis 1 with start/end timestamps and confidence percentages.

**Why this priority**: Produces the core deliverable (word-level timestamp table) so recordings can be indexed and searched.

**Independent Test**: Run the CLI against a known chapter and verify the exported table covers 100% of expected verses with confidence values and sequential timestamps.

**Acceptance Scenarios**:

1. **Given** a valid MP3 and accessible canonical Hebrew text, **When** the archivist runs `hb-align process genesis-001.mp3`, **Then** a CSV is created containing book/chapter/verse/word rows with start/end timestamps and ≥95% coverage of expected words (matching the clarified gate).
2. **Given** a filename whose chapter metadata conflicts with detected verse count, **When** the run completes, **Then** the tool flags the mismatch in the summary and still exports the alignment with the problematic rows labeled.

---

### User Story 2 - Quality Review & Flagging (Priority: P2)

A language reviewer opens the alignment output, sorts by confidence, and exports a review report highlighting verses/words below a configurable threshold to schedule re-recordings or manual fixes.

**Why this priority**: Enables a QA loop so low-confidence alignments do not silently ship.

**Independent Test**: Process any chapter, then run the review command to ensure rows below the threshold are surfaced with reasons and can be exported without re-running alignment.

**Acceptance Scenarios**:

1. **Given** an alignment table with word confidences, **When** the reviewer runs `hb-align review --input alignments.csv --threshold 0.85`, **Then** the tool produces a filtered report listing each low-confidence word with verse context and summary statistics.
2. **Given** review feedback marking certain verses for manual inspection, **When** the reviewer exports the flagged rows, **Then** the output includes timestamps and original confidence so downstream editors know where to focus.

---

### User Story 3 - Batch Chapters & Metadata Audit (Priority: P3)

A production operator processes an entire book (multiple chapter files) in one batch, receives per-chapter summaries (duration, alignment accuracy, failure counts), and stores the outputs in a consistent directory layout for ingestion downstream.

**Why this priority**: Supports production-scale workflows where dozens of chapters are processed nightly without manual intervention.

**Independent Test**: Provide a folder with ≥3 chapter files and verify the batch command generates per-chapter alignment files, an aggregate manifest, and clear failure logs without depending on the review workflow.

**Acceptance Scenarios**:

1. **Given** a folder of correctly named MP3s, **When** the operator runs `hb-align batch --input ./genesis-book`, **Then** the tool processes each file sequentially (or in configurable parallel) and writes outputs under `./genesis-book/output/<chapter>/alignments.csv` with a manifest summarizing success/failure per file.
2. **Given** one corrupted audio file in the batch, **When** the batch run finishes, **Then** the manifest shows the failure, the process exits non-zero, yet completed chapter outputs remain intact.

### Edge Cases

- Audio duration shorter/longer than expected text (reader skipped or repeated verses) → system must flag gaps/overlaps in the manifest and confidence summary.
- Filenames that do not map to a known Tanakh book or contain non-numeric chapter segments → run should fail fast with guidance.
- Audio containing background noise/cantillation leading to misalignments → reviewer report should highlight words with low signal-to-noise and recommend manual inspection.
- Hebrew text sources with cantillation/vowel marks differing from spoken form → normalization/transliteration step must strip diacritics before alignment to avoid mismatches.
- Chapters exceeding target runtime (e.g., Psalms 119) → chunking logic should keep buffer windows under 60 seconds to stay within alignment engine limits.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST ingest a single-chapter audio file (MP3 or WAV) and parse the canonical book/chapter from the filename pattern `<book>-<chapter>.mp3`.
- **FR-002**: System MUST load the corresponding canonical Hebrew text from the bundled Westminster Leningrad Codex dataset (stored locally with the tool) and normalize it by removing cantillation marks, diacritics, and punctuation prior to processing.
- **FR-003**: System MUST generate both native Hebrew and phonetic transliteration (ISO 259-style) representations to enable acoustic alignment even when pronunciations vary.
- **FR-004**: System MUST align audio to text at word granularity, producing start and end timestamps for every word, including verse identifiers and sequential ordering metadata, and treat runs with <95% aligned words as failures (exit code 2) per CLI contract.
- **FR-005**: System MUST compute confidence percentages per word and roll them up to verse-level aggregates for QA reporting.
- **FR-006**: CLI MUST export the alignment table in both CSV and JSON formats, with schema `book,chapter,verse,word_index,word_text,start_ms,end_ms,confidence`.
- **FR-007**: Review workflow MUST allow users to set a confidence threshold and emit a filtered report/CSV of low-confidence words grouped by verse.
- **FR-008**: Batch mode MUST accept a directory, process each chapter according to FR-001—FR-007, and produce a manifest summarizing success/failure, coverage %, and runtime per file.
- **FR-009**: System MUST store intermediate acoustic/phonetic representations (e.g., Mel-frequency features, transliteration tokens) on disk so reruns can skip recomputation when inputs are unchanged.
- **FR-010**: Each run MUST emit a structured log/summary (text + JSON) describing audio metadata, processing duration, confidence stats, and any anomalies (missing verses, repeated sections, parse failures).
- **FR-011**: Users MUST be able to configure pronunciation profiles (Ashkenazi, Sephardi, Modern Israeli) to adjust transliteration → phoneme mapping before alignment.
- **FR-012**: When the Hebrew text source or audio length is inconsistent with the filename metadata, the CLI MUST exit non-zero and include actionable error messaging.

### Non-Functional Requirements

- **NFR-001**: Tooling MUST operate fully offline after initial MFA/ffmpeg installation; all alignment inputs (WLC text, pronunciation profiles) ship with the repository to meet Delivery Constraints §1.
- **NFR-002**: Review workflow MUST surface low-confidence rows for a 1,500-word chapter within 5 seconds on baseline 8-core hardware (mirrors SC-002) and log duration in `summary.json`.
- **NFR-003**: Batch mode MUST process at least 10 chapters (≈45 minutes of audio) in under 30 minutes while keeping average CPU utilization below 80% (SC-003) and recording metrics for audit.
- **NFR-004**: Observability outputs (logs, manifests, summaries) MUST remain text/JSON-based and include actionable error codes so ≤2% of chapters fail without diagnostics (SC-004, Principle IV).

### Key Entities *(include if feature involves data)*

- **AudioChapter**: Reference to a single chapter recording including file path, detected duration, sample rate, encoding, and derived metadata (book, chapter, reading tradition).
- **TextChapter**: Canonical Hebrew text for the same book/chapter, stored as ordered verses and tokenized words with transliteration/phoneme variants.
- **WordAlignment**: Atomic record linking a word token to start/end timestamps, acoustic scores, verse context, and confidence metrics.
- **ConfidenceProfile**: Aggregated stats per verse/chapter capturing min/avg confidence, flagged anomalies, and reviewer threshold decisions.

### Interface & CLI Contracts *(mandatory when runtime I/O exists)*

- **Command**: `hb-align process`
  - **Inputs**: `--input <path/to/book-chapter.mp3>` (required), `--book <BookName>` (optional override), `--chapter <#>` (optional override), `--tradition <ashkenazi|sephardi|modern>` default `modern`, `--output-dir <path>` default `./output`.
  - **Outputs**: Writes `alignments.csv` and `alignments.json` inside `output/<book>/<chapter>/`. Prints run summary to stdout; warnings/errors go to stderr. Exit code `0` on success, `2` on alignment coverage below threshold, `3` on fatal I/O errors.
  - **Contracts Folder Link**: `specs/001-hebrew-audio-align/contracts/process.md`

- **Command**: `hb-align review`
  - **Inputs**: `--input <alignments.csv>`, `--threshold <0-1>` default `0.9`, `--format <csv|json>` default `csv`.
  - **Outputs**: Filtered rows printed to stdout or saved via `--output <path>`. Exit code `0` when file generated, `4` when no rows fall below threshold.
  - **Contracts Folder Link**: `specs/001-hebrew-audio-align/contracts/review.md`

- **Command**: `hb-align batch`
  - **Inputs**: `--input-dir <folder>`, optional `--parallel <n>`, inherits all process command flags as defaults.
  - **Outputs**: Per-chapter alignment artifacts plus `manifest.json` summarizing stats. Exit code `0` on full success, `5` if any chapter fails (details in manifest).
  - **Contracts Folder Link**: `specs/001-hebrew-audio-align/contracts/batch.md`

*Mark "N/A" only when the feature has no runtime interface; otherwise automation cannot validate Principle IV.*

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: ≥95% of words per processed chapter receive a timestamp with confidence ≥0.85 during automated alignment on benchmark recordings.
- **SC-002**: Review workflow surfaces 100% of words below the configured threshold within 5 seconds for a 1500-word chapter.
- **SC-003**: Batch processing can align at least 10 chapters (≈45 minutes of audio) in under 30 minutes on baseline hardware while keeping CPU usage under 80%.
- **SC-004**: ≤2% of chapters per batch fail due to metadata or processing errors, and every failure is recorded in the manifest with actionable error codes.

## Clarifications

### Session 2025-11-30

- Q: How should the canonical Hebrew text be sourced for alignment (local copy vs. remote API vs. user-provided files)? → A: Ship a vetted, normalized Westminster Leningrad Codex dataset with the tool and load chapters locally each run.
- Q: What aligned-word coverage threshold should cause the CLI to fail instead of warn (90%, 95%, or 98%)? → A: Require ≥95% aligned words; exit code 2 when coverage drops below this target.

## Assumptions

- Source audio is a single speaker reading Modern Israeli pronunciation at ≥128 kbps MP3, mono or stereo.
- Canonical text source is a bundled, normalized Westminster Leningrad Codex dataset distributed with the tool; verse numbering follows the same tradition as the filenames.
- Users operate the system via CLI; no graphical interface is required in this phase.
- Storage and compute resources are sufficient to hold intermediate feature files up to 5× the input audio size per chapter.
