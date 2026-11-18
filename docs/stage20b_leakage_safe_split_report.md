# Stage 20B — Leakage-safe classifier split report

**Status: COMPLETE — split created and independently verified.**  
**Dataset:** selected top-level PlantVillage classifier folders  
**Seed:** 42  
**Training status:** No classifier training was performed.

## 1. Why Stage 20 stopped

The prior seed-42 per-image stratified split assigned seven byte-identical PlantVillage groups across train/validation/test (four train/test, two train/validation, one validation/test). The 8,779-image original split was not suitable for independent held-out evaluation. Stage 20 stopped before the training sanity batch.

The new split groups exact copies and source/family relationships before partition assignment. A conservative near-match audit is also included. No images were modified, removed, or added to training.

## 2. Dataset, labels, and inventory

The existing adapter reads only the seven configured top-level class folders. It derives `class_id` from the configuration’s explicit PlantVillage folder mapping; files are enumerated in sorted filename order. The nested `data/PlantVillage/PlantVillage/` tree remains excluded.

Configured labels remain unchanged:

`tomato_healthy`, `tomato_bacterial_spot`, `tomato_early_blight`, `tomato_late_blight`, `potato_healthy`, `potato_early_blight`, `potato_late_blight`.

The inventory has 8,779 rows and records relative path, class ID, SHA-256, filename, stem, source-family ID, EXIF-oriented dimensions, dHash, and final group ID. All selected filenames had a UUID prefix followed by `___` and a non-empty suffix; every selected record received a derivable source-family ID.

- Inventory: [`reports/data_manifest/plantvillage_classifier_inventory.csv`](../reports/data_manifest/plantvillage_classifier_inventory.csv)
- Split manifest: [`reports/data_manifest/plantvillage_classifier_split.csv`](../reports/data_manifest/plantvillage_classifier_split.csv)
- Machine-readable summary: [`reports/data_manifest/plantvillage_split_summary.json`](../reports/data_manifest/plantvillage_split_summary.json)
- Near-match candidates and decisions: [`reports/data_manifest/plantvillage_near_duplicate_candidates.csv`](../reports/data_manifest/plantvillage_near_duplicate_candidates.csv)
- Visual review sheet: [`reports/data_manifest/near_duplicate_review.png`](../reports/data_manifest/near_duplicate_review.png)

## 3. Exact duplicates and nested-tree audit

SHA-256 over the 8,779 selected records produced **8,765 unique hashes**, **14 exact-duplicate groups**, and **14 duplicate records beyond unique content**. The pairs are class-pure. All exact copies now share one group ID and one partition.

The nested tree contains **20,638 image files** and **20,624 unique hashes**. It shares **8,765 unique SHA-256 hashes** with the selected top-level classifier set; **8,779 nested files** match selected records (one exact nested counterpart for each selected record, counting exact-copy records). None of those nested files is included in the classifier inventory or split manifest.

## 4. Source/family grouping rule

For a filename whose prefix before the first `___` parses as a UUID, `source_family_id` is the case-folded suffix after that separator, excluding the extension. The identifier is grouped within its class. In this selected dataset the rule applies to all 8,779 records; 14 source-family IDs repeat, and those repeated groups coincide with the 14 exact-hash duplicate groups. No source IDs collide across classes.

This rule is based on the actual UUID-prefixed PlantVillage filename convention and was cross-checked against hashes. It does not infer relationships from generic crop/disease words. When a filename cannot be parsed under this convention, the source-family value is blank and exact-hash grouping still applies.

## 5. Near-duplicate audit

No `imagehash`, OpenCV, or other perceptual-hash package was installed. A lightweight 64-bit difference hash was computed with existing Pillow and NumPy: apply EXIF orientation, convert to grayscale, Lanczos resize to 9×8, then compare adjacent pixels. Candidate pairs at Hamming distance **≤2/64** were recorded. This is a deliberately tight candidate threshold, but the method is not a general image-identity proof.

Two distinct-hash candidates were found. Both were conservatively kept in one partition group; they are not reported as exact duplicates:

| Class | Candidate filenames | dHash distance | Review/grouping rationale |
|---|---|---:|---|
| Tomato bacterial spot | `...___GCREC_Bact.Sp 5840.JPG` and `...___GCREC_Bact.Sp 2989.JPG` | 2/64 | Visual review shows distinct leaf shapes in similar dataset conditions. Not called duplicates; co-assigned conservatively because the hash distance met the strict candidate threshold. |
| Tomato late blight | `...___GHLB_PS Leaf 35.1 Day 13.jpg` and `...___GHLB_PS Leaf 35 Day 13.jpg` | 2/64 | Similar silhouette and closely related `Leaf 35`/same-day source suffixes suggest a potentially related capture. Grouped together conservatively; not asserted to be byte-identical. |

The CSV contains complete paths, SHA-256 values, distances, and grouping rationale. Visual comparisons are in the review sheet. This check can miss rotated, cropped, recompressed, or more substantially transformed related images. The grouping should not be interpreted as a complete near-duplicate guarantee.

## 6. Grouped split method and result

Exact SHA-256, parsed source-family IDs, and dHash candidate pairs are combined transitively into connected groups. Every resulting group is class-pure; any class-spanning group causes generation to fail rather than silently alter labels or scope.

The deterministic splitter processes groups by class, seed-shuffles ties, orders groups largest-first, and greedily chooses the partition that minimizes normalized squared deviation from configured per-class targets (70% train, 15% validation, 15% test). Each class must have at least three independent groups and receives at least one group per partition. Group integrity takes priority over exact ratio targets. It produced **8,763 groups** for **8,779 records**, with the largest group containing two records.

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

Actual ratios are **69.9966% train / 15.0017% validation / 15.0017% test**. Per-class counts happen to match the former split counts, but the assignments differ and now respect grouping constraints.

## 7. Independent verification and reproducibility

`python -m scripts.create_leakage_safe_split` creates the inventory, split, summary, nested-tree hash audit, and near-match CSV. `python -m scripts.verify_leakage_safe_split` independently checks path coverage, current file hashes, class mapping, source IDs, group/hash/family purity, candidate-pair group integrity, class presence, nested-tree exclusion, output checksums, and reconstruction through the classifier training manifest loader.

The generation command was run again with the same seed. The manifest SHA-256 was identical both times:

`40b08f14a9085b26004633fb9123159766ba795892bc6afc483a3f4e76de64bc`

The independent verifier passed for all 8,779 records. It found 8,765 unique hashes, no exact-hash/source-family/group crossing, two near-match candidates together in one group, and all seven labels represented in every partition. The training pipeline’s full-run path now requires and integrity-checks this saved manifest; smoke-test behavior remains separate.

## 8. Dataset validation and remaining limitations

`python -m scripts.validate_datasets` passed: 41,276 PlantVillage files (top-level plus nested), 814 PlantDoc images, and 11,458 PlantSeg images and masks decoded; unreadable files and missing image/mask pairs were zero. Fourteen raw PlantSeg dimension differences were corrected by EXIF orientation; oriented mismatches were zero.

This work establishes a deterministic grouped split for the configured data snapshot. It does not establish that labels are correct, that source families are complete, or that the dHash procedure detects every related capture. Dataset provenance, class imbalance, field representativeness, and agricultural validity remain separate concerns.

## 9. Training boundary

**No EfficientNet training, classifier evaluation, PlantDoc evaluation, checkpoint creation, Grad-CAM candidate check, or model promotion was performed in Stage 20B.** The production checkpoint remains absent and production inference remains unavailable. This split is prepared for a separately authorized continuation of Stage 20; it is not evidence of model performance or agricultural validity.

## 10. Software regression checks

The Stage 20B quality gate passed: Python syntax validation **59 files**, Ruff passed, backend pytest **94 passed**, frontend Vitest **30 passed**, and Vite production build passed. Two existing third-party FastAPI/Starlette test-client deprecation warnings remain. The full dataset validator and independent split verifier passed. No coverage percentage was measured. These checks validate the software/split tooling, not classifier accuracy.
