"""Publication-style figures generated from persisted experiment results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes

POLICY_STYLE: dict[str, tuple[str, str]] = {
    "q_learning": ("Q-learning", "#2a78d6"),
    "shortest_path": ("Shortest path", "#eb6834"),
    "congestion_aware": ("Congestion-aware", "#1baf7a"),
    "random": ("Random", "#eda100"),
}

INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e4e3df"
SURFACE = "#fcfcfb"

COMPARISONS: tuple[tuple[str, str, str, str], ...] = (
    ("latency_comparison.png", "mean_latency_ms", "Mean end-to-end latency", "Latency (ms)"),
    (
        "throughput_comparison.png",
        "mean_throughput",
        "Mean delivered throughput per flow",
        "Throughput (Mb/s)",
    ),
    ("packet_loss_comparison.png", "plr", "Packet loss ratio", "PLR (lower is better)"),
    (
        "utilization_comparison.png",
        "avg_link_utilization",
        "Average link utilization",
        "Utilization",
    ),
)


def _style_axes(ax: Axes) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _new_figure() -> tuple[plt.Figure, Axes]:
    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    _style_axes(ax)
    return fig, ax


def _title(ax: Axes, title: str, subtitle: str) -> None:
    ax.set_title(title, loc="left", fontsize=12, color=INK_PRIMARY, pad=22, fontweight="bold")
    ax.text(0, 1.03, subtitle, transform=ax.transAxes, fontsize=9, color=INK_SECONDARY)


def plot_reward_curve(history: pd.DataFrame, out_path: Path, window: int = 50) -> Path:
    smoothed = (
        history.sort_values(["seed", "episode"])
        .groupby("seed")["total_reward"]
        .transform(lambda s: s.rolling(window, min_periods=1).mean())
    )
    frame = history.assign(smoothed=smoothed)
    stats = frame.groupby("episode")["smoothed"].agg(["mean", "std"]).fillna(0.0)
    color = POLICY_STYLE["q_learning"][1]

    fig, ax = _new_figure()
    ax.fill_between(
        stats.index,
        stats["mean"] - stats["std"],
        stats["mean"] + stats["std"],
        color=color,
        alpha=0.18,
        linewidth=0,
    )
    ax.plot(stats.index, stats["mean"], color=color, linewidth=2)
    seeds = history["seed"].nunique()
    _title(
        ax,
        "Q-learning training reward",
        f"{window}-episode rolling mean, band = ±1 std across {seeds} seeds",
    )
    ax.set_xlabel("Episode", color=INK_SECONDARY)
    ax.set_ylabel("Episode reward", color=INK_SECONDARY)
    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)
    return out_path


def plot_metric_comparison(
    summary: dict[str, Any], metric: str, title: str, ylabel: str, out_path: Path
) -> Path:
    policies = [p for p in POLICY_STYLE if p in summary["policies"]]
    means = [summary["policies"][p][metric]["mean"] for p in policies]
    stds = [summary["policies"][p][metric]["std"] for p in policies]
    labels = [POLICY_STYLE[p][0] for p in policies]
    colors = [POLICY_STYLE[p][1] for p in policies]

    fig, ax = _new_figure()
    bars = ax.bar(
        labels,
        means,
        yerr=stds,
        color=colors,
        width=0.55,
        edgecolor=SURFACE,
        linewidth=2,
        error_kw={"ecolor": INK_SECONDARY, "elinewidth": 1, "capsize": 4},
    )
    top = max(m + s for m, s in zip(means, stds, strict=True)) or 1.0
    for bar, mean, std in zip(bars, means, stds, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            mean + std + top * 0.02,
            f"{mean:.3f}" if top < 10 else f"{mean:.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=INK_PRIMARY,
        )
    ax.set_ylim(0, top * 1.15)
    seeds = len(summary.get("seeds", []))
    _title(ax, title, f"Mean ± 1 std across {seeds} seeds, held-out evaluation traffic")
    ax.set_ylabel(ylabel, color=INK_SECONDARY)
    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)
    return out_path


def plot_load_sweep(sweep: list[dict[str, Any]], out_path: Path) -> Path:
    """PDR gain of Q-learning over each baseline as relative load grows, with 95% CIs.

    Filled markers are significant (permutation p < 0.05); hollow markers are not.
    """
    loads = [entry["relative_load"] for entry in sweep]
    fig, ax = _new_figure()
    ax.axhline(0, color=INK_SECONDARY, linewidth=1)
    for baseline in ("shortest_path", "congestion_aware"):
        label, color = POLICY_STYLE[baseline]
        gain = [entry[baseline]["mean_diff"] * 100 for entry in sweep]
        low = [entry[baseline]["ci_low"] * 100 for entry in sweep]
        high = [entry[baseline]["ci_high"] * 100 for entry in sweep]
        significant = [entry[baseline]["significant"] for entry in sweep]
        ax.fill_between(loads, low, high, color=color, alpha=0.16, linewidth=0)
        ax.plot(loads, gain, color=color, linewidth=2)
        for x, y, sig in zip(loads, gain, significant, strict=True):
            ax.plot(
                x,
                y,
                "o",
                markersize=8,
                color=color,
                markerfacecolor=color if sig else SURFACE,
                markeredgewidth=2,
            )
        ax.annotate(
            f"vs {label.lower()}",
            (loads[-1], gain[-1]),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
            color=INK_PRIMARY,
        )
    seeds = sweep[0]["shortest_path"]["n"] if sweep else 0
    _title(
        ax,
        "Where learning pays off: PDR gain vs. network load",
        f"Q-learning minus baseline, mean of {seeds} paired seeds, band = 95% bootstrap CI, "
        "filled = p < 0.05",
    )
    ax.set_xlabel("Relative load (1 / capacity scale)", color=INK_SECONDARY)
    ax.set_ylabel("PDR gain (percentage points)", color=INK_SECONDARY)
    ax.set_xlim(min(loads) - 0.05, max(loads) + 0.25)
    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)
    return out_path


def generate_all_plots(results_dir: str | Path) -> list[Path]:
    results = Path(results_dir)
    summary_path = results / "summary.json"
    history_path = results / "training_history.csv"
    if not summary_path.exists() or not history_path.exists():
        raise FileNotFoundError(f"run experiments first: missing results in {results}")

    figures = results / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    history = pd.read_csv(history_path)

    paths = [plot_reward_curve(history, figures / "reward_curve.png")]
    for filename, metric, title, ylabel in COMPARISONS:
        paths.append(plot_metric_comparison(summary, metric, title, ylabel, figures / filename))
    sweep_path = results / "load_sweep.json"
    if sweep_path.exists():
        sweep = json.loads(sweep_path.read_text(encoding="utf-8"))
        paths.append(plot_load_sweep(sweep, figures / "load_sweep.png"))
    return paths
