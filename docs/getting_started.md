# Getting started

This guide starts the existing local application on Windows. It does not train or evaluate the production classifier.

## Prerequisites

- Windows PowerShell or Command Prompt.
- Python 3.11 (project metadata supports Python 3.11–3.12).
- Node.js/npm compatible with the Vite dependencies.
- Git checkout plus the configured data only if you intend to train later. The API/UI can start without local training datasets.

## 1. Create the Python environment

From the repository root, create and activate a clean environment. A Conda example:

```powershell
conda create -n crop-health python=3.11 -y
conda activate crop-health
python -m pip install -e .
```

The declared requirements include backend, ML, test, and quality-check packages. For an existing suitable environment, `python -m pip install -r requirements.txt` is the alternative. The package installs the `crop_health` domain module; run commands from the repository root so `backend`, `configs`, and Alembic files resolve correctly.

## 2. Install frontend packages

```powershell
Set-Location frontend
npm.cmd ci
Copy-Item .env.example .env
```

Leave `VITE_API_BASE_URL` blank for local development; Vite proxies the API requests to `http://127.0.0.1:8000`. To point the browser directly at another API origin, set `VITE_API_BASE_URL` in `frontend/.env` and allow the frontend origin in backend CORS. `VITE_*` values are public client settings, never secrets.

## 3. Configure backend environment

The backend reads process environment variables; it does not automatically load a `.env` file. Set them in the same PowerShell session used to run the backend. The repository `.env.example` is a template and contains a placeholder database URL, not usable credentials.

For isolated local development, use SQLite:

```powershell
Set-Location ..
$env:DATABASE_URL = "sqlite:///./data/crop_health_local.sqlite3"
$env:CORS_ALLOWED_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
$env:API_HOST = "127.0.0.1"
$env:API_PORT = "8000"
$env:API_WORKERS = "1"
$env:API_LOG_LEVEL = "info"
```

SQLite is for local development/tests; PostgreSQL is the intended deployment database. For Open-Meteo, defaults are in `configs/weather_config.yaml`. Optional process overrides are `WEATHER_API_BASE_URL`, `WEATHER_FORECAST_URL`, `WEATHER_GEOCODING_URL`, and `WEATHER_TIMEOUT_SECONDS`. Provider failures are safe and produce unavailable weather context.

Production model variables are `CROP_HEALTH_MODEL_CHECKPOINT`, `CROP_HEALTH_CLASS_MAPPING`, `CROP_HEALTH_MODEL_VERSION`, and `CROP_HEALTH_DEVICE`. The defaults target `models/classifier/production/`. Do not point them at `models/classifier/smoke/`: smoke assets are rejected. No production checkpoint currently exists.

## 4. Apply the local database migration

From the repository root, using the same Python environment and `DATABASE_URL`:

```powershell
python -m alembic -c alembic.ini upgrade head
python -m alembic -c alembic.ini current
```

Alembic owns schema evolution. FastAPI does not create tables or run migrations at startup. Tests apply migrations to isolated temporary SQLite files and do not touch this local database.

## 5. Start the backend

```powershell
.\scripts\start_backend.cmd
```

The helper uses `API_HOST`, `API_PORT`, `API_WORKERS`, and `API_LOG_LEVEL`; defaults are `0.0.0.0`, `8000`, `1`, and `info`. For a loopback-only local API set `API_HOST=127.0.0.1`. Alternatively run `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload` for development reload.

Check process health and DB readiness:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/health/ready
```

`/health` returns `{"status":"ok"}` without loading the model or requiring the database. `/health/ready` returns HTTP 200 when a configured database connection works and includes separate `database` and `model` statuses. It returns 503 if the database is unconfigured/unreachable. The classifier is not loaded during either check.

The API documentation UI is at `http://127.0.0.1:8000/docs`.

## 6. Start the frontend

In a second terminal:

```powershell
Set-Location frontend
npm.cmd run dev
```

Open the URL printed by Vite (normally `http://localhost:5173`). The Vite proxy covers health, prediction/history, weather, and recommendation API paths. Browser requests are limited by the backend's explicit CORS origin configuration.

## 7. Expected model-unavailable behavior

The UI can load and non-inference endpoints can operate without a production classifier. `GET /health/ready` reports `model: unavailable`, and a valid multipart request to `POST /predict` returns HTTP 503 with code `model_unavailable` until both a separately trained production checkpoint and matching class mapping are supplied. The API never uses the one-epoch smoke checkpoint as a fallback and never fabricates a prediction. An unavailable model is an expected current project state.

## 8. Tests and frontend production build

From the repository root:

```powershell
python -m pytest -q
Push-Location frontend
npm.cmd test -- --run
npm.cmd run build
Pop-Location
```

Or run the full syntax/Ruff/backend/frontend/build gate:

```powershell
cmd.exe /c scripts\quality_check.cmd
```

To verify a production API origin is embedded at build time:

```powershell
Push-Location frontend
$env:VITE_API_BASE_URL = "https://<backend-host>"
npm.cmd run build
Remove-Item Env:VITE_API_BASE_URL
Pop-Location
```

Use a real configured backend origin for a deployment; the placeholder above is documentation only. See [deployment](deployment.md), [API reference](prediction_api.md), and [troubleshooting](troubleshooting.md).
