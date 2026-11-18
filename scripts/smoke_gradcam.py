"""Generate a Grad-CAM overlay from a real PlantVillage sample."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from crop_health.classification.inference import predict_image
from crop_health.data.plantvillage import plantvillage_records
from crop_health.explainability.gradcam import generate_gradcam


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    config = yaml.safe_load((ROOT / "configs/dataset_config.yaml").read_text(encoding="utf-8"))
    record = plantvillage_records(ROOT, config)[0]
    model_dir = ROOT / "models/classifier/smoke"
    checkpoint = model_dir / "efficientnet_b0_best.pt"
    mapping = model_dir / "class_mapping.json"
    image_size = yaml.safe_load((ROOT / "configs/model_config.yaml").read_text(encoding="utf-8"))["model"]["image_size"]
    prediction = predict_image(record.path, checkpoint, mapping, image_size=image_size)
    result = generate_gradcam(record.path, checkpoint, mapping, image_size=image_size)
    if prediction["class_id"] != result.class_id:
        raise AssertionError("Grad-CAM class does not match the classifier prediction")
    if abs(prediction["confidence"] - result.confidence) > 1e-6:
        raise AssertionError("Grad-CAM confidence does not match the classifier prediction")

    output_dir = ROOT / "reports/explainability/smoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    result.heatmap.save(output_dir / "gradcam_heatmap.png")
    result.overlay.save(output_dir / "gradcam_overlay.png")
    summary = {
        "image": str(record.path.relative_to(ROOT)),
        "class_id": result.class_id,
        "confidence": result.confidence,
        "input_size": list(result.overlay.size),
        "heatmap_size": list(result.heatmap.size),
        "same_class_as_prediction": True,
        "note": "Grad-CAM visualizes model evidence; it does not establish biological causation.",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
