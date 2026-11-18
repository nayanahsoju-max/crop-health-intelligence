# Severity estimation baseline

## Calculation

`estimate_severity` uses a PlantSeg image and its disease-region mask. It applies image EXIF orientation, resizes large pairs together with bicubic image and nearest-neighbor mask interpolation, thresholds the mask to find annotated diseased pixels, and estimates visible leaf/foliage area using configurable HSV green thresholds, morphological closing, small-component removal, and the lesion mask.

The reported percentage is:

```text
severity_percentage = diseased_leaf_area_pixels / estimated_leaf_area_pixels * 100
```

The percentage is clipped to 0-100. A zero/too-small green foreground raises a clear `ValueError` rather than dividing by zero. The estimator is deterministic for the same image, mask, and configuration.

## Demonstration categories

`configs/severity_config.yaml` contains example thresholds:

- Mild: below 10%
- Moderate: 10% to below 30%
- Severe: 30% or higher

These values are configurable demonstration defaults, not universal agricultural thresholds. They have not been validated against expert-scored severity or field outcomes.

## Validation and measured sample outputs

No trainable segmentation network was trained. This stage uses the classical HSV/morphology baseline because execution is CPU-only and PlantSeg provides masks. Four severity unit tests cover deterministic calculation, configurable category boundaries, bounded percentages, and a blank-image failure. `scripts.smoke_severity` processed one real PlantSeg pair for each of the five selected disease classes; its outputs are saved in `reports/severity/smoke_summary.json`.

`reports/severity/leaf_mask_preview.png` shows the Stage 6 tomato early-blight sample with the estimated foliage mask in green and annotated lesion pixels in red. It is a qualitative inspection aid, not a validated segmentation result.

The PlantSeg masks annotate disease regions; they do not supply a complete leaf silhouette. The HSV foreground approximation can include green fruit or background vegetation and can miss discolored foliage. Therefore the denominator, percentage, and category are provisional. Validate both segmentation and thresholds on labeled field images before interpreting severity operationally.
