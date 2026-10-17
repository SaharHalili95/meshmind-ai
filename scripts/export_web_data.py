"""Export benchmark results from results/ into web/src/data/results.json for the website."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

CURVE_STEP = 10
WINDOW = 50


def build_payload(results_dir: Path) -> dict:
    summary = json.loads((results_dir / "summary.json").read_text(encoding="utf-8"))
    per_seed = pd.read_csv(results_dir / "per_seed_results.csv")
    history = pd.read_csv(results_dir / "training_history.csv").sort_values(["seed", "episode"])

    history["smoothed"] = history.groupby("seed")["total_reward"].transform(
        lambda s: s.rolling(WINDOW, min_periods=1).mean()
    )
    curve = history.groupby("episode")["smoothed"].agg(["mean", "std"]).fillna(0.0)
    curve = curve.iloc[::CURVE_STEP]

    sweep_path = results_dir / "load_sweep.json"
    sweep = json.loads(sweep_path.read_text(encoding="utf-8")) if sweep_path.exists() else []

    return {
        "config": summary["config"],
        "seeds": summary["seeds"],
        "policies": summary["policies"],
        "comparisons": summary.get("comparisons", []),
        "loadSweep": sweep,
        "perSeed": per_seed.round(6).to_dict("records"),
        "rewardCurve": {
            "window": WINDOW,
            "episode": [int(e) for e in curve.index],
            "mean": [round(float(v), 3) for v in curve["mean"]],
            "std": [round(float(v), 3) for v in curve["std"]],
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--output", default="web/src/data/results.json")
    args = parser.parse_args()
    payload = build_payload(Path(args.results_dir))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
