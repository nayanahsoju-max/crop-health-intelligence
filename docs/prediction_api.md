# API usage and prediction workflow

This is the API reference for the existing FastAPI application. Interactive OpenAPI documentation is served at `/docs`; schema JSON is at `/openapi.json`. The API process can start without a database or production classifier, but database-backed routes and real image prediction require their corresponding services/artifacts.

## Endpoint summary

| Method | Path | Request | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | None | Lightweight process health. |
| `GET` | `/health/ready` | None | Checks database connection and separately reports model asset availability. |
| `GET` | `/weather/current` | `location` query parameter | Geocode a place and retrieve current weather, or return unavailable status. |
| `POST` | `/recommendations/current` | JSON `RecommendationRequest` | Deterministic knowledge-base recommendations for caller-supplied class/confidence and optional context. |
| `POST` | `/predictions` | JSON `PredictionRecordCreate` | Persist an already-produced result snapshot; it does not perform inference. |
| `GET` | `/predictions` | `limit`, `offset`, optional `class_id` query | Return newest-first prediction history. |
| `GET` | `/predictions/{record_id}` | Record ID path parameter | Retrieve one stored prediction snapshot. |
| `POST` | `/predict` | Multipart form | Validate image, run production inference workflow, and persist its output. |

JSON requests to `/predictions` and `/recommendations/current` are limited to 1 MiB. `/predict` uses its separate streamed image/mask byte and dimension limits.

## Health endpoints

### `GET /health`

Returns HTTP 200 with `{"status":"ok"}`. This lightweight process check does not connect to PostgreSQL or load model weights.

### `GET /health/ready`

Checks configured database connectivity with `SELECT 1`; it does not check migration revision and does not load model weights. It reports the database and production asset status separately:

- HTTP 200: `status` is `ready`, database is available, and model is `available` or `unavailable`.
- HTTP 503: `status` is `not_ready` and database is unavailable/unconfigured; model status is still reported.

The response contains `checks.database` and `checks.model`. A missing model does not make non-inference routes unavailable. `POST /predict` still returns `model_unavailable` in that state.

## `GET /weather/current`

Required query: `location` (1–120 characters). Example request:

```powershell
curl.exe "http://127.0.0.1:8000/weather/current?location=<place-name>"
```

An available response contains `status`, provider, resolved location/coordinates/timezone, observation time, and weather measures (`temperature_c`, `relative_humidity_percent`, `precipitation_mm`, `wind_speed_kmh`). A provider error, timeout, invalid place, or malformed response returns an explicit `status: "unavailable"`, `weather: null`, and an error object; the service does not fabricate or reuse stale readings. A missing query or out-of-range length is rejected by FastAPI validation (HTTP 422); a whitespace-only location is handled by the service as `invalid_location`. Automated tests mock weather calls; a live Open-Meteo response is not claimed.

Provider configuration is in `configs/weather_config.yaml` and may be overridden with `WEATHER_API_BASE_URL`, `WEATHER_FORECAST_URL`, `WEATHER_GEOCODING_URL`, and `WEATHER_TIMEOUT_SECONDS`. See [weather integration](weather.md).

## `POST /recommendations/current`

Consumes JSON with these Pydantic fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `class_id` | string, 1–120 characters | Candidate class ID. |
| `confidence` | number | Caller-supplied classifier confidence; recommendation engine validates its usable range. |
| `severity` | object, string, or null | Optional severity context. |
| `location` | string or null, maximum 120 characters | Optional place for weather context. |

The engine returns a structured recommendation with `status`, `prediction_status`, candidate prediction/severity context, disease information (or null), `general_guidance`, `weather_context`, `weather_guidance`, and `message`. Guidance carries knowledge-base source references and configured rule IDs. Below the configured 0.5 default confidence threshold or for unsupported/malformed classes, it uses safe fallback behavior without disease-specific content. Weather unavailable or omitted preserves disease-based guidance and reports why weather guidance could not be generated. Values in a request are caller-provided inputs, not proof of an actual classifier prediction.

## Persistence/history endpoints

### `POST /predictions`

Creates a record from JSON; returns HTTP 201 and the serialized record. This route stores data supplied by its caller and **does not run the classifier**. Fields are:

- Required `class_id` (nonblank, max 120) and `confidence` (`0`–`1`).
- Optional `severity`, `weather_context`, `recommendation_result`, `result_metadata` objects.
- Optional `model_version` (max 120).
- Optional `image_reference` object with `filename`, `media_type`, 64-character hexadecimal `sha256`, and `storage_uri`; extra image-reference keys are rejected.

The serializer returns `id`, `predicted_class_id`, `confidence`, `severity`, `weather_context`, `recommendation_result`, `result_metadata`, `model_version`, optional `image_reference`, and `created_at`. Invalid schema/constraints return 422. Unconfigured database returns 503. The endpoint's 1 MiB JSON request bound is enforced before body parsing.

### `GET /predictions`

Query parameters: `limit` (default 50, range 1–200), `offset` (default 0, nonnegative), and optional exact `class_id` (1–120 characters). Returns a JSON array newest-first, ordered by timestamp and then ID. There is no total-count response field; the frontend fetches pages and computes analytics over its current page.

### `GET /predictions/{record_id}`

Returns the same serialized stored snapshot as the list item, with full nested metadata, or HTTP 404 when the ID is not found. History endpoints return HTTP 503 when the database is not configured. A database that becomes unreachable can cause a server-side database error; check `/health/ready` and backend logs without exposing connection credentials.

These endpoints preserve recommendation/source/rule traceability stored by the prediction workflow. They do not store original image bytes; metadata and SHA-256 are persisted. See [database documentation](database.md).

## `POST /predict`

Multipart form fields:

| Field | Required | Details |
| --- | --- | --- |
| `image` | Yes | JPEG, PNG, or WEBP with matching filename extension, media type, and decoded content. Default maximum is 10 MiB; dimensions/pixels are also bounded in `configs/prediction_config.yaml`. |
| `location` | No | Place name, maximum 120 characters, passed to optional weather/recommendation context. |
| `lesion_mask` | No | PNG mask that must align with the image after EXIF orientation; default maximum is 10 MiB. Needed for the current severity estimate. |

Example request only (no classifier output is implied):

```powershell
curl.exe -X POST http://127.0.0.1:8000/predict `
  -F "image=@<leaf-image.jpg>;type=image/jpeg" `
  -F "location=<optional-place-name>"
```

The workflow validates and decodes uploads, applies the existing classification preprocessing, checks the production checkpoint and mapping, invokes classifier inference, optional severity and Grad-CAM, knowledge base/weather/recommendations, persists the result, and returns a structured response. A successful response includes:

- `status`, `prediction_status`, `recommendation_status`;
- `prediction.class_id`, `prediction.confidence`, optional class `probabilities`;
- `model.version`;
- `severity.status` and optional `severity.estimate`;
- `disease_information`, `general_guidance`;
- `weather_context`, `weather_guidance`, and optional `recommendation_message`;
- `explainability.status` and bounded JPEG data URLs/dimensions when available;
- `history.record_id` and `history.created_at`.

No concrete successful prediction response is shown because the production checkpoint is absent. Until both real production assets are supplied, valid image requests return HTTP 503 with `detail.code: "model_unavailable"`; the smoke checkpoint and mapping are never used. If weather is unavailable, prediction can still succeed when a production model/database are available. Grad-CAM failure is nonfatal. Persistence must succeed for `/predict` to return a completed result.

Typical errors:

| HTTP | Code / condition | Meaning |
| --- | --- | --- |
| 400 | `invalid_image`, `empty_upload`, `missing_filename` | Empty or undecodable upload. |
| 413 | `upload_too_large`, `image_dimensions_too_large` | Configured byte or image-dimension bound exceeded. |
| 415 | `unsupported_image_type`, `unsupported_image_content`, `content_type_mismatch` | Unsupported or inconsistent image type/extension/content. |
| 422 | invalid/misaligned lesion mask or form validation | Request data or mask is invalid. |
| 503 | `model_unavailable` | Production checkpoint/mapping is absent, rejected, or unusable. |
| 503 | `database_unavailable` | History storage is not configured/available. |
| 503 | `persistence_failed` | Result could not be safely saved; no successful history ID is returned. |

Error bodies use FastAPI's `detail` field; workflow errors contain a stable `code` and safe `message`. Internal paths, stack traces, and raw database exceptions are not returned.

## CORS and frontend

`CORS_ALLOWED_ORIGINS` accepts comma-separated explicit HTTP(S) origins; wildcard origins are rejected and credentials are disabled. In production, configure the exact browser frontend origin. The Vite production client uses `VITE_API_BASE_URL`; blank uses the local Vite proxy. See [frontend](frontend.md) and [deployment](deployment.md).
