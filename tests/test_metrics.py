from __future__ import annotations

import pytest

from meshmind.metrics import FlowResult, MetricsTracker, aggregate_metrics


def flow(offered: float, delivered: float, latency: float, hops: int, ok: bool) -> FlowResult:
    return FlowResult(
        source=0,
        destination=1,
        offered_demand=offered,
        delivered_demand=delivered,
        latency_ms=latency,
        hops=hops,
        success=ok,
        failure_reason=None if ok else "loop",
    )


def test_pdr_and_plr() -> None:
    tracker = MetricsTracker()
    tracker.record_flow(flow(100.0, 80.0, 10.0, 2, True))
    tracker.record_flow(flow(50.0, 0.0, 4.0, 1, False))
    assert tracker.pdr == pytest.approx(80.0 / 150.0)
    assert tracker.plr == pytest.approx(1.0 - 80.0 / 150.0)
    assert tracker.pdr + tracker.plr == pytest.approx(1.0)


def test_zero_offered_traffic_does_not_divide_by_zero() -> None:
    tracker = MetricsTracker()
    summary = tracker.summary()
    assert summary["pdr"] == 0.0
    assert summary["plr"] == 0.0
    assert summary["mean_latency_ms"] == 0.0
    assert summary["mean_throughput"] == 0.0
    assert summary["avg_link_utilization"] == 0.0
    assert summary["mean_hops"] == 0.0


def test_zero_demand_flows_are_safe() -> None:
    tracker = MetricsTracker()
    tracker.record_flow(flow(0.0, 0.0, 1.0, 1, True))
    assert tracker.pdr == 0.0
    assert tracker.plr == 0.0


def test_latency_and_hops_average_successful_flows_only() -> None:
    tracker = MetricsTracker()
    tracker.record_flow(flow(10.0, 10.0, 10.0, 2, True))
    tracker.record_flow(flow(10.0, 10.0, 20.0, 4, True))
    tracker.record_flow(flow(10.0, 0.0, 999.0, 9, False))
    assert tracker.mean_latency_ms == pytest.approx(15.0)
    assert tracker.mean_hops == pytest.approx(3.0)
    assert tracker.mean_throughput == pytest.approx(20.0 / 3.0)
    assert tracker.routing_failures == 1
    assert tracker.failure_breakdown() == {"loop": 1}


def test_utilization_samples_are_averaged() -> None:
    tracker = MetricsTracker()
    for value in (0.2, 0.4, 0.9):
        tracker.record_utilization(value)
    assert tracker.avg_link_utilization == pytest.approx(0.5)
    with pytest.raises(ValueError):
        tracker.record_utilization(-0.1)


def test_rejects_inconsistent_flows() -> None:
    tracker = MetricsTracker()
    with pytest.raises(ValueError):
        tracker.record_flow(flow(10.0, 11.0, 1.0, 1, True))
    with pytest.raises(ValueError):
        tracker.record_flow(flow(-1.0, 0.0, 1.0, 1, False))


def test_reset_clears_state() -> None:
    tracker = MetricsTracker()
    tracker.record_flow(flow(10.0, 10.0, 1.0, 1, True))
    tracker.record_utilization(0.3)
    tracker.reset()
    assert tracker.flows == [] and tracker.utilization_samples == []


def test_aggregate_metrics_mean_and_sample_std() -> None:
    runs = [{"pdr": 0.8}, {"pdr": 0.9}, {"pdr": 1.0}]
    result = aggregate_metrics(runs, keys=["pdr"])
    assert result["pdr"]["mean"] == pytest.approx(0.9)
    assert result["pdr"]["std"] == pytest.approx(0.1)


def test_aggregate_single_run_has_zero_std() -> None:
    assert aggregate_metrics([{"pdr": 0.5}], keys=["pdr"])["pdr"] == {"mean": 0.5, "std": 0.0}


def test_aggregate_empty_raises() -> None:
    with pytest.raises(ValueError):
        aggregate_metrics([])
