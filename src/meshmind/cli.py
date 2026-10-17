"""Command-line interface: ``python -m meshmind.cli <command>``."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pandas as pd

from meshmind.agent import QLearningAgent
from meshmind.config import ExperimentConfig, TopologyConfig, load_config
from meshmind.evaluation import evaluate_agent, evaluate_policy
from meshmind.experiments import (
    DEFAULT_SWEEP_SCALES,
    build_baselines,
    build_environment,
    format_comparisons,
    format_summary_table,
    run_experiment_pipeline,
    run_load_sweep,
    run_seed,
    summarize_load_sweep,
)
from meshmind.metrics import aggregate_metrics
from meshmind.plotting import generate_all_plots
from meshmind.training import train_agent

DEFAULT_CONFIG = Path("configs/default.yaml")


def _load(path: str | None) -> ExperimentConfig:
    if path is not None:
        return load_config(path)
    if DEFAULT_CONFIG.exists():
        return load_config(DEFAULT_CONFIG)
    return ExperimentConfig()


def _single_seed_summary(seed: int, metrics: dict[str, dict[str, float]]) -> dict:
    return {
        "seeds": [seed],
        "policies": {name: aggregate_metrics([m]) for name, m in metrics.items()},
    }


def cmd_smoke_test(args: argparse.Namespace) -> int:
    config = replace(
        ExperimentConfig(),
        topology=TopologyConfig(name="small_grid"),
        seeds=(args.seed,),
        train_episodes=200,
        eval_episodes=10,
    )
    run = run_seed(config, args.seed)
    print(f"Smoke test on small_grid, seed {args.seed}: 200 train / 10 eval episodes")
    print(format_summary_table(_single_seed_summary(args.seed, run.metrics)))
    first, last = run.history[0]["total_reward"], run.history[-1]["total_reward"]
    print(f"\nreward: first episode {first:.1f} -> last episode {last:.1f}")
    print("SMOKE TEST PASSED")
    return 0


def cmd_train(args: argparse.Namespace) -> int:
    config = _load(args.config)
    episodes = args.episodes or config.train_episodes
    env = build_environment(config, args.seed)
    agent = QLearningAgent(config.agent, seed=args.seed)
    history = train_agent(env, agent, episodes, base_seed=args.seed)
    output = Path(args.output)
    agent.save(output)
    history_path = output.with_name(output.stem + "_history.csv")
    pd.DataFrame(history).to_csv(history_path, index=False)
    last = history[-1]
    print(f"Trained {episodes} episodes on {config.topology.name} ({config.traffic.profile})")
    print(
        f"final reward {last['total_reward']:.1f}, epsilon {agent.epsilon:.3f}, "
        f"|Q| = {len(agent.q_table)}"
    )
    print(f"saved Q-table -> {output}\nsaved history -> {history_path}")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    config = _load(args.config)
    episodes = args.episodes or config.eval_episodes
    env = build_environment(config, args.seed)
    agent = QLearningAgent.load(args.q_table, seed=args.seed)
    metrics = {agent.name: evaluate_agent(env, agent, episodes, base_seed=args.seed)}
    for baseline in build_baselines(args.seed):
        metrics[baseline.name] = evaluate_policy(env, baseline, episodes, base_seed=args.seed)
    print(f"Evaluation on {episodes} held-out episodes, seed {args.seed}")
    print(format_summary_table(_single_seed_summary(args.seed, metrics)))
    return 0


def cmd_experiments(args: argparse.Namespace) -> int:
    config = _load(args.config)
    results_dir = Path(args.results_dir or config.results_dir)
    summary = run_experiment_pipeline(config, results_dir, verbose=True)
    print()
    print(format_summary_table(summary))
    print()
    print(format_comparisons(summary))
    print(f"\nresults written to {results_dir}/")
    if not args.no_plots:
        for path in generate_all_plots(results_dir):
            print(f"figure -> {path}")
    return 0


def cmd_sweep(args: argparse.Namespace) -> int:
    config = _load(args.config)
    results_dir = Path(args.results_dir or config.results_dir)
    scales = tuple(args.scales) if args.scales else DEFAULT_SWEEP_SCALES
    frame = run_load_sweep(config, scales, results_dir, verbose=True)
    sweep = summarize_load_sweep(frame)
    (results_dir / "load_sweep.json").write_text(json.dumps(sweep, indent=2), encoding="utf-8")
    print(f"\n{'Load':>6}  {'vs shortest path':>26}  {'vs congestion-aware':>26}")
    for entry in sweep:
        cells = []
        for baseline in ("shortest_path", "congestion_aware"):
            c = entry[baseline]
            cells.append(f"{c['mean_diff'] * 100:+.2f} pts (p={c['p_value']:.3f})".rjust(26))
        print(f"{entry['relative_load']:>6.2f}  {cells[0]}  {cells[1]}")
    print(f"\nresults written to {results_dir}/load_sweep.csv and load_sweep.json")
    if not args.no_plots:
        for path in generate_all_plots(results_dir):
            print(f"figure -> {path}")
    return 0


def cmd_plot(args: argparse.Namespace) -> int:
    for path in generate_all_plots(args.results_dir):
        print(f"figure -> {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="meshmind", description="MeshMind AI: Q-learning for adaptive network routing"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    smoke = sub.add_parser("smoke-test", help="fast end-to-end sanity run (no files written)")
    smoke.add_argument("--seed", type=int, default=42)
    smoke.set_defaults(func=cmd_smoke_test)

    train = sub.add_parser("train", help="train a single agent and save its Q-table")
    train.add_argument("--config", default=None)
    train.add_argument("--seed", type=int, default=42)
    train.add_argument("--episodes", type=int, default=None)
    train.add_argument("--output", default="results/q_table.json")
    train.set_defaults(func=cmd_train)

    evaluate = sub.add_parser("evaluate", help="evaluate a saved Q-table against baselines")
    evaluate.add_argument("--config", default=None)
    evaluate.add_argument("--q-table", default="results/q_table.json")
    evaluate.add_argument("--seed", type=int, default=42)
    evaluate.add_argument("--episodes", type=int, default=None)
    evaluate.set_defaults(func=cmd_evaluate)

    experiments = sub.add_parser("experiments", help="full multi-seed benchmark")
    experiments.add_argument("--config", default=None)
    experiments.add_argument("--results-dir", default=None)
    experiments.add_argument("--no-plots", action="store_true")
    experiments.set_defaults(func=cmd_experiments)

    sweep = sub.add_parser("sweep", help="benchmark across network load levels")
    sweep.add_argument("--config", default=None)
    sweep.add_argument("--results-dir", default=None)
    sweep.add_argument("--scales", type=float, nargs="+", default=None)
    sweep.add_argument("--no-plots", action="store_true")
    sweep.set_defaults(func=cmd_sweep)

    plot = sub.add_parser("plot", help="regenerate figures from saved results")
    plot.add_argument("--results-dir", default="results")
    plot.set_defaults(func=cmd_plot)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
