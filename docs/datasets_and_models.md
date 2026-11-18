# Datasets and models

This document describes what is configured and what was actually run. The production classifier has not been trained; the configured class set is not evidence of model performance.

## Dataset roles and on-disk layout

Paths and label mappings are recorded in `configs/dataset_config.yaml`; detailed audit counts and exclusions are in [dataset analysis](dataset_analysis.md). The data itself is locally supplied and may not be present in a clean clone.

### PlantVillage: classification source

The current adapter expects one selected class-folder tree rooted at `data/PlantVillage/`:

```text
data/PlantVillage/
  Tomato_healthy/
    <image files>
  Tomato_Bacterial_spot/
    <image files>
  ...
```

The seven explicitly mapped PlantVillage folders and expected counts are in `configs/dataset_config.yaml`. The checked-out data audit found a nested second tree repeating class labels/counts; `plantvillage_records` reads only configured root class folders, not the nested duplicate tree. File counts are checked against configuration. Do not merge both trees without a duplicate/leakage audit.

### PlantSeg v3: lesion-mask severity source

The adapter reads `data/plantsegv3/Metadatav2.csv`, paired images under `images/{train,val,test}/`, and masks under `annotations/{train,val,test}/`. Its lesion-region masks support the current optional severity estimator, not the seven-class training data loader. Annotations mark diseased regions and do not provide a complete leaf silhouette.

### PlantDoc-Selected: external evaluation only

PlantDoc is configured under `data/PlantDoc-Selected/` with its supplied `train/` and `test/` folders. The configured evaluator reads only compatible classes from its `test/` split. PlantDoc's training folders must not be used to train this classifier. Only five disease labels map to the current class scope; healthy classes have no PlantDoc coverage. Septoria and broad pepper leaf-spot labels were excluded following the documented compatibility audit.

## Project classification labels

The current seven configured labels are:

| Class ID | Meaning | Dataset coverage note |
| --- | --- | --- |
| `tomato_healthy` | Tomato healthy-status label | PlantVillage only. |
| `tomato_bacterial_spot` | Tomato bacterial spot | PlantVillage, compatible PlantSeg masks, and mapped PlantDoc test subset. |
| `tomato_early_blight` | Tomato early blight | PlantVillage, compatible PlantSeg masks, and mapped PlantDoc test subset. |
| `tomato_late_blight` | Tomato late blight | PlantVillage, compatible PlantSeg masks, and mapped PlantDoc test subset. |
| `potato_healthy` | Potato healthy-status label | PlantVillage only; only 152 examples in the recorded audit. |
| `potato_early_blight` | Potato early blight | PlantVillage, compatible PlantSeg masks, and mapped PlantDoc test subset. |
| `potato_late_blight` | Potato late blight | PlantVillage, compatible PlantSeg masks, and mapped PlantDoc test subset. |

These are the configured/project classes, not a claim that a trained model recognizes them reliably. The config status remains proposed after dataset inspection; any future scope changes require label/source review.

## Preprocessing and split design

`preprocess_classification_image` applies EXIF orientation, decodes RGB, resizes to the configured `224 × 224`, scales to `[0,1]`, then applies ImageNet channel mean/std normalization. Training can apply a seeded horizontal flip; validation, test, and inference are deterministic and do not augment.

PlantVillage has no supplied train/validation/test split. The original per-image stratified split was replaced for full training by a saved, deterministic, group-aware manifest generated with seed `42` and configured 70/15/15 targets. The full training path integrity-checks and loads this manifest; it no longer silently regenerates the old per-image split. PlantDoc remains a separate external check and is not used for fit/tuning.

**Stage 20B split:** The original seed-42 split had 14 exact-duplicate groups, seven crossing partitions; Stage 20 therefore stopped before training. Stage 20B produced a new manifest grouping exact hashes, UUID-prefixed source-family suffixes, and conservative dHash matches. Independent checks confirm no grouped identifier crosses partitions and every configured class occurs in train, validation, and test. See the [Stage 20B report](stage20b_leakage_safe_split_report.md) and machine-readable [split summary](../reports/data_manifest/plantvillage_split_summary.json). Near-duplicate methods can miss transformations, so this is not a guarantee of complete source independence. No classifier training or evaluation has been performed.

The full dataset validator (`python -m scripts.validate_datasets`) subsequently decoded 41,276 PlantVillage files across both trees, 814 PlantDoc files, and all 11,458 PlantSeg image/mask pairs without unreadable files or missing pairs. Fourteen raw PlantSeg image/mask dimensions differed, but EXIF orientation yielded zero oriented-size mismatches. This image-integrity check does not remove the duplicate leakage finding.

## Model and configured training

`configs/model_config.yaml` specifies torchvision EfficientNet-B0 with ImageNet pretrained weights, a replacement output layer for seven labels, image size 224, batch size 32, 30 maximum epochs, early stopping patience 5, learning rate `0.0003`, weight decay `0.0001`, class weighting, seed 42, and best checkpoint selection by validation macro-F1. These are configured defaults; a full training run has not been performed.

## Smoke test: pipeline check only

The smoke command samples four images per class and trains for one epoch:

```powershell
python -m crop_health.classification.training --smoke-test `
  --output-dir models/classifier/smoke `
  --report-dir reports/classification/smoke
```

The recorded run had 28 images total (4 × 7), split into 14 training, 7 validation, and 7 test images. It reported test accuracy **0.1429** and macro-F1 **0.0476**. The test holdout had just one image per class. These numbers verify that training/checkpoint/evaluation code executed; they are not a performance estimate, final result, or evidence of a useful diagnosis model. The smoke checkpoint and mapping under `models/classifier/smoke/` are explicitly rejected by `POST /predict`.

The separate recorded PlantDoc smoke evaluation in [evaluation notes](evaluation.md) also used that smoke checkpoint. It is an external-evaluation-path check, not production performance. Do not combine the smoke metrics with claims about a production model.

## Production model work still required

Before enabling real inference:

1. Confirm dataset provenance, licensing, label quality, exact class folders, and the nested PlantVillage duplicate/leakage risk.
2. Reassess class balance and label compatibility, especially the limited `potato_healthy` support; preserve PlantDoc as external data.
3. Re-run `python -m scripts.create_leakage_safe_split` and `python -m scripts.verify_leakage_safe_split`; review the saved grouped split and known perceptual-hash limitations before authorizing training.
4. After training is authorized, run the configured full training on suitable compute and evaluate on the untouched internal holdout plus a carefully interpreted compatible PlantDoc subset. Report per-class support/metrics and limitations.
5. Have domain reviewers assess whether the data and intended use support the proposed claims.
6. Place only the separately reviewed model checkpoint and its matching `class_mapping.json` at the configured production paths (`models/classifier/production/` by default), and set `CROP_HEALTH_MODEL_CHECKPOINT`, `CROP_HEALTH_CLASS_MAPPING`, and `CROP_HEALTH_MODEL_VERSION` as appropriate.
7. Verify inference and explainability with the real artifact before describing model readiness. Never copy the smoke artifact into the production directory.

The current API requires both assets and returns `model_unavailable` if they are missing or smoke paths. This documentation task did not train, promote, or evaluate a production model.

## Severity inputs and validation

Severity is a separate estimate, not a classifier output. The current API accepts an optional PNG lesion mask that must align with the uploaded leaf image after orientation. The estimator uses its lesion-positive pixels and an HSV/morphology estimate of visible leaf area:

```text
severity percentage = diseased area / estimated total leaf area × 100
```

The demonstration thresholds in `configs/severity_config.yaml` map `<10%` to Mild, `10%–<30%` to Moderate, and `≥30%` to Severe. They are configurable and not universal agricultural thresholds. Without a mask the result is `not_requested`. There is no expert-scored field dataset validating the leaf-area estimate, percentages, or categories; these values must not be presented as validated severity predictions.
