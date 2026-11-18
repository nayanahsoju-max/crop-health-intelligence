"""Seeded, stratified train/validation/test partitioning."""

from __future__ import annotations

import random
import csv
import hashlib
import uuid
from collections import defaultdict
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


def stratified_split(records: list[T], labels: list[str], seed: int = 42,
                     validation_fraction: float = 0.15,
                     test_fraction: float = 0.15) -> dict[str, list[T]]:
    if len(records) != len(labels):
        raise ValueError("records and labels must have the same length")
    if not 0 < validation_fraction < 1 or not 0 < test_fraction < 1 or validation_fraction + test_fraction >= 1:
        raise ValueError("validation and test fractions must be positive and sum to less than one")
    groups: dict[str, list[T]] = defaultdict(list)
    for record, label in zip(records, labels, strict=True):
        groups[label].append(record)
    result: dict[str, list[T]] = {"train": [], "validation": [], "test": []}
    for class_index, label in enumerate(sorted(groups)):
        group = list(groups[label])
        if len(group) < 3:
            raise ValueError(f"class {label!r} needs at least three records for three-way stratification")
        random.Random(seed + class_index).shuffle(group)
        n_test = max(1, round(len(group) * test_fraction))
        n_validation = max(1, round(len(group) * validation_fraction))
        if n_test + n_validation >= len(group):
            raise ValueError(f"class {label!r} is too small for the requested split fractions")
        result["test"].extend(group[:n_test])
        result["validation"].extend(group[n_test:n_test + n_validation])
        result["train"].extend(group[n_test + n_validation:])
    return result


def grouped_stratified_split(
    records: list[T],
    labels: list[str],
    group_ids: list[str],
    seed: int = 42,
    validation_fraction: float = 0.15,
    test_fraction: float = 0.15,
) -> dict[str, list[T]]:
    """Split records deterministically while keeping each group in one partition.

    Groups must be class-pure. Per-class groups are assigned with a seeded,
    largest-first greedy objective that minimizes normalized deviation from
    the requested per-class partition sizes. Group integrity takes priority
    over exact ratios.
    """
    if len(records) != len(labels) or len(records) != len(group_ids):
        raise ValueError("records, labels, and group_ids must have the same length")
    if not 0 < validation_fraction < 1 or not 0 < test_fraction < 1 or validation_fraction + test_fraction >= 1:
        raise ValueError("validation and test fractions must be positive and sum to less than one")

    members_by_group: dict[str, list[tuple[T, str]]] = defaultdict(list)
    labels_by_group: dict[str, set[str]] = defaultdict(set)
    for record, label, group_id in zip(records, labels, group_ids, strict=True):
        if not group_id:
            raise ValueError("group IDs must be non-empty")
        members_by_group[group_id].append((record, label))
        labels_by_group[group_id].add(label)
    mixed = [group_id for group_id, group_labels in labels_by_group.items() if len(group_labels) != 1]
    if mixed:
        raise ValueError(f"groups must not span class labels: {mixed[:5]}")

    by_class: dict[str, list[tuple[str, list[T]]]] = defaultdict(list)
    for group_id, members in members_by_group.items():
        by_class[members[0][1]].append((group_id, [record for record, _ in members]))

    result: dict[str, list[T]] = {"train": [], "validation": [], "test": []}
    ratios = {"train": 1 - validation_fraction - test_fraction,
              "validation": validation_fraction, "test": test_fraction}
    split_names = tuple(result)

    for class_index, label in enumerate(sorted(by_class)):
        rng = random.Random(seed + class_index)
        groups = list(by_class[label])
        rng.shuffle(groups)
        groups.sort(key=lambda item: len(item[1]), reverse=True)
        class_total = sum(len(members) for _, members in groups)
        if len(groups) < len(split_names):
            raise ValueError(f"class {label!r} needs at least three independent groups for three-way splitting")
        targets = {name: class_total * ratio for name, ratio in ratios.items()}
        counts = {name: 0 for name in split_names}
        assignments: dict[str, str] = {}
        tie_order = list(split_names)
        rng.shuffle(tie_order)

        for index, (group_id, members) in enumerate(groups):
            size = len(members)
            missing = [name for name in split_names if counts[name] == 0]
            remaining = len(groups) - index
            candidates = missing if remaining <= len(missing) else list(split_names)

            def cost(partition: str) -> float:
                total_cost = 0.0
                for name in split_names:
                    after = counts[name] + (size if name == partition else 0)
                    target = targets[name]
                    total_cost += ((after - target) ** 2 - (counts[name] - target) ** 2) / max(target, 1.0)
                return total_cost

            chosen = min(candidates, key=lambda name: (cost(name), tie_order.index(name)))
            assignments[group_id] = chosen
            counts[chosen] += size
            result[chosen].extend(members)

    return result


def load_grouped_manifest(
    records: list[T], manifest_path: str | Path, project_root: str | Path,
    *, verify_partitions: tuple[str, ...] = ("train", "validation", "test"),
) -> dict[str, list[T]]:
    """Load a grouped split, hashing image contents only in selected partitions.

    Training passes ``("train", "validation")`` so test contents are deferred
    to the separately invoked final evaluator. Other callers retain the
    historical all-partition integrity check by default.
    """
    invalid_partitions = set(verify_partitions) - {"train", "validation", "test"}
    if invalid_partitions:
        raise ValueError(f"invalid partitions requested for integrity checks: {sorted(invalid_partitions)}")
    root = Path(project_root).resolve()
    by_relative_path: dict[str, T] = {}
    record_classes: dict[str, str] = {}
    for record in records:
        path = Path(getattr(record, "path")).resolve()
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError as error:
            raise ValueError(f"classifier record is outside project root: {path}") from error
        if relative in by_relative_path:
            raise ValueError(f"duplicate classifier record path: {relative}")
        by_relative_path[relative] = record
        record_classes[relative] = str(getattr(record, "class_id"))

    partitions: dict[str, list[T]] = {"train": [], "validation": [], "test": []}
    seen: set[str] = set()
    group_partitions: dict[str, set[str]] = defaultdict(set)
    hash_partitions: dict[str, set[str]] = defaultdict(set)
    source_partitions: dict[tuple[str, str], set[str]] = defaultdict(set)
    rows_to_verify: list[tuple[Path, str, str]] = []
    with Path(manifest_path).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"relative_path", "class_id", "partition", "sha256", "group_id", "source_family_id"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("split manifest is missing required leakage-safety columns")
        for row in reader:
            relative = row["relative_path"]
            if relative not in by_relative_path:
                raise ValueError(f"manifest contains an unknown classifier record: {relative}")
            if relative in seen:
                raise ValueError(f"manifest contains a record more than once: {relative}")
            seen.add(relative)
            if row["class_id"] != record_classes[relative]:
                raise ValueError(f"manifest label does not match current record: {relative}")
            partition = row["partition"]
            if partition not in partitions:
                raise ValueError(f"manifest has an invalid partition for {relative}: {partition}")
            record_path = Path(getattr(by_relative_path[relative], "path"))
            if partition in verify_partitions:
                rows_to_verify.append((record_path, row["sha256"], relative))
            stem = record_path.stem
            expected_source = ""
            if "___" in stem:
                prefix, suffix = stem.split("___", 1)
                try:
                    uuid.UUID(prefix)
                except ValueError:
                    pass
                else:
                    expected_source = suffix.strip().casefold()
            if row["source_family_id"] != expected_source:
                raise ValueError(f"manifest source-family ID does not match current filename: {relative}")
            if not row["group_id"]:
                raise ValueError(f"manifest group ID is empty: {relative}")
            partitions[partition].append(by_relative_path[relative])
            group_partitions[row["group_id"]].add(partition)
            hash_partitions[row["sha256"]].add(partition)
            if row["source_family_id"]:
                source_partitions[(row["class_id"], row["source_family_id"])].add(partition)
    if seen != set(by_relative_path):
        missing = sorted(set(by_relative_path) - seen)
        raise ValueError(f"manifest omits classifier records: {missing[:5]}")
    for record_path, expected_digest, relative in rows_to_verify:
        digest = hashlib.sha256(record_path.read_bytes()).hexdigest()
        if digest != expected_digest:
            raise ValueError(f"manifest image hash does not match current file: {relative}")
    if any(len(values) > 1 for values in group_partitions.values()):
        raise ValueError("manifest places a group ID in multiple partitions")
    if any(len(values) > 1 for values in hash_partitions.values()):
        raise ValueError("manifest places an exact duplicate hash in multiple partitions")
    if any(len(values) > 1 for values in source_partitions.values()):
        raise ValueError("manifest places a source family in multiple partitions")
    class_partitions: dict[str, set[str]] = defaultdict(set)
    for partition, partition_records in partitions.items():
        for record in partition_records:
            class_partitions[str(getattr(record, "class_id"))].add(partition)
    if any(set(partitions) - class_partitions[label] for label in class_partitions):
        raise ValueError("every classifier class must occur in all three manifest partitions")
    return partitions
