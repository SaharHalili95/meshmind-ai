"""Seeded traffic-matrix generation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

TRAFFIC_PROFILES: dict[str, tuple[float, float]] = {
    "low": (5.0, 15.0),
    "moderate": (20.0, 50.0),
    "high": (60.0, 120.0),
    "dynamic": (10.0, 90.0),
}


@dataclass(frozen=True)
class Flow:
    source: int
    destination: int
    demand: float


class TrafficGenerator:
    """Generates source/destination/demand flows from a named profile.

    ``low``/``moderate``/``high`` draw demand uniformly from a fixed range. ``dynamic``
    models diurnal-style drift: the mean demand follows a sinusoid across the
    episode (random phase) and samples are clipped to the profile range.
    """

    def __init__(self, nodes: Sequence[int], profile: str = "moderate", seed: int = 0) -> None:
        if len(nodes) < 2:
            raise ValueError("traffic generation needs at least two nodes")
        if len(set(nodes)) != len(nodes):
            raise ValueError("node ids must be unique")
        if profile not in TRAFFIC_PROFILES:
            raise ValueError(
                f"unknown profile '{profile}', expected one of {list(TRAFFIC_PROFILES)}"
            )
        self.nodes = np.array(sorted(nodes))
        self.profile = profile
        self.low, self.high = TRAFFIC_PROFILES[profile]
        self.rng = np.random.default_rng(seed)

    def reseed(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed)

    def _sample_pair(self) -> tuple[int, int]:
        source, destination = self.rng.choice(self.nodes, size=2, replace=False)
        return int(source), int(destination)

    def _sample_demands(self, count: int) -> np.ndarray:
        if self.profile != "dynamic":
            return self.rng.uniform(self.low, self.high, size=count)
        phase = self.rng.uniform(0.0, 2.0 * np.pi)
        t = np.arange(count) / max(count, 1)
        midpoint = (self.low + self.high) / 2.0
        amplitude = (self.high - self.low) / 3.0
        mean = midpoint + amplitude * np.sin(2.0 * np.pi * t + phase)
        noise = self.rng.normal(0.0, (self.high - self.low) / 8.0, size=count)
        return np.clip(mean + noise, self.low, self.high)

    def generate(self, count: int, seed: int | None = None) -> list[Flow]:
        if count < 1:
            raise ValueError("count must be >= 1")
        if seed is not None:
            self.reseed(seed)
        pairs = [self._sample_pair() for _ in range(count)]
        demands = self._sample_demands(count)
        return [
            Flow(source=s, destination=d, demand=float(round(demand, 6)))
            for (s, d), demand in zip(pairs, demands, strict=True)
        ]
