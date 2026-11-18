"""Evaluate a saved classifier on compatible PlantDoc test folders only."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import torch
import yaml
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from torch.utils.data import DataLoader

from crop_health.classification.inference import load_classifier
from crop_health.classification.training import ImageDataset
from crop_health.data.plantvillage import ClassificationRecord, IMAGE_SUFFIXES


ROOT = Path(__file__).resolve().parents[1]


def evaluate() -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", default="models/classifier")
    parser.add_argument("--output-dir", default="reports/classification/external_plantdoc")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--model-description", default="saved_classifier")
    args = parser.parse_args()

    config = yaml.safe_load((ROOT / "configs/dataset_config.yaml").read_text(encoding="utf-8"))
    model_config = yaml.safe_load((ROOT / "configs/model_config.yaml").read_text(encoding="utf-8"))["model"]
    model_dir = ROOT / args.model_dir
    model, class_ids, device = load_classifier(
        model_dir / "efficientnet_b0_best.pt", model_dir / "class_mapping.json", args.device
    )
    model_to_index = {class_id: index for index, class_id in enumerate(class_ids)}
    selected = [item for item in config["class_selection"]["classes"] if item.get("plantdoc_label")]
    if any(item["id"] not in model_to_index for item in selected):
        raise ValueError("saved classifier does not contain every configured PlantDoc-compatible class")
    test_root = ROOT / config["datasets"]["plantdoc"]["path"] / "test"
    records: list[ClassificationRecord] = []
    expected_counts: dict[str, int] = {}
    mapped_folders = set()
    for item in selected:
        label = item["plantdoc_label"]
        mapped_folders.add(label)
        folder = test_root / label
        if not folder.is_dir():
            raise FileNotFoundError(f"compatible PlantDoc test class is missing: {folder}")
        images = sorted(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)
        expected = item["plantdoc_counts"]["test"]
        if len(images) != expected:
            raise ValueError(f"PlantDoc test count changed for {item['id']}: expected {expected}, got {len(images)}")
        expected_counts[item["id"]] = len(images)
        records.extend(ClassificationRecord(path, item["id"], item["crop"]) for path in images)

    unsupported: list[dict[str, object]] = []
    excluded_reasons = {
        entry.get("plantdoc_label"): entry["reason"]
        for entry in config.get("excluded_classes", [])
        if entry.get("plantdoc_label")
    }
    for folder in sorted(path for path in test_root.iterdir() if path.is_dir() and path.name not in mapped_folders):
        count = sum(1 for path in folder.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)
        unsupported.append({
            "folder_label": folder.name,
            "count": count,
            "reason": excluded_reasons.get(folder.name, "No compatible selected classifier class is configured."),
        })

    class_to_index = model_to_index
    dataset = ImageDataset(records, class_to_index, int(model_config["image_size"]), training=False, seed=0)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)
    y_true: list[int] = []
    y_pred: list[int] = []
    confidences: list[float] = []
    model.eval()
    with torch.inference_mode():
        for inputs, targets in loader:
            probabilities = torch.softmax(model(inputs.to(device)), dim=1)
            confidences.extend(probabilities.max(dim=1).values.cpu().tolist())
            y_true.extend(targets.tolist())
            y_pred.extend(probabilities.argmax(dim=1).cpu().tolist())

    evaluated_ids = [item["id"] for item in selected]
    evaluated_indices = [model_to_index[class_id] for class_id in evaluated_ids]
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=evaluated_indices, zero_division=0
    )
    results = {
        "evaluation_type": "external_plantdoc_test",
        "model_description": args.model_description,
        "model_architecture": "efficientnet_b0",
        "split": "test",
        "plantdoc_training_split_used": False,
        "test_samples": len(records),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_precision": float(precision.mean()),
        "macro_recall": float(recall.mean()),
        "macro_f1": float(f1.mean()),
        "per_class": {
            class_id: {
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "support": int(support[index]),
            }
            for index, class_id in enumerate(evaluated_ids)
        },
        "selected_class_counts": expected_counts,
        "unsupported_test_classes": unsupported,
        "note": "PlantDoc is a small external dataset. Smoke-model metrics verify evaluation wiring only and do not estimate model generalization.",
    }
    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "evaluation_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    matrix = confusion_matrix(y_true, y_pred, labels=list(range(len(class_ids))))
    with (output_dir / "confusion_matrix.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["true\\predicted", *class_ids])
        for class_id, row in zip(class_ids, matrix, strict=True):
            writer.writerow([class_id, *row.tolist()])
    with (output_dir / "per_image_predictions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["image", "crop", "true_class", "predicted_class", "confidence"])
        for record, predicted, confidence in zip(records, y_pred, confidences, strict=True):
            writer.writerow([
                str(record.path.relative_to(ROOT)), record.crop, record.class_id,
                class_ids[predicted], f"{confidence:.8f}",
            ])
    print(json.dumps(results))
    return results


if __name__ == "__main__":
    evaluate()
