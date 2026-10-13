"""Multi-seed benchmark: Q-learning vs. baselines, with persisted results."""

from __future__ import annotations

import json
from dataclasses import dataclass
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
from meshmind.topology import NetworkTopology
from meshmind.traffic import TrafficGenerator
from meshmind.training import train_agent

POLICY_ORDER: tuple[str, ...] = ("q_learning", "shortest_path", "congestion_aware", "random")


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
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


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
