import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

import pytest

from crop_health.classification.splits import grouped_stratified_split, load_grouped_manifest


@dataclass(frozen=True)
class Record:
    path: Path
    class_id: str


def test_grouped_split_is_deterministic_stratified_and_group_safe():
    records = []
    labels = []
    groups = []
    for class_id in ("tomato", "potato"):
        for group_number in range(40):
            for copy_index in range(2 if group_number < 4 else 1):
                records.append(f"{class_id}/{group_number}/{copy_index}")
                labels.append(class_id)
                groups.append(f"{class_id}-group-{group_number}")

    first = grouped_stratified_split(records, labels, groups, seed=42)
    second = grouped_stratified_split(records, labels, groups, seed=42)
    assert first == second

    partition_of = {record: partition for partition, values in first.items() for record in values}
    assert len(partition_of) == len(records)
    assert set(partition_of) == set(records)
    for group_id in set(groups):
        partitions = {partition_of[record] for record, group in zip(records, groups, strict=True)
                      if group == group_id}
        assert len(partitions) == 1
    for partition_records in first.values():
        assert {labels[records.index(record)] for record in partition_records} == {"tomato", "potato"}


def test_grouped_split_rejects_group_spanning_classes():
    with pytest.raises(ValueError, match="must not span class labels"):
        grouped_stratified_split(["a", "b", "c", "d", "e", "f"],
                                 ["tomato", "tomato", "tomato", "potato", "potato", "potato"],
                                 ["same", "t1", "t2", "same", "p1", "p2"])


def test_grouped_split_requires_three_independent_groups_per_class():
    with pytest.raises(ValueError, match="three independent groups"):
        grouped_stratified_split(["a", "b", "c"], ["tomato"] * 3, ["same"] * 3)


def test_saved_manifest_load_checks_hash_label_and_group_integrity(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    records = []
    rows = []
    for class_id in ("tomato", "potato"):
        for number, partition in enumerate(("train", "validation", "test")):
            path = root / class_id / f"{number}.jpg"
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(f"{class_id}-{number}".encode())
            record = Record(path, class_id)
            records.append(record)
            rows.append({
                "relative_path": path.relative_to(root).as_posix(),
                "class_id": class_id,
                "partition": partition,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "group_id": f"{class_id}-{number}",
                "source_family_id": "",
            })
    manifest = tmp_path / "manifest.csv"
    fields = list(rows[0])
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    loaded = load_grouped_manifest(records, manifest, root)
    assert {key: len(value) for key, value in loaded.items()} == {
        "train": 2, "validation": 2, "test": 2,
    }

    rows[1]["group_id"] = rows[0]["group_id"]
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="exact duplicate hash|group ID"):
        load_grouped_manifest(records, manifest, root)


def test_saved_manifest_rejects_hash_mismatch_or_missing_records(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    records = []
    rows = []
    for class_id in ("tomato", "potato"):
        for number, partition in enumerate(("train", "validation", "test")):
            path = root / class_id / f"{number}.jpg"
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(f"{class_id}-{number}".encode())
            records.append(Record(path, class_id))
            rows.append({
                "relative_path": path.relative_to(root).as_posix(),
                "class_id": class_id,
                "partition": partition,
                "sha256": "0" * 64,
                "group_id": f"{class_id}-{number}",
                "source_family_id": "",
            })
    manifest = tmp_path / "manifest.csv"
    fields = list(rows[0])
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="hash does not match"):
        load_grouped_manifest(records, manifest, root)


def test_manifest_can_defer_test_image_hashes_until_final_evaluation(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    records = []
    rows = []
    for class_id in ("tomato", "potato"):
        for number, partition in enumerate(("train", "validation", "test")):
            path = root / class_id / f"{number}.jpg"
            path.parent.mkdir(exist_ok=True)
            content = f"{class_id}-{number}".encode()
            path.write_bytes(content)
            records.append(Record(path, class_id))
            rows.append({
                "relative_path": path.relative_to(root).as_posix(),
                "class_id": class_id,
                "partition": partition,
                "sha256": hashlib.sha256(content).hexdigest(),
                "group_id": f"{class_id}-{number}",
                "source_family_id": "",
            })
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    original_read_bytes = Path.read_bytes
    read_paths = []
    allow_test_reads = False

    def guarded_read_bytes(path):
        if path.name == "2.jpg" and not allow_test_reads:
            raise AssertionError("test image content was read before final evaluation")
        read_paths.append(path)
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    loaded = load_grouped_manifest(records, manifest, root, verify_partitions=("train", "validation"))
    assert {key: len(value) for key, value in loaded.items()} == {
        "train": 2, "validation": 2, "test": 2,
    }
    assert all(path.name != "2.jpg" for path in read_paths)

    read_paths.clear()
    allow_test_reads = True
    loaded = load_grouped_manifest(records, manifest, root, verify_partitions=("test",))
    assert len(loaded["test"]) == 2
    assert {path.name for path in read_paths} == {"2.jpg"}
