import random

import numpy as np
from PIL import Image

from crop_health.preprocessing.classification import preprocess_classification_image
from crop_health.preprocessing.segmentation import preprocess_segmentation_pair


def test_classification_preprocess_transposes_exif_and_normalizes(tmp_path):
    path = tmp_path / "oriented.jpg"
    image = Image.new("RGB", (40, 20), (0, 0, 255))
    for x in range(20):
        for y in range(20):
            image.putpixel((x, y), (255, 0, 0))
    exif = Image.Exif()
    exif[274] = 6
    image.save(path, exif=exif)

    output = preprocess_classification_image(path, image_size=32)

    assert output.shape == (3, 32, 32)
    assert output.dtype == np.float32
    assert np.isfinite(output).all()
    assert output[0, :16, :].mean() > output[0, 16:, :].mean()


def test_validation_preprocessing_is_deterministic(tmp_path):
    path = tmp_path / "leaf.png"
    Image.new("RGB", (30, 24), (40, 120, 60)).save(path)

    first = preprocess_classification_image(path, image_size=16, training=False)
    second = preprocess_classification_image(path, image_size=16, training=False)

    assert np.array_equal(first, second)


def test_mask_resize_uses_nearest_and_keeps_categories(tmp_path):
    image_path = tmp_path / "leaf.jpg"
    mask_path = tmp_path / "mask.png"
    Image.new("RGB", (24, 18), (30, 130, 50)).save(image_path)
    mask = Image.new("L", (24, 18), 0)
    for x in range(6, 18):
        for y in range(4, 14):
            mask.putpixel((x, y), 255)
    mask.save(mask_path)

    _, output_mask = preprocess_segmentation_pair(image_path, mask_path, image_size=37)

    assert output_mask.shape == (37, 37)
    assert set(np.unique(output_mask)).issubset({0, 255})


def test_image_mask_augmentation_is_synchronized(tmp_path):
    image_path = tmp_path / "leaf.png"
    mask_path = tmp_path / "mask.png"
    image = Image.new("RGB", (20, 10), (0, 0, 0))
    mask = Image.new("L", (20, 10), 0)
    for x in range(2, 7):
        for y in range(2, 8):
            image.putpixel((x, y), (255, 255, 255))
            mask.putpixel((x, y), 255)
    image.save(image_path)
    mask.save(mask_path)

    image_array, mask_array = preprocess_segmentation_pair(
        image_path, mask_path, image_size=20, training=True, rng=random.Random(1)
    )

    image_center = np.argwhere(image_array.mean(axis=0) > 0.5).mean(axis=0)
    mask_center = np.argwhere(mask_array == 255).mean(axis=0)
    assert np.allclose(image_center, mask_center, atol=1.0)
