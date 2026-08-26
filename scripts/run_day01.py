from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from frontier_re.config import ExperimentConfig
from frontier_re.experiment import run_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--run-name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ExperimentConfig.from_json(args.config)

    if args.output_dir is not None:
        config = replace(config, output_dir=args.output_dir)
    if args.run_name is not None:
        config = replace(config, run_name=args.run_name)

    print(run_experiment(config))


if __name__ == "__main__":
    main()
