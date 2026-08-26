from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Self


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    seed: int
    dataset_version: str
    output_dir: Path
    run_name: str

    def __post_init__(self) -> None:
        # TODO 02: Reject booleans/non-integers and seeds outside [0, 2**32).
        if (
            isinstance(self.seed, bool)
            or not isinstance(self.seed, int)
            or not (0 <= self.seed < 2**32)
        ):
            raise ValueError(
                f"Invalid seed: {self.seed}." "Must be an integer in [0, 2**32)"
            )
        # TODO 03: Reject empty or whitespace-only dataset_version and run_name.
        if not self.dataset_version or self.dataset_version.isspace():
            raise ValueError(
                "dataset_version cannot be empty or whitespace-only")
        if not self.run_name or self.run_name.isspace():
            raise ValueError("run_name cannot be empty or whitespace-only")

    def scientific_dict(self) -> dict[str, Any]:
        # TODO 04: Return only fields that can change the scientific result.
        return {
            "seed": self.seed,
            "dataset_version": self.dataset_version
        }

    def canonical_bytes(self) -> bytes:
        # TODO 05: Serialize scientific_dict with sorted keys, compact separators,
        # UTF-8 and allow_nan=False.
        return json.dumps(self.scientific_dict(), sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')

    def fingerprint(self) -> str:
        # TODO 06: Return the SHA-256 hexadecimal digest of canonical_bytes().
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    @classmethod
    def from_json(cls, path: Path) -> Self:
        # TODO 07: Load JSON, reject missing/unknown keys, convert output_dir to
        # Path and construct the validated configuration.
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Configuration must be a JSON object.")
        expected_keys = {"seed", "dataset_version", "output_dir", "run_name"}
        actual_keys = set(data)
        missing = expected_keys - actual_keys
        unknown = actual_keys - expected_keys

        if missing or unknown:
            raise ValueError(
                f"Invalid configuration keys:"
                f"missing = {sorted(missing)}, unknown = {sorted(unknown)}"

            )

        return cls(
            seed=data["seed"],
            dataset_version=data['dataset_version'],
            output_dir=Path(data["output_dir"]),
            run_name=data["run_name"]
        )
