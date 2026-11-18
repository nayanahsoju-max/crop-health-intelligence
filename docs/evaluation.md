# Classification evaluation

## Evaluation roles

**Stage 20/20B status:** no production candidate was trained or evaluated. Stage 20 stopped when exact duplicates crossed the original split. Stage 20B created and independently verified a grouped manifest that keeps detected exact hashes, source-family groups, and dHash candidates in one partition. The old split is invalid; the new split is ready for a separately authorized training continuation. No classifier metrics are available. See the [Stage 20 report](stage20_classifier_training_report.md) and [Stage 20B report](stage20b_leakage_safe_split_report.md). Do not interpret the historical smoke results below as full-model results.

- The classifier training pipeline creates an internal PlantVillage test holdout from one selected class tree.
- PlantDoc remains a separate external dataset. The smoke checkpoint was run through the compatible PlantDoc test-set evaluation path below; this is only a pipeline check. Full production evaluation remains outstanding, after label compatibility and split isolation checks.
- The smoke-run metrics below verify the pipeline; they do not estimate generalization or constitute final project results.

## Actual smoke-run metrics

Run: one epoch of pretrained EfficientNet B0 fine-tuning on 28 PlantVillage images (four per class); 14 train, 7 validation, 7 test. Each test class has support 1.

| Metric | Measured value |
|---|---:|
| Accuracy | 0.1429 |
| Macro precision | 0.0286 |
| Macro recall | 0.1429 |
| Macro F1 | 0.0476 |
| Validation macro F1 (one epoch) | 0.0952 |

The single correct test prediction was for `potato_late_blight`. All class-level metrics are based on one test image per class, and the untrained classification head had only one epoch to adapt. These figures are pipeline smoke results only and should not be compared to published model performance.

Full dataset training and internal metrics remain to be run on suitable compute. PlantDoc was checked later with the same smoke checkpoint; that separate result is recorded below. The exact internal smoke outputs, confusion matrix, training curve, and inference check are in `reports/classification/smoke/`.

## Actual PlantDoc smoke-model external check

The external evaluator used only PlantDoc's supplied `test/` folders for the five configured compatible disease classes. It did not read PlantDoc's `train/` folder. The evaluated model was the one-epoch smoke checkpoint trained on 28 PlantVillage images, so these results verify the external evaluation path and do not estimate the final classifier's real-world performance.

| Metric | Measured value |
|---|---:|
| Accuracy (all 44 mapped test images) | 0.1818 |
| Macro precision (five mapped disease classes) | 0.3820 |
| Macro recall (five mapped disease classes) | 0.1794 |
| Macro F1 (five mapped disease classes) | 0.2012 |

| PlantDoc test class | Support |
|---|---:|
| Tomato bacterial spot | 9 |
| Tomato early blight | 9 |
| Tomato late blight | 10 |
| Potato early blight | 8 |
| Potato late blight | 8 |

The metrics have small per-class support, omit no mapped disease class, and do not cover either healthy class. Twenty-eight other PlantDoc test images were unsupported or label-mismatched: `Bell_pepper leaf` (8), `Bell_pepper leaf spot` (9), and `Tomato Septoria leaf spot` (11). The Septoria label is excluded pending audit because early-blight-named files appear in its PlantDoc training folder. The exact results, unsupported labels, confusion matrix, and per-image predictions are in `reports/classification/external_plantdoc_smoke/`.

These PlantDoc values are separate from the internal PlantVillage smoke results above. Full model training and a final external generalization evaluation remain to be run.
