# Contract: `hb-align batch`

**Purpose**: Process multiple chapter recordings in one command, orchestrating per-file `process` runs, handling parallelism, and producing a manifest of results.

## CLI Synopsis
```bash
hb-align batch \
  --input-dir ./audio/genesis \
  [--pattern "*.mp3"] \
  [--parallel 3] \
  [--tradition modern] \
  [--resume manifest.json] \
  [--output-dir ./output]
```

## Inputs
| Flag | Required | Description | Default |
|------|----------|-------------|---------|
| `--input-dir` | Yes | Directory containing chapter audio files | — |
| `--pattern` | No | Glob filter for filenames | `*.mp3` |
| `--parallel` | No | Max concurrent chapters (1–cpu_count) | `min(3, cpu//2)` |
| `--tradition` | No | Pronunciation profile applied to all unless overrides exist | `modern` |
| `--resume` | No | Existing manifest to continue/retry | None |
| `--output-dir` | No | Base directory for generated artifacts | `./output` |
| `--cache-dir` | No | Cache root | `~/.hb-align/cache` |
| `--stop-on-fail` | No | Abort batch when any chapter fails | `false` |
| `--book` | No | Override book for all files (when folder contains single book) | derived from filenames |

### Preconditions
- Input directory exists and contains files following `<book>-<chapter>.*` naming or metadata overrides provided.
- `hb-align process` contract satisfied for each file (MFA installed, WLC bundle available, etc.).

## Outputs
- Per-chapter artifacts identical to `hb-align process`, stored under `--output-dir/<book>/<chapter>/`.
- Batch manifest written to `--output-dir/<book>/manifest.json` (or path from `--resume`).

### Manifest Schema
```json
{
  "batch_id": "UUID",
  "input_dir": "./audio/genesis",
  "started_at": "2025-11-30T12:00:00Z",
  "completed_at": "2025-11-30T12:25:00Z",
  "summary": {
    "total": 10,
    "success": 9,
    "failed": 1,
    "avg_runtime_ms": 142000,
    "avg_coverage_pct": 97.6,
    "avg_confidence": 0.90
  },
  "items": [
    {
      "file_name": "genesis-001.mp3",
      "status": "success",
      "coverage_pct": 98.2,
      "confidence_avg": 0.91,
      "exit_code": 0,
      "artifacts": {
        "csv": "output/genesis/001/alignments.csv",
        "json": "output/genesis/001/alignments.json",
        "summary": "output/genesis/001/summary.json"
      }
    },
    {
      "file_name": "genesis-002.mp3",
      "status": "failed",
      "exit_code": 2,
      "error_message": "Coverage 92.7%",
      "artifacts": {}
    }
  ]
}
```

## Exit Codes
| Code | Meaning |
|------|---------|
| `0` | All chapters succeeded |
| `5` | At least one chapter failed (see manifest) |
| `3` | Fatal batch-level error (input dir missing, manifest invalid, etc.) |

## Error Conditions
| Condition | Behavior |
|-----------|----------|
| Input directory missing | Exit 3 `INPUT_DIR_NOT_FOUND` |
| Manifest resume file invalid JSON | Exit 3 `INVALID_MANIFEST` |
| Parallel value outside allowed range | Exit 3 `INVALID_PARALLELISM` |
| Chapter process failure | Recorded in manifest `items[]`; batch exit 5 if any |

## Sample Console Output
```
[hb-align] Batch start: ./audio/genesis (parallel=3)
✔ genesis-001.mp3 (98.2% coverage, 0.91 confidence)
✖ genesis-002.mp3 (coverage 92.7% < 95%)
✔ genesis-003.mp3 (97.5% coverage)
Summary: total=3 success=2 failed=1 duration=00:07:12
Manifest: output/genesis/manifest.json
Exit code: 5
```

## Observability
- Progress bar per chapter plus aggregate ETA.
- Manifest includes provisional flags when calibration constants marked provisional.
- Optional `--json` flag (future) may stream NDJSON events for integration.
