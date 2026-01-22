# Improved Octo Chainsaw – Hebrew Bible Audio/Text Alignment

This repository hosts the CLI described in `specs/001-hebrew-audio-align/spec.md`. The
tooling aligns Hebrew Bible chapter recordings to the bundled Westminster Leningrad
Codex text, then surfaces QA reports and batch manifests per the Constitution.

## Getting Started (Setup Phase T001–T005)

1. **Install dependencies**
	```bash
	pip install poetry
	poetry install
	```
2. **Configure environment variables** – copy `.env.example` to `.env` and adjust
	cache/output/MFA paths for your workstation. The config loader reads the `.env`
	file automatically before falling back to defaults.
3. **Install MFA + ffmpeg** – follow the detailed steps in
	`specs/001-hebrew-audio-align/quickstart.md` §§1–5.
4. **Verify the WLC bundle** – once you drop the normalized JSONL files under
	`resources/wlc/`, run:
	```bash
	poetry run python scripts/verify_wlc.py
	```
	The script checks checksums and schema fields so downstream tasks can rely on the
	bundled text.

## Running the CLI (stubs during Setup)

The Typer application is wired and published as `hb-align`, but commands currently
emit "not implemented" guidance until their corresponding tasks are delivered.

```bash
poetry run hb-align --help
```

Refer to `specs/001-hebrew-audio-align/tasks.md` for the detailed plan and phase
checkpoints. Quickstart instructions (sections 7–9) will be updated as soon as the
`process`, `review`, and `batch` commands ship.