# Classifier training

## Pipeline

The classifier uses torchvision EfficientNet B0 with the ImageNet pretrained weights, replaces the final layer with the seven configured outputs, and fine-tunes the network. Dataset records come only from the selected primary PlantVillage class folders. PlantDoc is never read by the training script.

The full-data split is a saved group-aware manifest with seed 42 and configured validation/test targets of 15% each. It keeps exact hashes, UUID-prefixed source families, and reviewed low-distance perceptual-hash candidates together. Training validates manifest structure and hashes only train and validation images. It does not read, hash, decode, load, or iterate over test images. Train records receive seeded horizontal flips only; validation uses the same EXIF-aware resize and ImageNet normalization without augmentation. Cross-entropy class weights are calculated from the training split. AdamW, a validation macro-F1 learning-rate scheduler, early stopping, and best-validation-F1 checkpointing are configured.

Final test evaluation is a separate command run only after training and checkpoint selection finish. It uses the manifest copy and checksum saved with that run, verifies the test-image hashes at evaluation time, and writes results to a fresh evaluation directory.

## Commands

Run a small, one-epoch training/validation smoke check. It does not access its held-out test records and is not a model-performance evaluation. Choose new, unused run directories each time:

```powershell
python -m crop_health.classification.training --smoke-test `
  --output-dir models/classifier/runs/smoke-2026-11-17-a `
  --report-dir reports/classification/runs/smoke-2026-11-17-a
```

Run full configured training on suitable compute with fresh run-specific directories:

```powershell
$env:PYTHONPATH = "src;."
python -m crop_health.classification.training `
  --device cpu `
  --output-dir models/classifier/runs/tomato-potato-2026-11-17-b `
  --report-dir reports/classification/runs/tomato-potato-2026-11-17-b
```

The training pipeline is restart-resilient:
- After every completed epoch, it writes a comprehensive recovery checkpoint (`recovery_checkpoint.pt`) containing model state, optimizer state, LR scheduler state, completed epoch, best validation macro-F1, best epoch, early-stopping counter, and Python/NumPy/PyTorch RNG states.
- It also flushes `training_history.json`, updates `training_config.json` (`training_status: in_progress`), and updates `training_curves.png` after every epoch.
- If a run is interrupted (e.g. by server restart), `training_status` remains `in_progress` or `interrupted`, and `final_test_evaluation_required` remains `false`.
- To safely resume an interrupted run from its last completed epoch:

```powershell
$env:PYTHONPATH = "src;."
python -m crop_health.classification.training `
  --resume `
  --device cpu `
  --output-dir models/classifier/runs/tomato-potato-2026-11-17-b `
  --report-dir reports/classification/runs/tomato-potato-2026-11-17-b
```

The resume command verifies the directory and recovery checkpoint exist, restores all weights, optimizer, scheduler, and RNG states, and continues training from the next epoch until completion or early stopping. Attempting to resume an already completed run is rejected. Existing destinations for fresh runs are refused to preserve prior runs (such as `tomato-potato-2026-11-17-a`). No test metrics are produced by training.

The old per-image split is invalid and must not be used. Stage 20B created a grouped manifest. To regenerate and verify it without training, run:

```powershell
python -m scripts.create_leakage_safe_split
python -m scripts.verify_leakage_safe_split
```

The full training command will require and verify `reports/data_manifest/plantvillage_classifier_split.csv`. Stage 20B did not authorize or perform training; see the [split report](stage20b_leakage_safe_split_report.md).

After reviewing the completed run and selecting its checkpoint, invoke final test evaluation separately. The evaluation output directory must also be new and unused:

```powershell
python -m scripts.evaluate_classifier `
  --model-dir models/classifier/runs/tomato-potato-2026-11-17-b `
  --report-dir reports/classification/runs/tomato-potato-2026-11-17-b `
  --output-dir reports/classification/evaluations/tomato-potato-2026-11-17-b
```

Evaluation refuses smoke runs, mismatched model/run configurations, modified run manifests, and existing output directories. It is the only training-pipeline command that reads test-image contents.

## Smoke-run status

The available execution environment has PyTorch 2.14.0 CPU-only and no CUDA device. Full training was not attempted. A transfer-learning smoke run used the official pretrained EfficientNet B0 weights for one epoch on four images per class (28 total), split into 14 train, 7 validation, and 7 test examples. This run checks data loading, training, checkpoint save/load, metrics, and inference; it is not a model-performance estimate.

Smoke artifacts are stored in the explicitly selected fresh run directories. No smoke test accuracy or other test metric is generated by training. No PlantDoc images were used.
