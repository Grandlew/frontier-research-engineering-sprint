from frontier_re.baseline import Record, fit_majority_label


def test_majority_fit_does_not_use_nontraining_targets() -> None:
    records = (
        Record("t1", "train-one", "A", "train"),
        Record("t2", "train-two", "A", "train"),
        Record("v1", "validation-one", "Z", "validation"),
        Record("v2", "validation-two", "Z", "validation"),
        Record("e1", "test-one", "Z", "test"),
        Record("e2", "test-two", "Z", "test"),
        Record("e3", "test-three", "Z", "test"),
    )

    assert fit_majority_label(records) == "A"
