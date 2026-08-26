from dataclasses import replace
from pathlib import Path

import pytest

from frontier_re.config import ExperimentConfig


def test_configuration_contract(tmp_path: Path) -> None:
    config = ExperimentConfig(
        seed=1729,
        dataset_version="day01-toy-v1",
        output_dir=tmp_path / "a",
        run_name="a",
    )
    # TODO 19: Add assertions proving:
    # - operational-field changes preserve the fingerprint;
    # - a seed change changes the fingerprint;
    # - negative, boolean and 2**32 seeds raise ValueError or TypeError;
    # - canonical bytes are unchanged across repeated calls.

    operational_change = replace(
        config,
        output_dir=tmp_path / "b",
        run_name="b",
    )
    assert operational_change.fingerprint() == config.fingerprint()

    seed_change = replace(config, seed=config.seed + 1)
    assert seed_change.fingerprint() != config.fingerprint()

    for invalid_seed in (-1, True, 2**32):
        with pytest.raises((ValueError, TypeError)):
            replace(config, seed=invalid_seed)

    canonical = config.canonical_bytes()
    assert config.canonical_bytes() == canonical
