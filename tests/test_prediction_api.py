from __future__ import annotations

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
import numpy as np
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from backend.app.prediction_repository import PredictionRepository
from backend.app.prediction_service import PredictionWorkflow
from crop_health.knowledge_base.service import KnowledgeBase
from crop_health.preprocessing.classification import preprocess_classification_image
from crop_health.recommendations.engine import RecommendationEngine
from crop_health.severity.estimator import SeverityEstimate


@pytest.fixture
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    url = f"sqlite:///{(tmp_path / 'prediction_api.sqlite3').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    with TestClient(app) as client:
        yield client


def image_bytes(format="PNG", size=(64, 48), color=(35, 150, 50)):
    stream = BytesIO()
    Image.new("RGB", size, color).save(stream, format=format)
    return stream.getvalue()


class FakeWeather:
    def __init__(self, result):
        self.result = result
        self.locations = []

    def current(self, location):
        self.locations.append(location)
        return self.result


class FakeRecommendation:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def recommend(self, prediction, severity=None, location=None):
        self.calls.append((prediction, severity, location))
        return self.result


def supported_recommendation(weather_status="unavailable"):
    return {
        "status": "available", "prediction_status": "accepted",
        "disease_information": {"id": "tomato_early_blight", "name": "Early blight", "trace": {"sources": [{"url": "https://example.test/source"}]}},
        "general_guidance": [{"category": "prevention", "text": "Use disease-free planting material"}],
        "weather_context": {"status": weather_status, "weather": None},
        "weather_guidance": [], "message": "Weather-specific guidance could not be generated; disease-based guidance is still available.",
    }


def make_workflow(recommender=None, *, repository_factory=PredictionRepository):
    predictor_calls = []

    def predictor(path, checkpoint, mapping, **kwargs):
        predictor_calls.append((path, checkpoint, mapping, kwargs))
        if "grape" in str(checkpoint).lower() or "grape" in str(mapping).lower():
            return {
                "class_id": "grape_black_rot",
                "confidence": 0.95,
                "probabilities": {
                    "grape_black_rot": 0.95,
                    "grape_esca": 0.03,
                    "grape_isariopsis_leaf_blight": 0.02,
                },
            }
        return {"class_id": "tomato_early_blight", "confidence": 0.88,
                "probabilities": {"tomato_early_blight": 0.88, "tomato_late_blight": 0.12}}

    def severity(_image, _mask):
        return SeverityEstimate(22.4, "Moderate", 224, 1000, "mocked")

    def gradcam(_path, _checkpoint, _mapping, **_kwargs):
        return SimpleNamespace(class_id="tomato_early_blight", confidence=0.88,
                               heatmap=Image.new("RGB", (64, 48), "red"),
                               overlay=Image.new("RGB", (64, 48), "green"))

    recommendation = recommender or FakeRecommendation(supported_recommendation())
    workflow = PredictionWorkflow(predictor=predictor, severity_estimator=severity,
                                  gradcam_generator=gradcam, recommendation_engine=recommendation,
                                  repository_factory=repository_factory)
    return workflow, predictor_calls, recommendation


def post_image(client, content, filename="leaf.png", content_type="image/png", crop: str | None = "tomato", **data):
    form_data = dict(data)
    if crop is not None:
        form_data["crop"] = crop
    return client.post("/predict", files={"image": (filename, content, content_type)}, data=form_data)


def test_valid_upload_runs_existing_inference_components_and_creates_history(api_client):
    weather = FakeWeather({"status": "unavailable", "provider": "Open-Meteo", "weather": None,
                           "location": None, "observed_at": None, "error": {"code": "offline"}})
    recommender = RecommendationEngine(knowledge_base=KnowledgeBase(), weather_service=weather)
    workflow, predictor_calls, _ = make_workflow(recommender)
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes(), location="Pune")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "completed"
    assert result["prediction"]["class_id"] == "tomato_early_blight"
    assert result["prediction"]["confidence"] == pytest.approx(0.88)
    assert result["crop"] == "tomato"
    assert result["model"]["version"] == "efficientnet_b0_tomato_potato_2026_11_17_b"
    assert result["model"]["route"] == "tomato_potato"
    assert result["explainability"]["status"] == "available"
    assert result["explainability"]["heatmap_data_url"].startswith("data:image/jpeg;base64,")
    assert result["history"]["record_id"]
    assert len(predictor_calls) == 1
    assert weather.locations == ["Pune"]
    assert result["weather_context"]["status"] == "unavailable"
    assert result["disease_information"]["id"] == "tomato_early_blight"
    assert result["general_guidance"]
    history = api_client.get(f"/predictions/{result['history']['record_id']}")
    assert history.status_code == 200
    record = history.json()
    assert record["predicted_class_id"] == "tomato_early_blight"
    assert record["result_metadata"]["explainability_status"] == "available"
    assert record["recommendation_result"]["disease_information"]["trace"]["sources"]


def test_valid_jpeg_upload_is_accepted(api_client):
    api_client.app.state.prediction_workflow = make_workflow()[0]
    response = post_image(api_client, image_bytes("JPEG"), "leaf.jpg", "image/jpeg")
    assert response.status_code == 200, response.text


def test_upload_filename_is_stored_as_basename(api_client):
    workflow = make_workflow()[0]
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes(), filename="../../field/leaf.png")
    assert response.status_code == 200, response.text
    record = api_client.get(f"/predictions/{response.json()['history']['record_id']}").json()
    assert record["image_reference"]["filename"] == "leaf.png"
    assert "/" not in record["image_reference"]["filename"]
    assert "\\" not in record["image_reference"]["filename"]


def test_invalid_corrupt_image_returns_400(api_client):
    api_client.app.state.prediction_workflow = make_workflow()[0]
    response = post_image(api_client, b"not an image")
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_image"


def test_unsupported_format_and_declared_type_mismatch_are_rejected(api_client):
    api_client.app.state.prediction_workflow = make_workflow()[0]
    unsupported = post_image(api_client, image_bytes("GIF"), "leaf.gif", "image/gif")
    mismatch = post_image(api_client, image_bytes(), "leaf.png", "image/jpeg")
    assert unsupported.status_code == 415
    assert unsupported.json()["detail"]["code"] == "unsupported_image_type"
    assert mismatch.status_code == 415


def test_missing_image_is_rejected_by_request_validation(api_client):
    response = api_client.post("/predict")
    assert response.status_code == 422


def test_oversized_upload_returns_413(api_client):
    workflow = make_workflow()[0]
    workflow.config["max_upload_bytes"] = 100
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, b"a" * 101)
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "upload_too_large"


def test_production_model_unavailable_never_uses_smoke_checkpoint(api_client, monkeypatch):
    from backend.app.prediction_service import PredictionWorkflow
    monkeypatch.setenv("CROP_HEALTH_MODEL_CHECKPOINT", "models/classifier/production/not-installed.pt")
    monkeypatch.setenv("CROP_HEALTH_CLASS_MAPPING", "models/classifier/production/not-installed.json")
    workflow = PredictionWorkflow()
    assert "smoke" not in str(workflow.checkpoint_path).lower()
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes())
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "model_unavailable"
    assert "prediction" not in response.json()


@pytest.mark.parametrize("setting", ["CROP_HEALTH_MODEL_CHECKPOINT", "CROP_HEALTH_CLASS_MAPPING"])
def test_smoke_artifacts_are_rejected_as_production_inputs(api_client, monkeypatch, setting):
    monkeypatch.setenv("CROP_HEALTH_MODEL_CHECKPOINT", "models/classifier/production/real.pt")
    monkeypatch.setenv("CROP_HEALTH_CLASS_MAPPING", "models/classifier/production/classes.json")
    monkeypatch.setenv(setting, "models/classifier/smoke/class_mapping.json")
    workflow = PredictionWorkflow()
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes())
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "model_unavailable"


def test_controlled_inference_integrates_preprocessing_weather_recommendation_and_history(api_client):
    from datetime import datetime

    weather_payload = {
        "status": "available", "provider": "Open-Meteo",
        "location": {"name": "Pune", "latitude": 18.5, "longitude": 73.8},
        "observed_at": "2026-09-30T10:00:00Z",
        "weather": {"temperature_c": 25.0, "relative_humidity_percent": 92.0,
                    "precipitation_mm": 0.2, "wind_speed_kmh": 5.0},
    }
    weather = FakeWeather(weather_payload)
    engine = RecommendationEngine(knowledge_base=KnowledgeBase(), weather_service=weather)
    workflow, _, recommendation = make_workflow(engine)
    preprocessed = []

    def controlled_inference(path, _checkpoint, _mapping, *, image_size, device):
        tensor = preprocess_classification_image(path, image_size=image_size)
        preprocessed.append((tensor.shape, tensor.dtype, device))
        return {"class_id": "tomato_early_blight", "confidence": 0.88,
                "probabilities": {"tomato_early_blight": 0.88, "tomato_late_blight": 0.12}}

    workflow.predictor = controlled_inference
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes(), location="Pune")
    assert response.status_code == 200, response.text
    result = response.json()
    assert preprocessed == [((3, workflow.image_size, workflow.image_size), np.float32, workflow.device)]
    assert weather.locations == ["Pune"]
    assert result["prediction"]["class_id"] == "tomato_early_blight"
    assert result["prediction"]["confidence"] == pytest.approx(0.88)
    assert result["severity"] == {"status": "not_requested", "estimate": None}
    assert result["disease_information"]["id"] == "tomato_early_blight"
    assert result["disease_information"]["trace"]["sources"]
    assert result["weather_context"] == weather_payload
    assert result["weather_guidance"][0]["trace"]["rule_id"] == "early_blight_wet_context"
    assert result["explainability"]["class_id"] == result["prediction"]["class_id"]
    assert result["explainability"]["status"] == "available"
    assert recommendation is engine

    record_id = result["history"]["record_id"]
    listing = api_client.get("/predictions", params={"class_id": "tomato_early_blight"})
    detail = api_client.get(f"/predictions/{record_id}")
    assert listing.status_code == detail.status_code == 200
    assert len(listing.json()) == 1
    record = listing.json()[0]
    assert record == detail.json()
    assert record["id"] == record_id
    assert record["predicted_class_id"] == result["prediction"]["class_id"]
    assert record["confidence"] == pytest.approx(result["prediction"]["confidence"])
    assert record["severity"] is None
    assert record["weather_context"] == result["weather_context"]
    assert record["recommendation_result"]["weather_guidance"][0]["trace"]["rule_id"] == "early_blight_wet_context"
    assert record["recommendation_result"]["disease_information"]["trace"]["sources"]
    assert record["model_version"] == result["model"]["version"]
    assert len(record["image_reference"]["sha256"]) == 64
    assert record["created_at"] == result["history"]["created_at"]
    assert datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))


def test_missing_location_is_explicitly_not_requested_and_does_not_call_weather(api_client):
    weather = FakeWeather({"status": "available", "weather": {
        "temperature_c": 25, "relative_humidity_percent": 92,
        "precipitation_mm": 0.2, "wind_speed_kmh": 5}})
    workflow, _, _ = make_workflow(RecommendationEngine(knowledge_base=KnowledgeBase(), weather_service=weather))
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes())
    assert response.status_code == 200, response.text
    result = response.json()
    assert weather.locations == []
    assert result["weather_context"]["status"] == "not_requested"
    assert result["weather_context"]["weather"] is None
    assert result["disease_information"]["id"] == "tomato_early_blight"
    assert result["weather_guidance"] == []


def test_gradcam_failure_is_nonfatal_and_persisted_as_unavailable(api_client):
    workflow, _, _ = make_workflow()

    def unavailable_gradcam(*_args, **_kwargs):
        raise RuntimeError("test-only explainability failure")

    workflow.gradcam_generator = unavailable_gradcam
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes())
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["prediction"]["class_id"] == "tomato_early_blight"
    assert result["explainability"] == {
        "status": "unavailable", "heatmap_data_url": None, "overlay_data_url": None}
    record = api_client.get(f"/predictions/{result['history']['record_id']}").json()
    assert record["result_metadata"]["explainability_status"] == "unavailable"


def test_health_endpoint_contract(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    description = api_client.get("/openapi.json").json()["info"]["description"]
    assert "prediction-history API" in description
    assert "Production inference requires separately supplied" in description


def test_readiness_reports_database_and_model_assets_separately(api_client):
    response = api_client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "available", "model": "available"},
    }


def test_health_allows_configured_local_frontend_origin(api_client):
    response = api_client.options(
        "/predict",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-credentials" not in response.headers


def test_readiness_returns_503_when_database_is_not_configured(api_client):
    configured_engine = api_client.app.state.database_engine
    api_client.app.state.database_engine = None
    try:
        response = api_client.get("/health/ready")
    finally:
        api_client.app.state.database_engine = configured_engine
    assert response.status_code == 503
    assert response.json()["detail"] == {
        "status": "not_ready",
        "checks": {"database": "unavailable", "model": "available"},
    }


def test_readiness_returns_503_when_model_is_unavailable(api_client):
    configured_workflow = api_client.app.state.prediction_workflow
    api_client.app.state.prediction_workflow = None
    try:
        response = api_client.get("/health/ready")
    finally:
        api_client.app.state.prediction_workflow = configured_workflow
    assert response.status_code == 503
    assert response.json()["detail"] == {
        "status": "not_ready",
        "checks": {"database": "available", "model": "unavailable"},
    }


def test_readiness_returns_503_when_both_database_and_model_are_unavailable(api_client):
    configured_engine = api_client.app.state.database_engine
    configured_workflow = api_client.app.state.prediction_workflow
    api_client.app.state.database_engine = None
    api_client.app.state.prediction_workflow = None
    try:
        response = api_client.get("/health/ready")
    finally:
        api_client.app.state.database_engine = configured_engine
        api_client.app.state.prediction_workflow = configured_workflow
    assert response.status_code == 503
    assert response.json()["detail"] == {
        "status": "not_ready",
        "checks": {"database": "unavailable", "model": "unavailable"},
    }


def test_severity_estimator_is_used_when_matching_lesion_mask_is_supplied(api_client):
    workflow, _, _ = make_workflow()
    api_client.app.state.prediction_workflow = workflow
    response = api_client.post("/predict", files={
        "image": ("leaf.png", image_bytes(), "image/png"),
        "lesion_mask": ("mask.png", image_bytes("PNG", color=(255, 255, 255)), "image/png"),
    }, data={"crop": "tomato"})
    assert response.status_code == 200, response.text
    assert response.json()["severity"]["status"] == "estimated"
    result = response.json()
    assert result["severity"]["estimate"]["category"] == "Moderate"
    record = api_client.get(f"/predictions/{result['history']['record_id']}").json()
    assert record["severity"]["category"] == "Moderate"
    assert record["severity"]["severity_percentage"] == pytest.approx(22.4)


def test_mask_dimension_mismatch_is_rejected(api_client):
    api_client.app.state.prediction_workflow = make_workflow()[0]
    response = api_client.post("/predict", files={
        "image": ("leaf.png", image_bytes(size=(64, 48)), "image/png"),
        "lesion_mask": ("mask.png", image_bytes(size=(32, 32), color=(255, 255, 255)), "image/png"),
    }, data={"crop": "tomato"})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "mask_dimensions_mismatch"
    assert api_client.get("/predictions").json() == []


def test_low_confidence_uses_existing_recommendation_fallback(api_client):
    weather = FakeWeather({"status": "unavailable", "weather": None})
    workflow, _, _ = make_workflow(RecommendationEngine(knowledge_base=KnowledgeBase(), weather_service=weather))
    workflow.predictor = lambda *args, **kwargs: {"class_id": "tomato_early_blight", "confidence": 0.2, "probabilities": {}}
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes())
    assert response.status_code == 200
    assert response.json()["prediction_status"] == "low_confidence"
    assert response.json()["disease_information"] is None


def test_unavailable_weather_still_returns_disease_information(api_client):
    workflow, _, _ = make_workflow(FakeRecommendation(supported_recommendation("unavailable")))
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes(), location="Pune")
    assert response.status_code == 200
    assert response.json()["weather_context"]["status"] == "unavailable"
    assert response.json()["disease_information"]["id"] == "tomato_early_blight"
    assert "could not be generated" in response.json()["recommendation_message"]


def test_unsupported_recommendation_fallback_is_returned_safely(api_client):
    weather = FakeWeather({"status": "unavailable", "weather": None})
    workflow, _, _ = make_workflow(RecommendationEngine(knowledge_base=KnowledgeBase(), weather_service=weather))
    workflow.predictor = lambda *args, **kwargs: {"class_id": "unsupported_class", "confidence": 0.92, "probabilities": {}}
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes())
    assert response.status_code == 200
    assert response.json()["prediction_status"] == "unsupported_disease"
    assert response.json()["disease_information"] is None


def test_persistence_failure_returns_error_not_unpersisted_success(api_client):
    def failing_repository(_session):
        class Repo:
            def create(self, **_kwargs):
                raise RuntimeError("database down")
        return Repo()

    workflow, _, _ = make_workflow(repository_factory=failing_repository)
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes())
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "persistence_failed"
    assert "database down" not in response.text


def test_no_lesion_mask_makes_severity_explicitly_not_requested(api_client):
    workflow, _, _ = make_workflow()
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes())
    assert response.status_code == 200
    assert response.json()["severity"] == {"status": "not_requested", "estimate": None}


def test_routing_tomato_routes_to_tomato_potato_model(api_client):
    workflow, predictor_calls, _ = make_workflow()
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes(), crop="tomato")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["crop"] == "tomato"
    assert result["model"]["route"] == "tomato_potato"
    assert result["model"]["version"] == "efficientnet_b0_tomato_potato_2026_11_17_b"
    assert result["prediction"]["class_id"] == "tomato_early_blight"
    assert len(predictor_calls) == 1
    checkpoint_used = str(predictor_calls[0][1])
    assert "tomato-potato-2026-11-17-b" in checkpoint_used


def test_routing_potato_routes_to_tomato_potato_model(api_client):
    workflow, predictor_calls, _ = make_workflow()
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes(), crop="potato")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["crop"] == "potato"
    assert result["model"]["route"] == "tomato_potato"
    assert result["model"]["version"] == "efficientnet_b0_tomato_potato_2026_11_17_b"
    assert len(predictor_calls) == 1
    checkpoint_used = str(predictor_calls[0][1])
    assert "tomato-potato-2026-11-17-b" in checkpoint_used


def test_routing_grape_routes_to_grape_model(api_client):
    recommender = RecommendationEngine(knowledge_base=KnowledgeBase())
    workflow, predictor_calls, _ = make_workflow(recommender)
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes(), crop="grape")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["crop"] == "grape"
    assert result["model"]["route"] == "grape"
    assert result["model"]["version"] == "efficientnet_b0_grape_2026_11_17_a"
    assert result["prediction"]["class_id"] == "grape_black_rot"
    assert result["prediction_status"] == "accepted"
    assert result["recommendation_status"] == "available"
    assert result["disease_information"]["id"] == "grape_black_rot"
    assert result["disease_information"]["name"] == "Grape black rot"
    assert len(result["general_guidance"]) >= 4
    assert len(predictor_calls) == 1
    checkpoint_used = str(predictor_calls[0][1])
    assert "grape-2026-11-17-a" in checkpoint_used


def test_crop_parameter_case_and_whitespace_tolerance(api_client):
    workflow, predictor_calls, _ = make_workflow()
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes(), crop="  GrApE  ")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["crop"] == "grape"
    assert result["model"]["route"] == "grape"


def test_invalid_crop_returns_422(api_client):
    workflow, _, _ = make_workflow()
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes(), crop="banana")
    assert response.status_code == 422
    data = response.json()["detail"]
    assert data["code"] == "invalid_crop"
    assert "banana" in data["message"]
    assert "grape" in data["message"]
    assert "tomato" in data["message"]


def test_missing_crop_returns_422(api_client):
    workflow, _, _ = make_workflow()
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes(), crop=None)
    assert response.status_code == 422
    data = response.json()["detail"]
    assert data["code"] == "invalid_crop"
    assert "required" in data["message"]


def test_model_caching_loads_weights_only_once(tmp_path: Path):
    load_counts = {"count": 0}

    def spy_loader(ckpt, mapping, device="cpu"):
        load_counts["count"] += 1
        class DummyModel:
            def __call__(self, x):
                import torch
                return torch.zeros((1, 3))
            def eval(self):
                return self
            def to(self, _):
                return self
        return DummyModel(), ["c0", "c1", "c2"], device

    workflow = PredictionWorkflow(model_loader=spy_loader)
    route_tomato = workflow.get_route("tomato")
    route_grape = workflow.get_route("grape")

    # Load tomato twice
    m1 = workflow.get_loaded_model(route_tomato["checkpoint_path"], route_tomato["class_mapping_path"])
    m2 = workflow.get_loaded_model(route_tomato["checkpoint_path"], route_tomato["class_mapping_path"])
    assert m1 is m2
    assert load_counts["count"] == 1

    # Load grape twice
    g1 = workflow.get_loaded_model(route_grape["checkpoint_path"], route_grape["class_mapping_path"])
    g2 = workflow.get_loaded_model(route_grape["checkpoint_path"], route_grape["class_mapping_path"])
    assert g1 is g2
    assert load_counts["count"] == 2


def test_crop_saved_in_history_metadata(api_client):
    workflow, _, _ = make_workflow()
    api_client.app.state.prediction_workflow = workflow
    response = post_image(api_client, image_bytes(), crop="grape")
    assert response.status_code == 200, response.text
    record_id = response.json()["history"]["record_id"]
    detail = api_client.get(f"/predictions/{record_id}").json()
    assert detail["result_metadata"]["crop"] == "grape"
    assert detail["result_metadata"]["model_route"] == "grape"
