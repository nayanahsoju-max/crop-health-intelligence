"""Configurable classical severity estimate from PlantSeg lesion masks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image, ImageOps
from scipy import ndimage


@dataclass(frozen=True)
class SeverityEstimate:
    severity_percentage: float
    category: str
    diseased_leaf_area_pixels: int
    estimated_leaf_area_pixels: int
    method: str


def load_severity_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict) or not isinstance(data.get("severity"), dict):
        raise ValueError("severity config must contain a 'severity' mapping")
    return data["severity"]


def _working_arrays(image_path: Path, mask_path: Path, maximum_dimension: int) -> tuple[np.ndarray, np.ndarray]:
    if maximum_dimension < 32:
        raise ValueError("maximum_working_dimension must be at least 32")
    with Image.open(image_path) as source:
        source.load()
        image = ImageOps.exif_transpose(source).convert("RGB")
    with Image.open(mask_path) as source_mask:
        source_mask.load()
        mask = source_mask.copy()
    if image.size != mask.size:
        raise ValueError(f"image/mask dimensions do not align after EXIF orientation: {image.size} vs {mask.size}")
    width, height = image.size
    scale = min(1.0, maximum_dimension / max(width, height))
    if scale < 1.0:
        target = (max(1, round(width * scale)), max(1, round(height * scale)))
        image = image.resize(target, Image.Resampling.BICUBIC)
        mask = mask.resize(target, Image.Resampling.NEAREST)
    return np.asarray(image), np.asarray(mask)


def _leaf_foreground(rgb: np.ndarray, lesion: np.ndarray, config: dict[str, Any]) -> np.ndarray:
    hsv = np.asarray(Image.fromarray(rgb).convert("HSV"))
    threshold = config["leaf_segmentation"]
    hue, saturation, value = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    green = (
        (hue >= int(threshold["hue_min_0_255"]))
        & (hue <= int(threshold["hue_max_0_255"]))
        & (saturation >= int(threshold["saturation_min_0_255"]))
        & (value >= int(threshold["value_min_0_255"]))
    )
    pixels = rgb.shape[0] * rgb.shape[1]
    if int(green.sum()) < max(1, int(pixels * float(threshold["minimum_green_fraction"]))):
        raise ValueError("leaf foreground could not be estimated from green pixels")

    kernel_size = max(1, int(threshold["closing_kernel_size"]))
    if kernel_size % 2 == 0:
        kernel_size += 1
    structure = np.ones((kernel_size, kernel_size), dtype=bool)
    green = ndimage.binary_closing(green, structure=structure)
    labels, count = ndimage.label(green)
    if count:
        component_sizes = np.bincount(labels.ravel())
        min_area = max(1, int(pixels * float(threshold["minimum_component_fraction"])))
        keep = component_sizes >= min_area
        keep[0] = False
        green = keep[labels]
    # Include annotated lesions so brown/yellow diseased tissue remains in the
    # estimated leaf denominator instead of being mistaken for background.
    return green | lesion


def estimate_severity(image_path: str | Path, mask_path: str | Path,
                      config: dict[str, Any] | None = None) -> SeverityEstimate:
    """Compute annotated lesion pixels as a percentage of estimated leaf area.

    This is an image-processing baseline, not a validated agronomic severity
    model. The HSV foreground mask can confuse fruit, soil, and foliage.
    """
    if config is None:
        config = load_severity_config(Path(__file__).resolve().parents[3] / "configs" / "severity_config.yaml")
    thresholds = config["thresholds_percent"]
    mild_max = float(thresholds["mild_max_exclusive"])
    moderate_max = float(thresholds["moderate_max_exclusive"])
    if not 0 <= mild_max < moderate_max <= 100:
        raise ValueError("severity thresholds must satisfy 0 <= mild < moderate <= 100")
    rgb, mask = _working_arrays(
        Path(image_path), Path(mask_path), int(config["maximum_working_dimension"])
    )
    lesion = mask > int(config["mask_positive_threshold"])
    leaf = _leaf_foreground(rgb, lesion, config)
    leaf_area = int(leaf.sum())
    if leaf_area == 0:
        raise ValueError("estimated leaf area is zero; severity cannot be calculated")
    affected_area = int(np.logical_and(lesion, leaf).sum())
    percentage = 100.0 * affected_area / leaf_area
    percentage = min(100.0, max(0.0, percentage))
    category = "Mild" if percentage < mild_max else "Moderate" if percentage < moderate_max else "Severe"
    return SeverityEstimate(
        severity_percentage=percentage,
        category=category,
        diseased_leaf_area_pixels=affected_area,
        estimated_leaf_area_pixels=leaf_area,
        method=str(config["leaf_segmentation"]["method"]),
    )
