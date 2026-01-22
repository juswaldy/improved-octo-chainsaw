# Tasks: Hebrew Bible Audio/Text Alignment

**Input**: specs/001-hebrew-audio-align/
**Prerequisites**: spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Evidence-first principle applies—test artifacts called out below are mandatory for their stories (spec.md §Success Criteria).

**Organization**: Phases progress from setup → shared foundations → independent user stories → polish. Tasks remain traceable to spec sections.

## Format: `[ID] [P?] [Story] Description`

- **[P]** means the task can proceed in parallel (different files, no dependency).
- **[Story]** is required for user story slices (US1–US3) and references spec.md sections.
- Include file paths + spec references per Constitution Principle V.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the repository tooling, environment, and reference assets before foundational coding.

- [X] T001 Initialize Poetry project with Python 3.11, Typer entrypoint stub, and base deps (Typer, Rich, pandas) in `pyproject.toml` (plan.md §Technical Context).
- [X] T002 [P] Configure linting/formatting (`ruff`, `black`, `mypy`, `pytest`) plus `pre-commit` hooks in `.pre-commit-config.yaml` and `pyproject.toml` (plan.md §Setup).
- [X] T003 [P] Add `.env.example` and config loader scaffold in `src/hb_align/utils/config.py` to surface MFA paths/cache dirs (plan.md §Foundational).
- [X] T004 Bundle Westminster Leningrad Codex JSONL + transliteration assets under `resources/wlc/` and create verification script `scripts/verify_wlc.py` (spec.md Clarifications, research.md §Text preparation).
- [X] T005 [P] Update root `README.md` with MFA/ffmpeg install steps and troubleshooting pointers consistent with quickstart.md §§1–4.

**Checkpoint**: Repo installs cleanly; WLC assets + documentation verified.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared services (text, MFA, chunking, caching, logging) required before any user story can execute.

- [X] T006 Implement transliteration + IPA generator covering Modern/Ashkenazi/Sephardi profiles in `src/hb_align/text/transliterator.py` using `resources/confidence.yml` (data-model.md §PronunciationProfile, research.md §Transliteration).
- [X] T007 Create WLC loader/tokenizer with verse/word metadata in `src/hb_align/text/wlc_loader.py` that outputs `TextChapter` objects (data-model.md §TextChapter).
- [X] T008 Build MFA orchestration wrapper (subprocess checks, health validation, CLI detection) in `src/hb_align/aligner/mfa_runner.py` (plan.md §Foundational, research.md §MFA Pipeline).
- [X] T009 Add chunking + stitching utilities capped at 50s/5s overlap in `src/hb_align/audio/chunker.py` with unit coverage in `tests/unit/test_chunker.py` (research.md §Chunking).
- [X] T010 Implement cache manager keyed by audio/text/profile hash in `src/hb_align/utils/cache.py` with purge helper (research.md §Caching, spec.md FR-009).
- [X] T011 Provide structured logging + summary writer (text + JSON) capturing coverage/confidence/durations in `src/hb_align/utils/logging.py` (spec.md FR-010).
- [X] T012 Seed `samples/genesis-001.mp3` (or stub) and golden fixtures under `tests/contract/data/` plus docs explaining provenance (spec.md §User Story 1 Independent Test).

**Checkpoint**: Text, audio, MFA, caching, and logging infrastructure ready; all user stories can now proceed.

---

## Phase 3: User Story 1 – Single-Chapter Alignment (Priority: P1) 🎯 MVP

**Goal**: Deliver `hb-align process` CLI that turns one chapter audio file into CSV/JSON alignments with ≥95% coverage and summary logs (spec.md §User Story 1).

**Independent Test**: Run `hb-align process samples/genesis-001.mp3` and verify coverage ≥95%, CSV schema compliance, and exit codes per contracts/process.md.

### Tests for User Story 1

- [X] T013 [P] [US1] Create contract test `tests/contract/test_process_cli.py` validating required outputs + exit codes 0/2/3 using sample assets (contracts/process.md).
- [X] T014 [P] [US1] Add integration test `tests/integration/test_alignment_pipeline.py` covering chunking → MFA → stitching pipeline with stubbed MFA outputs (research.md §Chunking, spec.md SC-001).
- [ ] T039 [P] [US1] Extend contract coverage to assert metadata/file-name mismatches exit with code 3 and actionable messaging in `tests/contract/test_process_cli.py` (spec.md FR-012).

### Implementation for User Story 1

- [X] T015 [US1] Implement Typer `process` command orchestration in `src/hb_align/cli/process.py` (ingest → normalize → transliterate → align → export) (spec.md §User Story 1 scenario 1).
- [ ] T016 [P] [US1] Build alignment formatter + CSV/JSON writers in `src/hb_align/aligner/formatter.py` emitting the schema from data-model.md §WordAlignment.
- [ ] T017 [US1] Add coverage validator + exit code enforcement (95% threshold) in `src/hb_align/aligner/validators.py` (spec.md FR-004, SC-001).
- [ ] T018 [P] [US1] Generate chunk-map diagnostics and `summary.json` aggregator capturing coverage/confidence/CPU metrics in `src/hb_align/aligner/summary.py` (plan.md §Foundational Observability).
- [ ] T019 [US1] Integrate cache manager + CLI flags (`--cache-dir`, `--dry-run`) into `src/hb_align/cli/process.py` ensuring reruns reuse artifacts (spec.md FR-009).
- [ ] T020 [US1] Update `quickstart.md` §§7–8 with exact `hb-align process` invocation, sample outputs, and troubleshooting for coverage failures (spec.md §Independent Test US1).
- [ ] T040 [US1] Implement filename/text reconciliation + error messaging in `src/hb_align/cli/validators.py`, wiring it into `process` prior to alignment so FR-012 exits code 3 on mismatch.
- [ ] T041 [P] [US1] Add verse-level confidence aggregation + serialization to `src/hb_align/aligner/summary.py`, emitting `ConfidenceProfile` entries for review tooling (spec.md FR-005, NFR-004).
- [ ] T042 [P] [US1] Create unit tests `tests/unit/test_confidence_profile.py` ensuring verse aggregates appear in `summary.json` and match alignment inputs.

**Checkpoint**: `hb-align process` produces alignments + summaries that meet SC-001; MVP ready.

---

## Phase 4: User Story 2 – Quality Review & Flagging (Priority: P2)

**Goal**: Enable reviewers to filter/export low-confidence words without rerunning alignment via `hb-align review` (spec.md §User Story 2).

**Independent Test**: Run `hb-align review --input output/genesis/001/alignments.csv --threshold 0.9` and confirm flagged rows + exit codes 0/4 per contracts/review.md.

### Tests for User Story 2

- [ ] T021 [P] [US2] Add contract test `tests/contract/test_review_cli.py` covering threshold validation, CSV/JSON outputs, and exit code 4 when no rows flagged (spec.md §User Story 2 scenario 1).
- [ ] T022 [P] [US2] Write unit tests for aggregations/grouping in `tests/unit/test_review_aggregator.py` (data-model.md §ConfidenceProfile).
- [ ] T043 [US2] Add performance benchmark `tests/perf/test_review_latency.py` (pytest-benchmark) confirming `hb-align review` processes a 1,500-word alignment in <5 seconds and logs duration (spec.md SC-002, NFR-002).

### Implementation for User Story 2

- [ ] T023 [US2] Implement Typer `review` command in `src/hb_align/cli/review.py` (input parsing, threshold validation, outputs) (contracts/review.md).
- [ ] T024 [US2] Create review aggregator utilities computing per-verse stats + reasons in `src/hb_align/review/aggregator.py` (spec.md FR-007).
- [ ] T025 [P] [US2] Build CSV/JSON/Markdown exporter helpers with metadata headers in `src/hb_align/review/exporters.py` (contracts/review.md Outputs).
- [ ] T026 [US2] Expand quickstart §8 and add reviewer workflow notes to `README.md` linking to acceptance scenarios (spec.md §User Story 2 Independent Test).

**Checkpoint**: Review workflow surfaces low-confidence rows and can be tested independently of alignment runs.

---

## Phase 5: User Story 3 – Batch Chapters & Metadata Audit (Priority: P3)

**Goal**: Provide `hb-align batch` to process multiple chapters, produce manifests, and support resumable executions (spec.md §User Story 3).

**Independent Test**: Run `hb-align batch --input-dir samples/genesis-book --parallel 2` with ≥3 chapters to verify per-chapter outputs, manifest data, and exit code 5 on any failure (contracts/batch.md).

### Tests for User Story 3

- [ ] T027 [P] [US3] Author contract test `tests/contract/test_batch_cli.py` ensuring manifest schema + exit codes 0/5 based on mixed success (spec.md §User Story 3 scenario 1).
- [ ] T028 [P] [US3] Create integration test `tests/integration/test_batch_runner.py` using stubbed process invocations to simulate failures/resume (plan.md §User Story 3 Strategy).
- [ ] T044 [US3] Build load/performance test `tests/perf/test_batch_throughput.py` simulating ≥10 chapters to assert runtime <30 minutes and CPU <80% using telemetry hooks (spec.md SC-003, NFR-003).

### Implementation for User Story 3

- [ ] T029 [US3] Implement batch runner/orchestrator with queue + parallelism controls in `src/hb_align/batch/runner.py` (spec.md FR-008).
- [ ] T030 [US3] Build manifest writer + validation utilities in `src/hb_align/batch/manifest.py` capturing stats + provisional flags (data-model.md §BatchManifest).
- [ ] T031 [US3] Add Typer `batch` CLI wiring CLI flags, resume support, and shared options in `src/hb_align/cli/batch.py` (contracts/batch.md Inputs/Outputs).
- [ ] T032 [P] [US3] Implement resume + retry helpers (reading prior manifest, re-queuing failures) in `src/hb_align/batch/resume.py` (spec.md §User Story 3 scenario 2).
- [ ] T033 [US3] Document batch usage + troubleshooting in `quickstart.md` §9 and create operator checklist in `README.md` (spec.md §Independent Test US3).
- [ ] T045 [P] [US3] Extend manifest writer to capture failure percentages and actionable error codes, enforcing SC-004 thresholds inside `src/hb_align/batch/manifest.py`.
- [ ] T046 [US3] Create validation script/tests (`tests/integration/test_manifest_quality.py`) that fail CI when >2% chapters lack actionable diagnostics, documenting remediation guidance.

**Checkpoint**: Batch automation runs independently, producing manifests + resumable state per SC-003/SC-004.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, documentation, and calibration tasks impacting multiple stories.

- [ ] T034 [P] Refine confidence calibration constants per tradition in `resources/confidence.yml`, documenting procedure in `specs/001-hebrew-audio-align/research.md` addendum (research.md §Confidence Calibration).
- [ ] T035 Instrument telemetry (CPU %, stage durations) within `src/hb_align/utils/logging.py` and ensure `summary.json` matches SC-003 metrics (plan.md §Performance Goals).
- [ ] T036 [P] Broaden quickstart + README troubleshooting (multi-speaker limits, WSL guidance, cache purge) referencing research.md risks.
- [ ] T037 Execute end-to-end validation on Windows (WSL2) and macOS, logging platform notes in `docs/platform-notes.md` with any deltas (plan.md §Target Platform).
- [ ] T038 Run Constitution compliance audit: verify each spec acceptance scenario has tasks/tests mapped, recording checklist in `specs/001-hebrew-audio-align/tasks.md` appendix or `notes.md`.

---

## Dependencies & Execution Order

- Setup (Phase 1) → Foundational (Phase 2) → {US1, US2, US3 in priority order}. Polish follows once desired stories complete.
- User story dependencies:
  - US1 depends only on foundational tasks.
  - US2 reuses US1 outputs but can proceed once foundational + US1 schema exist (independent test via alignments fixture).
  - US3 depends on US1 command for individual runs; US2 is optional but provides QA context.
- Critical path: T001 → T012 → T013–T020 (MVP). US2/US3 can start after T012 if contract tests stub `process` output fixtures.

## Parallel Execution Examples

- **Setup**: T002 and T003 execute concurrently after T001 scaffolds the project; T005 can update docs while code tools install.
- **US1**: T013 and T014 run in parallel to define contract + integration shells; T016 and T018 develop formatter + summary concurrently once data models exist.
- **US2**: T021 and T022 (tests) can proceed simultaneously; T025 exporter work can happen alongside T023 command wiring so long as CLI interfaces are stubbed.
- **US3**: T027/T028 tests parallelize; T030 manifest writer and T032 resume logic can develop concurrently after T029 defines runner interfaces.

## Implementation Strategy

1. Finish Phases 1–2 to satisfy Constitution Gate and unlock shared infrastructure.
2. Deliver MVP by completing all US1 tasks (T013–T020) and validating SC-001 via contract/integration tests.
3. Layer US2 review workflow focusing on analytics/export independence; release to reviewers once T021–T026 pass.
4. Implement US3 batch processing, ensuring manifests + resumable logic align with SC-003/SC-004.
5. Execute Polish tasks (T034–T038) before final QA/demo to cover calibration, documentation, and platform verification.
