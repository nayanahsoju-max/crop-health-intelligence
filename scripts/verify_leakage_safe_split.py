"""Independently validate the saved PlantVillage inventory and split manifest."""

from __future__ import annotations

import csv
import hashlib
import json
import uuid
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from crop_health.data.plantvillage import plantvillage_records
from crop_health.classification.splits import load_grouped_manifest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "reports" / "data_manifest"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def expected_source_family(path: Path) -> str:
    stem = path.stem
    if "___" not in stem:
        return ""
    prefix, suffix = stem.split("___", 1)
    try:
        uuid.UUID(prefix)
    except ValueError:
        return ""
    return suffix.strip().casefold()


def main() -> None:
    config = yaml.safe_load((ROOT / "configs/dataset_config.yaml").read_text(encoding="utf-8"))
    records = plantvillage_records(ROOT, config)
    expected = {record.path.relative_to(ROOT).as_posix(): record for record in records}
    inventory_path = MANIFEST_DIR / "plantvillage_classifier_inventory.csv"
    manifest_path = MANIFEST_DIR / "plantvillage_classifier_split.csv"
    summary_path = MANIFEST_DIR / "plantvillage_split_summary.json"
    with inventory_path.open(encoding="utf-8", newline="") as stream:
        inventory = {row["relative_path"]: row for row in csv.DictReader(stream)}
    with manifest_path.open(encoding="utf-8", newline="") as stream:
        manifest_rows = list(csv.DictReader(stream))
    near_path = MANIFEST_DIR / "plantvillage_near_duplicate_candidates.csv"
    with near_path.open(encoding="utf-8", newline="") as stream:
        near_pairs = list(csv.DictReader(stream))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    if set(inventory) != set(expected) or len(inventory) != len(records):
        raise SystemExit("FAIL: inventory does not contain every selected record exactly once")
    if len(manifest_rows) != len(records):
        raise SystemExit("FAIL: manifest record count differs from selected records")
    if digest(inventory_path) != summary["inventory_sha256"]:
        raise SystemExit("FAIL: inventory checksum differs from summary")
    if digest(manifest_path) != summary["manifest_sha256"]:
        raise SystemExit("FAIL: manifest checksum differs from summary")

    training_partitions = load_grouped_manifest(records, manifest_path, ROOT)
    loaded_paths = {
        record.path.relative_to(ROOT).as_posix()
        for partition_records in training_partitions.values()
        for record in partition_records
    }
    if loaded_paths != set(expected):
        raise SystemExit("FAIL: training loader does not reconstruct the saved manifest")

    partition_by_path: dict[str, str] = {}
    group_by_path: dict[str, str] = {}
    group_parts: dict[str, set[str]] = defaultdict(set)
    hash_parts: dict[str, set[str]] = defaultdict(set)
    source_parts: dict[tuple[str, str], set[str]] = defaultdict(set)
    group_by_hash: dict[str, set[str]] = defaultdict(set)
    group_by_source: dict[tuple[str, str], set[str]] = defaultdict(set)
    class_counts: dict[str, Counter] = defaultdict(Counter)
    for row in manifest_rows:
        path = row["relative_path"]
        if path not in expected or path in partition_by_path:
            raise SystemExit(f"FAIL: unknown or duplicated manifest path: {path}")
        if path.startswith("data/PlantVillage/PlantVillage/"):
            raise SystemExit(f"FAIL: excluded nested tree appears in manifest: {path}")
        record = expected[path]
        if row["class_id"] != record.class_id or inventory[path]["class_id"] != record.class_id:
            raise SystemExit(f"FAIL: class mapping mismatch: {path}")
        actual_hash = digest(record.path)
        if row["sha256"] != actual_hash or inventory[path]["sha256"] != actual_hash:
            raise SystemExit(f"FAIL: stale or incorrect SHA-256: {path}")
        if row["source_family_id"] != expected_source_family(record.path):
            raise SystemExit(f"FAIL: source-family ID mismatch: {path}")
        partition = row["partition"]
        if partition not in {"train", "validation", "test"}:
            raise SystemExit(f"FAIL: invalid partition {partition!r}: {path}")
        if not row["group_id"] or inventory[path].get("group_id") != row["group_id"]:
            raise SystemExit(f"FAIL: inventory/manifest group mismatch: {path}")
        partition_by_path[path] = partition
        group_by_path[path] = row["group_id"]
        group_parts[row["group_id"]].add(partition)
        hash_parts[actual_hash].add(partition)
        group_by_hash[actual_hash].add(row["group_id"])
        if row["source_family_id"]:
            source_key = (row["class_id"], row["source_family_id"])
            source_parts[source_key].add(partition)
            group_by_source[source_key].add(row["group_id"])
        class_counts[row["class_id"]][partition] += 1

    if set(partition_by_path) != set(expected):
        raise SystemExit("FAIL: manifest does not cover every selected record")
    for label, groups in (("group ID", group_parts), ("SHA-256", hash_parts), ("source family", source_parts)):
        conflicts = [key for key, partitions in groups.items() if len(partitions) > 1]
        if conflicts:
            raise SystemExit(f"FAIL: {label} crosses partitions: {conflicts[:5]}")
    if any(len(ids) != 1 for ids in group_by_hash.values()):
        raise SystemExit("FAIL: an exact SHA-256 duplicate group has multiple group IDs")
    if any(len(ids) != 1 for ids in group_by_source.values()):
        raise SystemExit("FAIL: a source family has multiple group IDs")
    for pair in near_pairs:
        if (pair["path_a"] not in group_by_path or pair["path_b"] not in group_by_path
                or group_by_path[pair["path_a"]] != group_by_path[pair["path_b"]]):
            raise SystemExit(f"FAIL: near-match candidate is split across groups: {pair}")
        if int(pair["dhash_hamming_distance"]) > 2:
            raise SystemExit(f"FAIL: near-match candidate exceeds configured threshold: {pair}")
    all_labels = set(config["class_selection"]["classes"][i]["id"]
                     for i in range(len(config["class_selection"]["classes"])))
    for class_id in all_labels:
        if any(class_counts[class_id][part] == 0 for part in ("train", "validation", "test")):
            raise SystemExit(f"FAIL: class {class_id} is missing from a partition")

    print(f"PASS: {len(records)} selected records occur exactly once; nested tree excluded.")
    print("PASS: classifier training manifest loader reconstructs the same selected path set.")
    print(f"PASS: {len(hash_parts)} unique SHA-256 hashes; exact hashes, family IDs, and group IDs are partition-pure.")
    print(f"PASS: {len(near_pairs)} perceptual near-match candidates are grouped together (distance <= 2/64).")
    print("Class counts:")
    for class_id in sorted(all_labels):
        print(f"  {class_id}: {dict(class_counts[class_id])}")
    print("Partition totals:", dict(Counter(partition_by_path.values())))


if __name__ == "__main__":
    main()
