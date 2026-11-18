# Dataset analysis and proposed class set

Analysis date: 2026-09-29. Counts below were read from the files in this checkout. The reproducible inventory is `scripts/dataset_inventory.py`; the full per-class/per-split count export is [`reports/dataset_class_counts.csv`](../reports/dataset_class_counts.csv). A tiny one-epoch smoke run was performed only to validate the pipeline; full configured model training has not been run (see [evaluation notes](evaluation.md)).

## Observed locations and structure

| Dataset | Actual path | Structure and supplied split |
|---|---|---|
| PlantVillage | `data/PlantVillage/` | Fifteen class directories at the root, plus a second `PlantVillage/` directory containing the same fifteen class names with the same per-class image counts. There is no supplied train/validation/test split. Treat the nested tree as a second extraction/mirror and use only one tree; exact duplicate bytes have not been hash-verified. |
| PlantSeg v3 | `data/plantsegv3/` | `images/{train,val,test}`, paired `annotations/{train,val,test}` PNGs, `Metadatav2.csv`, and COCO-like JSON annotation files. Metadata split counts agree with the JSON image counts. |
| PlantDoc-Selected | `data/PlantDoc-Selected/` | Eight class folders under each of `train/` and `test/`; no validation directory. Keep this dataset separate from training. |

The requested canonical paths `data/plantvillage`, `data/plantseg`, and `data/plantdoc` do not exist. The discovered paths and case are recorded in `configs/dataset_config.yaml`; nothing has been renamed or copied.

## Dataset statistics

### PlantVillage

The selected primary tree has 15 classes and 20,638 images. The second nested tree repeats those class names and per-class counts, giving 41,276 decodable image files when both trees are recursively counted. The class inventory below is for one tree only; do not combine the two trees without a duplicate/leakage audit.

| Folder label | Images |
|---|---:|
| `Pepper__bell___Bacterial_spot` | 997 |
| `Pepper__bell___healthy` | 1,478 |
| `Potato___Early_blight` | 1,000 |
| `Potato___healthy` | 152 |
| `Potato___Late_blight` | 1,000 |
| `Tomato_Bacterial_spot` | 2,127 |
| `Tomato_Early_blight` | 1,000 |
| `Tomato_healthy` | 1,591 |
| `Tomato_Late_blight` | 1,909 |
| `Tomato_Leaf_Mold` | 952 |
| `Tomato_Septoria_leaf_spot` | 1,771 |
| `Tomato_Spider_mites_Two_spotted_spider_mite` | 1,676 |
| `Tomato__Target_Spot` | 1,404 |
| `Tomato__Tomato_mosaic_virus` | 373 |
| `Tomato__Tomato_YellowLeaf__Curl__Virus` | 3,208 |

PlantVillage images are 41,272 `.jpg`, 2 `.jpeg`, and 2 `.png` per both-tree recursive count; all decoded successfully and measured 256×256. It has no on-disk train/test/validation organization. Counts for the one selected tree are in the table; the CSV also records both folder trees.

### PlantSeg v3

The metadata contains 115 crop/disease labels and 11,458 images: 7,916 training, 1,247 validation, and 2,295 test. There are 11,458 PNG mask files with matching stems. COCO-like JSON counts are 7,916/52,898 images/annotations for train, 1,247/8,927 for validation, and 2,295/15,569 for test. The JSON `categories` lists are empty while polygon annotations use `category_id: 0`; this schema detail must be handled explicitly by any later parser rather than treating the JSON as a standard categorized COCO file.

The filename/mask pairing check found no missing pairs and no unreadable image or mask. Fourteen stored image dimensions differ from their mask dimensions; each difference is explained by the image EXIF orientation (rotating the stored dimensions makes them agree). Validation must apply EXIF orientation consistently before resizing or comparing against masks. After orientation, the check found zero dimension mismatches.

PlantSeg images use `.jpg`; masks use `.png`. Across each type, observed dimensions range from 65×52 to 8,256×5,504. All images and masks decoded successfully. The complete set of 115 labels and exact train/validation/test counts is in `reports/dataset_class_counts.csv`.

### PlantDoc-Selected

PlantDoc has 8 labels, 742 training images and 72 test images (814 total); there is no validation split. The class inventory is:

| Folder label | Train | Test | Total |
|---|---:|---:|---:|
| `Bell_pepper leaf` | 53 | 8 | 61 |
| `Bell_pepper leaf spot` | 62 | 9 | 71 |
| `Potato leaf early blight` | 109 | 8 | 117 |
| `Potato leaf late blight` | 97 | 8 | 105 |
| `Tomato Early blight leaf` | 79 | 9 | 88 |
| `Tomato leaf bacterial spot` | 101 | 9 | 110 |
| `Tomato leaf late blight` | 101 | 10 | 111 |
| `Tomato Septoria leaf spot` | 140 | 11 | 151 |

PlantDoc files are 813 `.jpg` and 1 `.png`, with observed dimensions from 143×137 to 6,000×4,000. All 814 decoded successfully. The supplied test set is small, so any external class metrics will have substantial sampling uncertainty.

## Compatibility and proposed scope

PlantVillage labels are matched to the closest crop/disease labels in the other datasets only where the crop and disease meaning align. Similar wording alone is not treated as proof of compatibility. “Severity possible” means a PlantSeg lesion annotation/mask exists; later leaf-area estimation still needs validation. PlantDoc is used only as a held-out external dataset.

| Crop | Disease/class | PlantVillage count | PlantSeg images / masks | PlantDoc count (train + test) | Classification possible | Severity possible | External testing possible |
|---|---|---:|---:|---:|---|---|---|
| Tomato | Healthy | 1,591 | No healthy class | None | Yes, PlantVillage only | No | No |
| Tomato | Bacterial spot | 2,127 | 109 / yes | 110 (`Tomato leaf bacterial spot`) | Yes | Yes | Yes, small test n=9 |
| Tomato | Early blight | 1,000 | 187 / yes | 88 (`Tomato Early blight leaf`) | Yes | Yes | Yes, small test n=9 |
| Tomato | Late blight | 1,909 | 163 / yes | 111 (`Tomato leaf late blight`) | Yes | Yes | Yes, small test n=10 |
| Potato | Healthy | 152 | No healthy class | None | Yes, PlantVillage only; underrepresented | No | No |
| Potato | Early blight | 1,000 | 126 / yes | 117 (`Potato leaf early blight`) | Yes | Yes | Yes, small test n=8 |
| Potato | Late blight | 1,000 | 117 / yes | 105 (`Potato leaf late blight`) | Yes | Yes | Yes, small test n=8 |

This is the proposed seven-class classifier: two crop-specific healthy labels and five shared disease labels. Healthy classes are PlantVillage-only; do not claim PlantDoc or PlantSeg coverage for them. Potato healthy has only 152 images and needs explicit imbalance handling and careful per-class evaluation.

### Classes excluded from the final set

- **Tomato Septoria leaf spot:** Present in PlantVillage (1,771) and PlantSeg (130 masks), and has a nominal PlantDoc class (151 total). A filename inspection found four early-blight-named images inside the PlantDoc Septoria training folder, including `confused-early-blight-septoria-zoom.jpg`, `early-blight-septoria-ls-fig-3.jpg`, and `tomato-early-blight-e1437503226856.jpg` (filename evidence is a warning signal, not a content-level diagnosis). Because the small external reference class appears contaminated, exclude it from the initial final set until the folder is manually audited. Do not report Septoria external performance as valid without that audit.
- **Bell pepper bacterial spot:** PlantVillage has 997 images and PlantSeg has 76 masks, but PlantDoc calls its closest class `Bell_pepper leaf spot` (71 images), a broader label; visible filenames also suggest the folder may include other conditions. Do not merge these labels as if equivalent.
- **Other PlantVillage tomato diseases** (leaf mold, spider mites, target spot, mosaic virus, yellow leaf curl virus) lack PlantDoc counterparts in this checkout, so they do not support a compatible PlantDoc external test set.
- **Other PlantSeg crops/diseases** lack a PlantVillage classification class in this checkout and are outside the proposed classifier scope.

The exclusions are based on the actual folders, metadata, and label wording in this checkout. Filename checks identify audit targets, not proof of a biological diagnosis.

## File integrity, naming, and limitations

- Programmatically decoded all recognized image files using Pillow: zero unreadable files in either PlantVillage tree (41,276 files total), PlantSeg images and masks (22,916 files), and PlantDoc (814 files).
- PlantVillage class folders have no explicit split; a deterministic split must be created later from one selected tree only.
- PlantSeg uses crop names such as `Bell pepper` and disease strings such as `tomato bacterial leaf spot`, unlike PlantVillage's underscore-based folder labels. PlantDoc has its own natural-language labels. Use the explicit mapping in the config; do not infer labels from common words.
- PlantSeg's disease-region masks do not by themselves give a total leaf-area denominator. Severity will need a separate leaf-area estimate, and the configured thresholds will require domain validation.
- PlantDoc label noise is a risk, especially for the Septoria class; PlantDoc remains external and will not be merged into model training.
- The outer/nested PlantVillage trees have matching class names and counts, but exact file-content identity has not been hash-verified. Select one tree and check for leakage before training.
- Dataset counts and successful file decoding establish file readability, not label correctness, representativeness, or expected model performance.

## Stage 1 decision

The checked-out datasets support a manageable shared disease set for Tomato and Potato, plus PlantVillage-only healthy classes. The seven proposed model classes and explicit source-label mappings are recorded in `configs/dataset_config.yaml`. This completes class selection only; no training is authorized or started before subsequent preprocessing and validation stages.
