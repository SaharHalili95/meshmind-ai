"""Flow-level performance accounting and cross-seed aggregation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np

METRIC_KEYS: tuple[str, ...] = (
    "pdr",
    "plr",
    "mean_latency_ms",
    "mean_throughput",
    "avg_link_utilization",
    "routing_failures",
    "mean_hops",
)


@dataclass(frozen=True)
class FlowResult:
    source: int
    destination: int
    offered_demand: float
    delivered_demand: float
    latency_ms: float
    hops: int
    success: bool
    failure_reason: str | None = None
    path: tuple[int, ...] = field(default_factory=tuple)


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator > 0 else 0.0


class MetricsTracker:
    """Accumulates flow outcomes and link-utilization samples.

    PDR = delivered demand / offered demand and PLR = 1 - PDR. A failed flow
    (invalid action, loop, step cap) delivers nothing. Latency and hop count
    average over successful flows only; throughput averages delivered demand
    over all offered flows.
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.flows: list[FlowResult] = []
        self.utilization_samples: list[float] = []

    def record_flow(self, result: FlowResult) -> None:
        if result.offered_demand < 0 or result.delivered_demand < 0:
            raise ValueError("demands must be non-negative")
        if result.delivered_demand > result.offered_demand + 1e-9:
            raise ValueError("delivered demand cannot exceed offered demand")
        self.flows.append(result)

    def record_utilization(self, value: float) -> None:
        if value < 0:
            raise ValueError("utilization must be non-negative")
        self.utilization_samples.append(float(value))

    @property
    def offered_demand(self) -> float:
        return sum(f.offered_demand for f in self.flows)

    @property
    def delivered_demand(self) -> float:
        return sum(f.delivered_demand for f in self.flows)

    @property
    def pdr(self) -> float:
        return _safe_ratio(self.delivered_demand, self.offered_demand)

    @property
    def plr(self) -> float:
        if self.offered_demand <= 0:
            return 0.0
        return 1.0 - self.pdr

    @property
    def routing_failures(self) -> int:
        return sum(1 for f in self.flows if not f.success)

    @property
    def mean_latency_ms(self) -> float:
        latencies = [f.latency_ms for f in self.flows if f.success]
        return _safe_ratio(sum(latencies), len(latencies))

    @property
    def mean_hops(self) -> float:
        hops = [f.hops for f in self.flows if f.success]
        return _safe_ratio(sum(hops), len(hops))

    @property
    def mean_throughput(self) -> float:
        return _safe_ratio(self.delivered_demand, len(self.flows))

    @property
    def avg_link_utilization(self) -> float:
        return _safe_ratio(sum(self.utilization_samples), len(self.utilization_samples))

    def failure_breakdown(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for flow in self.flows:
            if not flow.success and flow.failure_reason is not None:
                counts[flow.failure_reason] = counts.get(flow.failure_reason, 0) + 1
        return counts

    def summary(self) -> dict[str, float]:
        return {
            "pdr": self.pdr,
            "plr": self.plr,
            "mean_latency_ms": self.mean_latency_ms,
            "mean_throughput": self.mean_throughput,
            "avg_link_utilization": self.avg_link_utilization,
            "routing_failures": float(self.routing_failures),
            "mean_hops": self.mean_hops,
            "flows": float(len(self.flows)),
            "offered_demand": self.offered_demand,
            "delivered_demand": self.delivered_demand,
        }


def aggregate_metrics(
    runs: Sequence[Mapping[str, float]], keys: Sequence[str] = METRIC_KEYS
) -> dict[str, dict[str, float]]:
    """Mean and sample standard deviation (ddof=1) of each metric across runs."""
    if not runs:
        raise ValueError("cannot aggregate an empty list of runs")
    aggregated: dict[str, dict[str, float]] = {}
    for key in keys:
        values = np.array([float(run[key]) for run in runs])
        std = float(values.std(ddof=1)) if len(values) > 1 else 0.0
        aggregated[key] = {"mean": float(values.mean()), "std": std}
    return aggregated
