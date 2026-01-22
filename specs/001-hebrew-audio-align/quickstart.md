# Quickstart: Hebrew Bible Audio/Text Alignment CLI

**Feature Branch**: `001-hebrew-audio-align`  
**Purpose**: Help contributors and reviewers set up the environment, install Montreal Forced Aligner (MFA), verify the Westminster Leningrad Codex bundle, and run sample commands.

## 1. Prerequisites
- **OS**: macOS 13+, Windows 11 (WSL2 recommended), or Ubuntu 22.04+.
- **Python**: 3.11.x (managed via `pyenv`, `asdf`, or system install).
- **Package Manager**: `pip` or `poetry`; instructions assume `poetry` for reproducibility.
- **Audio tooling**: `ffmpeg` (for MP3 → WAV conversion), `sox` optional for inspection.
- **Montreal Forced Aligner**: v3.2 (CLI `mfa`). Installed via Conda or pip package as recommended by MFA docs.

### Optional Utilities
- `make` for scripted setup steps.
- `jq` for inspecting JSON summaries.

## 2. Clone & Environment Setup
```bash
# Clone repo
 git clone git@github.com:juswaldy/improved-octo-chainsaw.git
 cd improved-octo-chainsaw
 git checkout 001-hebrew-audio-align

# Create virtual environment with Poetry
 poetry env use 3.11
 poetry install
```
If using plain pip:
```bash
python3.11 -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate for Windows
pip install -r requirements.txt
```

## 3. Install Montreal Forced Aligner (MFA)
### Using Conda (recommended)
```bash
conda create -n mfa3 python=3.11 -y
conda activate mfa3
conda install -c conda-forge montreal-forced-aligner=3.2
```
Make sure `mfa` is on PATH:
```bash
mfa version
```
If Conda is unavailable, follow MFA docs for standalone installers. Document path in env var `MFA_HOME` if not on PATH.

## 4. Install ffmpeg
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt install ffmpeg`
- Windows: use `choco install ffmpeg` or install via Scoop.

## 5. Verify Westminster Leningrad Codex Bundle
The feature bundles normalized WLC text under `resources/wlc/`.
```bash
ls resources/wlc
cat resources/wlc/README.md
sha256sum resources/wlc/checksums.txt
```
Run the provided integrity script (once implemented):
```bash
poetry run hb-align assets verify-wlc
```
This checks JSONL schema and ensures transliteration columns exist.

## 6. Prepare Sample Assets
A demo chapter (`samples/genesis-001.mp3`) will ship with the feature. Until then, place a short MP3 at `samples/genesis-001.mp3` adhering to the naming convention `<book>-<chapter>.mp3`.

Convert to WAV (if desired) to inspect:
```bash
ffmpeg -i samples/genesis-001.mp3 -ar 16000 -ac 1 samples/genesis-001.wav
```

## 7. Run Single-Chapter Alignment
```bash
poetry run hb-align process \
  --input samples/genesis-001.mp3 \
  --tradition modern \
  --output-dir ./output-demo
```
Expected output:
- `output-demo/genesis/001/alignments.csv`
- `output-demo/genesis/001/summary.json`
Check coverage in summary:
```bash
jq '.coverage_pct, .avg_confidence' output-demo/genesis/001/summary.json
```
Exit code should be `0` (>=95% coverage). Coverage failures exit `2`.

## 8. Review Low-Confidence Words
```bash
poetry run hb-align review \
  --input output-demo/genesis/001/alignments.csv \
  --threshold 0.9 \
  --output reports/genesis-001-low.csv
```
Check exit code `0` if rows emitted, `4` if none below threshold.

## 9. Batch Processing (Optional)
```bash
poetry run hb-align batch \
  --input-dir samples/genesis-book \
  --parallel 3 \
  --output-dir ./output-demo
```
Inspect manifest:
```bash
jq '.summary' output-demo/genesis/manifest.json
```
Batch exits `0` when all succeed, `5` if any chapter fails.

## 10. Troubleshooting Checklist
| Symptom | Check |
|---------|-------|
| `mfa` not found | Confirm Conda env activated or add MFA install path to PATH/`MFA_HOME`. |
| Coverage <95% | Inspect summary JSON for flagged verses; re-run with `--chunk-size 40` or review audio quality. |
| Missing WLC bundle | Run `git lfs pull` if bundle stored via LFS (future) or fetch from secure storage. |
| Windows performance issues | Prefer WSL2 for running MFA; ensure ffmpeg available inside WSL. |

## 11. Next Steps for Contributors
- Update `README.md` once CLI stabilizes.
- Add integration tests referencing these steps.
- Keep quickstart aligned with future automation (e.g., `make setup-mfa`).
