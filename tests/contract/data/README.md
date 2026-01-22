# Contract Test Data

This folder holds canonical fixtures referenced by contract tests under `tests/contract/`.

## Genesis 1 Sample

T012 seeds metadata for the `samples/genesis-001.mp3` demo chapter so contract tests can reason about expected outputs once alignment pipelines exist.

Artifacts to add in later tasks (US1 contract tests):
- `tests/contract/data/genesis-001-expected.csv` — golden alignment rows.
- `tests/contract/data/genesis-001-summary.json` — summary snapshot with coverage ≥95%.

For now, the README documents the structure so future tests know where to place fixtures. Once real alignments are generated, update this directory accordingly and keep provenance notes (source audio, generation command) in this file.
