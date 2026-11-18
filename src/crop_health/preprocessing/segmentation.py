"""Image/mask pair preprocessing with categorical-mask-safe resizing."""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


def preprocess_segmentation_pair(
    image_path: str | Path,
    mask_path: str | Path,
    image_size: int = 512,
    *,
    training: bool = False,
    rng: random.Random | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Load an aligned RGB image and mask, resizing masks with nearest-neighbor.

    Palette and grayscale mask values are preserved. If EXIF orientation makes
    the image dimensions match its mask, orientation is applied before resize.
    """
    if image_size <= 0:
        raise ValueError("image_size must be positive")
    with Image.open(image_path) as source:
        source.load()
        image = ImageOps.exif_transpose(source).convert("RGB")
    with Image.open(mask_path) as source_mask:
        source_mask.load()
        mask = source_mask.copy()

    if image.size != mask.size:
        raise ValueError(f"image/mask dimensions do not align: {image.size} vs {mask.size}")

    image = image.resize((image_size, image_size), Image.Resampling.BICUBIC)
    mask = mask.resize((image_size, image_size), Image.Resampling.NEAREST)
    if training and (rng or random).random() < 0.5:
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        mask = mask.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    image_array = np.asarray(image, dtype=np.float32) / 255.0
    mask_array = np.asarray(mask)
    return np.ascontiguousarray(image_array.transpose(2, 0, 1)), mask_array
