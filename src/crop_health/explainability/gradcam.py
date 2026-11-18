"""Grad-CAM visualization for a saved EfficientNet B0 classifier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from matplotlib import colormaps
from PIL import Image, ImageOps

from crop_health.classification.inference import load_classifier
from crop_health.preprocessing.classification import preprocess_classification_image


@dataclass(frozen=True)
class GradCAMResult:
    class_id: str
    confidence: float
    probabilities: dict[str, float]
    heatmap: Image.Image
    overlay: Image.Image


def normalize_cam(cam: np.ndarray) -> np.ndarray:
    """Scale a nonnegative CAM to 0..1 without a zero-range division."""
    cam = np.maximum(np.asarray(cam, dtype=np.float32), 0.0)
    minimum = float(cam.min())
    maximum = float(cam.max())
    if not np.isfinite(minimum) or not np.isfinite(maximum) or maximum <= minimum:
        return np.zeros_like(cam, dtype=np.float32)
    return (cam - minimum) / (maximum - minimum)


def generate_gradcam(image_path: str | Path, checkpoint_path: str | Path,
                     class_mapping_path: str | Path, image_size: int = 224,
                     device: str | torch.device = "cpu", overlay_alpha: float = 0.42) -> GradCAMResult:
    """Generate an overlay for the classifier's predicted class.

    Grad-CAM is a visualization of model activation gradients; it does not
    establish biological causation or confirm that the highlighted tissue is
    the true disease region.
    """
    if not 0.0 <= overlay_alpha <= 1.0:
        raise ValueError("overlay_alpha must be in [0, 1]")
    model, class_ids, device = load_classifier(checkpoint_path, class_mapping_path, device)
    with Image.open(image_path) as source:
        source.load()
        original = ImageOps.exif_transpose(source).convert("RGB")
    array = preprocess_classification_image(image_path, image_size=image_size)
    inputs = torch.from_numpy(array).unsqueeze(0).to(device)
    activations: dict[str, torch.Tensor] = {}
    gradients: dict[str, torch.Tensor] = {}

    def capture_activation(_module: torch.nn.Module, _inputs: tuple[torch.Tensor, ...],
                          output: torch.Tensor) -> None:
        activations["value"] = output
        output.register_hook(lambda grad: gradients.__setitem__("value", grad))

    handle = model.features[-1].register_forward_hook(capture_activation)
    try:
        model.zero_grad(set_to_none=True)
        logits = model(inputs)
        probabilities = torch.softmax(logits, dim=1)[0]
        class_index = int(probabilities.argmax().item())
        logits[0, class_index].backward()
    finally:
        handle.remove()

    if "value" not in activations or "value" not in gradients:
        raise RuntimeError("Grad-CAM target activations or gradients were not captured")
    feature_map = activations["value"].detach()
    gradient_map = gradients["value"].detach()
    weights = gradient_map.mean(dim=(2, 3), keepdim=True)
    cam = torch.relu((weights * feature_map).sum(dim=1))[0].cpu().numpy()
    cam = normalize_cam(cam)

    grayscale = Image.fromarray(np.uint8(cam * 255), mode="L")
    grayscale = grayscale.resize(original.size, Image.Resampling.BILINEAR)
    colored_array = np.uint8(colormaps["jet"](np.asarray(grayscale, dtype=np.float32) / 255.0)[..., :3] * 255)
    heatmap = Image.fromarray(colored_array, mode="RGB")
    overlay = Image.blend(original, heatmap, alpha=overlay_alpha)
    score_values = probabilities.detach().cpu().tolist()
    return GradCAMResult(
        class_id=class_ids[class_index],
        confidence=float(score_values[class_index]),
        probabilities={class_ids[index]: float(value) for index, value in enumerate(score_values)},
        heatmap=heatmap,
        overlay=overlay,
    )
