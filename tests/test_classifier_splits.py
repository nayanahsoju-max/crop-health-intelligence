import pytest

from crop_health.classification.splits import stratified_split


def test_split_is_reproducible_stratified_and_disjoint():
    records = [f"{class_id}_{index}" for class_id in ("tomato", "potato") for index in range(40)]
    labels = [record.split("_")[0] for record in records]

    first = stratified_split(records, labels, seed=13)
    second = stratified_split(records, labels, seed=13)

    assert first == second
    assert not set(first["train"]).intersection(first["validation"])
    assert not set(first["train"]).intersection(first["test"])
    assert not set(first["validation"]).intersection(first["test"])
    for split_records in first.values():
        assert {record.split("_")[0] for record in split_records} == {"tomato", "potato"}


def test_split_rejects_too_small_class():
    with pytest.raises(ValueError, match="at least three"):
        stratified_split(["a", "b", "c"], ["single", "single", "other"])
