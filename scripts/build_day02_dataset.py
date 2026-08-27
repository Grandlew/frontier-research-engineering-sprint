from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from frontier_re.data import DataConfig
from frontier_re.data_build import build_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--run-name", type=str)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = DataConfig.from_json(args.config)

    if args.output_dir is not None:
        config = replace(config, output_dir=args.output_dir)
    if args.run_name is not None:
        config = replace(config, run_name=args.run_name)

    result = build_dataset(config)
    print(f"source_sha256={result.source_sha256}")
    print(f"dataset_sha256={result.dataset_sha256}")


if __name__ == "__main__":
    main()
