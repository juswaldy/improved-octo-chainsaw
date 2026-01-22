"""Validation helpers for coverage and exit code enforcement (T017)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoverageStatus:
    """Represents coverage metrics for a processed chapter."""

    expected_words: int
    aligned_words: int
    coverage_pct: float
    threshold: float = 95.0

    @property
    def passed(self) -> bool:
        return self.coverage_pct >= self.threshold


def evaluate_coverage(
    *, expected_words: int, aligned_words: int, threshold: float = 95.0
) -> CoverageStatus:
    """Compute basic coverage metrics."""

    coverage_pct = (aligned_words / expected_words) * 100 if expected_words else 0.0
    return CoverageStatus(
        expected_words=expected_words,
        aligned_words=aligned_words,
        coverage_pct=round(coverage_pct, 3),
        threshold=threshold,
    )


def determine_exit_code(status: CoverageStatus) -> int:
    """Map coverage status to CLI exit codes (0 on pass, 2 on failure)."""

    return 0 if status.passed else 2


__all__ = ["CoverageStatus", "evaluate_coverage", "determine_exit_code"]
