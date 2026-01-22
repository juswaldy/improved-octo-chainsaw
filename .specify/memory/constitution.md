<!--
Sync Impact Report
Version change: 0.0.0 → 1.0.0
Modified principles:
- None (initial ratification)
Added sections:
- Delivery Constraints
- Workflow & Quality
Removed sections:
- None
Templates requiring updates:
- .specify/templates/plan-template.md ✅
- .specify/templates/spec-template.md ✅
- .specify/templates/tasks-template.md ✅
- .specify/templates/commands (not present) ⚠
Follow-up TODOs:
- None
-->

# Improved Octo Chainsaw Constitution

## Core Principles

### I. Independent Value Slices
- Every `spec.md` MUST define user stories that deliver user value independently, with clear priorities and acceptance tests that can be executed in isolation.
- Implementation plans and `tasks.md` MUST keep work scoped to a single story unless a shared prerequisite is explicitly listed under "Foundational" tasks.
- Releases MUST stop once a single story reaches demo-ready status; bundling multiple unfinished stories is prohibited.
Rationale: Independent slices let the team pause after any story while still shipping value, matching the repository's template-driven workflow.

### II. Constitution Gate Before Research
- `/speckit.plan` cannot start until the Constitution Check affirms: (1) the problem statement, (2) measurable success criteria, and (3) blockers/constraints pulled from prior specs.
- Any missing information must be captured as `NEEDS CLARIFICATION` notes inside the plan before research proceeds.
- Exceptions require written approval recorded in the plan's "Complexity Tracking" table.
Rationale: Early validation prevents speculative planning and keeps features within declared constraints.

### III. Evidence Before Build
- Tests, acceptance scenarios, and measurable outcomes MUST be written and linked to user stories before implementation tasks are created.
- Tasks marked as tests in `tasks.md` MUST run and fail before corresponding implementation items can begin.
- Success metrics in specs MUST be referenced by the plan and verified post-implementation before claiming completion.
Rationale: Leading with evidence preserves quality and ensures every artifact can be audited quickly.

### IV. Text-First, Scriptable Interfaces
- All tooling interacting with this repo MUST read/write plain-text artifacts (Markdown, JSON) and be runnable via CLI so that automation can execute without IDE context.
- Features requiring runtime I/O MUST describe their CLI or API contract in `contracts/` within the spec folder before coding starts.
- Logs, diagnostics, and data samples stored in the repo MUST be text-based to remain reviewable in PRs.
Rationale: Text-first workflows keep automation portable and simplify reviews across environments.

### V. Traceable Changes
- Every artifact MUST cite the files and stories it depends on (e.g., linking tasks to `spec.md` stories, plans to research docs).
- When updating shared constraints or governance rules, the corresponding templates MUST be updated in the same change.
- Pull requests MUST reference the constitution version they comply with; reviewers block merges when references are missing.
Rationale: Explicit traceability prevents drift between templates, specs, and implementation tasks.

## Delivery Constraints

- Each feature folder under `specs/` MUST include `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, and `tasks.md` unless a document is explicitly waived in writing.
- User stories MUST stay independent end-to-end: specs state acceptance, plans outline isolation strategy, tasks/timeline preserve separations, and checklists validate independence before completion.
- Shared infrastructure (e.g., authentication, logging) belongs in the "Foundational" phase of `tasks.md`; any new shared dependency requires justification in the plan's "Complexity Tracking" table.
- Observability and versioning requirements belong inside each plan's Technical Context; missing entries mean the Constitution Gate fails.

## Workflow & Quality

- Workflow follows: Constitution Gate → Research (Phase 0) → Design (Phase 1) → User Story implementation (Phase 2+) → Polish. Each transition requires verifying the prior artifact is complete and reviewed.
- Checklists generated via `/speckit.checklist` MUST reference constitution principles for each category to prove compliance (e.g., "Principle III" for test evidence).
- Tasks flagged `[P]` MUST operate on different files or services to respect parallelization rules and avoid collisions.
- Any deviation (skipping documents, merging stories, deferring tests) must include a risk entry in the plan and obtain reviewer sign-off documented in the PR.

## Governance

- This constitution supersedes conflicting guidance in README or templates; changes to other docs follow from here.
- Amendments require: (1) proposal PR referencing the desired version bump, (2) evidence that affected templates/docs were updated, and (3) reviewer consensus recorded in the PR description.
- Versioning follows SemVer semantics: MAJOR for removing or redefining principles, MINOR for new principles/sections, PATCH for clarifications.
- Compliance reviews occur at each PR: reviewers verify Constitution version references, check template alignment, and block merges when principles are violated.
- Ratification and amendment dates must use ISO-8601 (YYYY-MM-DD) to stay machine-parseable.

**Version**: 1.0.0 | **Ratified**: 2025-11-30 | **Last Amended**: 2025-11-30
