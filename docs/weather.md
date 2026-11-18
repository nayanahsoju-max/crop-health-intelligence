# Weather context integration

The domain adapter in `src/crop_health/weather/service.py` uses Open-Meteo's geocoding endpoint to resolve a place name, then requests current conditions from its forecast endpoint. It returns the resolved place, coordinates, timezone, observation time, temperature (°C), relative humidity (%), precipitation (mm), and wind speed (km/h). Weather is contextual information; it does not establish disease causation.

## API

`GET /weather/current?location=Pune` returns the service payload. When a place cannot be resolved or the provider is unavailable, the endpoint returns an explicit `status: "unavailable"`, an error code and message, and `weather: null`. A missing or blank query is rejected by request validation (HTTP 422 for a missing query); a whitespace-only value is handled by the service as `invalid_location`. Provider failures do not produce fabricated or stale measurements.

The FastAPI lifespan loads project configuration and creates the weather service. The route calls the synchronous adapter from a normal FastAPI `def` handler, so network I/O is run in FastAPI's worker pool.

## Configuration

Defaults are in `configs/weather_config.yaml`. Optional environment variables override them:

- `WEATHER_API_BASE_URL` changes the forecast API host; `/v1/forecast` is appended. The geocoding host remains Open-Meteo's separate geocoding service unless overridden.
- `WEATHER_FORECAST_URL` sets the complete forecast URL and takes precedence over the base URL.
- `WEATHER_GEOCODING_URL` sets the complete geocoding URL.
- `WEATHER_TIMEOUT_SECONDS` sets the per-request timeout; it must be a positive number.

Both endpoint URLs must use HTTPS. The timeout applies independently to geocoding and forecast requests. No API key is required by the configured Open-Meteo endpoints. `.env.example` lists the optional settings; the application reads process environment variables and does not automatically load a `.env` file.

## Verification

`tests/test_weather.py` uses an injected fake provider, so tests make no live network calls. It covers URL construction, successful geocoding and current conditions, unknown places, invalid and incomplete provider responses, HTTP/network errors, timeout handling, environment overrides, and the FastAPI route.
