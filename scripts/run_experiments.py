"""Run the full multi-seed benchmark and regenerate every figure."""

from __future__ import annotations

import argparse
import sys

from meshmind.cli import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()
    sys.exit(main(["experiments", "--config", args.config, "--results-dir", args.results_dir]))
