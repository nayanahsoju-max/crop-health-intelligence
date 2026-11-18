import argparse
import hashlib
import json
from types import SimpleNamespace

import pytest
from torch import nn

from crop_health.classification import training


def test_training_never_constructs_or_evaluates_test_dataset(tmp_path, monkeypatch):
    monkeypatch.setattr(training, "PROJECT_ROOT", tmp_path)
    class_ids = [f"class_{index}" for index in range(7)]
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    (config_dir / "dataset_config.yaml").write_text(
        "class_selection:\n  classes:\n" + "".join(f"    - id: {class_id}\n" for class_id in class_ids),
        encoding="utf-8",
    )
    (config_dir / "model_config.yaml").write_text(
        "model:\n"
        "  seed: 17\n  image_size: 224\n  batch_size: 2\n  pretrained: false\n"
        "  class_weighting: true\n  learning_rate: 0.001\n  weight_decay: 0.0\n"
        "  epochs: 1\n  early_stopping_patience: 2\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "source_manifest.csv"
    manifest.write_text("metadata only\n", encoding="utf-8")

    records = {
        split: [
            SimpleNamespace(path=tmp_path / "data" / class_id / f"{split}.jpg", class_id=class_id)
            for class_id in class_ids
        ]
        for split in ("train", "validation", "test")
    }
    monkeypatch.setattr(training, "plantvillage_records", lambda *_: [record for part in records.values() for record in part])

    def load_manifest(_records, _manifest, _root, *, verify_partitions):
        assert verify_partitions == ("train", "validation")
        return records

    monkeypatch.setattr(training, "load_grouped_manifest", load_manifest)
    created_datasets = []

    class DatasetSpy:
        def __init__(self, selected, _mapping, _size, *, training, seed):
            self.records = selected
            self.training = training
            created_datasets.append(self)

        def __len__(self):
            return len(self.records)

        def __getitem__(self, index):
            raise AssertionError("the mocked epoch/evaluation must not load image contents")

    monkeypatch.setattr(training, "ImageDataset", DatasetSpy)
    monkeypatch.setattr(training, "build_classifier", lambda *_args, **_kwargs: nn.Linear(1, 7))

    class LoaderSpy:
        def __init__(self, dataset, **_kwargs):
            self.dataset = dataset

    monkeypatch.setattr(training, "DataLoader", LoaderSpy)
    evaluated = []

    def fake_train_epoch(_model, loader, _optimizer, _loss_fn, _device):
        assert loader.dataset.training is True
        return 1.0, 0.5

    def fake_evaluate(_model, loader, _device, _weights=None):
        assert loader.dataset.training is False
        assert len(loader.dataset.records) == 7
        evaluated.append(loader.dataset.records)
        return 1.0, list(range(7)), list(range(7))

    monkeypatch.setattr(training, "train_epoch", fake_train_epoch)
    monkeypatch.setattr(training, "evaluate", fake_evaluate)
    monkeypatch.setattr(training, "save_curves", lambda *_: None)

    result = training.run_training(argparse.Namespace(
        output_dir="models/classifier/runs/safety-test",
        report_dir="reports/classification/runs/safety-test",
        split_manifest="source_manifest.csv",
        smoke_test=False,
        smoke_samples_per_class=1,
        seed=17,
        batch_size=2,
        epochs=1,
        device="cpu",
    ))

    used_paths = {record.path for dataset in created_datasets for record in dataset.records}
    test_paths = {record.path for record in records["test"]}
    assert not (used_paths & test_paths)
    assert len(created_datasets) == 2
    assert len(evaluated) == 1
    assert result["final_test_evaluation_required"] is True
    report_dir = tmp_path / "reports/classification/runs/safety-test"
    assert (report_dir / "split_manifest.csv").is_file()
    assert not (report_dir / "evaluation_results.json").exists()
    assert not (report_dir / "confusion_matrix.csv").exists()
    assert not (report_dir / "inference_smoke.json").exists()


def test_training_output_directories_refuse_existing_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(training, "PROJECT_ROOT", tmp_path)
    existing = tmp_path / "models/classifier/runs/existing"
    existing.mkdir(parents=True)
    checkpoint = existing / "checkpoint.pt"
    checkpoint.write_bytes(b"preserve me")
    before = hashlib.sha256(checkpoint.read_bytes()).hexdigest()

    with pytest.raises(FileExistsError, match="already exists"):
        training.create_fresh_output_directories(existing)

    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == before


def test_evaluator_refuses_existing_output_before_loading_test_data(tmp_path, monkeypatch):
    from scripts import evaluate_classifier

    monkeypatch.setattr(evaluate_classifier, "ROOT", tmp_path)
    monkeypatch.setattr(training, "PROJECT_ROOT", tmp_path)
    model_dir = tmp_path / "models/run-1"
    report_dir = tmp_path / "reports/run-1"
    output_dir = tmp_path / "reports/evaluations/run-1"
    model_dir.mkdir(parents=True)
    report_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    result_file = output_dir / "keep.json"
    result_file.write_text("existing", encoding="utf-8")
    manifest = report_dir / "split_manifest.csv"
    manifest.write_text("metadata only\n", encoding="utf-8")
    (report_dir / "training_config.json").write_text(json.dumps({
        "run_type": "full",
        "final_test_evaluation_required": True,
        "model_output_dir": "models/run-1",
        "split_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
    }), encoding="utf-8")

    monkeypatch.setattr(
        evaluate_classifier, "plantvillage_records",
        lambda *_: pytest.fail("test data must not be inspected when output path is not fresh"),
    )
    monkeypatch.setattr("sys.argv", [
        "evaluate_classifier",
        "--model-dir", "models/run-1",
        "--report-dir", "reports/run-1",
        "--output-dir", "reports/evaluations/run-1",
    ])

    with pytest.raises(FileExistsError, match="already exists"):
        evaluate_classifier.main()
    assert result_file.read_text(encoding="utf-8") == "existing"


def test_incremental_recovery_checkpoint_and_history_saved_every_epoch(tmp_path, monkeypatch):
    import torch
    monkeypatch.setattr(training, "PROJECT_ROOT", tmp_path)
    class_ids = [f"class_{index}" for index in range(7)]
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    (config_dir / "dataset_config.yaml").write_text(
        "class_selection:\n  classes:\n" + "".join(f"    - id: {class_id}\n" for class_id in class_ids),
        encoding="utf-8",
    )
    (config_dir / "model_config.yaml").write_text(
        "model:\n"
        "  seed: 17\n  image_size: 224\n  batch_size: 2\n  pretrained: false\n"
        "  class_weighting: true\n  learning_rate: 0.001\n  weight_decay: 0.0\n"
        "  epochs: 2\n  early_stopping_patience: 3\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "source_manifest.csv"
    manifest.write_text("relative_path,class_id,partition,sha256,group_id,source_family_id\n", encoding="utf-8")

    records = {
        split: [SimpleNamespace(path=tmp_path / f"{split}_{i}.jpg", class_id=cid) for i, cid in enumerate(class_ids)]
        for split in ("train", "validation", "test")
    }
    monkeypatch.setattr(training, "plantvillage_records", lambda *_: [r for part in records.values() for r in part])
    monkeypatch.setattr(training, "load_grouped_manifest", lambda *a, **k: records)

    class FakeDataset:
        def __init__(self, recs, mapping, size, *, training, seed):
            self.records = recs
            self.training = training

        def __len__(self):
            return len(self.records)

    monkeypatch.setattr(training, "ImageDataset", FakeDataset)
    monkeypatch.setattr(training, "DataLoader", lambda ds, **k: SimpleNamespace(dataset=ds))
    monkeypatch.setattr(training, "build_classifier", lambda *a, **k: nn.Linear(1, 7))
    monkeypatch.setattr(training, "train_epoch", lambda *a: (0.1, 0.9))
    monkeypatch.setattr(training, "evaluate", lambda *a: (0.05, list(range(7)), list(range(7))))
    monkeypatch.setattr(training, "save_curves", lambda *_: None)

    output_dir = tmp_path / "models/runs/incr-test"
    report_dir = tmp_path / "reports/runs/incr-test"

    result = training.run_training(argparse.Namespace(
        output_dir=str(output_dir.relative_to(tmp_path)),
        report_dir=str(report_dir.relative_to(tmp_path)),
        split_manifest="source_manifest.csv",
        smoke_test=False,
        smoke_samples_per_class=1,
        seed=17,
        batch_size=2,
        epochs=2,
        device="cpu",
        resume=False,
    ))

    assert result["training_status"] == "completed"
    assert result["epochs_completed"] == 2
    recovery_path = output_dir / "recovery_checkpoint.pt"
    assert recovery_path.is_file()
    recovery = torch.load(recovery_path, weights_only=False)
    assert recovery["completed_epoch"] == 2
    assert recovery["best_epoch"] in (1, 2)
    assert "model_state_dict" in recovery
    assert "optimizer_state_dict" in recovery
    assert "scheduler_state_dict" in recovery
    assert "rng_states" in recovery
    assert "python" in recovery["rng_states"]
    assert "numpy" in recovery["rng_states"]
    assert "torch" in recovery["rng_states"]
    assert recovery["class_ids"] == class_ids

    history_path = report_dir / "training_history.json"
    assert history_path.is_file()
    history = json.loads(history_path.read_text(encoding="utf-8"))
    assert len(history) == 2

    config_path = report_dir / "training_config.json"
    assert config_path.is_file()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["training_status"] == "completed"
    assert config["final_test_evaluation_required"] is True
    assert config["completed_epochs"] == 2


def test_training_resume_restores_complete_state_and_continues(tmp_path, monkeypatch):
    monkeypatch.setattr(training, "PROJECT_ROOT", tmp_path)
    class_ids = [f"class_{index}" for index in range(7)]
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    (config_dir / "dataset_config.yaml").write_text(
        "class_selection:\n  classes:\n" + "".join(f"    - id: {class_id}\n" for class_id in class_ids),
        encoding="utf-8",
    )
    (config_dir / "model_config.yaml").write_text(
        "model:\n"
        "  seed: 17\n  image_size: 224\n  batch_size: 2\n  pretrained: false\n"
        "  class_weighting: true\n  learning_rate: 0.001\n  weight_decay: 0.0\n"
        "  epochs: 2\n  early_stopping_patience: 3\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "source_manifest.csv"
    manifest.write_text("relative_path,class_id,partition,sha256,group_id,source_family_id\n", encoding="utf-8")

    records = {
        split: [SimpleNamespace(path=tmp_path / f"{split}_{i}.jpg", class_id=cid) for i, cid in enumerate(class_ids)]
        for split in ("train", "validation", "test")
    }
    monkeypatch.setattr(training, "plantvillage_records", lambda *_: [r for part in records.values() for r in part])
    monkeypatch.setattr(training, "load_grouped_manifest", lambda *a, **k: records)

    class FakeDataset:
        def __init__(self, recs, mapping, size, *, training, seed):
            self.records = recs
            self.training = training

        def __len__(self):
            return len(self.records)

    monkeypatch.setattr(training, "ImageDataset", FakeDataset)
    monkeypatch.setattr(training, "DataLoader", lambda ds, **k: SimpleNamespace(dataset=ds))
    monkeypatch.setattr(training, "build_classifier", lambda *a, **k: nn.Linear(1, 7))
    monkeypatch.setattr(training, "save_curves", lambda *_: None)

    epochs_trained = []

    def fake_train_epoch(_model, _loader, _opt, _loss, _dev):
        epochs_trained.append(len(epochs_trained) + 1)
        return 0.1, 0.9

    monkeypatch.setattr(training, "train_epoch", fake_train_epoch)
    monkeypatch.setattr(training, "evaluate", lambda *a: (0.05, list(range(7)), list(range(7))))

    output_dir = tmp_path / "models/runs/resume-test"
    report_dir = tmp_path / "reports/runs/resume-test"

    # Step 1: Run only 1 epoch out of 2 requested
    training.run_training(argparse.Namespace(
        output_dir=str(output_dir.relative_to(tmp_path)),
        report_dir=str(report_dir.relative_to(tmp_path)),
        split_manifest="source_manifest.csv",
        smoke_test=False,
        smoke_samples_per_class=1,
        seed=17,
        batch_size=2,
        epochs=1,
        device="cpu",
        resume=False,
    ))
    assert epochs_trained == [1]

    # Modify status to simulate an interrupted run before resume
    cfg = json.loads((report_dir / "training_config.json").read_text(encoding="utf-8"))
    cfg["training_status"] = "interrupted"
    cfg["final_test_evaluation_required"] = False
    (report_dir / "training_config.json").write_text(json.dumps(cfg), encoding="utf-8")

    # Step 2: Resume for 2 total epochs
    result = training.run_training(argparse.Namespace(
        output_dir=str(output_dir.relative_to(tmp_path)),
        report_dir=str(report_dir.relative_to(tmp_path)),
        split_manifest="source_manifest.csv",
        smoke_test=False,
        smoke_samples_per_class=1,
        seed=17,
        batch_size=2,
        epochs=2,
        device="cpu",
        resume=True,
    ))

    assert epochs_trained == [1, 2]
    assert result["epochs_completed"] == 2
    assert result["training_status"] == "completed"
    assert result["final_test_evaluation_required"] is True

    # Step 3: Attempting to resume an already completed run should fail
    with pytest.raises(ValueError, match="already completed"):
        training.run_training(argparse.Namespace(
            output_dir=str(output_dir.relative_to(tmp_path)),
            report_dir=str(report_dir.relative_to(tmp_path)),
            split_manifest="source_manifest.csv",
            smoke_test=False,
            smoke_samples_per_class=1,
            seed=17,
            batch_size=2,
            epochs=2,
            device="cpu",
            resume=True,
        ))


def test_evaluator_refuses_interrupted_run(tmp_path, monkeypatch):
    from scripts import evaluate_classifier

    monkeypatch.setattr(evaluate_classifier, "ROOT", tmp_path)
    monkeypatch.setattr(training, "PROJECT_ROOT", tmp_path)
    model_dir = tmp_path / "models/interrupted-run"
    report_dir = tmp_path / "reports/interrupted-run"
    output_dir = tmp_path / "reports/evaluations/interrupted-run"
    model_dir.mkdir(parents=True)
    report_dir.mkdir(parents=True)
    manifest = report_dir / "split_manifest.csv"
    manifest.write_text("metadata\n", encoding="utf-8")
    (report_dir / "training_config.json").write_text(json.dumps({
        "run_type": "full",
        "training_status": "interrupted",
        "final_test_evaluation_required": False,
        "model_output_dir": "models/interrupted-run",
        "split_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
    }), encoding="utf-8")

    monkeypatch.setattr("sys.argv", [
        "evaluate_classifier",
        "--model-dir", "models/interrupted-run",
        "--report-dir", "reports/interrupted-run",
        "--output-dir", str(output_dir),
    ])

    with pytest.raises(ValueError, match="completed full training run"):
        evaluate_classifier.main()


def test_evaluator_supports_custom_dataset_config_and_manifest_filtering(tmp_path, monkeypatch):
    import yaml
    from scripts import evaluate_classifier

    monkeypatch.setattr(evaluate_classifier, "ROOT", tmp_path)
    monkeypatch.setattr(training, "PROJECT_ROOT", tmp_path)

    parser = evaluate_classifier.make_parser()
    args_default = parser.parse_args([
        "--model-dir", "models/run-1",
        "--report-dir", "reports/run-1",
        "--output-dir", "reports/evaluations/run-1",
    ])
    assert args_default.dataset_config == "configs/dataset_config.yaml"

    model_dir = tmp_path / "models/run-1"
    report_dir = tmp_path / "reports/run-1"
    output_dir = tmp_path / "reports/evaluations/run-1"
    config_dir = tmp_path / "configs"
    model_dir.mkdir(parents=True)
    report_dir.mkdir(parents=True)
    config_dir.mkdir(parents=True)

    custom_cfg = config_dir / "dataset_config_custom.yaml"
    custom_cfg.write_text(yaml.dump({
        "version": 1,
        "class_selection": {
            "classes": [
                {"id": "cls_0", "crop": "Grape"},
                {"id": "cls_1", "crop": "Grape"},
            ]
        }
    }), encoding="utf-8")

    model_cfg = config_dir / "model_config.yaml"
    model_cfg.write_text(yaml.dump({
        "model": {"image_size": 224, "batch_size": 2}
    }), encoding="utf-8")

    manifest = report_dir / "split_manifest.csv"
    manifest.write_text(
        "relative_path,class_id,partition,sha256,group_id,source_family_id\n"
        "data/cls_0/img1.jpg,cls_0,test,hash1,g1,fam1\n",
        encoding="utf-8",
    )
    manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()

    (report_dir / "training_config.json").write_text(json.dumps({
        "run_type": "full",
        "training_status": "completed",
        "final_test_evaluation_required": True,
        "model_output_dir": "models/run-1",
        "split_manifest_sha256": manifest_sha,
    }), encoding="utf-8")

    (model_dir / "class_mapping.json").write_text(json.dumps({
        "class_to_index": {"cls_0": 0, "cls_1": 1},
        "index_to_class": ["cls_0", "cls_1"],
    }), encoding="utf-8")

    matching_rec = SimpleNamespace(path=tmp_path / "data/cls_0/img1.jpg", class_id="cls_0")
    unmanifested_rec = SimpleNamespace(path=tmp_path / "data/cls_0/img2_excluded.jpg", class_id="cls_0")
    monkeypatch.setattr(evaluate_classifier, "plantvillage_records", lambda _root, _cfg: [matching_rec, unmanifested_rec])

    passed_records = []
    def mock_load_manifest(records, manifest_p, project_r, *, verify_partitions):
        assert verify_partitions == ("test",)
        passed_records.extend(records)
        return {"test": [matching_rec], "train": [], "validation": []}

    monkeypatch.setattr(evaluate_classifier, "load_grouped_manifest", mock_load_manifest)
    monkeypatch.setattr(evaluate_classifier, "load_classifier", lambda *_: (nn.Linear(1, 2), ["cls_0", "cls_1"], "cpu"))
    monkeypatch.setattr(evaluate_classifier, "ImageDataset", lambda selected, *args, **kwargs: selected)
    monkeypatch.setattr(evaluate_classifier, "DataLoader", lambda dataset, *args, **kwargs: [dataset])
    monkeypatch.setattr(evaluate_classifier, "evaluate", lambda model, loader, device: (0.05, [0], [0]))

    monkeypatch.setattr("sys.argv", [
        "evaluate_classifier",
        "--model-dir", "models/run-1",
        "--report-dir", "reports/run-1",
        "--output-dir", "reports/evaluations/run-1",
        "--dataset-config", "configs/dataset_config_custom.yaml",
    ])

    evaluate_classifier.main()

    assert passed_records == [matching_rec]
    assert (output_dir / "evaluation_results.json").is_file()
    assert (output_dir / "confusion_matrix.csv").is_file()

