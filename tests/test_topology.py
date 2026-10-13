from __future__ import annotations

import pytest

from meshmind.baselines import shortest_path
from meshmind.topology import NetworkTopology, congestion_penalty

EDGE_KEYS = {"capacity", "base_latency", "load", "utilization", "congestion_penalty"}


@pytest.mark.parametrize(("name", "nodes", "edges"), [("small_grid", 6, 14), ("abilene", 12, 30)])
def test_named_topologies_are_valid(name: str, nodes: int, edges: int) -> None:
    topo = NetworkTopology.from_name(name)
    assert topo.num_nodes == nodes
    assert len(topo.edges) == edges
    assert topo.nodes == list(range(nodes))
    for u, v in topo.edges:
        data = topo.edge_attributes(u, v)
        assert set(data) == EDGE_KEYS
        assert data["capacity"] > 0
        assert data["base_latency"] >= 0
        assert data["load"] == data["utilization"] == data["congestion_penalty"] == 0.0
        assert topo.has_edge(v, u)


def test_named_topologies_are_deterministic() -> None:
    a = NetworkTopology.from_name("abilene")
    b = NetworkTopology.from_name("abilene")
    assert [a.edge_attributes(*e) for e in a.edges] == [b.edge_attributes(*e) for e in b.edges]
    assert a.graph.nodes[0]["label"] == "Seattle"


def test_unknown_topology_name_raises() -> None:
    with pytest.raises(ValueError, match="unknown topology"):
        NetworkTopology.from_name("nsfnet")


def test_custom_attributes_and_capacity_scale() -> None:
    topo = NetworkTopology([(0, 1, 40.0, 3.5)], capacity_scale=2.0)
    assert topo.edge_attributes(0, 1)["capacity"] == 80.0
    assert topo.edge_attributes(1, 0)["base_latency"] == 3.5


def test_directed_only_topology() -> None:
    topo = NetworkTopology(
        [(0, 1, 10.0, 1.0), (1, 2, 10.0, 1.0), (2, 0, 10.0, 1.0)], bidirectional=False
    )
    assert topo.has_edge(0, 1)
    assert not topo.has_edge(1, 0)
    assert topo.neighbors(0) == [1]


@pytest.mark.parametrize(
    ("utilization", "expected"),
    [(0.0, 0.0), (0.5, 0.0), (0.8, 0.0), (0.9, 0.25 * 4.0), (1.0, 4.0), (1.2, 4.0 * 4.0)],
)
def test_congestion_penalty_formula(utilization: float, expected: float) -> None:
    assert congestion_penalty(4.0, utilization) == pytest.approx(expected)


def test_load_update_refreshes_utilization_and_penalty(line_topology: NetworkTopology) -> None:
    line_topology.add_load(0, 1, 90.0)
    data = line_topology.edge_attributes(0, 1)
    assert data["load"] == 90.0
    assert data["utilization"] == pytest.approx(0.9)
    assert data["congestion_penalty"] == pytest.approx(0.25)
    assert line_topology.edge_cost(0, 1) == pytest.approx(1.25)
    assert line_topology.edge_attributes(1, 0)["load"] == 0.0


def test_utilization_is_capped(line_topology: NetworkTopology) -> None:
    line_topology.add_load(0, 1, 1000.0)
    data = line_topology.edge_attributes(0, 1)
    assert data["load"] == 1000.0
    assert data["utilization"] == pytest.approx(1.5)
    assert line_topology.delivery_fraction(0, 1) == pytest.approx(0.1)


def test_reset_and_decay_loads(line_topology: NetworkTopology) -> None:
    line_topology.add_load(1, 2, 80.0)
    line_topology.decay_loads(0.5)
    assert line_topology.edge_attributes(1, 2)["load"] == pytest.approx(40.0)
    assert line_topology.edge_attributes(1, 2)["utilization"] == pytest.approx(0.4)
    line_topology.reset_loads()
    assert all(u == 0.0 for u in line_topology.utilizations())


def test_outgoing_and_average_utilization(line_topology: NetworkTopology) -> None:
    line_topology.set_load(0, 1, 50.0)
    line_topology.set_load(0, 4, 100.0)
    assert line_topology.outgoing_utilization(0) == pytest.approx(0.75)
    assert line_topology.average_utilization() == pytest.approx(1.5 / 10)


def test_negative_load_rejected(line_topology: NetworkTopology) -> None:
    with pytest.raises(ValueError):
        line_topology.add_load(0, 1, -1.0)
    with pytest.raises(ValueError):
        line_topology.add_load(0, 2, 1.0)


@pytest.mark.parametrize(
    "links",
    [
        [],
        [(0, 1, 0.0, 1.0)],
        [(0, 1, -5.0, 1.0)],
        [(0, 1, 10.0, -1.0)],
        [(0, 0, 10.0, 1.0)],
        [(0, 1, 10.0, 1.0), (0, 1, 20.0, 1.0)],
    ],
)
def test_invalid_topologies_raise(links: list) -> None:
    with pytest.raises(ValueError):
        NetworkTopology(links)


def test_disconnected_topology_raises_by_default() -> None:
    links = [(0, 1, 10.0, 1.0), (2, 3, 10.0, 1.0)]
    with pytest.raises(ValueError, match="not strongly connected"):
        NetworkTopology(links)


def test_disconnected_topology_allowed_when_requested() -> None:
    topo = NetworkTopology([(0, 1, 10.0, 1.0), (2, 3, 10.0, 1.0)], require_connected=False)
    assert topo.has_path(0, 1)
    assert not topo.has_path(0, 3)
    assert shortest_path(topo, 0, 3) is None
