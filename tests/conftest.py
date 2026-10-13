from __future__ import annotations

import pytest

from meshmind.config import EnvironmentConfig
from meshmind.environment import NetworkEnvironment
from meshmind.topology import NetworkTopology
from meshmind.traffic import TrafficGenerator

# 0 -- 1 -- 2 -- 3 -- 4 with a long shortcut 0 -- 4
LINE_LINKS = [
    (0, 1, 100.0, 1.0),
    (1, 2, 100.0, 1.0),
    (2, 3, 100.0, 1.0),
    (3, 4, 100.0, 1.0),
    (0, 4, 100.0, 50.0),
]


@pytest.fixture
def line_topology() -> NetworkTopology:
    return NetworkTopology(LINE_LINKS, name="line")


@pytest.fixture
def line_env(line_topology: NetworkTopology) -> NetworkEnvironment:
    traffic = TrafficGenerator(line_topology.nodes, "moderate", seed=0)
    return NetworkEnvironment(line_topology, traffic, flows_per_episode=3)


@pytest.fixture
def grid_env() -> NetworkEnvironment:
    topology = NetworkTopology.from_name("small_grid")
    traffic = TrafficGenerator(topology.nodes, "high", seed=0)
    return NetworkEnvironment(topology, traffic, flows_per_episode=10, config=EnvironmentConfig())
