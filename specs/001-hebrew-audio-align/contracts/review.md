# Contract: `hb-align review`

**Purpose**: Inspect previously generated alignment files, flag low-confidence/missing words, and produce QA reports without rerunning alignment.

## CLI Synopsis
```bash
hb-align review \
  --input output/genesis/001/alignments.csv \
  [--threshold 0.9] [--format csv|json|md] \
  [--group-by verse|chapter|word] \
  [--output ./reports/genesis-001-low-confidence.csv]
```

## Inputs
| Flag | Required | Description | Default |
|------|----------|-------------|---------|
| `--input` | Yes | Path to alignment CSV or JSON | — |
| `--threshold` | No | Confidence threshold (0–1) | 0.90 |
| `--format` | No | Output format: `csv`, `json`, `md`, or `stdout` table | `csv` |
| `--group-by` | No | Aggregation level (`word`, `verse`, `chapter`) | `word` |
| `--limit` | No | Max rows to emit (int) | unlimited |
| `--output` | No | Destination file; stdout if omitted | stdout |
| `--notes` | No | Freeform note appended to exported report metadata | — |

### Preconditions
- Input file conforms to alignment schema (columns `book,chapter,verse,...` etc).
- Threshold ∈ [0.5, 0.99]; CLI validates range.

## Outputs
Depending on format:

| Format | Description |
|--------|-------------|
| `csv` | Columns: `book,chapter,verse,word_index,word_text,start_ms,end_ms,confidence,reason` |
| `json` | Array of objects containing same fields plus `notes` |
| `md` | Markdown table grouped per `group-by` with summary counts |
| `stdout` | Rich-rendered table (color-coded) |

CLI also prints summary stats: count of flagged words, min/avg confidence, verse distribution.

## Exit Codes
| Code | Meaning |
|------|---------|
| `0` | Report generated; at least one row matched OR summary produced |
| `4` | No rows below threshold (nothing to report) |
| `3` | Fatal error (input missing/invalid) |

## Error Conditions
| Condition | Behavior |
|-----------|----------|
| Input file missing | Exit 3 with `REVIEW_INPUT_NOT_FOUND` |
| Schema mismatch | Exit 3 `INVALID_ALIGNMENT_SCHEMA` |
| Threshold outside allowed range | Exit 3 `INVALID_THRESHOLD` |

## Sample Output (stdout)
```
Low-confidence words (<0.85): 12
Worst verse: Genesis 1:5 (avg 0.74)
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━┳━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┓
┃ verse              ┃ word ┃ idx ┃ text ┃ start_ms   ┃ end_ms     ┃ confidence ┃ reason ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━╇━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━┩
│ Genesis 1:5        │ אור  │ 12  │ or   │ 15230      │ 15980      │ 0.74       │ low    │
│ Genesis 1:27       │ בצלמו│ 320 │ btzl │ 98110      │ 98690      │ 0.76       │ low    │
└────────────────────┴──────┴─────┴──────┴────────────┴────────────┴────────────┴────────┘
Report saved: reports/genesis-001-low-confidence.csv
Exit code: 0
```

## Metadata & Traceability
- Exported files include header comment with source `alignments.csv` path, threshold, CLI version, and timestamp.
- When `--notes` provided, appended to JSON/CSV metadata for downstream QA systems.
