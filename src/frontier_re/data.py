from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import unicodedata
from typing import Any, Literal, Sequence, Self


Split = Literal["train", "validation", "test"]


@dataclass(frozen=True, slots=True)
class DataConfig:
    dataset_name: str
    schema_version: str
    split_seed: int
    train_fraction: float
    validation_fraction: float
    raw_csv: Path
    output_dir: Path
    run_name: str

    def __post_init__(self) -> None:
        # TODO 01: Reject Boolean/non-integer seeds and values outside [0, 2**32).
        if (
            isinstance(self.split_seed, bool)
            or not isinstance(self.split_seed, int)
            or not (0 <= self.split_seed < 2**32)
        ):
            raise ValueError(
                f"Invalid seed: {self.split_seed}." "Must be an integer in [0, 2**32)"
            )

        # TODO 02: Require non-empty dataset_name, schema_version and run_name.
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.dataset_name, self.schema_version, self.run_name)
        ):
            raise ValueError(
                "Invalid configuration: dataset_name, schema_version, and "
                "run_name must be non-empty."
            )

        # TODO 03: Require 0 < train_fraction < 1,
        # 0 < validation_fraction < 1 and their sum < 1.
        if not (
            0 < self.train_fraction < 1
            and 0 < self.validation_fraction < 1
            and self.train_fraction + self.validation_fraction < 1
        ):
            raise ValueError(
                "Invalid configuration: train_fraction and validation_fraction "
                "must be in (0, 1) and their sum must be < 1."
            )

    def scientific_dict(self) -> dict[str, Any]:
        # TODO 04: Return dataset name, schema version, seed and fractions.
        # Exclude paths and run_name. Add a fingerprint method using canonical
        # compact JSON and SHA-256.
        return {
            "dataset_name": self.dataset_name,
            "schema_version": self.schema_version,
            "split_seed": self.split_seed,
            "train_fraction": self.train_fraction,
            "validation_fraction": self.validation_fraction,
        }

    def fingerprint(self) -> str:
        canonical = json.dumps(
            self.scientific_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    @classmethod
    def from_json(cls, path: Path) -> Self:
        # TODO 05: Load an exact-key JSON object, reject missing/unknown keys,
        # convert both path fields and construct the validated object.
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Configuration must be a JSON object.")

        required_keys = {
            "dataset_name",
            "schema_version",
            "split_seed",
            "train_fraction",
            "validation_fraction",
            "raw_csv",
            "output_dir",
            "run_name",
        }
        actual_keys = set(data)
        missing = required_keys - actual_keys
        unknown = actual_keys - required_keys
        if missing or unknown:
            raise ValueError(
                "Invalid configuration keys: "
                f"missing={sorted(missing)}, unknown={sorted(unknown)}"
            )

        return cls(
            dataset_name=data["dataset_name"],
            schema_version=data["schema_version"],
            split_seed=data["split_seed"],
            train_fraction=data["train_fraction"],
            validation_fraction=data["validation_fraction"],
            raw_csv=Path(data["raw_csv"]),
            output_dir=Path(data["output_dir"]),
            run_name=data["run_name"],
        )


@dataclass(frozen=True, slots=True)
class RawExample:
    example_id: str
    group_id: str
    prompt: str
    target: str

    def __post_init__(self) -> None:
        # TODO 06: Require every field to be a non-empty string after stripping.
        for field in ("example_id", "group_id", "prompt", "target"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Field '{field}' must be a non-empty string.")


@dataclass(frozen=True, slots=True)
class DatasetExample:
    example_id: str
    group_id: str
    prompt: str
    target: str
    split: Split


def normalize_text(value: str) -> str:
    # TODO 07: Apply Unicode NFKC normalization, collapse whitespace and casefold.
    value = unicodedata.normalize("NFKC", value)
    value = " ".join(value.split())
    return value.casefold()


def load_raw_examples(path: Path) -> tuple[RawExample, ...]:
    # TODO 08: Use csv.DictReader with newline=""; require the exact four-column
    # schema; reject an empty file and construct immutable RawExample objects.
    if not path.exists():
        raise FileNotFoundError(f"Raw examples file not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"Empty CSV file: {path}")
        required_columns = ["example_id", "group_id", "prompt", "target"]
        if reader.fieldnames != required_columns:
            raise ValueError(
                "CSV columns do not match required schema. "
                f"Expected {required_columns}, got {reader.fieldnames}"
            )
        examples = []
        for row in reader:
            examples.append(RawExample(**row))
    if not examples:
        raise ValueError(f"Empty CSV file after reading headers: {path}")
    return tuple(examples)


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    # TODO 09: Stream the file in chunks into hashlib.sha256.
    # Reject chunk_size <= 0.
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def split_score(group_id: str, seed: int) -> float:
    # TODO 10: Hash f"{seed}:{group_id}", interpret the first eight bytes as an
    # unsigned big-endian integer and divide by 2**64. Assert 0 <= score < 1.
    h = hashlib.sha256()
    h.update(f"{seed}:{group_id}".encode("utf-8"))
    score = int.from_bytes(h.digest()[:8], byteorder="big") / 2**64
    assert 0 <= score < 1, f"Score {score} is not in [0, 1)"
    return score


def assign_split(group_id: str, config: DataConfig) -> Split:
    # TODO 11: Map split_score through the two configured thresholds.
    score = split_score(group_id, config.split_seed)
    if score < config.train_fraction:
        return "train"
    if score < config.train_fraction + config.validation_fraction:
        return "validation"
    return "test"


def attach_splits(
    examples: Sequence[RawExample],
    config: DataConfig,
) -> tuple[DatasetExample, ...]:
    # TODO 12: Assign splits by group_id and return records sorted by example_id.
    records = []
    for example in examples:
        split = assign_split(example.group_id, config)
        records.append(
            DatasetExample(
                example_id=example.example_id,
                group_id=example.group_id,
                prompt=example.prompt,
                target=example.target,
                split=split,
            )
        )
    return tuple(sorted(records, key=lambda record: record.example_id))


def assert_unique_example_ids(examples: Sequence[RawExample]) -> None:
    # TODO 13: Raise ValueError containing every duplicated example_id.
    seen: set[str] = set()
    duplicates: set[str] = set()
    for example in examples:
        if example.example_id in seen:
            duplicates.add(example.example_id)
        seen.add(example.example_id)
    if duplicates:
        raise ValueError(f"Duplicate example_ids found: {sorted(duplicates)}")


def assert_group_isolation(records: Sequence[DatasetExample]) -> None:
    # TODO 14: Build group_id -> set[split] and reject groups in multiple splits.
    group_splits: dict[str, set[Split]] = {}
    for record in records:
        group_id = record.group_id
        split = record.split
        if group_id not in group_splits:
            group_splits[group_id] = set()
        group_splits[group_id].add(split)
    for group_id, splits in group_splits.items():
        if len(splits) > 1:
            raise ValueError(
                f"Group {group_id} is present in multiple splits: {sorted(splits)}"
            )


def assert_prompt_group_consistency(
    examples: Sequence[RawExample],
) -> None:
    # TODO 15: Map normalized prompts to group IDs and reject any normalized
    # prompt assigned to more than one group.
    prompt_groups: dict[str, set[str]] = {}
    for example in examples:
        normalized_prompt = normalize_text(example.prompt)
        prompt_groups.setdefault(
            normalized_prompt, set()).add(example.group_id)
    for normalized_prompt, groups in prompt_groups.items():
        if len(groups) > 1:
            raise ValueError(
                f"Normalized prompt '{normalized_prompt}' is assigned to "
                f"multiple groups: {sorted(groups)}"
            )


def canonical_dataset_bytes(
    records: Sequence[DatasetExample],
) -> bytes:
    # TODO 16: Sort by example_id and encode one canonical compact JSON object
    # per line. Output must end in exactly one newline.
    sorted_records = sorted(records, key=lambda record: record.example_id)
    json_lines = "\n".join(
        json.dumps(
            asdict(record),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        for record in sorted_records
    )
    return (json_lines + "\n").encode("utf-8")


def dataset_digest(records: Sequence[DatasetExample]) -> str:
    # TODO 17: Hash canonical_dataset_bytes with SHA-256.
    return hashlib.sha256(canonical_dataset_bytes(records)).hexdigest()
