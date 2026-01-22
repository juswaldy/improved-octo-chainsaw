import subprocess
from pathlib import Path

import pytest

import hb_align.aligner.mfa_runner as mfa_runner
from hb_align.aligner.mfa_runner import (
    MfaCommandError,
    MfaNotFoundError,
    MfaRunner,
)
from hb_align.utils.config import AppConfig


def _app_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        project_root=tmp_path,
        wlc_root=tmp_path / "wlc",
        cache_dir=tmp_path / "cache",
        output_root=tmp_path / "outputs",
        logs_dir=tmp_path / "logs",
        mfa_executable="mfa-custom",
        log_format="text",
    )


def test_from_config_uses_custom_executable(tmp_path):
    config = _app_config(tmp_path)
    runner = MfaRunner.from_config(config)
    assert runner.executable == "mfa-custom"


def test_check_health_runs_version(monkeypatch):
    runner = MfaRunner("mfa")

    monkeypatch.setattr(mfa_runner.shutil, "which", lambda _: "C:/fake/mfa.exe")

    captured = {}

    def fake_run(cmd, **kwargs):  # noqa: ANN001
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="MFA 3.2.0", stderr="")

    monkeypatch.setattr(mfa_runner.subprocess, "run", fake_run)

    result = runner.check_health()
    assert captured["cmd"] == ["C:/fake/mfa.exe", "version"]
    assert "MFA" in result.stdout


def test_align_corpus_dry_run(tmp_path, monkeypatch):
    fake_exe = tmp_path / "mfa.exe"
    fake_exe.write_text("echo", encoding="utf-8")
    runner = MfaRunner(str(fake_exe))

    result = runner.align_corpus(
        corpus_dir=tmp_path / "corpus",
        dictionary_path=tmp_path / "dict",
        acoustic_model_path=tmp_path / "model",
        output_dir=tmp_path / "out",
        num_jobs=2,
        config_path=tmp_path / "config.yml",
        dry_run=True,
        extra_args=["--debug"],
    )

    assert result.command[0] == str(fake_exe)
    assert "--debug" in result.command
    assert "-j" in result.command
    assert result.returncode == 0


def test_align_corpus_raises_on_failure(monkeypatch):
    runner = MfaRunner("mfa")
    monkeypatch.setattr(mfa_runner.shutil, "which", lambda _: "C:/fake/mfa.exe")

    def fake_run(cmd, **kwargs):  # noqa: ANN001
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="boom")

    monkeypatch.setattr(mfa_runner.subprocess, "run", fake_run)

    with pytest.raises(MfaCommandError):
        runner.align_corpus("c", "d", "m", "o")


def test_resolve_executable_not_found(monkeypatch):
    runner = MfaRunner("mfa-missing")
    monkeypatch.setattr(mfa_runner.shutil, "which", lambda _: None)
    with pytest.raises(MfaNotFoundError):
        runner.check_health()
