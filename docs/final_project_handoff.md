# Developer handoff

This handoff describes the current checkout for the next engineer. Stages 0–19 are complete. Stage 20 stopped before training due to leakage in the original split; Stage 20B created and independently verified a grouped manifest. Read both the [Stage 20 report](stage20_classifier_training_report.md) and [Stage 20B report](stage20b_leakage_safe_split_report.md) before any future classifier training. Do not mistake tested software integration or a clean split for a trained or validated classifier.

## 1. Complete

- Seven-class EfficientNet-B0 transfer-learning training and inference code, shared preprocessing, reproducible split logic, evaluation scripts, severity baseline, and Grad-CAM are implemented.
- Structured disease knowledge, Open-Meteo adapter, deterministic traceable recommendations, FastAPI endpoints, SQLAlchemy repository/models, and Alembic migrations are implemented.
- React/Vite upload/results/history dashboard and page-scoped analytics are implemented.
- Backend/frontend tests, Ruff/syntax checks, fail-fast quality gate, CORS, backend launcher, health/readiness, and setup/deployment docs are present.

## 2. Not complete / current constraints

- Full EfficientNet training has not been run. There is no production checkpoint or production class mapping. `/predict` intentionally returns `model_unavailable`; do not promote the smoke checkpoint.
- The original Stage 20 split is invalid. Stage 20B's replacement manifest at `reports/data_manifest/plantvillage_classifier_split.csv` passed independent hash/group/path verification; run the documented builder and verifier again if dataset files change. Near-duplicate detection remains limited. Training validates only train/validation image content and does not access test images; final test evaluation is a separately invoked command. No Stage 20 training metrics or artifact exist.
- Severity is provisional and requires an aligned PNG mask. Thresholds and HSV leaf-area approximation lack expert-field validation.
- Knowledge-base advice needs local expert/geographic review. Weather is contextual, external, and mocked in automated tests.
- PostgreSQL and Docker deployment have not been verified live. No cloud deployment has been performed.
- Classifier accuracy, field diagnosis validity, and agricultural outcomes have not been established.

## 3. Start locally

Prerequisites: Python 3.11–3.12 and Node/npm. See [getting started](getting_started.md) for complete setup. From the repository root, after activating the Python environment:

```powershell
$env:DATABASE_URL = "sqlite:///./data/crop_health_local.sqlite3"
$env:CORS_ALLOWED_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
python -m alembic -c alembic.ini upgrade head
.\scripts\start_backend.cmd
```

In another terminal:

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run dev
```

Check `GET /health`, `GET /health/ready`, and `/docs`. Health should be 200. Readiness requires a working configured database, but reports model status separately; with current artifacts it reports the model unavailable. `/predict` will not yield a real result until production artifacts exist.

## 4. Source map

- `src/crop_health/classification/`: model factory, training/split, and inference.
- `src/crop_health/preprocessing/`: shared classification and segmentation preprocessing.
- `src/crop_health/severity/`, `explainability/`: severity estimate and Grad-CAM.
- `src/crop_health/knowledge_base/`, `recommendations/`, `weather/`: sourced content, deterministic rules, and Open-Meteo client.
- `backend/app/`: routes, orchestration, database, models, repository, deployment config.
- `frontend/src/`: React workflow, centralized API client, history/analytics, tests.
- `configs/`: dataset/model/prediction/severity/weather/recommendation settings.
- `alembic/versions/`: database schema migrations.
- `reports/classification/smoke/`: tiny pipeline smoke outputs, not model results.

## 5. Configuration that matters

- `DATABASE_URL`: production PostgreSQL URL; local tests/development may use SQLite.
- `CORS_ALLOWED_ORIGINS`: exact comma-separated browser origins; no wildcard.
- `CROP_HEALTH_MODEL_CHECKPOINT`, `CROP_HEALTH_CLASS_MAPPING`, `CROP_HEALTH_MODEL_VERSION`, `CROP_HEALTH_DEVICE`: production inference asset settings. Default paths target `models/classifier/production/`.
- `WEATHER_API_BASE_URL`, `WEATHER_FORECAST_URL`, `WEATHER_GEOCODING_URL`, `WEATHER_TIMEOUT_SECONDS`: optional weather settings.
- `API_HOST`, `API_PORT`, `API_WORKERS`, `API_LOG_LEVEL`: launcher settings.
- `VITE_API_BASE_URL`: API origin embedded in the frontend at build time.

Backend does not auto-load the root `.env`; pass environment settings through the shell/service. See `.env.example` and `frontend/.env.example` for placeholders.

## 6. Main endpoints

- `GET /health`, `GET /health/ready`
- `GET /weather/current?location=...`
- `POST /recommendations/current`
- `POST /predict`
- `POST /predictions`, `GET /predictions`, `GET /predictions/{record_id}`

Exact request fields, limits, response fields, and error codes are in the [API reference](prediction_api.md).

## 7. Run tests and quality gate

```powershell
python -m pytest -q
Push-Location frontend
npm.cmd test -- --run
npm.cmd run build
Pop-Location
cmd.exe /c scripts\quality_check.cmd
```

The quality gate also runs in-memory Python syntax validation and Ruff. After Stage 20B changes: backend **94 passed**, frontend **30 passed**, syntax **59 files passed**, Ruff passed, build passed. Two third-party TestClient deprecation warnings remain. Coverage was not measured. Tests use temporary SQLite and mocked weather/inference rather than live PostgreSQL, network, or production weights.

## 8. Train and replace the production model when ready

The full-training command below is the configured training path; it was **not run** as part of this handoff. First run `python -m scripts.verify_leakage_safe_split` and review `docs/stage20b_leakage_safe_split_report.md`. Full training requires the saved grouped manifest, checks train and validation image hashes, and keeps the test partition untouched. Use new, run-specific output directories; the command refuses existing destinations:

```powershell
python -m crop_health.classification.training `
  --output-dir models/classifier/runs/tomato-potato-YYYYMMDD-HHMMSS `
  --report-dir reports/classification/runs/tomato-potato-YYYYMMDD-HHMMSS
```

This command trains the full configured model unless `--smoke-test` is supplied. It saves the selected checkpoint, class mapping, manifest copy/checksum, training config, history, and curves. It does not compute test metrics or access test images. After training and model selection are complete, run the separate final evaluator into another fresh directory:

```powershell
python -m scripts.evaluate_classifier `
  --model-dir models/classifier/runs/tomato-potato-YYYYMMDD-HHMMSS `
  --report-dir reports/classification/runs/tomato-potato-YYYYMMDD-HHMMSS `
  --output-dir reports/classification/evaluations/tomato-potato-YYYYMMDD-HHMMSS
```

The evaluator checks the run's saved manifest checksum and test-image hashes. Review its held-out metrics, per-class support, and external PlantDoc results, and obtain appropriate domain review. The smoke command/artifacts are for train/validation pipeline checks only.

Only after review should a selected candidate checkpoint and its matching `class_mapping.json` be deliberately installed under `models/classifier/production/` (or configured using `CROP_HEALTH_MODEL_CHECKPOINT` and `CROP_HEALTH_CLASS_MAPPING`), with `CROP_HEALTH_MODEL_VERSION` set appropriately. Re-run inference-contract and explainability checks against the real files. Do not copy the smoke artifact into production.

## 9. Before any production-readiness claim

Complete and document model evaluation on suitable held-out and external data, domain review of labels/recommendations, field validation of severity, production artifact/version control, PostgreSQL migration/backup/restore/rollback checks, host/reverse-proxy/CORS and upload-limit review, operational logging/monitoring, and real deployment smoke tests. These steps are beyond the current verification evidence.

## 10. Known warnings and next engineering work

- Two third-party warnings: Starlette TestClient's current httpx compatibility path and AnyIO's deprecated `BlockingPortal` alias.
- No live PostgreSQL, Docker, cloud host, or weather-provider verification.
- Frontend analytics remain page-scoped because history lacks total count.
- Smoke model metrics are not production performance.

The final audit found that the application has no authentication or per-user history isolation. Before any public exposure, establish a trusted access-control boundary and assess privacy/security needs. Any later model-training or production-infrastructure work requires separate authorization and evidence; do not claim classifier accuracy or diagnosis validity without validation.
