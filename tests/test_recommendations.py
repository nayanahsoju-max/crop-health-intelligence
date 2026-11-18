from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from backend.app.main import RecommendationRequest, app
from crop_health.knowledge_base.service import KnowledgeBase
from crop_health.recommendations.engine import RecommendationEngine


class FakeWeather:
    def __init__(self, result):
        self.result = result
        self.locations = []

    def current(self, location):
        self.locations.append(location)
        return deepcopy(self.result)


def available_weather(**values):
    weather = {"temperature_c": 25.0, "relative_humidity_percent": 65.0,
               "precipitation_mm": 0.0, "wind_speed_kmh": 5.0}
    weather.update(values)
    return {"status": "available", "provider": "Open-Meteo", "location": {"name": "Pune"},
            "observed_at": "2026-09-30T10:00", "weather": weather, "error": None}


def engine(weather=None):
    return RecommendationEngine(knowledge_base=KnowledgeBase(), weather_service=weather or FakeWeather({
        "status": "unavailable", "weather": None, "error": {"code": "provider_unavailable"}
    }))


def test_normal_recommendation_separates_information_and_management_and_traces_sources():
    result = engine().recommend({"class_id": "tomato_early_blight", "confidence": 0.91})
    assert result["status"] == "available"
    assert result["disease_information"]["name"] == "Early blight"
    assert result["disease_information"]["trace"]["sources"]
    assert {item["category"] for item in result["general_guidance"]} == {"prevention", "general_management"}
    assert all(item["trace"]["sources"] for item in result["general_guidance"])
    assert result["weather_context"]["status"] == "not_requested"
    assert result["weather_guidance"] == []
    assert "could not be generated" in result["message"]


def test_weather_rule_adds_cautious_source_traced_context():
    fake = FakeWeather(available_weather(temperature_c=24, relative_humidity_percent=94))
    result = engine(fake).recommend({"class_id": "tomato_early_blight", "confidence": 0.8}, location="Pune")
    assert fake.locations == ["Pune"]
    assert result["weather_context"]["status"] == "available"
    assert len(result["weather_guidance"]) == 1
    guidance = result["weather_guidance"][0]
    assert guidance["trace"]["rule_id"] == "early_blight_wet_context"
    assert guidance["trace"]["sources"]
    assert "does not show that weather caused" in guidance["text"]


def test_weather_without_matching_rule_does_not_add_weather_claim():
    result = engine(FakeWeather(available_weather(relative_humidity_percent=40))).recommend(
        {"class_id": "tomato_early_blight", "confidence": 0.9}, location="Pune")
    assert result["weather_guidance"] == []
    assert result["message"] is None


def test_weather_failure_preserves_disease_guidance_and_explains_fallback():
    fake = FakeWeather({"status": "unavailable", "weather": None, "error": {"code": "timeout"}})
    result = engine(fake).recommend({"class_id": "tomato_late_blight", "confidence": 0.9}, location="Pune")
    assert result["disease_information"]
    assert result["general_guidance"]
    assert result["weather_context"]["status"] == "unavailable"
    assert result["weather_guidance"] == []
    assert "could not be generated" in result["message"]


@pytest.mark.parametrize("prediction,status", [
    ({"class_id": "not_supported", "confidence": 0.9}, "unsupported_disease"),
    ({"class_id": "tomato_early_blight", "confidence": 0.49}, "low_confidence"),
    ({"class_id": "tomato_early_blight", "confidence": float("nan")}, "invalid_prediction"),
    ({"confidence": 0.9}, "invalid_prediction"),
    (None, "invalid_prediction"),
])
def test_unsupported_low_confidence_and_malformed_predictions_fail_safely(prediction, status):
    fake = FakeWeather(available_weather(relative_humidity_percent=99))
    result = engine(fake).recommend(prediction, location="Pune")
    assert result["status"] == "safe_fallback"
    assert result["prediction_status"] == status
    assert result["disease_information"] is None
    assert result["general_guidance"] == []
    assert result["weather_guidance"] == []
    assert fake.locations == []


def test_malformed_weather_and_severity_are_not_used_as_advice():
    fake = FakeWeather({"status": "available", "weather": {"relative_humidity_percent": 99}})
    result = engine(fake).recommend(
        {"class_id": "tomato_early_blight", "confidence": 0.8},
        severity={"category": "Severe", "severity_percentage": 200}, location="Pune")
    assert result["severity"] is None
    assert result["weather_context"]["status"] == "unavailable"
    assert result["weather_guidance"] == []
    assert result["general_guidance"]


def test_severe_category_is_retained_with_traceable_caution():
    result = engine().recommend({"class_id": "potato_late_blight", "confidence": 0.8}, severity="Severe")
    assert result["severity"] == {"category": "Severe"}
    assert result["general_guidance"][0]["category"] == "severity_context"
    assert result["general_guidance"][0]["trace"]["rule_id"] == "high_severity_notice"
    assert result["general_guidance"][0]["trace"]["sources"]


def test_fastapi_endpoint_integrates_engine_without_live_weather():
    fake = FakeWeather({"status": "unavailable", "weather": None, "error": {"code": "offline"}})
    with TestClient(app) as client:
        app.state.recommendation_engine = engine(fake)
        response = client.post("/recommendations/current", json={
            "class_id": "tomato_bacterial_spot", "confidence": 0.75, "location": "Pune"
        })
    assert response.status_code == 200
    body = response.json()
    assert body["disease_information"]["id"] == "tomato_bacterial_spot"
    assert body["weather_context"]["status"] == "unavailable"
    assert fake.locations == ["Pune"]


def test_request_model_rejects_missing_required_prediction_fields():
    with pytest.raises(Exception):
        RecommendationRequest(class_id="tomato_early_blight")


def test_grape_black_rot_recommendation_and_weather_rule():
    fake = FakeWeather(available_weather(temperature_c=24.0, relative_humidity_percent=85.0))
    result = engine(fake).recommend({"class_id": "grape_black_rot", "confidence": 0.95}, location="Nashik")
    assert fake.locations == ["Nashik"]
    assert result["status"] == "available"
    assert result["prediction_status"] == "accepted"
    assert result["disease_information"]["id"] == "grape_black_rot"
    assert result["disease_information"]["crop"] == "Grape"
    assert result["disease_information"]["name"] == "Grape black rot"
    assert len(result["general_guidance"]) >= 4
    assert all(item["trace"]["sources"] for item in result["general_guidance"])
    assert result["weather_context"]["status"] == "available"
    assert len(result["weather_guidance"]) == 1
    assert result["weather_guidance"][0]["trace"]["rule_id"] == "grape_black_rot_warm_moist_context"
    assert "Guignardia bidwellii" in result["weather_guidance"][0]["trace"]["rule_note"]


def test_grape_black_rot_weather_rule_does_not_trigger_when_cold_or_dry():
    # Warm enough but dry
    fake_dry = FakeWeather(available_weather(temperature_c=25.0, relative_humidity_percent=60.0, precipitation_mm=0.0))
    result_dry = engine(fake_dry).recommend({"class_id": "grape_black_rot", "confidence": 0.95}, location="Nashik")
    assert result_dry["weather_guidance"] == []

    # Wet enough but cold (all_of requires temperature_c >= 20)
    fake_cold = FakeWeather(available_weather(temperature_c=16.0, relative_humidity_percent=95.0, precipitation_mm=2.0))
    result_cold = engine(fake_cold).recommend({"class_id": "grape_black_rot", "confidence": 0.95}, location="Nashik")
    assert result_cold["weather_guidance"] == []


def test_grape_isariopsis_leaf_blight_weather_rule():
    # Triggered by high humidity
    fake_humid = FakeWeather(available_weather(temperature_c=22.0, relative_humidity_percent=88.0, precipitation_mm=0.0))
    result = engine(fake_humid).recommend({"class_id": "grape_isariopsis_leaf_blight", "confidence": 0.92}, location="Nashik")
    assert result["status"] == "available"
    assert result["disease_information"]["id"] == "grape_isariopsis_leaf_blight"
    assert len(result["weather_guidance"]) == 1
    assert result["weather_guidance"][0]["trace"]["rule_id"] == "grape_isariopsis_humid_wet_context"

    # Triggered by precipitation
    fake_rain = FakeWeather(available_weather(temperature_c=20.0, relative_humidity_percent=70.0, precipitation_mm=1.0))
    result_rain = engine(fake_rain).recommend({"class_id": "grape_isariopsis_leaf_blight", "confidence": 0.92}, location="Nashik")
    assert len(result_rain["weather_guidance"]) == 1
    assert result_rain["weather_guidance"][0]["trace"]["rule_id"] == "grape_isariopsis_humid_wet_context"


def test_grape_isariopsis_weather_rule_does_not_trigger_in_dry_conditions():
    fake_dry = FakeWeather(available_weather(temperature_c=22.0, relative_humidity_percent=65.0, precipitation_mm=0.0))
    result = engine(fake_dry).recommend({"class_id": "grape_isariopsis_leaf_blight", "confidence": 0.92}, location="Nashik")
    assert result["weather_guidance"] == []


def test_grape_esca_recommendation_and_weather_isolation():
    fake = FakeWeather(available_weather(temperature_c=30.0, relative_humidity_percent=90.0, precipitation_mm=5.0))
    result = engine(fake).recommend({"class_id": "grape_esca", "confidence": 0.89}, location="Nashik")
    assert result["status"] == "available"
    assert result["prediction_status"] == "accepted"
    assert result["disease_information"]["id"] == "grape_esca"
    assert result["disease_information"]["crop"] == "Grape"
    assert result["disease_information"]["name"] == "Esca (black measles)"
    assert len(result["general_guidance"]) >= 4
    # Esca deliberately has no artificial short-term weather rule
    assert result["weather_guidance"] == []

