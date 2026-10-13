"""Benchmark routing policies sharing the ``select_action(env, state, valid_actions)`` API."""

from __future__ import annotations

from collections.abc import Sequence

import networkx as nx
import numpy as np

from meshmind.environment import NetworkEnvironment, State
from meshmind.topology import NetworkTopology


def _dynamic_cost(u: int, v: int, data: dict[str, float]) -> float:
    return data["base_latency"] + data["congestion_penalty"]


def shortest_path(
    topology: NetworkTopology, source: int, destination: int, dynamic: bool = False
) -> list[int] | None:
    """Least-cost path by base latency (or dynamic cost); ``None`` if unreachable."""
    weight = _dynamic_cost if dynamic else "base_latency"
    try:
        return nx.dijkstra_path(topology.graph, source, destination, weight=weight)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


class ShortestPathBaseline:
    """Static OSPF-like routing: always forward along the min base-latency path."""

    name = "shortest_path"

    def __init__(self) -> None:
        self._next_hop: dict[tuple[int, int], int] = {}

    def reset(self, seed: int | None = None) -> None:
        self._next_hop.clear()

    def select_action(
        self, env: NetworkEnvironment, state: State, valid_actions: Sequence[int]
    ) -> int:
        current, destination, _ = state
        key = (current, destination)
        if key not in self._next_hop:
            path = shortest_path(env.topology, current, destination)
            if path is None or len(path) < 2:
                raise ValueError(f"no route from {current} to {destination}")
            self._next_hop[key] = path[1]
        return self._next_hop[key]


class CongestionAwareBaseline:
    """Recomputes the min (base_latency + congestion_penalty) path at every hop.

    Nodes the flow has already visited are excluded so the recomputation cannot
    oscillate between two links whose penalties change mid-flow.
    """

    name = "congestion_aware"

    def reset(self, seed: int | None = None) -> None:
        return None

    def select_action(
        self, env: NetworkEnvironment, state: State, valid_actions: Sequence[int]
    ) -> int:
        current, destination, _ = state
        visited = set(env.path) - {current}
        graph = env.topology.graph.subgraph(n for n in env.topology.graph if n not in visited)
        try:
            path = nx.dijkstra_path(graph, current, destination, weight=_dynamic_cost)
        except nx.NetworkXNoPath:
            path = shortest_path(env.topology, current, destination, dynamic=True)
        if path is None or len(path) < 2:
            raise ValueError(f"no route from {current} to {destination}")
        return path[1]


class RandomRoutingBaseline:
    """Uniformly random next hop among valid neighbours (seeded)."""

    name = "random"

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def reset(self, seed: int | None = None) -> None:
        self.rng = np.random.default_rng(self.seed if seed is None else seed)

    def select_action(
        self, env: NetworkEnvironment, state: State, valid_actions: Sequence[int]
    ) -> int:
        if not valid_actions:
            raise ValueError("no valid actions available")
        return int(self.rng.choice(list(valid_actions)))
