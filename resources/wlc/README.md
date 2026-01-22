# Westminster Leningrad Codex Bundle (Sample)

The full Westminster Leningrad Codex (WLC) JSONL bundle is required for the
alignment CLI. The repository only includes a tiny sample so the verification
script and data model can be exercised without redistributing the full text.

## Expected Structure

```
resources/wlc/
├── checksums.txt
├── README.md
└── <book>-<chapter>.jsonl  # many files in real bundle
```

Each JSONL row includes `book`, `chapter`, `verse`, and a `tokens` array. Every
token must contain `index`, `hebrew`, `translit`, and pronunciation variants.

## Installing the Full Dataset

1. Download the normalized WLC export from the internal data lake or the secure
   artifact store authorised for this project.
2. Drop the files into this directory, keeping the `<book>-<chapter>.jsonl`
   naming scheme.
3. Regenerate `checksums.txt` using `sha256sum *.jsonl > checksums.txt` (or the
   PowerShell equivalent) so `scripts/verify_wlc.py` can validate integrity.

## Sample File

The included `sample_genesis-001.jsonl` file mirrors the real schema and allows
unit tests, contract fixtures, and verification tooling to run in CI.
