# Stage 20 — Classifier training and evaluation report

**Stage 20 status: STOPPED BEFORE TRAINING — original dataset split failed the exact-duplicate leakage gate.**  
**Audit date:** 2026-09-30

Stage 20B later created a replacement grouped manifest; see the [Stage 20B report](stage20b_leakage_safe_split_report.md). The Stage 20 training/evaluation outcome below remains unchanged: no model was trained or evaluated.

## Objective and decision

Stage 20 was intended to train the first full EfficientNet-B0 classifier and evaluate it on a clean, untouched holdout. The pre-training audit found exact duplicate images assigned across train/validation/test in the deterministic split. This makes the current holdout unsuitable for an honest independent evaluation. Following the Stage 20 stop condition, no sanity training batch, full training, candidate evaluation, PlantDoc evaluation, or artifact promotion was performed.

No production classifier was trained. `models/classifier/production/` remains absent. The existing smoke artifact was not used, copied, or reclassified as production. `/predict` therefore remains in its existing `model_unavailable` state when production assets are absent.

## Dataset and configured scope

The training adapter reads only the explicitly configured class folders at `data/PlantVillage/`; it does not recurse beyond each selected folder and does not read the nested `data/PlantVillage/PlantVillage/` tree. The requested `configs/classification_config.yaml` does not exist; the applicable settings are in `configs/dataset_config.yaml` and `configs/model_config.yaml`.

The seven configured classes are:

- `tomato_healthy`
- `tomato_bacterial_spot`
- `tomato_early_blight`
- `tomato_late_blight`
- `potato_healthy`
- `potato_early_blight`
- `potato_late_blight`

PlantVillage is the configured classification source. PlantSeg is not consumed by this classifier loader. PlantDoc remains external-only for five compatible disease classes. `scripts/validate_dataset_config.py` passed: seven configured class counts matched; 11,458 PlantSeg metadata rows were valid; five disease classes mapped to PlantDoc. The full command `python -m scripts.validate_datasets` also completed: all 41,276 PlantVillage images (including the nested tree), 814 PlantDoc images, 11,458 PlantSeg images, and 11,458 PlantSeg masks decoded; no unreadable files or missing image/mask pairs were reported. Fourteen raw PlantSeg dimension differences were aligned by EXIF orientation (zero oriented-dimension mismatches). These checks establish file/configuration consistency, not leakage freedom or annotation quality.

## Split inspected

The current split is generated at run time, not reused from a prior full-data manifest. With seed 42 and stratified per-class rounding at 15% validation and 15% test, the generated split contained:

| Class | Train | Validation | Test | Total |
|---|---:|---:|---:|---:|
| `tomato_healthy` | 1,113 | 239 | 239 | 1,591 |
| `tomato_bacterial_spot` | 1,489 | 319 | 319 | 2,127 |
| `tomato_early_blight` | 700 | 150 | 150 | 1,000 |
| `tomato_late_blight` | 1,337 | 286 | 286 | 1,909 |
| `potato_healthy` | 106 | 23 | 23 | 152 |
| `potato_early_blight` | 700 | 150 | 150 | 1,000 |
| `potato_late_blight` | 700 | 150 | 150 | 1,000 |
| **Total** | **6,145** | **1,317** | **1,317** | **8,779** |

These are counts from the deterministic split before deduplication and are **not a training manifest for a valid evaluation**. No split manifest was saved by this audit.

## Leakage audit

SHA-256 hashes were calculated for every selected image in the seven configured top-level class folders. The resulting 8,779 selected image records contained **14 exact-duplicate hash groups** (14 additional duplicate files). **Seven duplicate groups cross split boundaries**: four cross train/test, two cross train/validation, and one cross validation/test. Therefore a test image can have an identical byte-for-byte copy in training, and the current seeded split fails the independent-holdout requirement.

The cross-split duplicate groups, identified by their shared PlantVillage filename suffix, were:

| Class | Shared image/source suffix | Splits shared |
|---|---|---|
| `tomato_healthy` | `GH_HL Leaf 342.1.JPG` | validation, test |
| `tomato_healthy` | `GH_HL Leaf 434.JPG` | train, validation |
| `tomato_late_blight` | `GHLB2 Leaf 9011.JPG` | train, validation |
| `tomato_late_blight` | `GHLB_PS Leaf 24 Day 16.jpg` | train, test |
| `tomato_late_blight` | `GHLB_PS Leaf 23.7 Day 13.jpg` | train, test |
| `tomato_late_blight` | `GHLB2 Leaf 8999.JPG` | train, test |
| `tomato_late_blight` | `GHLB_PS Leaf 24 Day 13.jpg` | train, test |

The duplicated records have different UUID prefixes but identical file content. They are not merely similar-looking leaves. The remaining exact-duplicate groups were within one split each; that does not repair the cross-split leakage.

The selected-tree hash audit is decisive enough to stop this run. It did not complete a byte-level hash comparison of every file under the nested repeated PlantVillage tree. The full image validator observed 41,276 decodable PlantVillage files across the top-level and nested tree; the configured nested tree has repeated class labels and counts close to the selected tree, but byte identity across the complete nested tree was not established. No robust perceptual near-duplicate audit was run; the environment does not have `imagehash`. Filename/source-suffix review and exact hashes cannot rule out resized, recompressed, or sequentially captured related images across splits. PlantDoc compatibility and external evaluation were not attempted in this stage because no valid candidate checkpoint exists.

## Training and evaluation outcome

| Item | Outcome |
|---|---|
| Training sanity batch / finite loss and gradients | Not run; leakage gate failed first |
| Full EfficientNet-B0 training | Not run |
| Training configuration | Existing configuration inspected: ImageNet-pretrained EfficientNet-B0, 224 input, batch 32, up to 30 epochs, patience 5, learning rate 0.0003, weight decay 0.0001, class weights, seed 42, validation macro-F1 checkpoint selection |
| Best checkpoint | None produced in Stage 20 |
| Internal held-out test metrics | Not available; current split is leakage-contaminated |
| Per-class metrics and confusion matrix | Not produced |
| Confidence/probability summary | Not produced |
| Train/validation overfit assessment | Not produced |
| PlantDoc external evaluation | Not run |
| Candidate Grad-CAM verification | Not run; no candidate exists |
| Production artifact and hash | None; production directory remains absent |
| Real production inference / history model version | Not available; no prediction was submitted with a production model |

No classifier metrics are reported for Stage 20. The historical smoke run’s metrics remain pipeline-only and are not evidence about a production classifier.

## Artifact and implementation contract inspected

The existing inference loader expects `efficientnet_b0_best.pt` and `class_mapping.json`; the checkpoint stores `state_dict` and `class_ids`, and mapping consistency is checked before loading. Preprocessing applies EXIF orientation, RGB conversion, 224 resizing, ImageNet normalization, and no evaluation-time augmentation. Training-only augmentation is a seeded horizontal flip. Training computes class weights from the training split and selects by validation macro-F1.

The training CLI’s default output is `models/classifier/`, whereas inference defaults to the `models/classifier/production/` assets via application configuration. No artifact was placed at either path during this audit. A future run must save a reviewed candidate separately and must not make it available to inference until leakage and evaluation criteria are satisfied.

## Required work before restarting Stage 20 training

1. Review and independently verify the Stage 20B manifest, particularly the stated near-duplicate limits.
2. If training is separately authorized, use the configured full EfficientNet training path, which now requires and verifies the saved grouped manifest.
3. Evaluate the resulting candidate on the untouched manifest test partition and compatible external PlantDoc set; report real metrics and limitations.
4. Promote only a separately reviewed candidate whose mapping, preprocessing, checkpoint, and evaluation evidence agree.

## Validation status and scientific limitations

This report documents a pre-training integrity stop, not a failed model. No model quality conclusion can be drawn. Even after a clean split and successful metrics, those metrics alone will not establish agricultural diagnosis validity. Expert review, representative field data, severity validation, geographic review of recommendations, and operational validation remain distinct requirements.

The software regression quality gate passed after recording the finding: Python syntax validation **56 files**, Ruff passed, backend pytest **89 passed**, frontend Vitest **30 passed**, and Vite production build passed. The existing two third-party FastAPI/Starlette test-client deprecation warnings remain. Markdown relative-link validation passed for **24 documents**. The full dataset validator passed using its documented module invocation, `python -m scripts.validate_datasets`; invoking it as `python scripts/validate_datasets.py` instead fails because the `scripts` package is not on that invocation's import path. No coverage percentage was measured. These software checks do not validate classifier performance.

## Stage 20B follow-up — grouped split created

The original per-image split remains invalid. Stage 20B created `reports/data_manifest/plantvillage_classifier_split.csv` from 8,779 selected top-level images using groups formed by exact SHA-256, UUID-prefixed source-family suffixes, and the two conservative dHash candidates. The new 6,145/1,317/1,317 manifest was independently verified; all 8,763 groups remain partition-pure. The full nested tree was hashed: 20,638 files, 20,624 unique hashes, with 8,779 files matching the selected images' 8,765 unique hashes. No nested files were included.

The Stage 20B report documents the method, near-match paths, actual class counts, reproducibility checksum, independent verification, and limitations. Stage 20B performed no training, classifier evaluation, PlantDoc evaluation, checkpoint creation, Grad-CAM candidate check, or model promotion. Production inference remains unavailable. The next task within Stage 20 is training/evaluation only after the grouped manifest has been reviewed and training is authorized.
