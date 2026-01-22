# Data Model: Hebrew Bible Audio/Text Alignment

**Branch**: `001-hebrew-audio-align`  
**Source**: specs/001-hebrew-audio-align/spec.md + research.md  
**Last Updated**: 2025-11-30

## Overview

The CLI persists and exchanges structured data through CSV/JSON files, cached JSONL documents, and manifests. Core entities and their relationships are defined below so contracts, tasks, and implementations remain synchronized.

## Entities

### AudioChapter
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `id` | UUID | Unique run-scoped identifier | Generated per invocation |
| `book` | Enum (39 OT books) | Derived from filename | MUST match canonical list |
| `chapter` | Int | Parsed from filename | 1 ≤ chapter ≤ book.maxChapter |
| `file_path` | Path | Location of MP3/WAV | MUST exist & be readable |
| `duration_ms` | Int | Detected length post-normalization | > 0 |
| `sample_rate` | Int | Resampled rate (default 16000) | MUST equal MFA config |
| `profile` | Enum (modern, ashkenazi, sephardi) | Selected pronunciation | default `modern` |
| `hash` | Hex string | SHA256 of normalized WAV | used for caching |

Relationships: `AudioChapter` 1→1 `ChunkSet`, 1→1 `TextChapter`, 1→1 `AlignmentRun` (per invocation).

### TextChapter
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `book` | Enum | canonical | matches AudioChapter.book |
| `chapter` | Int | canonical | matches AudioChapter.chapter |
| `verses` | List<`VerseTokens`> | ordered content | cannot be empty |
| `text_version` | String | e.g., `wlc-2023.09` | stored in metadata |

`VerseTokens`
| Field | Type | Description |
| `verse` | String (e.g., `1:3`) | Bible verse number |
| `tokens` | List<`WordToken`> | sequential words |

`WordToken`
| Field | Type | Description |
| `index` | Int | 0-based within verse |
| `hebrew` | String | Original Hebrew (with niqqud removed) |
| `translit` | String | ISO-259 transliteration |
| `ipa_modern` / `ipa_ashkenazi` / `ipa_sephardi` | String | Pronunciation variants |

### PronunciationProfile
Represents mapping rules per tradition.
| Field | Type | Description |
| `name` | Enum | `modern`, `ashkenazi`, `sephardi` |
| `vowel_map` | Dict | transliteration vowel → IPA |
| `consonant_map` | Dict | transliteration consonant → IPA |
| `g2p_rules` | List | overrides triggered by regex |
| `calibration` | Object | constants `a`, `b` for confidence scaling |

### ChunkSet & Chunk
| Field | Type | Description |
| `chunk_id` | UUID | per chunk |
| `start_ms` / `end_ms` | Int | audio range | windows ≤ 50s |
| `overlap_ms` | Int | default 5000 |
| `verse_span` | Range | inclusive verse indexes |
| `status` | Enum (`pending`, `aligned`, `failed`) |
| `text_slice` | List<WordToken> | tokens included |

ChunkSet belongs to an `AudioChapter`; each `Chunk` references chunk-specific MFA outputs.

### AlignmentRun
| Field | Type | Description | Validation |
| `run_id` | UUID | CLI invocation |
| `audio_chapter_id` | UUID | FK | |
| `profile` | PronunciationProfile | used lexicon |
| `chunk_set_id` | UUID | link |
| `started_at` / `completed_at` | Timestamps | | completed_at > started_at |
| `status` | Enum (`success`, `warning`, `failed`) | derived from coverage + MFA exit |
| `coverage_pct` | Float | aligned words / expected | must be recorded |
| `min_confidence` / `avg_confidence` | Float | aggregated from WordAlignment | |
| `output_paths` | Dict | `csv`, `json`, `log`, `manifest` | paths exist |
| `cache_key` | String | hash combination |

### WordAlignment
| Field | Type | Description |
| `book` | Enum |
| `chapter` | Int |
| `verse` | String |
| `word_index` | Int (global) |
| `token_index` | Int (within verse) |
| `word_text` | String (Hebrew) |
| `translit` | String |
| `start_ms` / `end_ms` | Int | -1 if missing |
| `confidence` | Float 0-1 |
| `chunk_id` | UUID | source chunk |
| `flags` | Set (`missing`, `duplicate`, `low_snr`) |

### ConfidenceProfile
Aggregated per verse/chapter.
| Field | Type | Description |
| `scope` | Enum (`verse`, `chapter`) |
| `scope_id` | e.g., `Genesis 1:3` |
| `word_count` | Int |
| `min_confidence` / `avg_confidence` | Float |
| `low_conf_words` | List<WordAlignment.id> |
| `threshold` | Float | user selection |
| `status` | Enum (`pass`, `needs_review`) |

### ReviewFinding
Represents output rows from `hb-align review`.
| Field | Type | Description |
| `word_alignment_id` | UUID |
| `reason` | Enum (`low_confidence`, `missing_timestamp`) |
| `notes` | String |
| `exported_at` | Timestamp |

### BatchManifest & BatchItem
| Field | Type | Description |
| `batch_id` | UUID |
| `input_dir` | Path |
| `started_at` / `completed_at` | Timestamp |
| `summary` | Stats (success_count, fail_count, avg_runtime, avg_coverage) |

`BatchItem`
| Field | Type | Description |
| `file_name` | String |
| `status` | Enum (`pending`, `success`, `failed`) |
| `coverage_pct` | Float |
| `confidence_avg` | Float |
| `error_code` | Int (0,2,3,5) |
| `error_message` | String |
| `artifacts` | Dict (`csv`, `json`, `log`) |

## Relationships Diagram (textual)

```
AudioChapter --1:1--> TextChapter
AudioChapter --1:1--> ChunkSet --1:N--> Chunk
Chunk --N:1--> AlignmentRun
AlignmentRun --1:N--> WordAlignment --N:1--> ConfidenceProfile
AlignmentRun --1:1--> BatchItem (when run via batch)
ConfidenceProfile --N:1--> ReviewFinding (subset flagged)
BatchManifest --1:N--> BatchItem
```

## State Transitions

### AlignmentRun Lifecycle
1. `initialized` → created after CLI validates inputs.
2. `chunking` → chunk set generated.
3. `aligning` → MFA invoked per chunk.
4. `stitching` → chunk outputs merged, coverage computed.
5. `validating` → coverage vs 95% threshold, logs emission.
6. End states:
   - `success`: coverage ≥95%, exit code 0.
   - `warning`: coverage ≥95% but low-confidence words recorded (exit 0, review recommended).
   - `failed`: coverage <95% (exit 2) or MFA/I/O errors (exit 3).

### BatchItem Lifecycle
`pending` → `running` → (`success` | `failed`). On `failed`, manifest retains error metadata; batch exit code 5 if any failure occurs.

### ReviewFinding Lifecycle
`identified` (upon running review) → `exported` (written to file) → optional `resolved` (when user marks completed; stored outside MVP scope).

## Validation Rules & Constraints
- **Coverage Rule**: `aligned_words / expected_words >= 0.95` or AlignmentRun fails (exit 2). Derived from WordAlignment counts.
- **Timestamp Ordering**: For each verse, `start_ms` must be non-decreasing; detection of overlaps >250 ms flagged in `flags`.
- **Chunk Consistency**: Adjacent chunks must overlap exactly `chunk_overlap` ms; mismatch triggers warning and re-chunk suggestion.
- **Cache Integrity**: `hash` stored in AlignmentRun must match cached corpus/dictionary directories; CLI verifies before reusing.
- **Manifest Integrity**: BatchManifest totals must equal sum of BatchItems; validations run before writing manifest.

## Data Storage Formats
- `alignments.csv/json`: Flattened WordAlignment entities.
- `manifest.json`: {batch metadata, items[], stats, provisional flags}.
- `review.csv/json`: Filtered subset of WordAlignment + ConfidenceProfile.
- `resources/wlc/*.jsonl`: Serialized TextChapter + WordToken data.
- `resources/confidence.yml`: Pronunciation calibration constants.

## Open Questions Affecting Data Model
- Should ReviewFindings persist between runs (dedicated DB/file) to support multi-session triage? (Not in MVP.)
- Do we need explicit schema versioning for alignment outputs? Proposed: add `schema_version` field to CSV/JSON (default `1.0`).
- Handling multi-speaker recordings may require `SpeakerSegment` entity if scope expands.
