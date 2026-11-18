# GVLiD v5 Dataset Acquisition and Validation Report

**Status:** Acquired and extracted for audit; not merged into any classifier dataset. The source contains significant duplicate and label-metadata integrity issues. Do not use for training until these are reviewed and the future grouped split accounts for all duplicate groups.

**Audit date:** 2026-11-15 (Asia/Kolkata, UTC+05:30)

## Source and provenance

- **Source:** [GVLiD: GrapeVine Leaf identification of the Diseases, Mendeley Data v5](https://data.mendeley.com/datasets/wkymf8bhcg/5)
- **Version/DOI:** Version 5; DOI `10.17632/wkymf8bhcg.5` (record published 2026-04-06).
- **License:** CC BY 4.0, stated on the Mendeley record and in the preserved `DATASET/license.txt`.
- **Downloaded archive:** `C:\Users\ASUS\Downloads\GVLiD GrapeVine Leaf identification of the Disease.zip`
- **Observed local file timestamp:** 2026-11-15 22:05:23 +05:30. This is the filesystem timestamp and is used as the acquisition-date proxy.
- **Downloaded ZIP size:** 901,747,958 bytes.
- **Downloaded ZIP SHA-256:** `7A83CD28A8342683E8715D9295EDBD5EACA46939CBB65EAE4CE02D87C548E16B`.
- **Nested archive:** ZIP contains one entry, `GVLiD GrapeVine Leaf identification of the Disease/GVLiD.rar` (902,251,054 bytes); SHA-256 `3C867EE21E799FC6A695917A1281E3E7190ED49AC7C74F8FCB98308091EAA76F`.
- The original ZIP remains unchanged in Downloads. The extracted copy is at `data/GVLiD-v5/DATASET/`. The RAR listing contained no absolute or parent-traversal paths. The extracted 3,488 files exactly matched the RAR listing; extraction completed without an error.

The archive layout, four grape class folders, 3,477 image records, and vineyard metadata are consistent with the Mendeley GVLiD record. The package itself does not contain an explicit version or DOI marker, so v5 provenance is supported by the approved Mendeley download, filename, and content, rather than a version identifier embedded inside the RAR.

## Preserved source content

Original class folder names were retained:

| Original folder | Project canonical label | Images |
|---|---|---:|
| `healthy` | `grape_healthy` | 1,109 |
| `Black rot` | `grape_black_rot` | 808 |
| `esca` | `grape_esca` | 888 |
| `leaf blight` | `grape_leaf_blight` | 672 |
| **Total** |  | **3,477** |

The folders were not renamed, and no images were merged or altered. Source materials retained under `data/GVLiD-v5/DATASET/` include `metadata.json`, `README.md`, `license.txt`, `desktop.ini`, and the original `docs/` files: `annotation_guidelines.md`, `checksums.txt`, `dataset_statistics.csv`, `data_collection_protocol.md`, `metadata_completeness.csv`, `metadata_completeness.txt`, and `preprocessing_pipeline.md`.

The README contains a citation line naming “Gayakwad M. et al.”, which does not match the Mendeley v5 record contributors (Anisa Shikalgar, Ayush Savalkar, Avishkar Bhasme, Snehal Chavan, and Vaishnavi Nikam). It also refers to `images/` and `metadata.csv`, while this archive has class folders and `metadata.json`. The embedded README was preserved; cite the Mendeley record/DOI pending clarification from the dataset authors.

## Image validation and count discrepancy

- **Images found:** 3,477.
- **Readable:** 3,477 (Pillow `verify()` followed by full image `load()`).
- **Unreadable/corrupt:** 0.
- **Image filename metadata:** 3,477 distinct metadata filenames; all 3,477 resolve to an extracted image.
- **Folder count sum:** 1,109 + 808 + 888 + 672 = **3,477**. This agrees with the Mendeley v5 record and README total.

The 3,478 figure is not supported by the extracted files. A reported distribution of 809 Black rot + 888 Esca + 672 leaf blight + 1,109 Healthy would produce 3,478; the archive contains 808 Black rot images. The bundled metadata independently has 3,477 rows, but its disease-label counts are Black Rot 809, Esca 888, Healthy 1,109, and Leaf Blight 671. These counts differ from the folder counts. The archive therefore resolves the total as 3,477 actual files, but does not resolve which conflicting class assignments are intended ground truth.

## Vineyard and metadata audit

- `metadata.json` was preserved without rewriting.
- All 3,477 records have a unique `image_filename` matching an extracted file.
- 28 distinct vineyard identifiers (`Vineyard_1` through `Vineyard_28`) are present; no record lacked a vineyard ID in this audit.
- The source-family information should remain available for future splitting. However, exact duplicate images frequently carry different vineyard IDs: **437 of 446 exact-duplicate groups span multiple vineyard IDs**. Vineyard IDs alone therefore do not safely group the duplicate copies; future grouping must union exact-image matches with vineyard/source-family groups.

### Folder labels versus `metadata.json` disease labels

There are **1,344 of 3,477 records (38.7%)** where `Disease_Type` does not match the containing class folder:

| Folder | Metadata `Disease_Type` | Records |
|---|---|---:|
| `healthy` | `Healthy` | 438 |
| `healthy` | `Leaf Blight` | 671 |
| `Black rot` | `Black Rot` | 808 |
| `esca` | `Esca` | 887 |
| `esca` | `Black Rot` | 1 |
| `leaf blight` | `Healthy` | 671 |
| `leaf blight` | `Esca` | 1 |

The 671 `healthy` images labeled `Leaf Blight` and 671 `leaf blight` images labeled `Healthy` indicate a large folder/metadata disagreement; the two additional records also disagree individually (`esca001.jpg` is metadata-labeled Black Rot; `leaf blight001.jpg` is metadata-labeled Esca). Do not select one label source silently. Label authority needs review before training or class mapping.

The bundled `docs/dataset_statistics.csv` reports Black_Rot 800, Esca 900, Leaf_Blight 877, Healthy 900, which does not match either the image-folder counts or metadata counts. `docs/metadata_completeness.txt` reports completeness but does not establish label correctness. `docs/checksums.txt` lists five MD5 entries for filenames such as `BR_001.jpg` and `HL_001.jpg`; none of those filenames exists in the extracted class folders, so the supplied checksum entries cannot validate this image payload. These source files were preserved unchanged.

## Exact duplicate and overlap audit

SHA-256 was calculated for every GVLiD image and compared with the images under these existing local dataset paths:

| Existing source | Files hashed |
|---|---:|
| PlantVillage (`data/PlantVillage/`, recursive) | 41,276 |
| PlantSeg images (`data/plantsegv3/images/`) | 11,458 |
| PlantSeg annotation masks (`data/plantsegv3/annotations/`) | 11,458 |
| PlantDoc (`data/PlantDoc-Selected/`, recursive) | 814 |

- **GVLiD exact SHA-256 matches against existing sources:** 0 across PlantVillage, PlantSeg source images, PlantSeg annotation masks, and PlantDoc. PlantSeg annotation-mask files were separately hashed (11,458 masks); no exact or dHash near-candidate overlap was found.
- **GVLiD exact duplicate groups internally:** 446 groups; 1,514 image files are members; 1,068 files are excess copies beyond one unique file per group. Only 2,409 unique SHA-256 image contents remain among the 3,477 files.
- Internal exact-duplicate group composition: 97 groups within `Black rot`, 16 within `healthy`, 331 within `leaf blight`, and 2 cross-class groups (`Black rot` and `esca`).
- The two cross-class exact duplicate conflicts are: `Black rot/black rot793.jpg`–`black rot800.jpg` and `esca/esca002.jpg`; and `Black rot/black rot801.jpg`–`black rot808.jpg` and `esca/esca248.jpg`. In each set, all listed files have identical SHA-256 bytes despite different class folders. Treat these as label conflicts pending review.

A 64-bit grayscale difference-hash (dHash) screen produced **385 internal GVLiD candidate pairs** at Hamming distance ≤4 (291 at 0, 78 at 1, 10 at 2, 4 at 3, and 2 at 4). These pairs are candidates only; perceptual hashes can collide, and they were not manually confirmed as the same leaf/source. They cross class folders, so review them before splitting. No cross-dataset dHash candidate was found at that threshold. The dHash screen is a heuristic, not proof that all near-duplicate leakage has been eliminated; exact SHA comparison is definitive only for byte-identical files.

The dHash candidate listing is provided in `reports/gvlid_v5_near_duplicate_candidates.csv`. Every image’s SHA-256 and dHash, metadata image ID, vineyard ID, and metadata class are recorded in `reports/gvlid_v5_hash_inventory.csv`.

## Readiness and limitations

GVLiD v5 is acquired and safely extracted, but it is **not ready to be merged or used for classifier training** without review. The actual image count is 3,477, all images load, and there is no exact-hash overlap with the three existing datasets. However, extensive repeated images, cross-class byte-identical images, a high metadata/folder label disagreement rate, stale statistics/checksum documentation, and multiple vineyard IDs assigned to exact duplicates create substantial data-quality and leakage risks. Preserve `Vineyard` metadata and group by both vineyard/source family and duplicate cluster in the future grouped split. Near-duplicate review remains heuristic and incomplete.

No model was trained. No source code, application, configuration, database schema, or existing dataset was changed. The original seven-class manifest remains unchanged and its SHA-256 still matches the recorded value `40b08f14a9085b26004633fb9123159766ba795892bc6afc483a3f4e76de64bc`.


