"""PlantSeg image/mask manifest helpers based on its metadata CSV."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


SPLIT_DIRECTORIES = {"training": "train", "validation": "val", "test": "test"}


@dataclass(frozen=True)
class SegmentationRecord:
    image_path: Path
    mask_path: Path
    crop: str
    disease: str
    split: str


def plantseg_records(dataset_root: Path, split: str | None = None) -> Iterator[SegmentationRecord]:
    """Yield metadata-defined pairs and fail clearly on missing paths."""
    selected_split = SPLIT_DIRECTORIES.get(split.lower()) if split else None
    if split and selected_split is None:
        raise ValueError(f"split must be one of {sorted(SPLIT_DIRECTORIES)}")

    metadata_path = dataset_root / "Metadatav2.csv"
    with metadata_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            metadata_split = row["Split"].strip().lower()
            image_split = SPLIT_DIRECTORIES.get(metadata_split)
            if image_split is None:
                raise ValueError(f"invalid PlantSeg split in metadata: {row['Split']!r}")
            if selected_split and image_split != selected_split:
                continue
            image_path = dataset_root / "images" / image_split / row["Name"]
            mask_path = dataset_root / "annotations" / image_split / row["Label file"]
            if not image_path.is_file():
                raise FileNotFoundError(f"PlantSeg image missing: {image_path}")
            if not mask_path.is_file():
                raise FileNotFoundError(f"PlantSeg mask missing: {mask_path}")
            yield SegmentationRecord(
                image_path=image_path,
                mask_path=mask_path,
                crop=row["Plant"].strip(),
                disease=row["Disease"].strip(),
                split=image_split,
            )
