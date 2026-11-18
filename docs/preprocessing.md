# Preprocessing and dataset validation

## Classification images

`preprocess_classification_image` in `src/crop_health/preprocessing/classification.py` applies EXIF orientation, decodes to RGB, resizes to the configured square input size with bicubic interpolation, scales pixels to `[0, 1]`, and applies ImageNet channel normalization. Training mode may apply a reproducibly sampled horizontal flip when the caller supplies a seeded random generator. It does not alter lesion colors or crop image regions. Validation and inference use no augmentation.

PlantVillage records are generated only from the explicit class mapping and the primary class directories. The nested `data/PlantVillage/PlantVillage` tree is excluded. The function checks configured per-class counts before returning the records.

## PlantSeg image/mask pairs

`plantseg_records` uses `Metadatav2.csv` to resolve the supplied split, image filename, and mask filename; it raises on missing paths or invalid split names. `preprocess_segmentation_pair` applies image EXIF orientation before checking alignment, then resizes RGB images with bicubic interpolation and masks with nearest-neighbor interpolation. It keeps categorical/palette mask values intact. Training flips are applied to image and mask together using the same random decision.

The checks found 14 stored image dimension differences that become aligned after EXIF orientation and zero mismatches after orientation. This orientation step is required when loading these pairs.

## Validation commands and measured results

Run from the project root in the configured Python environment:

```powershell
python -m scripts.validate_datasets
python -m scripts.smoke_preprocessing
python -m pytest -q
```

The dataset inventory decodes recognized images, reports class counts, formats and image-size ranges, checks selected label mappings, and verifies each PlantSeg metadata image/mask pair. The Stage 3 real-data validation report is `reports/stage3_validation.txt`. It records 0 unreadable images, 0 missing metadata pairs, 0 invalid PlantSeg label/split rows, and 0 oriented image/mask size mismatches. The smoke script processed one real PlantVillage example per selected class and one real PlantSeg pair per selected disease class.

No classification split has been materialized yet; Stage 4 will create the seeded, stratified split from the single selected PlantVillage class tree. PlantDoc is not a source for that split.
