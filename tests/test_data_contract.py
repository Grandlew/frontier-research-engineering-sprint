from dataclasses import replace
from pathlib import Path

import pytest

from frontier_re.data import (
    DataConfig,
    DatasetExample,
    RawExample,
    assert_group_isolation,
    assert_prompt_group_consistency,
    assert_unique_example_ids,
)


def test_day02_data_contracts(tmp_path: Path) -> None:
    # TODO 19: Prove all of the following:
    # - Boolean, negative and 2**32 seeds fail;
    # - invalid fractions fail;
    # - empty RawExample fields fail;
    # - duplicated IDs fail;
    # - one group placed in two splits fails;
    # - identical normalized prompts assigned to different groups fail;
    # - errors identify the offending ID or group.
    config = DataConfig(
        dataset_name="day02-test",
        schema_version="1.0.0",
        split_seed=1729,
        train_fraction=0.7,
        validation_fraction=0.15,
        raw_csv=tmp_path / "raw.csv",
        output_dir=tmp_path / "output",
        run_name="test-run",
    )

    for invalid_seed in (True, -1, 2**32):
        with pytest.raises((TypeError, ValueError)):
            replace(config, split_seed=invalid_seed)

    invalid_fractions = (
        (0.0, 0.15),
        (1.0, 0.15),
        (0.7, 0.0),
        (0.7, 1.0),
        (-0.1, 0.15),
        (0.7, -0.1),
        (0.8, 0.2),
    )
    for train_fraction, validation_fraction in invalid_fractions:
        with pytest.raises((TypeError, ValueError)):
            replace(
                config,
                train_fraction=train_fraction,
                validation_fraction=validation_fraction,
            )

    valid_fields = {
        "example_id": "example-one",
        "group_id": "group-one",
        "prompt": "Prompt",
        "target": "Target",
    }
    for field in valid_fields:
        invalid_fields = valid_fields | {field: " \t\n"}
        with pytest.raises((TypeError, ValueError), match=field):
            RawExample(**invalid_fields)

    duplicated = (
        RawExample("duplicate-id", "group-one", "First", "A"),
        RawExample("duplicate-id", "group-two", "Second", "B"),
    )
    with pytest.raises(ValueError) as duplicate_error:
        assert_unique_example_ids(duplicated)
    assert "duplicate-id" in str(duplicate_error.value)

    leaking_group = (
        DatasetExample("example-one", "leaking-group", "First", "A", "train"),
        DatasetExample(
            "example-two",
            "leaking-group",
            "Second",
            "B",
            "validation",
        ),
    )
    with pytest.raises(ValueError) as isolation_error:
        assert_group_isolation(leaking_group)
    assert "leaking-group" in str(isolation_error.value)

    inconsistent_prompts = (
        RawExample("example-one", "group-one", "Ａ  Shared Prompt", "A"),
        RawExample("example-two", "group-two", "a\tshared prompt", "B"),
    )
    with pytest.raises(ValueError) as prompt_error:
        assert_prompt_group_consistency(inconsistent_prompts)
    prompt_message = str(prompt_error.value)
    assert "group-one" in prompt_message
    assert "group-two" in prompt_message
