from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from meshmind.cli import main
from meshmind.config import ExperimentConfig, TopologyConfig, config_from_dict, load_config
from meshmind.experiments import (
    POLICY_ORDER,
    format_comparisons,
    run_experiment_pipeline,
    run_load_sweep,
    summarize_load_sweep,
)
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
    assert config.seeds == (42, 100, 2026, 7, 13, 21, 314, 777, 1234, 9001)
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

    comparisons = summary["comparisons"]
    assert len(comparisons) == 9
    first = comparisons[0]
    assert first["metric"] == "pdr" and first["baseline"] == "shortest_path"
    assert first["ci_low"] <= first["mean_diff"] <= first["ci_high"]
    assert 0.0 < first["p_value"] <= 1.0
    assert "p=" in format_comparisons(summary)

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


def test_load_sweep_writes_rows_and_figure(tmp_path: Path) -> None:
    frame = run_load_sweep(TINY, scales=(1.5, 0.7), results_dir=tmp_path)
    assert len(frame) == 2 * len(TINY.seeds) * len(POLICY_ORDER)
    assert sorted(frame["relative_load"].unique()) == [round(1 / 1.5, 4), round(1 / 0.7, 4)]
    assert (tmp_path / "load_sweep.csv").exists()

    sweep = summarize_load_sweep(frame)
    assert [entry["relative_load"] for entry in sweep] == sorted(e["relative_load"] for e in sweep)
    assert set(sweep[0]) == {"relative_load", "shortest_path", "congestion_aware", "pdr"}
    # Less capacity for the same traffic can only lower shortest-path delivery.
    assert sweep[-1]["pdr"]["shortest_path"] < sweep[0]["pdr"]["shortest_path"]

    run_experiment_pipeline(TINY, tmp_path)
    (tmp_path / "load_sweep.json").write_text(json.dumps(sweep))
    assert "load_sweep.png" in {p.name for p in generate_all_plots(tmp_path)}


def test_load_sweep_needs_scales(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        run_load_sweep(TINY, scales=(), results_dir=tmp_path)
