from __future__ import annotations

import numpy as np
import pytest

from meshmind.stats import bootstrap_ci, compare_paired, paired_permutation_test


def test_all_positive_differences_hit_the_exact_minimum_p() -> None:
    # Only the all-positive and all-negative sign patterns are as extreme: 2 / 2**5.
    assert paired_permutation_test([0.1, 0.2, 0.3, 0.4, 0.5]) == pytest.approx(2 / 32)


def test_three_seeds_can_never_be_significant() -> None:
    assert paired_permutation_test([1.0, 1.0, 1.0]) == pytest.approx(0.25)


def test_zero_differences_give_p_one() -> None:
    assert paired_permutation_test([0.0, 0.0, 0.0, 0.0]) == pytest.approx(1.0)


def test_p_value_is_symmetric_in_sign() -> None:
    d = [0.3, -0.1, 0.4, 0.2, 0.05, 0.15]
    assert paired_permutation_test(d) == pytest.approx(paired_permutation_test([-x for x in d]))


def test_exact_p_matches_hand_enumeration() -> None:
    # d = [1, 2, -1], observed |sum| = 2. Signed sums over the 8 patterns:
    # 2, 4, -2, 0, 0, 2, -4, -2 -> six have |sum| >= 2.
    assert paired_permutation_test([1.0, 2.0, -1.0]) == pytest.approx(6 / 8)


def test_monte_carlo_branch_for_many_pairs() -> None:
    rng = np.random.default_rng(0)
    p = paired_permutation_test(rng.normal(1.0, 0.5, size=30), n_resamples=20_000)
    assert p < 0.001


def test_bootstrap_ci_brackets_the_mean_and_is_reproducible() -> None:
    d = [0.010, 0.014, 0.016, 0.012, 0.018, 0.011]
    low, high = bootstrap_ci(d)
    assert low < np.mean(d) < high
    assert (low, high) == bootstrap_ci(d)
    assert min(d) <= low and high <= max(d)


def test_bootstrap_ci_of_a_single_value_is_degenerate() -> None:
    assert bootstrap_ci([0.5]) == (0.5, 0.5)


def test_compare_paired_counts_wins_in_the_right_direction() -> None:
    latency_ql = [10.0, 11.0, 9.0, 10.5]
    latency_sp = [12.0, 10.0, 11.0, 12.5]
    result = compare_paired(latency_ql, latency_sp, "latency", "sp", higher_is_better=False)
    assert result.wins == 3
    assert result.mean_diff == pytest.approx(-1.25)
    assert result.n == 4
    assert result.to_dict()["significant"] is result.significant


@pytest.mark.parametrize(
    ("args", "kwargs"),
    [(([], [], "m", "b"), {}), (([1.0, 2.0], [1.0], "m", "b"), {})],
)
def test_invalid_inputs(args: tuple, kwargs: dict) -> None:
    with pytest.raises(ValueError):
        compare_paired(*args, **kwargs)


def test_invalid_confidence() -> None:
    with pytest.raises(ValueError):
        bootstrap_ci([1.0, 2.0], confidence=1.5)
