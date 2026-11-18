from urllib.error import HTTPError, URLError

import pytest
from fastapi.testclient import TestClient

from crop_health.weather.service import WeatherService
from backend.app.main import app


class FakeProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.urls = []

    def __call__(self, url, timeout):
        self.urls.append((url, timeout))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_valid_location_returns_real_provider_payload_shape():
    fake = FakeProvider([
        {"results": [{"name": "Pune", "country": "India", "latitude": 18.5, "longitude": 73.8}]},
        {"timezone": "Asia/Kolkata", "current": {"time": "2026-09-30T10:00", "temperature_2m": 28.0, "relative_humidity_2m": 63, "precipitation": 0.2, "wind_speed_10m": 7.0}},
    ])
    result = WeatherService(fetch_json=fake).current("Pune")
    assert result["status"] == "available"
    assert result["weather"]["relative_humidity_percent"] == 63
    assert "latitude=18.5" in fake.urls[1][0]
    assert all(timeout == 8 for _, timeout in fake.urls)
    assert "name=Pune" in fake.urls[0][0]


def test_location_not_found_has_no_weather_values():
    result = WeatherService(fetch_json=FakeProvider([{"results": []}])).current("No Such Place")
    assert result["error"]["code"] == "location_not_found"
    assert result["weather"] is None


def test_provider_failure_and_timeout_have_explicit_fallback():
    failed = WeatherService(fetch_json=FakeProvider([URLError("offline")])).current("Pune")
    timeout = WeatherService(fetch_json=FakeProvider([TimeoutError()])).current("Pune")
    assert failed["status"] == "unavailable" and failed["weather"] is None
    assert timeout["error"]["code"] == "timeout"


def test_empty_location_does_not_call_provider():
    fake = FakeProvider([])
    result = WeatherService(fetch_json=fake).current("  ")
    assert result["error"]["code"] == "invalid_location"
    assert fake.urls == []


@pytest.mark.parametrize("exception,code", [
    (HTTPError("https://example.test", 503, "offline", {}, None), "provider_error"),
    (URLError("offline"), "provider_unavailable"),
    (TimeoutError(), "timeout"),
    (URLError(TimeoutError()), "timeout"),
])
def test_provider_errors_return_no_weather(exception, code):
    result = WeatherService(fetch_json=FakeProvider([exception])).current("Pune")
    assert result["status"] == "unavailable"
    assert result["error"]["code"] == code
    assert result["weather"] is None


@pytest.mark.parametrize("responses", [
    [None],
    [{"results": "invalid"}],
    [{"results": [{"name": "Pune", "latitude": 18.5, "longitude": 73.8}]}, None],
    [{"results": [{"name": "Pune", "latitude": 18.5, "longitude": 73.8}]}, {"current": {"time": "now"}}],
])
def test_invalid_or_incomplete_provider_data_is_unavailable(responses):
    result = WeatherService(fetch_json=FakeProvider(responses)).current("Pune")
    assert result["status"] == "unavailable"
    assert result["weather"] is None


def test_non_numeric_weather_values_are_unavailable():
    fake = FakeProvider([
        {"results": [{"name": "Pune", "latitude": 18.5, "longitude": 73.8}]},
        {"current": {"time": "now", "temperature_2m": "warm", "relative_humidity_2m": 63, "precipitation": 0, "wind_speed_10m": 7}},
    ])
    result = WeatherService(fetch_json=fake).current("Pune")
    assert result["status"] == "unavailable"
    assert result["error"]["code"] == "provider_error"
    assert result["weather"] is None


def test_environment_configuration_overrides_provider_and_timeout(tmp_path, monkeypatch):
    monkeypatch.setenv("WEATHER_API_BASE_URL", "https://weather.example")
    monkeypatch.setenv("WEATHER_GEOCODING_URL", "https://geo.example/search")
    monkeypatch.setenv("WEATHER_TIMEOUT_SECONDS", "2.5")
    service = WeatherService(fetch_json=FakeProvider([]))
    assert service.forecast_url == "https://weather.example/v1/forecast"
    assert service.geocoding_url == "https://geo.example/search"
    assert service.timeout_seconds == 2.5


def test_invalid_environment_timeout_is_rejected(monkeypatch):
    monkeypatch.setenv("WEATHER_TIMEOUT_SECONDS", "not-a-number")
    with pytest.raises(ValueError):
        WeatherService()


def test_weather_endpoint_uses_application_service_and_returns_fallback():
    fake = FakeProvider([{"results": []}])
    with TestClient(app) as client:
        app.state.weather_service = WeatherService(fetch_json=fake)
        response = client.get("/weather/current", params={"location": "Unknown"})
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "location_not_found"
    assert response.json()["weather"] is None


def test_weather_endpoint_validates_missing_location():
    with TestClient(app) as client:
        response = client.get("/weather/current")
    assert response.status_code == 422
