"""Inventory PlantVillage classifier images and create a leakage-safe split.

This command does not train a classifier or modify source dataset files.
Run from the repository root with ``python -m scripts.create_leakage_safe_split``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import uuid
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image, ImageOps

from crop_health.classification.splits import grouped_stratified_split
from crop_health.data.plantvillage import IMAGE_SUFFIXES, ClassificationRecord, plantvillage_records


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports" / "data_manifest"
PARTITION_ORDER = ("train", "validation", "test")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_family_id(path: Path) -> str | None:
    """Return the original PlantVillage suffix only for UUID-prefixed names."""
    stem = path.stem
    if "___" not in stem:
        return None
    prefix, suffix = stem.split("___", 1)
    try:
        uuid.UUID(prefix)
    except (ValueError, AttributeError):
        return None
    suffix = suffix.strip()
    return suffix.casefold() if suffix else None


def difference_hash(path: Path) -> int:
    """Compute a 64-bit EXIF-aware difference hash using only Pillow and NumPy."""
    with Image.open(path) as source:
        source.load()
        image = ImageOps.exif_transpose(source).convert("L")
        pixels = np.asarray(image.resize((9, 8), Image.Resampling.LANCZOS), dtype=np.int16)
    bits = pixels[:, 1:] > pixels[:, :-1]
    value = 0
    for bit in bits.flat:
        value = (value << 1) | int(bit)
    return value


def inventory_record(record: ClassificationRecord) -> dict[str, Any]:
    with Image.open(record.path) as source:
        source.load()
        width, height = ImageOps.exif_transpose(source).size
    return {
        "relative_path": record.path.relative_to(ROOT).as_posix(),
        "class_id": record.class_id,
        "sha256": sha256_file(record.path),
        "filename": record.path.name,
        "filename_stem": record.path.stem,
        "source_family_id": source_family_id(record.path) or "",
        "width_exif_oriented": width,
        "height_exif_oriented": height,
        "dhash64": f"{difference_hash(record.path):016x}",
    }


class _BKTree:
    """Small BK-tree for finding 64-bit perceptual hashes within radius two."""

    def __init__(self) -> None:
        self.root: list[Any] | None = None

    @staticmethod
    def distance(left: int, right: int) -> int:
        return (left ^ right).bit_count()

    def add(self, value: int, index: int) -> None:
        if self.root is None:
            self.root = [value, [index], {}]
            return
        node = self.root
        while True:
            distance = self.distance(value, node[0])
            if distance == 0:
                node[1].append(index)
                return
            child = node[2].get(distance)
            if child is None:
                node[2][distance] = [value, [index], {}]
                return
            node = child

    def query(self, value: int, radius: int) -> list[int]:
        if self.root is None:
            return []
        found: list[int] = []
        pending = [self.root]
        while pending:
            node = pending.pop()
            distance = self.distance(value, node[0])
            if distance <= radius:
                found.extend(node[1])
            low, high = distance - radius, distance + radius
            pending.extend(child for edge, child in node[2].items() if low <= edge <= high)
        return found


def near_duplicate_pairs(rows: list[dict[str, Any]], radius: int = 2) -> list[dict[str, Any]]:
    tree = _BKTree()
    pairs: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        value = int(row["dhash64"], 16)
        for earlier in tree.query(value, radius):
            if rows[earlier]["sha256"] == row["sha256"]:
                continue
            distance = _BKTree.distance(value, int(rows[earlier]["dhash64"], 16))
            pairs.append({
                "path_a": rows[earlier]["relative_path"],
                "path_b": row["relative_path"],
                "class_a": rows[earlier]["class_id"],
                "class_b": row["class_id"],
                "sha256_a": rows[earlier]["sha256"],
                "sha256_b": row["sha256"],
                "dhash_hamming_distance": distance,
                "similarity_bits": 64 - distance,
            })
        tree.add(value, index)
    return sorted(pairs, key=lambda item: (item["dhash_hamming_distance"], item["path_a"], item["path_b"]))


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, item: int) -> int:
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, left: int, right: int) -> None:
        root_left, root_right = self.find(left), self.find(right)
        if root_left == root_right:
            return
        if self.rank[root_left] < self.rank[root_right]:
            root_left, root_right = root_right, root_left
        self.parent[root_right] = root_left
        if self.rank[root_left] == self.rank[root_right]:
            self.rank[root_left] += 1


def build_group_ids(rows: list[dict[str, Any]], near_pairs: list[dict[str, Any]]) -> list[str]:
    union_find = _UnionFind(len(rows))
    first_by_sha: dict[str, int] = {}
    first_by_source: dict[tuple[str, str], int] = {}
    index_by_path = {row["relative_path"]: index for index, row in enumerate(rows)}
    for index, row in enumerate(rows):
        if row["sha256"] in first_by_sha:
            union_find.union(index, first_by_sha[row["sha256"]])
        else:
            first_by_sha[row["sha256"]] = index
        source = row["source_family_id"]
        if source:
            key = (row["class_id"], source)
            if key in first_by_source:
                union_find.union(index, first_by_source[key])
            else:
                first_by_source[key] = index
    for pair in near_pairs:
        union_find.union(index_by_path[pair["path_a"]], index_by_path[pair["path_b"]])

    components: dict[int, list[int]] = defaultdict(list)
    for index in range(len(rows)):
        components[union_find.find(index)].append(index)
    group_ids = [""] * len(rows)
    for members in components.values():
        classes = {rows[index]["class_id"] for index in members}
        if len(classes) != 1:
            paths = [rows[index]["relative_path"] for index in members[:8]]
            raise ValueError(f"duplicate/source/near-match group spans class labels: {paths}")
        identity = "\n".join(sorted(rows[index]["relative_path"] for index in members))
        group_id = "pv-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
        for index in members:
            group_ids[index] = group_id
    return group_ids


def audit_nested_tree(nested_root: Path, selected_hashes: set[str]) -> dict[str, Any]:
    paths = sorted(path for path in nested_root.rglob("*")
                   if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)
    with ThreadPoolExecutor(max_workers=8) as pool:
        hashes = list(pool.map(sha256_file, paths))
    counts = Counter(hashes)
    shared = set(counts).intersection(selected_hashes)
    return {
        "nested_root": nested_root.relative_to(ROOT).as_posix(),
        "nested_file_count": len(paths),
        "nested_unique_hash_count": len(counts),
        "unique_hashes_shared_with_selected": len(shared),
        "nested_files_matching_selected_hashes": sum(counts[digest] for digest in shared),
    }


def verify_rows(rows: list[dict[str, Any]], group_ids: list[str],
                partitions: dict[str, list[ClassificationRecord]]) -> dict[str, Any]:
    partition_by_path: dict[str, str] = {}
    class_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for partition, records in partitions.items():
        for record in records:
            path = record.path.relative_to(ROOT).as_posix()
            if path in partition_by_path:
                raise ValueError(f"record occurs more than once in split: {path}")
            partition_by_path[path] = partition
            class_counts[record.class_id][partition] += 1
    if set(partition_by_path) != {row["relative_path"] for row in rows}:
        raise ValueError("split records do not exactly match the selected classifier inventory")

    part_by_group: dict[str, set[str]] = defaultdict(set)
    part_by_sha: dict[str, set[str]] = defaultdict(set)
    part_by_source: dict[tuple[str, str], set[str]] = defaultdict(set)
    row_by_path = {row["relative_path"]: row for row in rows}
    row_index = {row["relative_path"]: index for index, row in enumerate(rows)}
    for path, partition in partition_by_path.items():
        row = row_by_path[path]
        part_by_group[group_ids[row_index[path]]].add(partition)
        part_by_sha[row["sha256"]].add(partition)
        if row["source_family_id"]:
            part_by_source[(row["class_id"], row["source_family_id"])].add(partition)
    for name, assignments in (("group", part_by_group), ("SHA-256", part_by_sha), ("source family", part_by_source)):
        conflicts = [key for key, values in assignments.items() if len(values) > 1]
        if conflicts:
            raise ValueError(f"{name} groups cross partitions: {conflicts[:5]}")
    if any(not class_counts[label].get(partition) for label in class_counts for partition in PARTITION_ORDER):
        raise ValueError("every class must have train, validation, and test samples")
    totals = {partition: sum(len(items) for items in [partitions[partition]]) for partition in PARTITION_ORDER}
    return {
        "total_records": len(rows),
        "group_count": len(part_by_group),
        "largest_group_records": max(Counter(group_ids).values(), default=0),
        "partition_counts": totals,
        "partition_ratios": {key: totals[key] / len(rows) for key in PARTITION_ORDER},
        "class_counts": {label: {part: class_counts[label].get(part, 0) for part in PARTITION_ORDER}
                         for label in sorted(class_counts)},
        "all_records_exactly_once": True,
        "sha256_groups_partition_pure": True,
        "source_family_groups_partition_pure": True,
        "group_ids_partition_pure": True,
    }


def create_artifacts(output_dir: Path) -> dict[str, Any]:
    dataset_config = yaml.safe_load((ROOT / "configs/dataset_config.yaml").read_text(encoding="utf-8"))
    model_config = yaml.safe_load((ROOT / "configs/model_config.yaml").read_text(encoding="utf-8"))["model"]
    records = plantvillage_records(ROOT, dataset_config)
    rows = [inventory_record(record) for record in records]

    sha_groups: dict[str, list[int]] = defaultdict(list)
    source_groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        sha_groups[row["sha256"]].append(index)
        if row["source_family_id"]:
            source_groups[(row["class_id"], row["source_family_id"])].append(index)
    conflicting_hashes = [indices for indices in sha_groups.values()
                          if len({rows[index]["class_id"] for index in indices}) > 1]
    conflicting_sources = [indices for indices in source_groups.values()
                           if len({rows[index]["class_id"] for index in indices}) > 1]
    if conflicting_hashes or conflicting_sources:
        raise ValueError("an exact/source family spans configured class labels; resolve labels before splitting")

    near_pairs = near_duplicate_pairs(rows, radius=2)
    group_ids = build_group_ids(rows, near_pairs)
    labels = [record.class_id for record in records]
    partitions = grouped_stratified_split(
        records, labels, group_ids, seed=int(model_config["seed"]),
        validation_fraction=float(model_config["validation_fraction"]),
        test_fraction=float(model_config["test_fraction"]),
    )
    summary = verify_rows(rows, group_ids, partitions)
    partition_by_path = {
        record.path.relative_to(ROOT).as_posix(): partition
        for partition, split_records in partitions.items()
        for record in split_records
    }
    for index, row in enumerate(rows):
        row["group_id"] = group_ids[index]
        row["partition"] = partition_by_path[row["relative_path"]]

    nested_path = ROOT / dataset_config["datasets"]["plantvillage"]["excluded_nested_tree"]
    nested_audit = audit_nested_tree(nested_path, set(sha_groups))
    duplicate_groups = []
    for digest, indices in sorted(sha_groups.items()):
        if len(indices) <= 1:
            continue
        duplicate_groups.append({
            "sha256": digest,
            "class_ids": sorted({rows[index]["class_id"] for index in indices}),
            "partition": rows[indices[0]]["partition"],
            "paths": sorted(rows[index]["relative_path"] for index in indices),
        })
    summary.update({
        "dataset": "PlantVillage selected top-level classifier folders",
        "seed": int(model_config["seed"]),
        "target_ratios": {"train": 1 - float(model_config["validation_fraction"]) - float(model_config["test_fraction"]),
                          "validation": float(model_config["validation_fraction"]),
                          "test": float(model_config["test_fraction"])},
        "grouping_policy": "transitive connected components of exact SHA-256, UUID-prefixed PlantVillage filename suffix (within class), and 64-bit EXIF-aware dHash pairs at Hamming distance <= 2",
        "dhash_method": "Pillow EXIF transpose, grayscale, Lanczos 9x8 resize, 64 horizontal comparisons; all pairs within Hamming distance 2 are conservatively grouped",
        "near_duplicate_threshold": {"hash_bits": 64, "max_hamming_distance": 2, "candidate_pairs": len(near_pairs)},
        "selected_unique_sha256": len(sha_groups),
        "exact_duplicate_groups": len(duplicate_groups),
        "exact_duplicate_records_beyond_unique": sum(len(indices) - 1 for indices in sha_groups.values() if len(indices) > 1),
        "exact_duplicate_group_details": duplicate_groups,
        "source_family_groups_with_multiple_files": sum(len(indices) > 1 for indices in source_groups.values()),
        "source_family_id_parseable_records": sum(bool(row["source_family_id"]) for row in rows),
        "source_family_grouping_details": "source_family_id is the case-folded suffix after the first ___ only when its prefix parses as a UUID; repeated IDs are grouped within class. All selected records use this format. Repeated IDs in the inspected inventory coincide with exact-hash duplicate groups.",
        "nested_tree_audit": nested_audit,
        "manifest": "reports/data_manifest/plantvillage_classifier_split.csv",
        "inventory": "reports/data_manifest/plantvillage_classifier_inventory.csv",
        "near_duplicate_candidates": "reports/data_manifest/plantvillage_near_duplicate_candidates.csv",
    })

    output_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = output_dir / "plantvillage_classifier_inventory.csv"
    inventory_columns = ["relative_path", "class_id", "sha256", "filename", "filename_stem",
                         "source_family_id", "width_exif_oriented", "height_exif_oriented", "dhash64", "group_id"]
    with inventory_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=inventory_columns)
        writer.writeheader()
        writer.writerows({key: row[key] for key in inventory_columns} for row in rows)

    manifest_path = output_dir / "plantvillage_classifier_split.csv"
    manifest_columns = ["relative_path", "class_id", "partition", "sha256", "group_id", "source_family_id"]
    ordered_rows = sorted(rows, key=lambda row: (PARTITION_ORDER.index(row["partition"]), row["relative_path"]))
    with manifest_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=manifest_columns)
        writer.writeheader()
        writer.writerows({key: row[key] for key in manifest_columns} for row in ordered_rows)

    near_path = output_dir / "plantvillage_near_duplicate_candidates.csv"
    with near_path.open("w", newline="", encoding="utf-8") as stream:
        columns = ["path_a", "path_b", "class_a", "class_b", "sha256_a", "sha256_b",
                   "dhash_hamming_distance", "similarity_bits", "grouping_decision", "grouping_rationale"]
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows({
            **pair,
            "grouping_decision": "same_partition_group",
            "grouping_rationale": "64-bit EXIF-aware dHash distance <= 2; conservatively grouped to avoid cross-partition exposure; not asserted to be duplicate files",
        } for pair in near_pairs)

    summary["manifest_sha256"] = sha256_file(manifest_path)
    summary["inventory_sha256"] = sha256_file(inventory_path)
    summary["near_duplicate_pair_count"] = len(near_pairs)
    summary_path = output_dir / "plantvillage_split_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = create_artifacts(args.output_dir.resolve())
    print(json.dumps({key: value for key, value in summary.items()
                      if key not in {"exact_duplicate_group_details", "nested_tree_audit"}}, indent=2))
    print(json.dumps(summary["nested_tree_audit"], indent=2))


if __name__ == "__main__":
    main()
