"""Paired significance testing for policy comparisons across seeds.

Every policy is evaluated on the same held-out traffic for each seed, so the
natural unit is the per-seed difference. Two distribution-free tools are used:

* a sign-flip permutation test: under H0 (no difference) each paired difference
  is equally likely to be positive or negative, so flipping signs enumerates the
  null distribution of the mean difference exactly;
* a percentile bootstrap confidence interval for the mean difference.
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from dataclasses import asdict, dataclass

import numpy as np

EXACT_LIMIT = 16
"""Up to this many pairs the permutation test enumerates all 2**n sign patterns."""


def _as_array(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("need a non-empty 1-D sequence of paired differences")
    return array


def paired_permutation_test(
    differences: Sequence[float], n_resamples: int = 100_000, seed: int = 0
) -> float:
    """Two-sided p-value for H0: the mean paired difference is zero.

    Exact for up to ``EXACT_LIMIT`` pairs, Monte Carlo otherwise. With n pairs the
    smallest attainable p-value is 2 / 2**n (0.25 for n = 3, about 0.002 for n = 10).
    """
    d = _as_array(differences)
    observed = abs(d.mean())
    if d.size <= EXACT_LIMIT:
        signs = np.array(list(itertools.product((1.0, -1.0), repeat=d.size)))
    else:
        signs = np.random.default_rng(seed).choice((1.0, -1.0), size=(n_resamples, d.size))
    null = np.abs((signs * d).mean(axis=1))
    return float(np.mean(null >= observed - 1e-12))


def bootstrap_ci(
    differences: Sequence[float],
    confidence: float = 0.95,
    n_resamples: int = 10_000,
    seed: int = 0,
) -> tuple[float, float]:
    """Percentile bootstrap confidence interval for the mean difference."""
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    d = _as_array(differences)
    rng = np.random.default_rng(seed)
    means = d[rng.integers(0, d.size, size=(n_resamples, d.size))].mean(axis=1)
    tail = (1.0 - confidence) / 2.0
    return float(np.quantile(means, tail)), float(np.quantile(means, 1.0 - tail))


@dataclass(frozen=True)
class PairedComparison:
    metric: str
    baseline: str
    mean_diff: float
    ci_low: float
    ci_high: float
    p_value: float
    wins: int
    n: int
    higher_is_better: bool

    @property
    def significant(self) -> bool:
        return self.p_value < 0.05

    def to_dict(self) -> dict[str, float | int | str | bool]:
        return {**asdict(self), "significant": self.significant}


def compare_paired(
    treatment: Sequence[float],
    baseline: Sequence[float],
    metric: str,
    baseline_name: str,
    higher_is_better: bool = True,
) -> PairedComparison:
    """Compare two policies seed by seed: mean(treatment - baseline), CI, p-value, wins."""
    t = _as_array(treatment)
    b = _as_array(baseline)
    if t.size != b.size:
        raise ValueError("treatment and baseline need the same number of seeds")
    d = t - b
    low, high = bootstrap_ci(d)
    better = d > 0 if higher_is_better else d < 0
    return PairedComparison(
        metric=metric,
        baseline=baseline_name,
        mean_diff=float(d.mean()),
        ci_low=low,
        ci_high=high,
        p_value=paired_permutation_test(d),
        wins=int(better.sum()),
        n=int(d.size),
        higher_is_better=higher_is_better,
    )
