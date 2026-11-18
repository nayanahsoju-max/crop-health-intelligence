"""Manifest helpers for the selected PlantVillage class folders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


@dataclass(frozen=True)
class ClassificationRecord:
    path: Path
    class_id: str
    crop: str


def plantvillage_records(project_root: Path, dataset_config: dict[str, Any]) -> list[ClassificationRecord]:
    """Enumerate only the explicitly selected primary-tree classes."""
    root = project_root / dataset_config["datasets"]["plantvillage"]["class_root"]
    records: list[ClassificationRecord] = []
    for item in dataset_config["class_selection"]["classes"]:
        folder = root / item["plantvillage_label"]
        if not folder.is_dir():
            raise FileNotFoundError(f"selected PlantVillage class folder is missing: {folder}")
        paths = sorted(
            path for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
        if len(paths) != item["plantvillage_count"]:
            raise ValueError(
                f"class count changed for {item['id']}: expected {item['plantvillage_count']}, got {len(paths)}"
            )
        records.extend(ClassificationRecord(path, item["id"], item["crop"]) for path in paths)
    return records
