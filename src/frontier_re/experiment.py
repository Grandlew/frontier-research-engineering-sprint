from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
import hashlib
import json
import logging
from pathlib import Path
import platform
import random
import sys
from typing import Any

from frontier_re.baseline import (
    exact_match,
    fit_majority_label,
    make_toy_records,
    predict_split,
)
from frontier_re.config import ExperimentConfig


def seed_everything(seed: int) -> None:
    # TODO 13: Seed Python's random module. Explain in a comment why this function
    # must later expand for NumPy, PyTorch, CUDA workers and distributed ranks.
    random.seed(seed)
    # Additional libraries maintain independent random-number generators.
    # This function must expand when NumPy, PyTorch, CUDA workers, or
    # distributed ranks are introduced so every source of randomness is seed


def canonical_json_bytes(value: Any) -> bytes:
    # TODO 14: Produce canonical UTF-8 JSON bytes ending in exactly one newline.
    # Reject NaN and infinity.
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8') + b'\n'


def sha256_hex(payload: bytes) -> str:
    # TODO 15: Return a lowercase SHA-256 hexadecimal digest.
    return hashlib.sha256(payload).hexdigest()


def build_logger(log_path: Path) -> logging.Logger:
    # TODO 16: Create one console and one file handler, avoid duplicate handlers,
    # use INFO level and include timestamp, level and message.

    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("frontier_re")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Reconfigure the dedicated logger so repeated calls never accumulate
    # console or file handlers.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(
        log_path,
        mode="a",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def capture_environment() -> dict[str, str]:
    # TODO 17: Capture exact Python version, implementation and platform.
    # Do not place this information in the scientific result.
    return {

        "python_version": sys.version,
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
    }


def run_experiment(config: ExperimentConfig) -> str:
    # TODO 18: Implement the orchestration:
    # 1. create output_dir;
    # 2. initialize logging and seed state;
    # 3. construct records;
    # 4. fit the baseline from train only;
    # 5. predict test examples;
    # 6. compute exact match;
    # 7. construct scientific_payload containing scientific config,
    #    config fingerprint, baseline name/label, ordered predictions and metric;
    # 8. write canonical result.json;
    # 9. hash the exact bytes written;
    # 10. write manifest.json containing operational metadata, UTC timestamp,
    #     environment and result hash;
    # 11. log the metric/hash and return the hash.
    config.output_dir.mkdir(parents=True, exist_ok=True)

    logger = build_logger(config.output_dir / "experiment.log")
    seed_everything(config.seed)

    records = make_toy_records()
    learned_label = fit_majority_label(records)
    predictions = predict_split(
        records,
        label=learned_label,
        split="test",
    )
    accuracy = exact_match(predictions)

    scientific_payload = {
        "config": config.scientific_dict(),
        "config_fingerprint": config.fingerprint(),
        "baseline": {
            "name": fit_majority_label.__name__.removeprefix("fit_"),
            "learned_label": learned_label,
        },
        "predictions": [
            asdict(prediction) for prediction in predictions
        ],
        "metrics": {
            "exact_match": accuracy,
        },
    }

    result_bytes = canonical_json_bytes(scientific_payload)
    result_path = config.output_dir / "result.json"
    result_path.write_bytes(result_bytes)

    result_hash = sha256_hex(result_bytes)

    manifest = {
        "run_name": config.run_name,
        "output_dir": str(config.output_dir),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "environment": capture_environment(),
        "result_file": result_path.name,
        "result_sha256": result_hash,
    }

    manifest_path = config.output_dir / "manifest.json"
    manifest_path.write_bytes(canonical_json_bytes(manifest))

    logger.info("exact_match=%s", accuracy)
    logger.info("result_sha256=%s", result_hash)

    return result_hash
