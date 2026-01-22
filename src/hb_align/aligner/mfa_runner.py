"""Montreal Forced Aligner (MFA) orchestration helpers (T008).

This module keeps MFA interactions centralized so higher-level commands can stay
focused on business logic. It performs three core responsibilities:

1. Discover the MFA executable (respecting configuration + PATH)
2. Provide lightweight health checks so the CLI can fail fast with guidance
3. Offer convenience wrappers (`align_corpus`) for core MFA operations

Real alignment happens via MFA's CLI, so the runner focuses on building
subprocess commands and surfacing actionable errors.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Sequence

from hb_align.utils.config import AppConfig


class MfaRunnerError(RuntimeError):
    """Base error for MFA orchestration issues."""


class MfaNotFoundError(MfaRunnerError):
    """Raised when the MFA executable cannot be located."""


class MfaCommandError(MfaRunnerError):
    """Raised when MFA returns a non-zero exit code."""


@dataclass(frozen=True)
class MfaCommandResult:
    command: Sequence[str]
    returncode: int
    stdout: str
    stderr: str


class MfaRunner:
    """Wrapper around the MFA CLI."""

    def __init__(
        self,
        executable: str = "mfa",
        *,
        env: Mapping[str, str] | None = None,
        timeout_seconds: int = 3600,
    ) -> None:
        self._executable = executable
        self._cached_path: str | None = None
        self._env: MutableMapping[str, str] = dict(env or {})
        self._timeout = timeout_seconds

    @classmethod
    def from_config(cls, config: AppConfig) -> "MfaRunner":
        return cls(config.mfa_executable)

    @property
    def executable(self) -> str:
        return self._executable

    def check_health(self) -> MfaCommandResult:
        """Run `mfa version` to verify the binary is callable."""

        return self._run(["version"], expect_success=True)

    def align_corpus(
        self,
        corpus_dir: Path | str,
        dictionary_path: Path | str,
        acoustic_model_path: Path | str,
        output_dir: Path | str,
        *,
        num_jobs: int | None = None,
        config_path: Path | str | None = None,
        dry_run: bool = False,
        extra_args: Iterable[str] | None = None,
    ) -> MfaCommandResult:
        """Execute `mfa align` with the provided paths."""

        args = [
            "align",
            str(Path(corpus_dir)),
            str(Path(dictionary_path)),
            str(Path(acoustic_model_path)),
            str(Path(output_dir)),
            "--clean",
            "--overwrite",
        ]
        if num_jobs:
            args.extend(["-j", str(num_jobs)])
        if config_path:
            args.extend(["--config_path", str(Path(config_path))])
        if extra_args:
            args.extend(list(extra_args))
        return self._run(args, expect_success=True, dry_run=dry_run)

    def _resolve_executable(self) -> str:
        if self._cached_path:
            return self._cached_path

        candidate = Path(self._executable)
        if candidate.is_file():
            resolved = str(candidate)
        else:
            discovered = shutil.which(self._executable)
            if not discovered:
                raise MfaNotFoundError(
                    "Montreal Forced Aligner executable not found. "
                    "Set MFA_BIN or install MFA per quickstart.md instructions."
                )
            resolved = discovered
        self._cached_path = resolved
        return resolved

    def _run(
        self,
        args: Sequence[str],
        *,
        expect_success: bool,
        dry_run: bool = False,
    ) -> MfaCommandResult:
        executable = self._resolve_executable()
        command = [executable, *args]
        if dry_run:
            return MfaCommandResult(command=command, returncode=0, stdout="", stderr="")

        try:
            completed = subprocess.run(  # noqa: S603,S607 (controlled command)
                command,
                capture_output=True,
                text=True,
                env=self._env or None,
                timeout=self._timeout,
                check=False,
            )
        except FileNotFoundError as exc:  # pragma: no cover - defensive guard
            raise MfaNotFoundError(str(exc)) from exc

        if expect_success and completed.returncode != 0:
            raise MfaCommandError(
                f"MFA command failed (exit {completed.returncode}): {completed.stderr.strip()}"
            )
        return MfaCommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


__all__ = [
    "MfaRunner",
    "MfaCommandResult",
    "MfaRunnerError",
    "MfaNotFoundError",
    "MfaCommandError",
]
