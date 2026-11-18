from pathlib import Path

import pytest
from PIL import Image

from crop_health.severity.estimator import estimate_severity, load_severity_config


def _write_leaf_pair(tmp_path, lesion_box=(40, 40, 50, 50)):
    image_path = tmp_path / "leaf.png"
    mask_path = tmp_path / "mask.png"
    image = Image.new("RGB", (100, 100), (255, 255, 255))
    for x in range(20, 80):
        for y in range(20, 80):
            image.putpixel((x, y), (40, 130, 50))
    mask = Image.new("L", (100, 100), 0)
    for x in range(lesion_box[0], lesion_box[2]):
        for y in range(lesion_box[1], lesion_box[3]):
            image.putpixel((x, y), (90, 60, 35))
            mask.putpixel((x, y), 1)
    image.save(image_path)
    mask.save(mask_path)
    return image_path, mask_path


def test_severity_percent_is_bounded_and_category_is_deterministic(tmp_path):
    image_path, mask_path = _write_leaf_pair(tmp_path, lesion_box=(35, 35, 55, 55))
    config_path = Path(__file__).resolve().parents[1] / "configs" / "severity_config.yaml"
    config = load_severity_config(config_path)

    first = estimate_severity(image_path, mask_path, config)
    second = estimate_severity(image_path, mask_path, config)

    assert first == second
    assert 0 <= first.severity_percentage <= 100
    assert first.diseased_leaf_area_pixels == 400
    assert first.category == "Moderate"


def test_severity_configuration_thresholds_are_used(tmp_path):
    image_path, mask_path = _write_leaf_pair(tmp_path, lesion_box=(35, 35, 55, 55))
    config_path = Path(__file__).resolve().parents[1] / "configs" / "severity_config.yaml"
    config = load_severity_config(config_path)
    config["thresholds_percent"] = {"mild_max_exclusive": 5.0, "moderate_max_exclusive": 10.0}

    estimate = estimate_severity(image_path, mask_path, config)

    assert estimate.category == "Severe"


def test_empty_leaf_estimate_fails_without_division_by_zero(tmp_path):
    image_path = tmp_path / "blank.png"
    mask_path = tmp_path / "mask.png"
    Image.new("RGB", (100, 100), (255, 255, 255)).save(image_path)
    Image.new("L", (100, 100), 0).save(mask_path)

    with pytest.raises(ValueError, match="leaf foreground could not be estimated"):
        estimate_severity(image_path, mask_path)
