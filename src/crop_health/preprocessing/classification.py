"""Classification image loading and deterministic preprocessing."""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def preprocess_classification_image(
    path: str | Path,
    image_size: int = 224,
    *,
    training: bool = False,
    rng: random.Random | None = None,
    mean: tuple[float, float, float] = IMAGENET_MEAN,
    std: tuple[float, float, float] = IMAGENET_STD,
) -> np.ndarray:
    """Return normalized RGB data in CHW float32 form.

    EXIF orientation is applied before resize. Training augmentation is a
    horizontal flip only; validation and inference are deterministic.
    """
    if image_size <= 0:
        raise ValueError("image_size must be positive")
    if len(mean) != 3 or len(std) != 3 or any(value <= 0 for value in std):
        raise ValueError("mean and std must contain three channels with positive std")

    with Image.open(path) as source:
        source.load()  # Force decoding here so damaged inputs fail early.
        image = ImageOps.exif_transpose(source).convert("RGB")
    image = image.resize((image_size, image_size), Image.Resampling.BICUBIC)

    if training and (rng or random).random() < 0.5:
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    array = np.asarray(image, dtype=np.float32) / 255.0
    array = (array - np.asarray(mean, dtype=np.float32)) / np.asarray(std, dtype=np.float32)
    return np.ascontiguousarray(array.transpose(2, 0, 1), dtype=np.float32)
