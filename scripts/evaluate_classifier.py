"""Run the final, separate evaluation on a completed classifier run's test split."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import yaml
from sklearn.metrics import confusion_matrix
from torch.utils.data import DataLoader

from crop_health.classification.inference import load_classifier
from crop_health.classification.splits import load_grouped_manifest
from crop_health.classification.training import (
    ImageDataset,
    create_fresh_output_directories,
    evaluate,
    metric_report,
)
from crop_health.data.plantvillage import plantvillage_records


ROOT = Path(__file__).resolve().parents[1]


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", required=True, help="Model directory from the completed training run.")
    parser.add_argument("--report-dir", required=True, help="Report directory from the completed training run.")
    parser.add_argument("--output-dir", required=True, help="Fresh directory for final evaluation outputs.")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--dataset-config",
        default="configs/dataset_config.yaml",
        help="Path to dataset config YAML (relative to project root).",
    )
    return parser


def main() -> None:
    args = make_parser().parse_args()

    model_dir = (ROOT / args.model_dir).resolve()
    report_dir = (ROOT / args.report_dir).resolve()
    if not model_dir.is_dir() or not report_dir.is_dir():
        raise FileNotFoundError("model and training report directories must exist from a completed run")
    training_config_path = report_dir / "training_config.json"
    manifest_path = report_dir / "split_manifest.csv"
    if not training_config_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("the run report must contain training_config.json and split_manifest.csv")

    training_config = json.loads(training_config_path.read_text(encoding="utf-8"))
    if (
        training_config.get("run_type") != "full"
        or not training_config.get("final_test_evaluation_required")
        or training_config.get("training_status") in ("interrupted", "in_progress")
    ):
        raise ValueError("final holdout evaluation requires a completed full training run")
    if (ROOT / training_config["model_output_dir"]).resolve() != model_dir:
        raise ValueError("model directory does not match the completed run configuration")
    expected_manifest_hash = training_config.get("split_manifest_sha256")
    actual_manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    if not expected_manifest_hash or actual_manifest_hash != expected_manifest_hash:
        raise ValueError("run split manifest does not match its recorded training-time checksum")

    (output_dir,) = create_fresh_output_directories(ROOT / args.output_dir)
    dataset_config_path = ROOT / getattr(args, "dataset_config", "configs/dataset_config.yaml")
    dataset_config = yaml.safe_load(dataset_config_path.read_text(encoding="utf-8"))
    model_config = yaml.safe_load((ROOT / "configs/model_config.yaml").read_text(encoding="utf-8"))["model"]
    records = plantvillage_records(ROOT, dataset_config)
    manifest_relative_paths: set[str] = set()
    with manifest_path.open(encoding="utf-8", newline="") as manifest_file:
        for row in csv.DictReader(manifest_file):
            manifest_relative_paths.add(row["relative_path"])
    root_resolved = ROOT.resolve()
    records = [
        r for r in records
        if Path(r.path).resolve().relative_to(root_resolved).as_posix()
        in manifest_relative_paths
    ]
    splits = load_grouped_manifest(
        records, manifest_path, ROOT, verify_partitions=("test",),
    )

    model, class_ids, device = load_classifier(
        model_dir / "efficientnet_b0_best.pt", model_dir / "class_mapping.json", args.device
    )
    class_to_index = {class_id: index for index, class_id in enumerate(class_ids)}
    dataset = ImageDataset(
        splits["test"], class_to_index, int(model_config["image_size"]), training=False, seed=0
    )
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)
    loss, y_true, y_pred = evaluate(model, loader, device)
    results = metric_report(y_true, y_pred, class_ids)
    results.update({
        "evaluation_loss": loss,
        "test_samples": len(y_true),
        "run_type": "saved_split",
        "split_manifest_sha256": actual_manifest_hash,
        "note": "PlantVillage internal holdout; PlantDoc remains external and is not used here.",
    })
    output_path = output_dir / "evaluation_results.json"
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    matrix = confusion_matrix(y_true, y_pred, labels=list(range(len(class_ids))))
    with (output_dir / "confusion_matrix.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["true\\predicted", *class_ids])
        for class_id, row in zip(class_ids, matrix, strict=True):
            writer.writerow([class_id, *row.tolist()])
    print(json.dumps(results))


if __name__ == "__main__":
    main()
