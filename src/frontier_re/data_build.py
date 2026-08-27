from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from frontier_re.data import (
    DataConfig,
    assert_group_isolation,
    assert_prompt_group_consistency,
    assert_unique_example_ids,
    attach_splits,
    canonical_dataset_bytes,
    dataset_digest,
    load_raw_examples,
    sha256_file,
)
from frontier_re.experiment import (
    canonical_json_bytes,
    capture_environment,
)


@dataclass(frozen=True, slots=True)
class DatasetBuildResult:
    source_sha256: str
    dataset_sha256: str
    output_dir: Path


def build_dataset(config: DataConfig) -> DatasetBuildResult:
    # TODO 18: Implement this order:
    # 1. hash the exact source file;
    # 2. load and validate raw examples;
    # 3. audit unique IDs and normalized-prompt grouping;
    # 4. attach deterministic group-aware splits;
    # 5. assert group isolation;
    # 6. write canonical dataset.jsonl;
    # 7. compute record and unique-group counts per split;
    # 8. compute a digest for each split;
    # 9. write deterministic data_manifest.json containing configuration,
    #    fingerprints, source/dataset hashes and split statistics;
    # 10. write operational build_manifest.json containing run name,
    #     output directory, UTC creation time and environment;
    # 11. return DatasetBuildResult.
    source_sha256 = sha256_file(config.raw_csv)

    examples = load_raw_examples(config.raw_csv)
    assert_unique_example_ids(examples)
    assert_prompt_group_consistency(examples)

    records = attach_splits(examples, config)
    assert_group_isolation(records)

    config.output_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = config.output_dir / "dataset.jsonl"
    dataset_bytes = canonical_dataset_bytes(records)
    dataset_path.write_bytes(dataset_bytes)
    dataset_sha256 = dataset_digest(records)

    split_names = ("train", "validation", "test")
    record_counts = Counter(record.split for record in records)
    unique_groups = {
        split: {
            record.group_id
            for record in records
            if record.split == split
        }
        for split in split_names
    }
    split_digests = {
        split: dataset_digest(
            tuple(record for record in records if record.split == split)
        )
        for split in split_names
    }
    split_statistics = {
        split: {
            "record_count": record_counts[split],
            "unique_group_count": len(unique_groups[split]),
            "sha256": split_digests[split],
        }
        for split in split_names
    }

    data_manifest = {
        "config": config.scientific_dict(),
        "config_fingerprint": config.fingerprint(),
        "source_sha256": source_sha256,
        "dataset_sha256": dataset_sha256,
        "split_statistics": split_statistics,
    }
    data_manifest_path = config.output_dir / "data_manifest.json"
    data_manifest_path.write_bytes(canonical_json_bytes(data_manifest))

    build_manifest = {
        "run_name": config.run_name,
        "output_dir": str(config.output_dir),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "environment": capture_environment(),
    }
    build_manifest_path = config.output_dir / "build_manifest.json"
    build_manifest_path.write_bytes(canonical_json_bytes(build_manifest))

    return DatasetBuildResult(
        source_sha256=source_sha256,
        dataset_sha256=dataset_sha256,
        output_dir=config.output_dir,
    )
