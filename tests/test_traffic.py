from __future__ import annotations

import pytest

from meshmind.traffic import TRAFFIC_PROFILES, TrafficGenerator

NODES = list(range(12))


@pytest.mark.parametrize("profile", list(TRAFFIC_PROFILES))
def test_demands_stay_within_profile_range(profile: str) -> None:
    low, high = TRAFFIC_PROFILES[profile]
    flows = TrafficGenerator(NODES, profile, seed=3).generate(500)
    demands = [f.demand for f in flows]
    assert min(demands) >= low
    assert max(demands) <= high


def test_profile_ranges_match_specification() -> None:
    assert TRAFFIC_PROFILES == {
        "low": (5.0, 15.0),
        "moderate": (20.0, 50.0),
        "high": (60.0, 120.0),
        "dynamic": (10.0, 90.0),
    }


@pytest.mark.parametrize("profile", list(TRAFFIC_PROFILES))
def test_source_never_equals_destination(profile: str) -> None:
    flows = TrafficGenerator(NODES, profile, seed=11).generate(1000)
    assert all(f.source != f.destination for f in flows)
    assert all(f.source in NODES and f.destination in NODES for f in flows)


def test_same_seed_gives_identical_flows() -> None:
    a = TrafficGenerator(NODES, "dynamic", seed=42).generate(50)
    b = TrafficGenerator(NODES, "dynamic", seed=42).generate(50)
    assert a == b


def test_different_seeds_give_different_flows() -> None:
    a = TrafficGenerator(NODES, "moderate", seed=1).generate(50)
    b = TrafficGenerator(NODES, "moderate", seed=2).generate(50)
    assert a != b


def test_generate_with_seed_reseeds() -> None:
    gen = TrafficGenerator(NODES, "high", seed=0)
    first = gen.generate(20, seed=7)
    gen.generate(20)
    assert gen.generate(20, seed=7) == first


def test_two_node_network_always_alternates() -> None:
    flows = TrafficGenerator([4, 9], "low", seed=0).generate(100)
    assert {(f.source, f.destination) for f in flows} <= {(4, 9), (9, 4)}


def test_dynamic_profile_varies_within_episode() -> None:
    flows = TrafficGenerator(NODES, "dynamic", seed=5).generate(100)
    demands = [f.demand for f in flows]
    assert max(demands) - min(demands) > 30.0


@pytest.mark.parametrize(("nodes", "profile"), [([0], "low"), ([0, 0], "low"), (NODES, "extreme")])
def test_invalid_generator_arguments(nodes: list[int], profile: str) -> None:
    with pytest.raises(ValueError):
        TrafficGenerator(nodes, profile)


def test_invalid_count() -> None:
    with pytest.raises(ValueError):
        TrafficGenerator(NODES, "low").generate(0)
