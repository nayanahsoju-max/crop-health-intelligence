import numpy as np

from crop_health.explainability.gradcam import normalize_cam


def test_normalize_cam_maps_values_to_zero_one():
    normalized = normalize_cam(np.array([[0.0, 1.0], [2.0, 3.0]], dtype=np.float32))

    assert np.isfinite(normalized).all()
    assert normalized.min() == 0.0
    assert normalized.max() == 1.0


def test_normalize_cam_handles_constant_map_without_nan():
    normalized = normalize_cam(np.full((3, 3), 4.0, dtype=np.float32))

    assert np.isfinite(normalized).all()
    assert np.count_nonzero(normalized) == 0
