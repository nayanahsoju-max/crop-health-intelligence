# Deployment preparation

This document describes how to run the existing FastAPI service and React client as separate services. No cloud deployment was performed as part of this stage. Docker is not installed in the checked environment, so there is no Docker configuration or Docker verification. PostgreSQL deployment was not tested against a live server.

## Readiness and limits

Infrastructure readiness and ML model readiness are separate. `GET /health` is a lightweight process check and does not require a database or classifier. `GET /health/ready` checks database connectivity with `SELECT 1` and reports model asset availability without loading model weights or running inference. It returns 503 when the database is absent/unreachable; a missing classifier is reported as `model: unavailable` while the service can still be ready for non-inference routes.

Production prediction requires both a real classifier checkpoint and its matching class mapping. Supply them through `CROP_HEALTH_MODEL_CHECKPOINT` and `CROP_HEALTH_CLASS_MAPPING`; optionally set `CROP_HEALTH_MODEL_VERSION` and `CROP_HEALTH_DEVICE`. The smoke-test checkpoint and mapping are rejected. Without production artifacts, the process can start, but `POST /predict` returns the established `model_unavailable` response. Deployment preparation does not provide or validate a classifier.

## Development setup (local SQLite)

For local software work, SQLite and the Vite proxy are sufficient; this is not the production database configuration. From the repository root:

```powershell
$env:DATABASE_URL = "sqlite:///./data/crop_health_local.sqlite3"
$env:CORS_ALLOWED_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
python -m alembic -c alembic.ini upgrade head
.\scripts\start_backend.cmd
```

In another terminal, run `Set-Location frontend; npm.cmd ci; npm.cmd run dev`. The frontend normally runs on port 5173 and the backend on port 8000. SQLite migration behavior is covered using isolated temporary SQLite databases in tests; a persistent local SQLite file is optional developer state and should not be treated as deployed data.

## Prerequisites

- Python 3.11 (the project dependency environment supports Python 3.11–3.12).
- Node.js/npm compatible with the pinned frontend dependencies.
- PostgreSQL for deployed prediction history and inference persistence.
- A private process environment/secret manager for database credentials and deployment-specific settings.

From the project root, install backend dependencies into an isolated environment and install the frontend dependencies:

```powershell
python -m pip install -r requirements.txt
Push-Location frontend
npm.cmd ci
Pop-Location
```

The application does not automatically load `.env`. Set variables in the service/process environment. `.env.example` contains placeholders and local defaults only; never put real credentials into the repository.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Required for database-backed deployment; use `postgresql+psycopg://<user>:<password>@<host>:5432/<database>`. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated exact browser origins, such as `https://<frontend-host>`. No wildcard is accepted. |
| `API_HOST`, `API_PORT` | Backend bind settings used by `scripts/start_backend.cmd`; defaults are `0.0.0.0` and `8000`. |
| `API_WORKERS`, `API_LOG_LEVEL` | Uvicorn worker count and log level; defaults are `1` and `info`. Start with one worker unless the host's memory/model-loading behavior has been assessed. |
| `WEATHER_API_BASE_URL` | Optional Open-Meteo forecast host override. |
| `WEATHER_FORECAST_URL`, `WEATHER_GEOCODING_URL` | Optional complete weather endpoint overrides. |
| `WEATHER_TIMEOUT_SECONDS` | Optional per-request weather timeout. |
| `CROP_HEALTH_MODEL_CHECKPOINT`, `CROP_HEALTH_CLASS_MAPPING` | Paths to separately supplied production model assets; no smoke artifact is accepted. |
| `CROP_HEALTH_MODEL_VERSION`, `CROP_HEALTH_DEVICE` | Optional model metadata/device settings. |

The prediction upload byte/dimension limits and 1 MiB JSON body limit remain enforced by the backend. Uploaded image bytes are held in a temporary directory and deleted after the request; only image metadata/hash is persisted.

## Database migration and startup order

PostgreSQL is the intended deployed database. Alembic owns schema changes; application startup does not create or mutate tables. Back up the database and review the target revision before migrating. Apply migrations as a release step before directing traffic:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://<user>:<password>@<host>:5432/<database>"
python -m alembic -c alembic.ini upgrade head
python -m alembic -c alembic.ini current
```

If a migration must be rolled back, inspect its downgrade and data impact first; `python -m alembic -c alembic.ini downgrade -1` reverses one revision and may discard schema/data. Restore from the database backup if rollback cannot safely preserve data. Do not run SQLite against deployed history data; SQLite is used for local checks and isolated tests.

## Backend service

Set the database and CORS variables in the service environment, apply migrations, install dependencies, then start Uvicorn. On Windows, the convenience command uses the configurable `API_*` values:

```powershell
.\scripts\start_backend.cmd
```

Or invoke Uvicorn directly on any supported host:

```text
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info
```

Set `API_HOST`, `API_PORT`, `API_WORKERS`, and `API_LOG_LEVEL` before running the helper. Do not enable debug mode in a public service; the application has no debug mode enabled by default. Keep logs and environment values free of secrets. Application errors return structured messages without filesystem paths or raw database exception text.

## Frontend build and hosting

Build the static React client with the backend origin embedded at build time. The origin must be the API origin only (no `/predict` suffix):

```powershell
Push-Location frontend
$env:VITE_API_BASE_URL = "https://<backend-host>"
npm.cmd ci
npm.cmd run build
Pop-Location
```

Host the generated `frontend/dist` directory with a static web server. Configure the backend with the matching exact origin, for example `CORS_ALLOWED_ORIGINS=https://<frontend-host>`. CORS permits the required GET/POST/OPTIONS methods and `Content-Type`, with credentials disabled. For local development, Vite proxies backend routes and the local origins are the default allow-list. `VITE_API_BASE_URL` is public client configuration, not a secret; do not place credentials or private keys in `VITE_*` values.

If a reverse proxy or TLS-terminating gateway is used, route the browser-visible API origin consistently with `VITE_API_BASE_URL`, preserve the API paths, and configure proxy request limits to permit the application's bounded image uploads (10 MiB per image/mask, plus multipart overhead). Configure the browser-visible frontend origin exactly in `CORS_ALLOWED_ORIGINS`. TLS certificates, proxy buffering/timeouts, and forwarded-header policy are host-specific and were not configured or tested in this repository. The API does not implement authentication or per-user history authorization; CORS does not provide access control, so do not expose these routes publicly without a trusted access-control boundary.

## Deployment verification

After startup, verify:

```text
GET https://<backend-host>/health
GET https://<backend-host>/health/ready
```

The first checks process health. The readiness response reports database and model availability separately. Check `GET /openapi.json` for the API contract and confirm browser requests from the configured frontend origin receive the expected CORS response. Validate the frontend against the backend without submitting real user images until a genuine production model has been separately prepared. A missing production model is expected to produce `model_unavailable`, not a fabricated result.

Automated SQLite migration and API tests plus the project quality gate provide local verification; they do not prove PostgreSQL, cloud-host, or network-proxy behavior. The deployment configuration does not establish classifier accuracy or agricultural diagnosis validity. No production checkpoint exists, full EfficientNet training has not been performed, and real production inference remains unavailable.
