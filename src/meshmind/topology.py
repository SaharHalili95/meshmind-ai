"""Directed network topology with capacity, latency and congestion-aware link state."""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Sequence

import networkx as nx

CONGESTION_THRESHOLD = 0.8

LinkSpec = tuple[int, int, float, float]
"""(source, target, capacity, base_latency_ms)."""

# 2x3 grid:  0 - 1 - 2
#            |   |   |
#            3 - 4 - 5
SMALL_GRID_LINKS: tuple[LinkSpec, ...] = (
    (0, 1, 100.0, 2.0),
    (1, 2, 100.0, 2.0),
    (3, 4, 100.0, 3.0),
    (4, 5, 100.0, 3.0),
    (0, 3, 100.0, 1.0),
    (1, 4, 60.0, 1.0),
    (2, 5, 100.0, 1.0),
)

ABILENE_NODE_LABELS: tuple[str, ...] = (
    "Seattle",
    "Sunnyvale",
    "Los Angeles",
    "Denver",
    "Kansas City",
    "Houston",
    "Indianapolis",
    "Atlanta",
    "Chicago",
    "New York",
    "Washington",
    "Atlanta-M5",
)

# Latencies approximate one-way fibre propagation delay in milliseconds.
ABILENE_LINKS: tuple[LinkSpec, ...] = (
    (0, 1, 100.0, 6.5),
    (0, 3, 100.0, 8.2),
    (1, 2, 100.0, 2.9),
    (1, 3, 100.0, 7.8),
    (2, 5, 100.0, 11.0),
    (3, 4, 100.0, 4.6),
    (4, 5, 100.0, 5.9),
    (4, 6, 100.0, 4.8),
    (5, 7, 100.0, 6.0),
    (6, 8, 80.0, 1.4),
    (6, 7, 100.0, 3.8),
    (8, 9, 100.0, 5.7),
    (9, 10, 80.0, 1.7),
    (10, 7, 100.0, 4.9),
    (7, 11, 150.0, 0.2),
)

TOPOLOGY_NAMES: tuple[str, ...] = ("small_grid", "abilene")


def congestion_penalty(base_latency: float, utilization: float) -> float:
    """Quadratic penalty that activates once utilization exceeds 80%."""
    if utilization <= CONGESTION_THRESHOLD:
        return 0.0
    excess = (utilization - CONGESTION_THRESHOLD) / (1.0 - CONGESTION_THRESHOLD)
    return base_latency * excess**2


class NetworkTopology:
    """A validated ``nx.DiGraph`` whose edges carry mutable load state.

    Edge attributes: ``capacity`` (>0), ``base_latency`` (>=0), ``load`` (>=0, uncapped),
    ``utilization`` (load / capacity, capped at ``max_utilization``) and
    ``congestion_penalty``.
    """

    def __init__(
        self,
        links: Sequence[LinkSpec],
        name: str = "custom",
        bidirectional: bool = True,
        max_utilization: float = 1.5,
        capacity_scale: float = 1.0,
        node_labels: Sequence[str] | None = None,
        require_connected: bool = True,
    ) -> None:
        if not links:
            raise ValueError("topology must contain at least one link")
        if max_utilization < 1.0:
            raise ValueError("max_utilization must be >= 1.0")
        if capacity_scale <= 0:
            raise ValueError("capacity_scale must be > 0")

        self.name = name
        self.max_utilization = float(max_utilization)
        self.graph: nx.DiGraph = nx.DiGraph(name=name)

        for source, target, capacity, latency in links:
            self._validate_link(source, target, capacity, latency)
            pairs = [(source, target), (target, source)] if bidirectional else [(source, target)]
            for u, v in pairs:
                if self.graph.has_edge(u, v):
                    raise ValueError(f"duplicate link {u}->{v}")
                self.graph.add_edge(
                    u,
                    v,
                    capacity=float(capacity) * capacity_scale,
                    base_latency=float(latency),
                    load=0.0,
                    utilization=0.0,
                    congestion_penalty=0.0,
                )

        if node_labels is not None:
            if len(node_labels) != self.graph.number_of_nodes():
                raise ValueError("node_labels length must match node count")
            for node in self.graph.nodes:
                self.graph.nodes[node]["label"] = node_labels[node]

        if require_connected and not nx.is_strongly_connected(self.graph):
            raise ValueError(f"topology '{name}' is not strongly connected")

    @staticmethod
    def _validate_link(source: int, target: int, capacity: float, latency: float) -> None:
        if source == target:
            raise ValueError(f"self-loop on node {source} is not allowed")
        if source < 0 or target < 0:
            raise ValueError("node ids must be non-negative integers")
        if capacity <= 0:
            raise ValueError(f"link {source}->{target} must have capacity > 0, got {capacity}")
        if latency < 0:
            raise ValueError(f"link {source}->{target} must have latency >= 0, got {latency}")

    @classmethod
    def from_name(
        cls, name: str, capacity_scale: float = 1.0, max_utilization: float = 1.5
    ) -> NetworkTopology:
        if name == "small_grid":
            return cls(
                SMALL_GRID_LINKS,
                name=name,
                capacity_scale=capacity_scale,
                max_utilization=max_utilization,
            )
        if name == "abilene":
            return cls(
                ABILENE_LINKS,
                name=name,
                capacity_scale=capacity_scale,
                max_utilization=max_utilization,
                node_labels=ABILENE_NODE_LABELS,
            )
        raise ValueError(f"unknown topology '{name}', expected one of {TOPOLOGY_NAMES}")

    @property
    def nodes(self) -> list[int]:
        return sorted(self.graph.nodes)

    @property
    def num_nodes(self) -> int:
        return self.graph.number_of_nodes()

    @property
    def edges(self) -> list[tuple[int, int]]:
        return sorted(self.graph.edges)

    def neighbors(self, node: int) -> list[int]:
        if node not in self.graph:
            raise ValueError(f"unknown node {node}")
        return sorted(self.graph.successors(node))

    def has_edge(self, u: int, v: int) -> bool:
        return self.graph.has_edge(u, v)

    def has_path(self, source: int, target: int) -> bool:
        return nx.has_path(self.graph, source, target)

    def edge_attributes(self, u: int, v: int) -> dict[str, float]:
        if not self.graph.has_edge(u, v):
            raise ValueError(f"no link {u}->{v}")
        return dict(self.graph.edges[u, v])

    def edge_cost(self, u: int, v: int) -> float:
        data = self.graph.edges[u, v]
        return data["base_latency"] + data["congestion_penalty"]

    def delivery_fraction(self, u: int, v: int) -> float:
        """Share of a flow the link can carry under proportional sharing (1.0 if not overloaded)."""
        data = self.graph.edges[u, v]
        if data["load"] <= data["capacity"]:
            return 1.0
        return data["capacity"] / data["load"]

    def _refresh_edge(self, u: int, v: int) -> None:
        data = self.graph.edges[u, v]
        utilization = min(data["load"] / data["capacity"], self.max_utilization)
        data["utilization"] = utilization
        data["congestion_penalty"] = congestion_penalty(data["base_latency"], utilization)

    def add_load(self, u: int, v: int, amount: float) -> None:
        if not self.graph.has_edge(u, v):
            raise ValueError(f"no link {u}->{v}")
        if amount < 0:
            raise ValueError("load amount must be non-negative")
        self.graph.edges[u, v]["load"] += float(amount)
        self._refresh_edge(u, v)

    def set_load(self, u: int, v: int, load: float) -> None:
        if not self.graph.has_edge(u, v):
            raise ValueError(f"no link {u}->{v}")
        if load < 0:
            raise ValueError("load must be non-negative")
        self.graph.edges[u, v]["load"] = float(load)
        self._refresh_edge(u, v)

    def decay_loads(self, factor: float) -> None:
        """Multiply every link load by ``factor`` to model traffic draining over time."""
        if not 0.0 <= factor <= 1.0:
            raise ValueError("decay factor must be in [0, 1]")
        for u, v in self.graph.edges:
            self.graph.edges[u, v]["load"] *= factor
            self._refresh_edge(u, v)

    def reset_loads(self) -> None:
        for u, v in self.graph.edges:
            self.graph.edges[u, v]["load"] = 0.0
            self._refresh_edge(u, v)

    def utilizations(self) -> list[float]:
        return [data["utilization"] for _, _, data in self.graph.edges(data=True)]

    def average_utilization(self) -> float:
        values = self.utilizations()
        return sum(values) / len(values)

    def outgoing_utilization(self, node: int) -> float:
        """Mean utilization over the node's outgoing links (0.0 for a sink)."""
        values = [self.graph.edges[node, v]["utilization"] for v in self.graph.successors(node)]
        if not values:
            return 0.0
        return sum(values) / len(values)

    def path_latency(self, path: Iterable[int]) -> float:
        nodes = list(path)
        return sum(self.edge_cost(u, v) for u, v in itertools.pairwise(nodes))
