from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from meshmind.cli import main
from meshmind.config import ExperimentConfig, TopologyConfig, config_from_dict, load_config
from meshmind.experiments import POLICY_ORDER, run_experiment_pipeline
from meshmind.plotting import generate_all_plots

ROOT = Path(__file__).resolve().parents[1]

TINY = replace(
    ExperimentConfig(),
    topology=TopologyConfig(name="small_grid"),
    seeds=(1, 2),
    train_episodes=30,
    eval_episodes=3,
)


def test_default_yaml_loads() -> None:
    config = load_config(ROOT / "configs" / "default.yaml")
    assert config.topology.name == "abilene"
    assert config.seeds == (42, 100, 2026)
    assert config.environment.max_steps == 20
    assert config.environment.invalid_action_penalty == -100.0


def test_config_rejects_unknown_keys() -> None:
    with pytest.raises(ValueError):
        config_from_dict({"agent": {"learning_rate": 0.1}})
    with pytest.raises(ValueError):
        config_from_dict({"unknown": {}})


def test_pipeline_writes_results_and_figures(tmp_path: Path) -> None:
    summary = run_experiment_pipeline(TINY, tmp_path)
    assert list(summary["policies"]) == list(POLICY_ORDER)
    pdr = summary["policies"]["q_learning"]["pdr"]
    assert set(pdr) == {"mean", "std"}

    per_seed = pd.read_csv(tmp_path / "per_seed_results.csv")
    assert len(per_seed) == len(TINY.seeds) * len(POLICY_ORDER)
    history = pd.read_csv(tmp_path / "training_history.csv")
    assert len(history) == len(TINY.seeds) * TINY.train_episodes
    assert json.loads((tmp_path / "summary.json").read_text())["seeds"] == [1, 2]

    paths = generate_all_plots(tmp_path)
    names = {p.name for p in paths}
    assert names == {
        "reward_curve.png",
        "latency_comparison.png",
        "throughput_comparison.png",
        "packet_loss_comparison.png",
        "utilization_comparison.png",
    }
    assert all(p.stat().st_size > 0 for p in paths)


def test_plot_without_results_fails(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        generate_all_plots(tmp_path)


def test_cli_smoke_test(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["smoke-test"]) == 0
    assert "SMOKE TEST PASSED" in capsys.readouterr().out


def test_cli_train_then_evaluate(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("topology: {name: small_grid}\nexperiment: {eval_episodes: 2}\n")
    q_path = tmp_path / "q.json"
    assert (
        main(["train", "--config", str(config_path), "--episodes", "20", "--output", str(q_path)])
        == 0
    )
    assert q_path.exists()
    assert main(["evaluate", "--config", str(config_path), "--q-table", str(q_path)]) == 0
    out = capsys.readouterr().out
    assert "q_learning" in out and "shortest_path" in out


def test_cli_reports_missing_results(tmp_path: Path) -> None:
    assert main(["plot", "--results-dir", str(tmp_path)]) == 1
