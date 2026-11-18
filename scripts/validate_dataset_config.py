"""Confirm that the proposed class mapping matches the on-disk datasets."""

from __future__ import annotations

import csv
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "configs" / "dataset_config.yaml").read_text(encoding="utf-8"))
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def count_images(folder: Path) -> int:
    return sum(1 for path in folder.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)


def main() -> None:
    datasets = CONFIG["datasets"]
    for key, entry in datasets.items():
        assert (ROOT / entry["path"]).is_dir(), f"missing dataset path for {key}: {entry['path']}"

    metadata: dict[tuple[str, str, str], int] = {}
    invalid_metadata: list[str] = []
    with (ROOT / datasets["plantseg"]["metadata"]).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if (
                not row.get("Plant", "").strip()
                or not row.get("Disease", "").strip()
                or row.get("Split", "").strip().lower() not in {"training", "validation", "test"}
                or not row.get("Name", "").strip()
                or not row.get("Label file", "").strip()
            ):
                invalid_metadata.append(row.get("Name", "<unknown>"))
                continue
            key = (row["Plant"].strip(), row["Disease"].strip().lower(), row["Split"].strip().lower())
            metadata[key] = metadata.get(key, 0) + 1
    assert not invalid_metadata, f"PlantSeg has metadata rows with invalid labels/splits: {invalid_metadata[:10]}"

    classes = CONFIG["class_selection"]["classes"]
    ids = {item["id"] for item in classes}
    assert len(ids) == len(classes) == 7, "the proposed set must contain seven unique class IDs"
    for item in classes:
        pv_dir = ROOT / datasets["plantvillage"]["class_root"] / item["plantvillage_label"]
        assert pv_dir.is_dir(), f"missing PlantVillage class for {item['id']}: {pv_dir}"
        pv_count = count_images(pv_dir)
        assert pv_count == item["plantvillage_count"], f"PlantVillage count changed for {item['id']}: {pv_count}"

        if item.get("plantseg_label"):
            crop, disease = item["plantseg_crop"], item["plantseg_label"].lower()
            actual = {
                split: metadata.get((crop, disease, split), 0)
                for split in ("training", "validation", "test")
            }
            expected = {
                "training": item["plantseg_counts"]["train"],
                "validation": item["plantseg_counts"]["validation"],
                "test": item["plantseg_counts"]["test"],
            }
            assert actual == expected, f"PlantSeg class/split count mismatch for {item['id']}: {actual}"
            assert item["segmentation_available"] is True
        else:
            assert item["segmentation_available"] is False

        if item.get("plantdoc_label"):
            expected = item["plantdoc_counts"]
            for split in ("train", "test"):
                pd_dir = ROOT / datasets["plantdoc"]["path"] / split / item["plantdoc_label"]
                assert pd_dir.is_dir(), f"missing PlantDoc class for {item['id']}: {pd_dir}"
                actual = count_images(pd_dir)
                assert actual == expected[split], f"PlantDoc {split} count mismatch for {item['id']}: {actual}"
            assert item["external_test_available"] is True
        else:
            assert item["external_test_available"] is False

    excluded = {item["id"] for item in CONFIG.get("excluded_classes", [])}
    assert not ids.intersection(excluded), "an excluded class is included in the proposed model set"
    external = set(CONFIG["external_evaluation"]["supported_classes"])
    assert external == {item["id"] for item in classes if item.get("plantdoc_label")}
    assert CONFIG["external_evaluation"]["use_training_split_for_model_training"] is False
    print(f"PASS: {len(classes)} configured classes match on-disk labels and measured counts.")
    print(f"PASS: {sum(metadata.values())} PlantSeg metadata rows have non-empty labels and valid splits; invalid rows=0.")
    print(f"PASS: {len(external)} disease classes map to PlantDoc; PlantDoc remains external-only.")


if __name__ == "__main__":
    main()
