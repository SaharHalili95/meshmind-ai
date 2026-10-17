"""Multi-seed benchmark: Q-learning vs. baselines, with persisted results."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pandas as pd

from meshmind import __version__
from meshmind.agent import QLearningAgent
from meshmind.baselines import CongestionAwareBaseline, RandomRoutingBaseline, ShortestPathBaseline
from meshmind.config import ExperimentConfig
from meshmind.environment import NetworkEnvironment
from meshmind.evaluation import RoutingPolicy, evaluate_agent, evaluate_policy
from meshmind.metrics import METRIC_KEYS, aggregate_metrics
from meshmind.stats import compare_paired
from meshmind.topology import NetworkTopology
from meshmind.traffic import TrafficGenerator
from meshmind.training import train_agent

POLICY_ORDER: tuple[str, ...] = ("q_learning", "shortest_path", "congestion_aware", "random")

COMPARED_METRICS: tuple[tuple[str, bool], ...] = (
    ("pdr", True),
    ("mean_latency_ms", False),
    ("avg_link_utilization", False),
)
"""(metric, higher_is_better) pairs tested for Q-learning against every baseline."""

DEFAULT_SWEEP_SCALES: tuple[float, ...] = (1.5, 1.25, 1.0, 0.85, 0.7)


@dataclass(frozen=True)
class SeedRun:
    seed: int
    agent: QLearningAgent
    history: list[dict[str, float]]
    metrics: dict[str, dict[str, float]]


def build_environment(config: ExperimentConfig, seed: int) -> NetworkEnvironment:
    topology = NetworkTopology.from_name(
        config.topology.name,
        capacity_scale=config.topology.capacity_scale,
        max_utilization=config.topology.max_utilization,
    )
    traffic = TrafficGenerator(topology.nodes, config.traffic.profile, seed=seed)
    return NetworkEnvironment(
        topology, traffic, config.traffic.flows_per_episode, config=config.environment
    )


def build_baselines(seed: int) -> list[RoutingPolicy]:
    return [ShortestPathBaseline(), CongestionAwareBaseline(), RandomRoutingBaseline(seed)]


def run_seed(config: ExperimentConfig, seed: int) -> SeedRun:
    env = build_environment(config, seed)
    agent = QLearningAgent(config.agent, seed=seed)
    history = train_agent(env, agent, config.train_episodes, base_seed=seed)

    metrics = {agent.name: evaluate_agent(env, agent, config.eval_episodes, base_seed=seed)}
    for baseline in build_baselines(seed):
        metrics[baseline.name] = evaluate_policy(
            env, baseline, config.eval_episodes, base_seed=seed
        )
    return SeedRun(seed=seed, agent=agent, history=history, metrics=metrics)


def run_experiment_pipeline(
    config: ExperimentConfig, results_dir: str | Path | None = None, verbose: bool = False
) -> dict[str, Any]:
    """Train/evaluate on every seed, aggregate mean ± std, and write result files.

    Writes ``summary.json``, ``per_seed_results.csv`` and ``training_history.csv``.
    """
    out_dir = Path(results_dir or config.results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    per_seed_rows: list[dict[str, Any]] = []
    history_rows: list[dict[str, Any]] = []
    for seed in config.seeds:
        if verbose:
            print(f"[seed {seed}] training {config.train_episodes} episodes ...", flush=True)
        run = run_seed(config, seed)
        run.agent.save(out_dir / f"q_table_seed{seed}.json")
        for policy, metrics in run.metrics.items():
            per_seed_rows.append({"seed": seed, "policy": policy, **metrics})
        history_rows.extend({"seed": seed, **row} for row in run.history)

    per_seed = pd.DataFrame(per_seed_rows)
    history = pd.DataFrame(history_rows)
    per_seed.to_csv(out_dir / "per_seed_results.csv", index=False)
    history.to_csv(out_dir / "training_history.csv", index=False)

    policies = {
        policy: aggregate_metrics(
            per_seed[per_seed["policy"] == policy].to_dict("records"), METRIC_KEYS
        )
        for policy in POLICY_ORDER
    }
    summary = {
        "meshmind_version": __version__,
        "config": config.to_dict(),
        "seeds": list(config.seeds),
        "aggregation": "mean and sample std (ddof=1) across seeds",
        "policies": policies,
        "comparisons": paired_comparisons(per_seed),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def paired_comparisons(per_seed: pd.DataFrame) -> list[dict[str, Any]]:
    """Q-learning minus each baseline, seed by seed: mean, 95% bootstrap CI, permutation p."""
    table = per_seed.pivot(index="seed", columns="policy")
    results = []
    for baseline in POLICY_ORDER[1:]:
        for metric, higher_is_better in COMPARED_METRICS:
            comparison = compare_paired(
                table[(metric, "q_learning")].tolist(),
                table[(metric, baseline)].tolist(),
                metric=metric,
                baseline_name=baseline,
                higher_is_better=higher_is_better,
            )
            results.append(comparison.to_dict())
    return results


def run_load_sweep(
    config: ExperimentConfig,
    scales: Sequence[float] = DEFAULT_SWEEP_SCALES,
    results_dir: str | Path | None = None,
    verbose: bool = False,
) -> pd.DataFrame:
    """Repeat the benchmark while scaling every link capacity, and write load_sweep.csv.

    A smaller capacity scale means the same traffic meets a smaller network, i.e. a
    higher relative load (reported as ``relative_load = 1 / capacity_scale``).
    """
    if not scales:
        raise ValueError("at least one capacity scale is required")
    out_dir = Path(results_dir or config.results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for scale in scales:
        scaled = replace(config, topology=replace(config.topology, capacity_scale=scale))
        for seed in config.seeds:
            if verbose:
                print(f"[capacity x{scale}] seed {seed} ...", flush=True)
            run = run_seed(scaled, seed)
            for policy, metrics in run.metrics.items():
                rows.append(
                    {
                        "capacity_scale": scale,
                        "relative_load": round(1.0 / scale, 4),
                        "seed": seed,
                        "policy": policy,
                        **metrics,
                    }
                )
    frame = pd.DataFrame(rows)
    frame.to_csv(out_dir / "load_sweep.csv", index=False)
    return frame


def summarize_load_sweep(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Per load level: Q-learning's paired PDR gain over each baseline, with CI and p."""
    out = []
    for load, group in frame.groupby("relative_load", sort=True):
        table = group.pivot(index="seed", columns="policy", values="pdr")
        entry: dict[str, Any] = {"relative_load": float(load)}
        for baseline in ("shortest_path", "congestion_aware"):
            comparison = compare_paired(
                table["q_learning"].tolist(), table[baseline].tolist(), "pdr", baseline
            )
            entry[baseline] = comparison.to_dict()
        entry["pdr"] = {p: float(table[p].mean()) for p in POLICY_ORDER}
        out.append(entry)
    return out


def format_summary_table(summary: dict[str, Any]) -> str:
    columns = [
        ("pdr", "PDR", 3),
        ("plr", "PLR", 3),
        ("mean_latency_ms", "Latency ms", 2),
        ("mean_throughput", "Throughput", 2),
        ("avg_link_utilization", "Link util", 3),
        ("routing_failures", "Failures", 1),
    ]
    header = f"{'Policy':<18}" + "".join(f"{label:>20}" for _, label, _ in columns)
    lines = [header, "-" * len(header)]
    for policy, metrics in summary["policies"].items():
        cells = ""
        for key, _, digits in columns:
            mean, std = metrics[key]["mean"], metrics[key]["std"]
            text = f"{mean:.{digits}f}"
            if len(summary.get("seeds", [])) > 1:
                text += f" ± {std:.{digits}f}"
            cells += text.rjust(20)
        lines.append(f"{policy:<18}{cells}")
    return "\n".join(lines)


def format_comparisons(summary: dict[str, Any]) -> str:
    """One line per test: Q-learning minus baseline, 95% CI, permutation p-value, wins."""
    lines = ["Q-learning vs baseline (paired by seed, 95% bootstrap CI, permutation p)"]
    for c in summary.get("comparisons", []):
        scale = 100 if c["metric"] in ("pdr", "avg_link_utilization") else 1
        unit = " pts" if scale == 100 else " ms"
        lines.append(
            f"  {c['metric']:<21} vs {c['baseline']:<17} "
            f"{c['mean_diff'] * scale:+7.2f}{unit} "
            f"[{c['ci_low'] * scale:+.2f}, {c['ci_high'] * scale:+.2f}]  "
            f"p={c['p_value']:.3f}  wins {c['wins']}/{c['n']}"
        )
    return "\n".join(lines)
