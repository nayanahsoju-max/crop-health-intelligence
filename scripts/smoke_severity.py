"""Estimate severity for one real PlantSeg pair per selected disease."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from crop_health.data.plantseg import plantseg_records
from crop_health.severity.estimator import estimate_severity


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    dataset = yaml.safe_load((ROOT / "configs/dataset_config.yaml").read_text(encoding="utf-8"))
    selected = {
        (item["plantseg_crop"], item["plantseg_label"].lower()): item["id"]
        for item in dataset["class_selection"]["classes"]
        if item.get("plantseg_label")
    }
    results: dict[str, dict[str, object]] = {}
    for record in plantseg_records(ROOT / dataset["datasets"]["plantseg"]["path"]):
        key = (record.crop, record.disease.lower())
        class_id = selected.get(key)
        if class_id is None or class_id in results:
            continue
        estimate = estimate_severity(record.image_path, record.mask_path)
        results[class_id] = {
            "image": str(record.image_path.relative_to(ROOT)),
            "mask": str(record.mask_path.relative_to(ROOT)),
            "severity_percentage": estimate.severity_percentage,
            "category": estimate.category,
            "diseased_leaf_area_pixels": estimate.diseased_leaf_area_pixels,
            "estimated_leaf_area_pixels": estimate.estimated_leaf_area_pixels,
            "method": estimate.method,
        }
    if set(results) != set(selected.values()):
        raise RuntimeError(f"severity samples missing selected classes: {set(selected.values()) - set(results)}")
    output = ROOT / "reports" / "severity" / "smoke_summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
