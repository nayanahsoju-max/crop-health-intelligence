"""Classifier loading and image inference."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch

from crop_health.classification.model import build_classifier
from crop_health.preprocessing.classification import preprocess_classification_image


def load_classifier(checkpoint_path: str | Path, class_mapping_path: str | Path,
                    device: str | torch.device = "cpu") -> tuple[torch.nn.Module, list[str], torch.device]:
    device = torch.device(device)
    mapping: dict[str, Any] = json.loads(Path(class_mapping_path).read_text(encoding="utf-8"))
    class_ids = mapping["index_to_class"]
    expected_mapping = {class_id: index for index, class_id in enumerate(class_ids)}
    if mapping.get("class_to_index") != expected_mapping or len(set(class_ids)) != len(class_ids):
        raise ValueError("saved class mapping is inconsistent")
    model = build_classifier(len(class_ids), pretrained=False)
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    if checkpoint["class_ids"] != class_ids:
        raise ValueError("checkpoint class IDs do not match the saved class mapping")
    model.load_state_dict(checkpoint["state_dict"])
    model.to(device).eval()
    return model, class_ids, device


@torch.inference_mode()
def predict_image(image_path: str | Path, checkpoint_path: str | Path,
                  class_mapping_path: str | Path, image_size: int = 224,
                  device: str | torch.device = "cpu") -> dict[str, Any]:
    model, class_ids, device = load_classifier(checkpoint_path, class_mapping_path, device)
    array = preprocess_classification_image(image_path, image_size=image_size)
    tensor = torch.from_numpy(array).unsqueeze(0).to(device)
    probabilities = torch.softmax(model(tensor), dim=1)[0].cpu().tolist()
    index = max(range(len(probabilities)), key=probabilities.__getitem__)
    return {
        "class_id": class_ids[index],
        "confidence": float(probabilities[index]),
        "probabilities": {class_ids[i]: float(value) for i, value in enumerate(probabilities)},
    }
