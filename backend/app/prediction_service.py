"""Validated upload and orchestration of existing crop-health components."""
from __future__ import annotations

import base64
import hashlib
import io
import math
import os
import warnings
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, BinaryIO, Callable

import numpy as np
import torch
import yaml
from matplotlib import colormaps
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from backend.app.prediction_repository import PredictionRepository
from crop_health.classification.inference import load_classifier
from crop_health.explainability.gradcam import GradCAMResult, normalize_cam
from crop_health.preprocessing.classification import preprocess_classification_image
from crop_health.recommendations.engine import RecommendationEngine
from crop_health.severity.estimator import estimate_severity

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class UploadValidationError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class ModelUnavailableError(Exception):
    pass


class PersistenceFailure(Exception):
    pass


def save_validated_upload(
    source: BinaryIO,
    destination: Path,
    filename: str | None,
    media_type: str | None,
    settings: dict[str, Any],
    *,
    role: str = "image",
) -> dict[str, Any]:
    """Stream to a private temporary path, enforce size/type/decode limits."""
    config = settings["prediction"]
    if not filename:
        raise UploadValidationError(400, "missing_filename", "The uploaded file needs a filename.")
    safe_name = Path(filename.replace("\\", "/")).name
    extension = Path(safe_name).suffix.lower()
    if role == "mask":
        allowed_bytes = int(config["severity_mask"]["max_upload_bytes"])
        if extension != ".png" or media_type != "image/png":
            raise UploadValidationError(415, "unsupported_mask_type", "Severity masks must be PNG images.")
        formats = {"PNG": {"extension": ".png", "media_type": "image/png"}}
    else:
        allowed_bytes = int(config["max_upload_bytes"])
        formats = config["supported_uploads"]
        matching = [item for item in formats.values() if extension in item.get("extensions", [item.get("extension")])]
        if not matching:
            raise UploadValidationError(415, "unsupported_image_type", "Supported image uploads are JPEG, PNG, and WEBP.")
        if media_type != matching[0]["media_type"]:
            raise UploadValidationError(415, "content_type_mismatch", "The declared content type does not match the filename type.")

    total = 0
    digest = hashlib.sha256()
    with destination.open("wb") as output:
        while True:
            chunk = source.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > allowed_bytes:
                output.close()
                destination.unlink(missing_ok=True)
                raise UploadValidationError(413, "upload_too_large", f"Upload exceeds the {allowed_bytes}-byte limit.")
            digest.update(chunk)
            output.write(chunk)
    if total == 0:
        raise UploadValidationError(400, "empty_upload", "The uploaded file is empty.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(destination) as image:
                image_format = image.format
                width, height = image.size
                if role == "mask":
                    expected = {"PNG": {"extension": ".png", "media_type": "image/png"}}
                else:
                    expected = settings["prediction"]["supported_uploads"]
                if image_format not in expected:
                    raise UploadValidationError(415, "unsupported_image_content", "The image content format is not supported.")
                config_entry = expected[image_format]
                expected_extensions = config_entry.get("extensions", [config_entry.get("extension")])
                if extension not in expected_extensions or media_type != config_entry["media_type"]:
                    raise UploadValidationError(415, "content_type_mismatch", "File extension, content type, and image content must match.")
                if width <= 0 or height <= 0 or width > config["max_image_dimension"] or height > config["max_image_dimension"] or width * height > config["max_image_pixels"]:
                    raise UploadValidationError(413, "image_dimensions_too_large", "Image dimensions exceed the configured safety limit.")
                image.verify()
            with Image.open(destination) as image:
                image.load()
    except UploadValidationError:
        destination.unlink(missing_ok=True)
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        destination.unlink(missing_ok=True)
        raise UploadValidationError(400, "invalid_image", "The uploaded file is not a valid, decodable image.") from exc
    return {"filename": safe_name[:255], "media_type": formats[image_format]["media_type"],
            "sha256": digest.hexdigest(), "format": image_format, "width": width, "height": height, "size_bytes": total}


class PredictionWorkflow:
    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        predictor: Callable[..., dict[str, Any]] | None = None,
        severity_estimator: Callable[..., Any] | None = None,
        gradcam_generator: Callable[..., Any] | None = None,
        recommendation_engine: RecommendationEngine | Any | None = None,
        repository_factory: Callable[[Session], PredictionRepository] = PredictionRepository,
        model_loader: Callable[..., tuple[torch.nn.Module, list[str], torch.device]] | None = None,
    ) -> None:
        path = Path(config_path) if config_path else PROJECT_ROOT / "configs/prediction_config.yaml"
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict) or not isinstance(loaded.get("prediction"), dict):
            raise ValueError("prediction config must contain a prediction mapping")
        self.settings = loaded
        self.config = loaded["prediction"]

        # Parse model routes
        self.routes: dict[str, dict[str, Any]] = {}
        self.crop_to_route: dict[str, str] = {}
        models_cfg = self.config.get("models")
        if isinstance(models_cfg, dict):
            for route_name, route_cfg in models_cfg.items():
                crops = [str(c).strip().lower() for c in route_cfg.get("crops", [])]
                ckpt = self._resolve_path(route_cfg["checkpoint_path"])
                mapping = self._resolve_path(route_cfg["class_mapping_path"])
                version = str(route_cfg.get("model_version", route_name))
                self.routes[route_name] = {
                    "name": route_name,
                    "crops": crops,
                    "checkpoint_path": ckpt,
                    "class_mapping_path": mapping,
                    "model_version": version,
                }
                for c in crops:
                    self.crop_to_route[c] = route_name

        # Fallback / backward-compatibility attributes
        self.checkpoint_path = self._configured_path("CROP_HEALTH_MODEL_CHECKPOINT", "checkpoint_path")
        self.class_mapping_path = self._configured_path("CROP_HEALTH_CLASS_MAPPING", "class_mapping_path")
        self.model_version = os.getenv(
            "CROP_HEALTH_MODEL_VERSION",
            self.config.get("model_version", "efficientnet_b0_tomato_potato_2026_11_17_b"),
        )
        self.image_size = int(self.config["image_size"])
        self.device = os.getenv("CROP_HEALTH_DEVICE", self.config["device"])

        # Environment variable overrides update primary route
        if "CROP_HEALTH_MODEL_CHECKPOINT" in os.environ and "tomato_potato" in self.routes:
            self.routes["tomato_potato"]["checkpoint_path"] = self.checkpoint_path
        if "CROP_HEALTH_CLASS_MAPPING" in os.environ and "tomato_potato" in self.routes:
            self.routes["tomato_potato"]["class_mapping_path"] = self.class_mapping_path
        if "CROP_HEALTH_MODEL_VERSION" in os.environ and "tomato_potato" in self.routes:
            self.routes["tomato_potato"]["model_version"] = self.model_version

        # Ensure at least a default route exists if models config was empty
        if not self.routes:
            default_crops = ["tomato", "potato"]
            self.routes["tomato_potato"] = {
                "name": "tomato_potato",
                "crops": default_crops,
                "checkpoint_path": self.checkpoint_path,
                "class_mapping_path": self.class_mapping_path,
                "model_version": self.model_version,
            }
            for c in default_crops:
                self.crop_to_route[c] = "tomato_potato"

        # Model caching
        self.model_loader = model_loader or load_classifier
        self._model_cache: dict[tuple[Path, Path, str], tuple[torch.nn.Module, list[str], torch.device]] = {}

        self.predictor = predictor or self._default_predictor
        self.severity_estimator = severity_estimator or estimate_severity
        self.gradcam_generator = gradcam_generator or self._default_gradcam
        self.recommendation_engine = recommendation_engine or RecommendationEngine()
        self.repository_factory = repository_factory
        self._test_injected_model = predictor is not None and gradcam_generator is not None

    def _resolve_path(self, path_str: str | Path) -> Path:
        candidate = Path(path_str)
        return candidate.resolve() if candidate.is_absolute() else (PROJECT_ROOT / candidate).resolve()

    def _configured_path(self, env_key: str, config_key: str) -> Path:
        value = os.getenv(env_key, self.config[config_key])
        return self._resolve_path(value)

    def get_loaded_model(
        self, checkpoint_path: Path, class_mapping_path: Path, device: str | torch.device = "cpu"
    ) -> tuple[torch.nn.Module, list[str], torch.device]:
        key = (checkpoint_path.resolve(), class_mapping_path.resolve(), str(device))
        if key not in self._model_cache:
            with torch.inference_mode(mode=False):
                self._model_cache[key] = self.model_loader(checkpoint_path, class_mapping_path, device)
        return self._model_cache[key]

    @torch.no_grad()
    def _default_predictor(
        self,
        image_path: str | Path,
        checkpoint_path: str | Path,
        class_mapping_path: str | Path,
        image_size: int = 224,
        device: str | torch.device = "cpu",
    ) -> dict[str, Any]:
        model, class_ids, resolved_device = self.get_loaded_model(
            Path(checkpoint_path), Path(class_mapping_path), device
        )
        array = preprocess_classification_image(image_path, image_size=image_size)
        tensor = torch.from_numpy(array).unsqueeze(0).to(resolved_device)
        probabilities = torch.softmax(model(tensor), dim=1)[0].cpu().tolist()
        index = max(range(len(probabilities)), key=probabilities.__getitem__)
        return {
            "class_id": class_ids[index],
            "confidence": float(probabilities[index]),
            "probabilities": {class_ids[i]: float(value) for i, value in enumerate(probabilities)},
        }

    def _default_gradcam(
        self,
        image_path: str | Path,
        checkpoint_path: str | Path,
        class_mapping_path: str | Path,
        image_size: int = 224,
        device: str | torch.device = "cpu",
        overlay_alpha: float = 0.42,
    ) -> GradCAMResult:
        if not 0.0 <= overlay_alpha <= 1.0:
            raise ValueError("overlay_alpha must be in [0, 1]")
        model, class_ids, resolved_device = self.get_loaded_model(
            Path(checkpoint_path), Path(class_mapping_path), device
        )
        with Image.open(image_path) as source:
            source.load()
            original = ImageOps.exif_transpose(source).convert("RGB")
        array = preprocess_classification_image(image_path, image_size=image_size)
        inputs = torch.from_numpy(array).unsqueeze(0).to(resolved_device)
        activations: dict[str, torch.Tensor] = {}
        gradients: dict[str, torch.Tensor] = {}

        def capture_activation(
            _module: torch.nn.Module, _inputs: tuple[torch.Tensor, ...], output: torch.Tensor
        ) -> None:
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

    def get_route(self, crop: str | None) -> dict[str, Any]:
        supported = ", ".join(sorted(self.crop_to_route.keys()))
        if crop is None or not str(crop).strip():
            raise UploadValidationError(
                422, "invalid_crop", f"Crop is required and must be one of: {supported}."
            )
        normalized = str(crop).strip().lower()
        route_name = self.crop_to_route.get(normalized)
        if route_name is None or route_name not in self.routes:
            raise UploadValidationError(
                422, "invalid_crop", f"Crop '{crop}' is not supported. Supported crops are: {supported}."
            )
        return self.routes[route_name]

    def ensure_model_available(self, crop: str | None = None) -> None:
        if self._test_injected_model:
            return
        if crop is not None:
            route = self.get_route(crop)
            routes_to_check = [route]
        else:
            routes_to_check = list(self.routes.values()) if self.routes else [
                {"checkpoint_path": self.checkpoint_path, "class_mapping_path": self.class_mapping_path}
            ]

        for r in routes_to_check:
            ckpt: Path = r["checkpoint_path"]
            mapping: Path = r["class_mapping_path"]
            if "smoke" in {part.lower() for part in ckpt.parts}:
                raise ModelUnavailableError("Smoke-test checkpoints are not production models.")
            if "smoke" in {part.lower() for part in mapping.parts}:
                raise ModelUnavailableError("Smoke-test class mappings are not production configuration.")
            if not ckpt.is_file() or not mapping.is_file():
                raise ModelUnavailableError(
                    f"Production classifier checkpoint or class mapping is not configured or does not exist for route '{r.get('name', 'default')}'."
                )

    def run(
        self,
        image_path: Path,
        upload_metadata: dict[str, Any],
        session: Session,
        *,
        crop: str = "tomato",
        location: str | None = None,
        mask_path: Path | None = None,
    ) -> dict[str, Any]:
        route = self.get_route(crop)
        self.ensure_model_available(crop)
        checkpoint_path = route["checkpoint_path"]
        class_mapping_path = route["class_mapping_path"]
        model_version = route["model_version"]

        model_args = {"image_size": self.image_size, "device": self.device}
        try:
            prediction = self.predictor(image_path, checkpoint_path, class_mapping_path, **model_args)
        except Exception as exc:
            raise ModelUnavailableError("Classifier inference failed; verify the production checkpoint and class mapping.") from exc
        if not isinstance(prediction, dict) or not isinstance(prediction.get("class_id"), str):
            raise ModelUnavailableError("Classifier returned an invalid prediction result.")
        confidence = prediction.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ModelUnavailableError("Classifier returned an invalid confidence score.")

        severity_data: dict[str, Any] | None = None
        severity_status = "not_requested"
        if mask_path is not None:
            try:
                estimate = self.severity_estimator(image_path, mask_path)
                severity_data = asdict(estimate) if is_dataclass(estimate) else dict(estimate)
                severity_status = "estimated"
            except (ValueError, OSError, TypeError):
                severity_status = "unavailable"

        try:
            gradcam = self.gradcam_generator(image_path, checkpoint_path, class_mapping_path, **model_args)
            if gradcam.class_id != prediction["class_id"] or not math.isclose(
                float(gradcam.confidence), float(prediction["confidence"]), rel_tol=0, abs_tol=1e-5
            ):
                raise RuntimeError("Grad-CAM result did not match classifier prediction")
            explainability = self._encode_gradcam(gradcam)
        except (ValueError, RuntimeError, OSError, AttributeError, KeyError):
            explainability = {"status": "unavailable", "heatmap_data_url": None, "overlay_data_url": None}

        recommendation = self.recommendation_engine.recommend(prediction, severity=severity_data, location=location)
        recommendation_safe = isinstance(recommendation, dict)
        if not recommendation_safe:
            recommendation = {"status": "safe_fallback", "prediction_status": "recommendation_unavailable",
                              "disease_information": None, "general_guidance": [], "weather_context": {
                                  "status": "unavailable", "weather": None}, "weather_guidance": [],
                              "message": "Recommendation service was unavailable; consult local agricultural extension."}

        repo = self.repository_factory(session)
        try:
            record = repo.create(
                predicted_class_id=prediction["class_id"],
                confidence=float(prediction["confidence"]),
                severity=severity_data,
                weather_context=recommendation.get("weather_context"),
                recommendation_result=recommendation,
                result_metadata={
                    "crop": str(crop).strip().lower(),
                    "model_route": route["name"],
                    "probabilities": prediction.get("probabilities"),
                    "severity_status": severity_status,
                    "explainability_status": explainability["status"],
                    "uploaded_image": {key: value for key, value in upload_metadata.items() if key != "sha256"},
                },
                model_version=model_version,
                image_reference={"filename": upload_metadata["filename"], "media_type": upload_metadata["media_type"],
                                 "sha256": upload_metadata["sha256"]},
            )
        except Exception as exc:
            session.rollback()
            raise PersistenceFailure("Prediction was computed but could not be saved to history.") from exc

        return {
            "status": "completed",
            "crop": str(crop).strip().lower(),
            "prediction_status": recommendation.get("prediction_status", "accepted"),
            "recommendation_status": recommendation.get("status", "safe_fallback"),
            "prediction": {"class_id": prediction["class_id"], "confidence": float(prediction["confidence"]),
                           "probabilities": prediction.get("probabilities")},
            "model": {"version": model_version, "route": route["name"]},
            "severity": {"status": severity_status, "estimate": severity_data},
            "disease_information": recommendation.get("disease_information"),
            "general_guidance": recommendation.get("general_guidance", []),
            "weather_context": recommendation.get("weather_context", {"status": "not_requested", "weather": None}),
            "weather_guidance": recommendation.get("weather_guidance", []),
            "recommendation_message": recommendation.get("message"),
            "explainability": explainability,
            "history": {"record_id": record.id, "created_at": record.created_at},
        }

    def _encode_gradcam(self, result: Any) -> dict[str, Any]:
        max_size = int(self.config["gradcam_preview_max_dimension"])
        encoded = {}
        dimensions = {}
        for key in ("heatmap", "overlay"):
            image = getattr(result, key).convert("RGB")
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=85, optimize=True)
            encoded[key] = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
            dimensions[key] = {"width": image.width, "height": image.height}
        return {"status": "available", "class_id": result.class_id, "confidence": float(result.confidence),
                "heatmap_data_url": encoded["heatmap"], "overlay_data_url": encoded["overlay"], "dimensions": dimensions}
