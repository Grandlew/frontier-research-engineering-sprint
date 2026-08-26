import json
from pathlib import Path

from frontier_re.config import ExperimentConfig
from frontier_re.experiment import run_experiment


def test_two_runs_are_scientifically_identical(tmp_path: Path) -> None:
    first = ExperimentConfig(
        seed=1729,
        dataset_version="day01-toy-v1",
        output_dir=tmp_path / "first",
        run_name="first",
    )
    second = ExperimentConfig(
        seed=1729,
        dataset_version="day01-toy-v1",
        output_dir=tmp_path / "second",
        run_name="second",
    )

    first_hash = run_experiment(first)
    second_hash = run_experiment(second)

    # TODO 20: Assert equal returned hashes, byte-identical result.json files,
    # existing manifest/log files, different run names in the manifests, and
    # absence of timestamps/output paths/run names from result.json.
    assert first_hash == second_hash

    first_result_path = first.output_dir / "result.json"
    second_result_path = second.output_dir / "result.json"
    first_result_bytes = first_result_path.read_bytes()
    second_result_bytes = second_result_path.read_bytes()
    assert first_result_bytes == second_result_bytes

    first_manifest_path = first.output_dir / "manifest.json"
    second_manifest_path = second.output_dir / "manifest.json"
    first_log_path = first.output_dir / "experiment.log"
    second_log_path = second.output_dir / "experiment.log"
    assert first_manifest_path.is_file()
    assert second_manifest_path.is_file()
    assert first_log_path.is_file()
    assert second_log_path.is_file()

    first_manifest = json.loads(
        first_manifest_path.read_text(encoding="utf-8"))
    second_manifest = json.loads(
        second_manifest_path.read_text(encoding="utf-8"))
    assert first_manifest["run_name"] == "first"
    assert second_manifest["run_name"] == "second"

    scientific_result = json.loads(first_result_bytes)
    operational_keys = {"created_at_utc", "output_dir", "run_name"}

    def collect_keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value) | {
                key
                for child in value.values()
                for key in collect_keys(child)
            }
        if isinstance(value, list):
            return {
                key
                for child in value
                for key in collect_keys(child)
            }
        return set()

    assert operational_keys.isdisjoint(collect_keys(scientific_result))
