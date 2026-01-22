"""Application configuration loader for hb_align.

The loader is intentionally lightweight so it can operate before external
dependencies (MFA, numpy, etc.) are installed. Configuration comes from, in
order of precedence:

1. Environment variables
2. A project-level `.env` file (optional)
3. Safe defaults that match the repository layout
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping

_ENV_FILE_NAME = ".env"


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Resolved runtime settings for the CLI."""

    project_root: Path
    wlc_root: Path
    cache_dir: Path
    output_root: Path
    logs_dir: Path
    mfa_executable: str
    log_format: str

    def ensure_directories(self) -> None:
        """Create directories that should always exist before running commands."""

        for candidate in (self.cache_dir, self.output_root, self.logs_dir):
            candidate.mkdir(parents=True, exist_ok=True)


def load_config(env_file: str | Path | None = None) -> AppConfig:
    """Load configuration using the precedence rules documented above."""

    project_root = Path(__file__).resolve().parents[3]
    env_map = _read_env_file(project_root, env_file)

    def read(key: str, default: str) -> str:
        return os.environ.get(key, env_map.get(key, default))

    def resolve_path(value: str) -> Path:
        return Path(value).expanduser().resolve()

    wlc_root = resolve_path(read("HB_ALIGN_WLC_DIR", str(project_root / "resources" / "wlc")))
    cache_dir = resolve_path(read("HB_ALIGN_CACHE_DIR", str(Path.home() / ".hb-align" / "cache")))
    output_root = resolve_path(read("HB_ALIGN_OUTPUT_ROOT", str(project_root / "outputs")))
    logs_dir = resolve_path(read("HB_ALIGN_LOG_DIR", str(output_root / "logs")))
    mfa_executable = read("MFA_BIN", "mfa")
    log_format = read("HB_ALIGN_LOG_FORMAT", "text")

    config = AppConfig(
        project_root=project_root,
        wlc_root=wlc_root,
        cache_dir=cache_dir,
        output_root=output_root,
        logs_dir=logs_dir,
        mfa_executable=mfa_executable,
        log_format=log_format,
    )

    config.ensure_directories()
    return config


def _read_env_file(project_root: Path, env_file: str | Path | None) -> Mapping[str, str]:
    """Parse KEY=VALUE lines from an env file without mutating os.environ."""

    path = Path(env_file) if env_file else project_root / _ENV_FILE_NAME
    if not path.exists():
        return {}

    values: Dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
