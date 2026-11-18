"""Run preprocessing on representative files from every proposed class."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml
import numpy as np

from crop_health.data.plantseg import plantseg_records
from crop_health.data.plantvillage import plantvillage_records
from crop_health.preprocessing.classification import preprocess_classification_image
from crop_health.preprocessing.segmentation import preprocess_segmentation_pair


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    config = yaml.safe_load((ROOT / "configs" / "dataset_config.yaml").read_text(encoding="utf-8"))
    pv_records = plantvillage_records(ROOT, config)
    expected_pv = sum(item["plantvillage_count"] for item in config["class_selection"]["classes"])
    assert len(pv_records) == expected_pv
    representative: dict[str, Path] = {}
    for record in pv_records:
        representative.setdefault(record.class_id, record.path)
    for class_item in config["class_selection"]["classes"]:
        array = preprocess_classification_image(representative[class_item["id"]], image_size=224)
        assert array.shape == (3, 224, 224)
        assert array.dtype.name == "float32"
        assert np.isfinite(array).all()
    print(f"PlantVillage samples: {len(pv_records)} across {len(representative)} selected classes")

    disease_classes = {
        (item["plantseg_crop"], item["plantseg_label"].lower()): item["id"]
        for item in config["class_selection"]["classes"]
        if item.get("plantseg_label")
    }
    pair_counts: Counter = Counter()
    preprocessed: set[str] = set()
    for record in plantseg_records(ROOT / config["datasets"]["plantseg"]["path"]):
        key = (record.crop, record.disease.lower())
        if key not in disease_classes:
            continue
        class_id = disease_classes[key]
        pair_counts[class_id] += 1
        if class_id not in preprocessed:
            image, mask = preprocess_segmentation_pair(record.image_path, record.mask_path, image_size=128)
            assert image.shape == (3, 128, 128)
            assert mask.shape == (128, 128)
            preprocessed.add(class_id)
    assert preprocessed == set(disease_classes.values())
    print(f"PlantSeg selected disease pairs: {dict(pair_counts)}")
    print(f"Preprocessed aligned real image/mask samples: {len(preprocessed)}")


if __name__ == "__main__":
    main()
