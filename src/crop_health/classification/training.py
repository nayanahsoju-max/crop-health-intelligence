"""Reproducible EfficientNet B0 transfer-learning training pipeline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.utils.class_weight import compute_class_weight
from torch import nn
from torch.utils.data import DataLoader, Dataset
import yaml

from crop_health.classification.model import build_classifier
from crop_health.classification.splits import load_grouped_manifest, stratified_split
from crop_health.data.plantvillage import ClassificationRecord, plantvillage_records
from crop_health.preprocessing.classification import preprocess_classification_image


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def validate_fresh_output_directories(*paths: Path) -> tuple[Path, ...]:
    """Require distinct, absent run directories contained within the project."""
    root = PROJECT_ROOT.resolve()
    resolved = tuple(path.resolve() for path in paths)
    if len(set(resolved)) != len(resolved):
        raise ValueError("each run artifact directory must be a distinct path")
    for path in resolved:
        try:
            path.relative_to(root)
        except ValueError as error:
            raise ValueError(f"run artifact directory must be inside the project: {path}") from error
        if path == root:
            raise ValueError("project root cannot be used as a run artifact directory")
        if path.exists():
            raise FileExistsError(f"run artifact directory already exists; choose a fresh run path: {path}")
    for index, path in enumerate(resolved):
        if any(path in other.parents or other in path.parents for other in resolved[index + 1:]):
            raise ValueError("run artifact directories cannot contain one another")
    return resolved


def create_fresh_output_directories(*paths: Path) -> tuple[Path, ...]:
    """Create run directories without ever reusing an existing destination."""
    resolved = validate_fresh_output_directories(*paths)
    for path in resolved:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.mkdir(exist_ok=False)
    return resolved


def validate_resumable_output_directories(*paths: Path) -> tuple[Path, ...]:
    """Validate that run artifact directories exist, are inside the project, and distinct."""
    root = PROJECT_ROOT.resolve()
    resolved = tuple(path.resolve() for path in paths)
    if len(set(resolved)) != len(resolved):
        raise ValueError("each run artifact directory must be a distinct path")
    for path in resolved:
        try:
            path.relative_to(root)
        except ValueError as error:
            raise ValueError(f"run artifact directory must be inside the project: {path}") from error
        if path == root:
            raise ValueError("project root cannot be used as a run artifact directory")
        if not path.is_dir():
            raise FileNotFoundError(f"cannot resume run; artifact directory does not exist: {path}")
    for index, path in enumerate(resolved):
        if any(path in other.parents or other in path.parents for other in resolved[index + 1:]):
            raise ValueError("run artifact directories cannot contain one another")
    return resolved


def persist_training_progress(
    model_output: Path,
    report_output: Path,
    history: list[dict[str, Any]],
    config_data: dict[str, Any],
    recovery_checkpoint: dict[str, Any] | None = None,
) -> None:
    """Persist history, configuration metadata, curves, and recovery checkpoint."""
    if recovery_checkpoint is not None:
        torch.save(recovery_checkpoint, model_output / "recovery_checkpoint.pt")
    (report_output / "training_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    (report_output / "training_config.json").write_text(json.dumps(config_data, indent=2), encoding="utf-8")
    if history:
        save_curves(history, report_output / "training_curves.png")


class ImageDataset(Dataset):
    def __init__(self, records: list[ClassificationRecord], class_to_index: dict[str, int],
                 image_size: int, *, training: bool, seed: int):
        self.records = records
        self.class_to_index = class_to_index
        self.image_size = image_size
        self.training = training
        self.rng = random.Random(seed)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        record = self.records[index]
        array = preprocess_classification_image(
            record.path, self.image_size, training=self.training, rng=self.rng
        )
        return torch.from_numpy(array), self.class_to_index[record.class_id]


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def _limit_smoke_records(records: list[ClassificationRecord], per_class: int, seed: int) -> list[ClassificationRecord]:
    groups: dict[str, list[ClassificationRecord]] = {}
    for record in records:
        groups.setdefault(record.class_id, []).append(record)
    limited: list[ClassificationRecord] = []
    for index, class_id in enumerate(sorted(groups)):
        group = groups[class_id]
        random.Random(seed + index).shuffle(group)
        if len(group) < per_class:
            raise ValueError(f"smoke test needs {per_class} samples for {class_id}, found {len(group)}")
        limited.extend(group[:per_class])
    return limited


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device,
             class_weights: torch.Tensor | None = None) -> tuple[float, list[int], list[int]]:
    model.eval()
    loss_fn = nn.CrossEntropyLoss(weight=class_weights)
    total_loss = 0.0
    y_true: list[int] = []
    y_pred: list[int] = []
    with torch.inference_mode():
        for inputs, targets in loader:
            inputs, targets = inputs.to(device), targets.to(device)
            logits = model(inputs)
            total_loss += loss_fn(logits, targets).item() * len(targets)
            y_true.extend(targets.cpu().tolist())
            y_pred.extend(logits.argmax(1).cpu().tolist())
    return total_loss / max(1, len(y_true)), y_true, y_pred


def metric_report(y_true: list[int], y_pred: list[int], class_ids: list[str]) -> dict[str, Any]:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(len(class_ids))), zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_precision": float(precision.mean()),
        "macro_recall": float(recall.mean()),
        "macro_f1": float(f1.mean()),
        "per_class": {
            class_id: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i, class_id in enumerate(class_ids)
        },
    }


def train_epoch(model: nn.Module, loader: DataLoader, optimizer: torch.optim.Optimizer,
                loss_fn: nn.Module, device: torch.device) -> tuple[float, float]:
    model.train()
    total_loss = 0.0
    correct = 0
    count = 0
    for inputs, targets in loader:
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad(set_to_none=True)
        logits = model(inputs)
        loss = loss_fn(logits, targets)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * len(targets)
        correct += (logits.argmax(1) == targets).sum().item()
        count += len(targets)
    return total_loss / max(1, count), correct / max(1, count)


def save_curves(history: list[dict[str, float]], output_path: Path) -> None:
    epochs = [item["epoch"] for item in history]
    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(epochs, [item["train_loss"] for item in history], label="train")
    axes[0].plot(epochs, [item["validation_loss"] for item in history], label="validation")
    axes[0].set_title("Loss")
    axes[1].plot(epochs, [item["train_accuracy"] for item in history], label="train accuracy")
    axes[1].plot(epochs, [item["validation_macro_f1"] for item in history], label="validation macro F1")
    axes[1].set_title("Accuracy and macro F1")
    for axis in axes:
        axis.set_xlabel("Epoch")
        axis.legend()
        axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def run_training(args: argparse.Namespace) -> dict[str, Any]:
    resume = getattr(args, "resume", False)
    if resume:
        model_output, report_output = validate_resumable_output_directories(
            PROJECT_ROOT / args.output_dir, PROJECT_ROOT / args.report_dir
        )
    else:
        model_output, report_output = validate_fresh_output_directories(
            PROJECT_ROOT / args.output_dir, PROJECT_ROOT / args.report_dir
        )
    dataset_config_path = PROJECT_ROOT / getattr(args, "dataset_config", "configs/dataset_config.yaml")
    dataset_config = yaml.safe_load(dataset_config_path.read_text(encoding="utf-8"))
    model_config = yaml.safe_load((PROJECT_ROOT / "configs/model_config.yaml").read_text(encoding="utf-8"))["model"]
    seed = args.seed if args.seed is not None else model_config["seed"]
    seed_everything(seed)

    class_ids = [item["id"] for item in dataset_config["class_selection"]["classes"]]
    class_to_index = {class_id: index for index, class_id in enumerate(class_ids)}
    records = plantvillage_records(PROJECT_ROOT, dataset_config)
    if args.smoke_test:
        records = _limit_smoke_records(records, args.smoke_samples_per_class, seed)
        labels = [record.class_id for record in records]
        fractions = model_config["validation_fraction"], model_config["test_fraction"]
        splits = stratified_split(records, labels, seed, *fractions)
    else:
        manifest_path = PROJECT_ROOT / args.split_manifest
        if not manifest_path.is_file():
            raise FileNotFoundError(
                f"leakage-safe classifier split manifest is required before full training: {manifest_path}; "
                "run python -m scripts.create_leakage_safe_split first"
            )
        # Filter records to only those covered by the manifest.
        # plantvillage_records() may return more images than the manifest covers
        # (e.g. when a small number of near-duplicate groups are excluded from
        # the split during dataset preparation).  load_grouped_manifest()
        # enforces that every record it receives appears in the manifest, so we
        # drop any surplus records before passing them in.
        manifest_relative_paths: set[str] = set()
        with manifest_path.open(encoding="utf-8", newline="") as manifest_file:
            for row in csv.DictReader(manifest_file):
                manifest_relative_paths.add(row["relative_path"])
        root_resolved = PROJECT_ROOT.resolve()
        records = [
            r for r in records
            if Path(r.path).resolve().relative_to(root_resolved).as_posix()
            in manifest_relative_paths
        ]
        splits = load_grouped_manifest(
            records, manifest_path, PROJECT_ROOT,
            verify_partitions=("train", "validation"),
        )

    checkpoint_path = model_output / "efficientnet_b0_best.pt"
    recovery_checkpoint_path = model_output / "recovery_checkpoint.pt"
    mapping_path = model_output / "class_mapping.json"
    manifest_copy_path = report_output / "split_manifest.csv"
    config_path = report_output / "training_config.json"

    manifest_hash = None
    if not args.smoke_test:
        manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    if not resume:
        model_output, report_output = create_fresh_output_directories(model_output, report_output)
        mapping = {"class_to_index": class_to_index, "index_to_class": class_ids}
        mapping_path.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
        if not args.smoke_test:
            shutil.copyfile(manifest_path, manifest_copy_path)
    else:
        if not recovery_checkpoint_path.is_file():
            raise FileNotFoundError(f"cannot resume run; recovery checkpoint not found: {recovery_checkpoint_path}")
        if not config_path.is_file():
            raise FileNotFoundError(f"cannot resume run; training config not found: {config_path}")
        existing_config = json.loads(config_path.read_text(encoding="utf-8"))
        if existing_config.get("training_status") == "completed":
            raise ValueError("cannot resume a training run that is already completed")
        if not args.smoke_test:
            if not manifest_copy_path.is_file():
                raise FileNotFoundError(f"cannot resume run; run split manifest missing: {manifest_copy_path}")
            run_manifest_hash = hashlib.sha256(manifest_copy_path.read_bytes()).hexdigest()
            if run_manifest_hash != manifest_hash:
                raise ValueError("run split manifest checksum does not match expected manifest hash")
            if existing_config.get("split_manifest_sha256") != manifest_hash:
                raise ValueError("training config split manifest checksum does not match expected manifest hash")

    image_size = int(model_config["image_size"])
    batch_size = args.batch_size or (4 if args.smoke_test else int(model_config["batch_size"]))
    loader_generator = torch.Generator().manual_seed(seed)
    loaders: dict[str, DataLoader] = {}
    for split in ("train", "validation"):
        split_records = splits[split]
        ds = ImageDataset(split_records, class_to_index, image_size,
                          training=split == "train", seed=seed + len(loaders))
        loaders[split] = DataLoader(
            ds, batch_size=batch_size, shuffle=(split == "train"), num_workers=0,
            generator=loader_generator if split == "train" else None,
        )

    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    pretrained = False if resume else bool(model_config["pretrained"])
    model = build_classifier(len(class_ids), pretrained=pretrained).to(device)
    observed = np.asarray([class_to_index[record.class_id] for record in splits["train"]])
    weights = compute_class_weight(class_weight="balanced", classes=np.arange(len(class_ids)), y=observed)
    class_weights = torch.tensor(weights, dtype=torch.float32, device=device) if model_config["class_weighting"] else None
    loss_fn = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(model_config["learning_rate"]),
                                  weight_decay=float(model_config["weight_decay"]))
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)
    max_epochs = args.epochs or (1 if args.smoke_test else int(model_config["epochs"]))
    patience = 2 if args.smoke_test else int(model_config["early_stopping_patience"])

    history: list[dict[str, Any]] = []
    best_f1 = -1.0
    best_epoch = None
    stale_epochs = 0
    start_epoch = 1

    if resume:
        recovery = torch.load(recovery_checkpoint_path, map_location=device, weights_only=False)
        if recovery.get("class_ids") != class_ids:
            raise ValueError("recovery checkpoint class IDs do not match dataset configuration")
        model.load_state_dict(recovery["model_state_dict"])
        optimizer.load_state_dict(recovery["optimizer_state_dict"])
        scheduler.load_state_dict(recovery["scheduler_state_dict"])
        start_epoch = int(recovery["completed_epoch"]) + 1
        best_f1 = float(recovery["best_validation_macro_f1"])
        best_epoch = recovery.get("best_epoch")
        stale_epochs = int(recovery.get("stale_epochs", 0))
        history = list(recovery.get("history", []))
        rng_states = recovery.get("rng_states", {})
        if "python" in rng_states and rng_states["python"] is not None:
            random.setstate(rng_states["python"])
        if "numpy" in rng_states and rng_states["numpy"] is not None:
            np.random.set_state(rng_states["numpy"])
        if "torch" in rng_states and rng_states["torch"] is not None:
            torch.set_rng_state(rng_states["torch"])
        if torch.cuda.is_available() and rng_states.get("torch_cuda") is not None:
            torch.cuda.set_rng_state_all(rng_states["torch_cuda"])

    config_data = {
        "run_identifier": model_output.name,
        "run_type": "smoke_test" if args.smoke_test else "full",
        "training_status": "in_progress",
        "completed_epochs": len(history),
        "epochs_requested": max_epochs,
        "best_epoch": best_epoch,
        "best_validation_macro_f1": best_f1 if best_f1 >= 0 else None,
        "early_stopped": False,
        "model": "efficientnet_b0",
        "pretrained": bool(model_config["pretrained"]),
        "device": str(device),
        "seed": seed,
        "image_size": image_size,
        "batch_size": batch_size,
        "learning_rate": float(model_config["learning_rate"]),
        "weight_decay": float(model_config["weight_decay"]),
        "early_stopping_patience": patience,
        "class_ids": class_ids,
        "class_mapping": {class_id: index for index, class_id in enumerate(class_ids)},
        "split_sizes": {key: len(value) for key, value in splits.items()},
        "split_manifest": str(args.split_manifest) if not args.smoke_test else None,
        "split_manifest_sha256": manifest_hash,
        "model_output_dir": str(model_output.relative_to(PROJECT_ROOT)),
        "report_output_dir": str(report_output.relative_to(PROJECT_ROOT)),
        "checkpoint_path": str((model_output / "efficientnet_b0_best.pt").relative_to(PROJECT_ROOT)),
        "recovery_checkpoint_path": str(recovery_checkpoint_path.relative_to(PROJECT_ROOT)),
        "final_test_evaluation_required": False,
        "plantdoc_used_for_training": False,
    }
    persist_training_progress(model_output, report_output, history, config_data)

    early_stopped = False
    try:
        for epoch in range(start_epoch, max_epochs + 1):
            train_loss, train_accuracy = train_epoch(model, loaders["train"], optimizer, loss_fn, device)
            validation_loss, y_true, y_pred = evaluate(model, loaders["validation"], device, class_weights)
            validation_metrics = metric_report(y_true, y_pred, class_ids)
            row = {
                "epoch": float(epoch),
                "train_loss": train_loss,
                "train_accuracy": train_accuracy,
                "validation_loss": validation_loss,
                "validation_accuracy": validation_metrics["accuracy"],
                "validation_macro_f1": validation_metrics["macro_f1"],
            }
            history.append(row)
            scheduler.step(validation_metrics["macro_f1"])
            if validation_metrics["macro_f1"] > best_f1:
                best_f1 = validation_metrics["macro_f1"]
                best_epoch = epoch
                stale_epochs = 0
                torch.save({"state_dict": model.state_dict(), "class_ids": class_ids}, checkpoint_path)
            else:
                stale_epochs += 1
            print(json.dumps(row), flush=True)

            recovery = {
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "completed_epoch": epoch,
                "best_validation_macro_f1": best_f1,
                "best_epoch": best_epoch,
                "stale_epochs": stale_epochs,
                "rng_states": {
                    "python": random.getstate(),
                    "numpy": np.random.get_state(),
                    "torch": torch.get_rng_state(),
                    "torch_cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
                },
                "class_ids": class_ids,
                "history": history,
            }
            config_data["completed_epochs"] = epoch
            config_data["best_epoch"] = best_epoch
            config_data["best_validation_macro_f1"] = best_f1
            config_data["training_status"] = "in_progress"
            config_data["final_test_evaluation_required"] = False
            persist_training_progress(model_output, report_output, history, config_data, recovery)

            if stale_epochs >= patience:
                early_stopped = True
                break

        config_data["training_status"] = "completed"
        config_data["early_stopped"] = early_stopped
        config_data["final_test_evaluation_required"] = not args.smoke_test
        config_data["completed_epochs"] = len(history)
        config_data["best_epoch"] = best_epoch
        config_data["best_validation_macro_f1"] = best_f1
        persist_training_progress(model_output, report_output, history, config_data)

    except (KeyboardInterrupt, SystemExit):
        config_data["training_status"] = "interrupted"
        config_data["interruption_reason"] = "process interrupted or terminated"
        config_data["final_test_evaluation_required"] = False
        persist_training_progress(model_output, report_output, history, config_data)
        raise
    except Exception as exc:
        config_data["training_status"] = "interrupted"
        config_data["interruption_reason"] = f"error: {exc}"
        config_data["final_test_evaluation_required"] = False
        persist_training_progress(model_output, report_output, history, config_data)
        raise

    result = {
        "run_type": "smoke_test" if args.smoke_test else "full",
        "training_status": config_data["training_status"],
        "best_validation_macro_f1": best_f1,
        "best_epoch": best_epoch,
        "epochs_completed": len(history),
        "checkpoint": str(checkpoint_path.relative_to(PROJECT_ROOT)),
        "final_test_evaluation_required": not args.smoke_test,
        "note": "Training completed using train and validation partitions only. Run the separate final evaluator after model selection."
        if not args.smoke_test else "Smoke training used train and validation partitions only; it is not a performance estimate.",
    }
    print(json.dumps(result), flush=True)
    return result


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true", help="Train one epoch on a tiny stratified subset.")
    parser.add_argument("--smoke-samples-per-class", type=int, default=4)
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--device")
    parser.add_argument("--output-dir", required=True, help="Fresh, run-specific model artifact directory.")
    parser.add_argument("--report-dir", required=True, help="Fresh, run-specific training report directory.")
    parser.add_argument("--split-manifest", default="reports/data_manifest/plantvillage_classifier_split.csv")
    parser.add_argument("--dataset-config", default="configs/dataset_config.yaml", help="Path to dataset config YAML (relative to project root).")
    parser.add_argument("--resume", action="store_true", help="Resume an interrupted training run from its recovery checkpoint.")
    return parser


def main() -> None:
    run_training(make_parser().parse_args())


if __name__ == "__main__":
    main()
