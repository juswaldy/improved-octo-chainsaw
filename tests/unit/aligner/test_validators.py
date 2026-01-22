from __future__ import annotations

from hb_align.aligner import validators


def test_coverage_pass() -> None:
    status = validators.evaluate_coverage(expected_words=100, aligned_words=97)
    assert status.coverage_pct == 97.0
    assert status.passed is True
    assert validators.determine_exit_code(status) == 0


def test_coverage_fail_when_below_threshold() -> None:
    status = validators.evaluate_coverage(expected_words=200, aligned_words=150, threshold=95.0)
    assert status.coverage_pct == 75.0
    assert status.passed is False
    assert validators.determine_exit_code(status) == 2


def test_coverage_handles_zero_expected_words() -> None:
    status = validators.evaluate_coverage(expected_words=0, aligned_words=0)
    assert status.coverage_pct == 0.0
    assert status.passed is False
    assert validators.determine_exit_code(status) == 2
