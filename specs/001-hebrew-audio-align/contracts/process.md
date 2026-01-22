# Contract: `hb-align process`

**Purpose**: Align a single Hebrew Bible chapter recording to canonical text and emit alignment tables.

## CLI Synopsis
```bash
hb-align process \
  --input path/to/genesis-001.mp3 \
  [--book Genesis] [--chapter 1] \
  [--tradition modern|ashkenazi|sephardi] \
  [--chunk-size 50] [--chunk-overlap 5] \
  [--output-dir ./output] [--cache-dir ~/.hb-align/cache]
```

## Inputs
| Flag | Required | Description | Default |
|------|----------|-------------|---------|
| `--input` | Yes | Path to MP3/WAV file for a single chapter | — |
| `--book` | No | Overrides book parsed from filename | Derived from filename prefix |
| `--chapter` | No | Overrides chapter parsed from filename | Derived from filename suffix |
| `--tradition` | No | Pronunciation profile (`modern`, `ashkenazi`, `sephardi`) | `modern` |
| `--chunk-size` | No | Chunk length in seconds (≤60) | 50 |
| `--chunk-overlap` | No | Overlap between chunks in seconds | 5 |
| `--output-dir` | No | Directory root for artifacts | `./output` |
| `--cache-dir` | No | Cache root for MFA corpora/dicts | `~/.hb-align/cache` |
| `--dry-run` | No | Validate inputs without running alignment | `false` |
| `--log-format` | No | `text` or `json` logs | `text` |

### Preconditions
- MFA executable available on PATH (`mfa --version` succeeds) or configured via `MFA_HOME` env.
- Westminster Leningrad Codex bundle present under `resources/wlc/` (validated via checksum file).
- Output directory writable; cache directory has ≥1 GB free.

## Outputs
Artifacts are written under `--output-dir/<book>/<chapter>/` by default.

| File | Description |
|------|-------------|
| `alignments.csv` | WordAlignment table (schema from data-model.md) |
| `alignments.json` | Same data in JSON (array of objects) |
| `summary.json` | AlignmentRun metadata (coverage, confidence stats, timings) |
| `log.txt` / `log.json` | Run log in requested format |
| `chunk-map.json` | Diagnostic map of chunking windows |

CLI stdout prints human-readable summary; stderr emits warnings/errors.

## Exit Codes
| Code | Meaning |
|------|---------|
| `0` | Success (coverage ≥95%, processing completed) |
| `2` | Alignment coverage <95% (failure per spec) |
| `3` | Fatal error (I/O, MFA failure, invalid inputs) |

## Error Conditions
| Condition | Behavior |
|-----------|----------|
| Missing/invalid input file | Immediate exit code 3 with message `INPUT_NOT_FOUND` |
| Filename cannot map to book/chapter and no overrides provided | Exit 3 `INVALID_METADATA` |
| MFA not installed/detected | Exit 3 `MFA_NOT_AVAILABLE` |
| Coverage <95% | Exit 2, summary includes `coverage_status: failed` |
| Cache corruption (hash mismatch) | Cache entries ignored; CLI warns and recomputes |

## Sample Success Response (stdout excerpt)
```
[hb-align] Processing Genesis 1 (tradition=modern)
Audio duration: 00:04:12 | Chunk size: 50s (overlap 5s)
Coverage: 98.2% (expected 434 words)
Avg confidence: 0.91 | Min confidence: 0.72 (6 words below threshold)
Artifacts:
  output/genesis/001/alignments.csv
  output/genesis/001/alignments.json
Exit code: 0
```

## Sample Failure (coverage)
```
Coverage fell to 92.7% (missing 32 words)
Affected verses: Gen 1:5, 1:27
See output/genesis/001/summary.json for details
Exit code: 2
```

## Logging & Observability
- Logs include run_id, cache_key, chunk metrics, MFA stage timings, CPU/memory sample.
- `summary.json` contains `metrics:{coverage_pct, avg_confidence, mfa_duration_ms, preprocessing_ms}`.
