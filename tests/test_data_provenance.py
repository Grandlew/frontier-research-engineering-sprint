import csv
from dataclasses import replace
from pathlib import Path
import random
from frontier_re.data import (
    DataConfig,
    DatasetExample,
    RawExample,
    attach_splits,
    dataset_digest,
    sha256_file,
)
def test_dataset_digest_is_directly_order_invariant() -> None:
    records = (
        DatasetExample(
            example_id="r002",
            group_id="g02",
            prompt="Second prompt",
            target="2",
            split="test",
        ),
        DatasetExample(
            example_id="r001",
            group_id="g01",
            prompt="First prompt",
            target="1",
            split="train",
        ),
    )

    reversed_records = tuple(reversed(records))

    # TODO: The digest function itself must remove incidental record ordering.
    assert dataset_digest(records) == dataset_digest(reversed_records)

def test_logical_identity_and_semantic_sensitivity(
    tmp_path: Path,
) -> None:
    # TODO 20: Build original, reversed and seed-1729-shuffled collections.
    # Assert:
    # - every collection receives identical group-aware split assignments;
    # - all three logical dataset digests match;
    # - raw CSV files with different row orders have different file hashes;
    # - changing exactly one target changes the logical dataset digest;
    # - no group occurs in more than one split.
    config = DataConfig(
        dataset_name="day02-provenance-test",
        schema_version="1.0.0",
        split_seed=1729,
        train_fraction=0.7,
        validation_fraction=0.15,
        raw_csv=tmp_path / "original.csv",
        output_dir=tmp_path / "output",
        run_name="provenance-test",
    )
    original = (
        RawExample("example-01", "group-a", "Prompt one", "A"),
        RawExample("example-02", "group-a", "Prompt two", "B"),
        RawExample("example-03", "group-b", "Prompt three", "C"),
        RawExample("example-04", "group-c", "Prompt four", "D"),
        RawExample("example-05", "group-c", "Prompt five", "E"),
        RawExample("example-06", "group-d", "Prompt six", "F"),
    )
    reversed_examples = tuple(reversed(original))
    shuffled_examples = list(original)
    random.Random(1729).shuffle(shuffled_examples)
    shuffled = tuple(shuffled_examples)
    collections = (original, reversed_examples, shuffled)

    attached_collections = tuple(
        attach_splits(examples, config) for examples in collections
    )
    assignments = tuple(
        {record.example_id: record.split for record in records}
        for records in attached_collections
    )
    assert assignments[0] == assignments[1] == assignments[2]

    digests = tuple(dataset_digest(records)
                    for records in attached_collections)
    assert digests[0] == digests[1] == digests[2]

    def write_raw_csv(path: Path, examples: tuple[RawExample, ...]) -> None:
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(("example_id", "group_id", "prompt", "target"))
            writer.writerows(
                (example.example_id, example.group_id,
                 example.prompt, example.target)
                for example in examples
            )

    csv_paths = tuple(
        tmp_path / filename
        for filename in ("original.csv", "reversed.csv", "shuffled.csv")
    )
    for path, examples in zip(csv_paths, collections, strict=True):
        write_raw_csv(path, examples)
    assert len({sha256_file(path) for path in csv_paths}) == len(csv_paths)

    target_changed = (
        replace(original[0], target="changed-target"),
        *original[1:],
    )
    changed_digest = dataset_digest(attach_splits(target_changed, config))
    assert changed_digest != digests[0]

    for records in attached_collections:
        group_splits: dict[str, set[str]] = {}
        for record in records:
            group_splits.setdefault(record.group_id, set()).add(record.split)
        assert all(len(splits) == 1 for splits in group_splits.values())
