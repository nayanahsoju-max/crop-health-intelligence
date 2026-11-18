"""Open-Meteo geocoding and current weather, with explicit unavailable states."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yaml


def _fetch_json(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "crop-health-intelligence/0.1"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class WeatherService:
    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        fetch_json: Callable[[str, float], dict[str, Any]] = _fetch_json,
        timeout_seconds: float | None = None,
    ) -> None:
        default_config = Path(__file__).resolve().parents[3] / "configs/weather_config.yaml"
        path = Path(config_path) if config_path else default_config
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("Weather configuration must be a YAML mapping")
        base_url = os.getenv("WEATHER_API_BASE_URL", "").rstrip("/")
        self.geocoding_url = os.getenv("WEATHER_GEOCODING_URL") or config.get("geocoding_url")
        self.forecast_url = os.getenv("WEATHER_FORECAST_URL") or config.get("forecast_url")
        if base_url:
            self.forecast_url = base_url + "/v1/forecast"
        configured_timeout = os.getenv("WEATHER_TIMEOUT_SECONDS", config.get("timeout_seconds", 8))
        self.timeout_seconds = float(timeout_seconds if timeout_seconds is not None else configured_timeout)
        if not isinstance(self.geocoding_url, str) or not isinstance(self.forecast_url, str):
            raise ValueError("Weather geocoding_url and forecast_url must be configured")
        if not self.geocoding_url.startswith("https://") or not self.forecast_url.startswith("https://"):
            raise ValueError("Weather provider URLs must use HTTPS")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.fetch_json = fetch_json

    def current(self, location: str) -> dict[str, Any]:
        query = location.strip()
        if not query:
            return self._unavailable("invalid_location", "A location name is required.")
        try:
            geo = self.fetch_json(self.geocoding_url + "?" + urlencode({"name": query, "count": 1, "language": "en", "format": "json"}), self.timeout_seconds)
            if not isinstance(geo, dict):
                return self._unavailable("provider_error", "Location service returned an invalid response.")
            places = geo.get("results") or []
            if not isinstance(places, list):
                return self._unavailable("provider_error", "Location service returned an invalid response.")
            if not places:
                return self._unavailable("location_not_found", "No matching location was found.")
            place = places[0]
            lat, lon = place.get("latitude"), place.get("longitude")
            if not self._is_number(lat) or not self._is_number(lon):
                return self._unavailable("provider_error", "Location service returned incomplete coordinates.")
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                "timezone": "auto",
            }
            forecast = self.fetch_json(self.forecast_url + "?" + urlencode(params), self.timeout_seconds)
            if not isinstance(forecast, dict):
                return self._unavailable("provider_error", "Weather service returned an invalid response.")
            current = forecast.get("current")
            if not isinstance(current, dict):
                return self._unavailable("provider_error", "Weather service returned no current conditions.")
            required = ("temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "time")
            if any(current.get(key) is None for key in required):
                return self._unavailable("provider_error", "Weather service returned incomplete current conditions.")
            measures = ("temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m")
            if any(not self._is_number(current[key]) for key in measures):
                return self._unavailable("provider_error", "Weather service returned invalid current conditions.")
            return {
                "status": "available",
                "provider": "Open-Meteo",
                "location": {
                    "name": place.get("name", query), "country": place.get("country"),
                    "latitude": lat, "longitude": lon, "timezone": forecast.get("timezone"),
                },
                "observed_at": current["time"],
                "weather": {
                    "temperature_c": current["temperature_2m"],
                    "relative_humidity_percent": current["relative_humidity_2m"],
                    "precipitation_mm": current["precipitation"],
                    "wind_speed_kmh": current["wind_speed_10m"],
                },
                "error": None,
            }
        except HTTPError:
            return self._unavailable("provider_error", "Weather provider returned an unsuccessful response.")
        except (TimeoutError, URLError) as exc:
            if isinstance(exc, URLError) and isinstance(exc.reason, TimeoutError):
                return self._unavailable("timeout", "Weather provider request timed out.")
            if isinstance(exc, TimeoutError):
                return self._unavailable("timeout", "Weather provider request timed out.")
            return self._unavailable("provider_unavailable", "Weather provider could not be reached.")
        except (ValueError, TypeError, KeyError, json.JSONDecodeError, AttributeError):
            return self._unavailable("provider_error", "Weather provider returned an invalid response.")

    @staticmethod
    def _is_number(value: Any) -> bool:
        return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)

    @staticmethod
    def _unavailable(code: str, message: str) -> dict[str, Any]:
        return {"status": "unavailable", "provider": "Open-Meteo", "location": None, "observed_at": None, "weather": None, "error": {"code": code, "message": message}}
