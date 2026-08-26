from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Literal, Sequence


Split = Literal["train", "validation", "test"]


@dataclass(frozen=True, slots=True)
class Record:
    example_id: str
    prompt: str
    target: str
    split: Split

    def __post_init__(self) -> None:
        # TODO 08: Validate non-empty ID/prompt/target and one of the three splits.
        if not self.example_id or self.example_id.isspace():
            raise ValueError("example_id cannot be empty or whitespace-only")
        if not self.prompt or self.prompt.isspace():
            raise ValueError("prompt cannot be empty or whitespace-only")
        if not self.target or self.target.isspace():
            raise ValueError("target cannot be empty or whitespace-only")
        if self.split not in {"train", "validation", "test"}:
            raise ValueError(f"Invalid split: {self.split}")


@dataclass(frozen=True, slots=True)
class Prediction:
    example_id: str
    target: str
    prediction: str


def make_toy_records() -> tuple[Record, ...]:
    # TODO 09: Return these records in a deliberately non-sorted ID order:
    # train: ("t2", "2-0", "2"), ("t1", "1+1", "2"), ("t3", "2+2", "4")
    # validation: ("v1", "3+3", "6")
    # test: ("e2", "4+4", "8"), ("e1", "3-1", "2")
    return (
        Record(example_id="t2", prompt="2-0", target="2", split="train"),
        Record(example_id="t1", prompt="1+1", target="2", split="train"),
        Record(example_id="t3", prompt="2+2", target="4", split="train"),
        Record(example_id="v1", prompt="3+3", target="6", split="validation"),
        Record(example_id="e2", prompt="4+4", target="8", split="test"),
        Record(example_id="e1", prompt="3-1", target="2", split="test"),
    )


def fit_majority_label(records: Sequence[Record]) -> str:
    # TODO 10: Fit using train targets only. Reject an empty training split.
    # Resolve count ties by choosing the lexicographically smallest label.
    train_targets = [
        record.target for record in records if record.split == "train"]
    if not train_targets:
        raise ValueError("No training records found.")
    target_counts = Counter(train_targets)
    max_count = max(target_counts.values())
    return min(label for label, count in target_counts.items() if count == max_count)


def predict_split(
    records: Sequence[Record],
    label: str,
    split: Split = "test",
) -> tuple[Prediction, ...]:
    # TODO 11: Predict only the requested split and return results sorted by ID.
    predictions = [
        Prediction(example_id=record.example_id,
                   target=record.target, prediction=label)
        for record in records if record.split == split
    ]
    return tuple(sorted(predictions, key=lambda p: p.example_id))


def exact_match(predictions: Sequence[Prediction]) -> float:
    # TODO 12: Reject an empty sequence and compute mean exact-match accuracy.
    if not predictions:
        raise ValueError("No predictions found.")
    correct = sum(1 for p in predictions if p.target == p.prediction)
    return correct / len(predictions)
