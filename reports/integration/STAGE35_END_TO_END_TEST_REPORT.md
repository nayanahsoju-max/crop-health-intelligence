# Stage 35 — End-to-End Application Testing Report

**Project:** AI-Powered Crop Health Intelligence System  
**Stage:** 35  
**Date:** 2026-11-18  
**Status:** ✅ COMPLETE

---

## 1. System Readiness Audit

Before launching services, a comprehensive environment, configuration, and dependency audit was performed:

| Component | Audit Observation | Status |
|---|---|---|
| **Backend Entry Point** | `backend.app.main:app` (FastAPI with lifespan managing database engines, models, weather, and recommendations). | ✅ Ready |
| **Startup Script** | `scripts/start_backend.cmd` runs uvicorn with configured host/port/workers. | ✅ Ready |
| **Backend Environment** | `C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe` contains FastAPI, Uvicorn, SQLAlchemy 2.x, Alembic, and PyTorch 2.14.0 CPU. | ✅ Ready |
| **Database Configuration** | Configured via `DATABASE_URL=sqlite:///./data/crop_health_local.sqlite3`. Migrations managed through Alembic. | ✅ Ready |
| **Database Migrations** | Ran `python -m alembic -c alembic.ini upgrade head` to apply revisions `0001_prediction_history` and `0002_prediction_result_metadata`. Verified at head revision. | ✅ Ready |
| **Weather Service** | Open-Meteo REST service (`https://api.open-meteo.com`) configured with graceful offline/unavailable fallbacks. | ✅ Ready |
| **Frontend Configuration** | React 18 + Vite client in `frontend/`. Proxies `/health`, `/predict`, `/predictions`, `/weather`, `/recommendations` to `http://127.0.0.1:8000`. | ✅ Ready |
| **Health & Readiness Endpoints** | `GET /health` and `GET /health/ready` check database and model availability. | ✅ Ready |
| **Classifier Models** | Tomato-Potato (7-class) and Grape (3-class) checkpoints and class mappings verified on disk. | ✅ Ready |

---

## 2. Startup Commands & Service Availability

The services were started and verified using the existing project configurations:

### 2.1 Backend Startup
```powershell
$env:DATABASE_URL="sqlite:///C:/Users/ASUS/Documents/crop-health-intelligence/data/crop_health_local.sqlite3"
$env:PYTHONPATH="C:\Users\ASUS\Documents\crop-health-intelligence;C:\Users\ASUS\Documents\crop-health-intelligence\src"
cd C:\Users\ASUS\Documents\crop-health-intelligence
C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --log-level info
```
- **Probe response (`GET /health`):** `{"status": "ok"}` (HTTP 200)
- **Probe response (`GET /health/ready`):** `{"status": "ready", "checks": {"database": "available", "model": "available"}}` (HTTP 200)

### 2.2 Frontend Startup
```powershell
cd C:\Users\ASUS\Documents\crop-health-intelligence\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
- **Local Origin:** `http://127.0.0.1:5173/` (HTTP 200)
- **Vite Proxy:** Verified proxying `/health` and `/health/ready` to backend uvicorn (HTTP 200).

---

## 3. Database Connectivity & Migration State

- **Database Engine:** SQLite (local development/staging persistent store at `data/crop_health_local.sqlite3`).
- **Alembic Revisions Applied:**
  1. `0001_prediction_history`: Created `prediction_records` table with constraints and indexes.
  2. `0002_prediction_result_metadata`: Added `result_metadata` column to store complete inference workflow metadata.
- **Current Revision:** `0002_prediction_result_metadata (head)` confirmed via `alembic current`.
- **Live Readiness Check:** Backend readiness check executes `SELECT 1` against the engine and reports `"database": "available"`.

---

## 4. Multi-Crop Prediction Workflow Results

Representative images from local datasets were evaluated against the live running API:

### 4.1 Tomato Workflow
- **Input Sample:** `data/PlantVillage/Tomato_Early_blight/0012b9d2-2130-4a06-a834-b1f3af34f57e___RS_Erly.B 8389.JPG`
- **Crop Selected:** `tomato`
- **Location:** `Pune`
- **HTTP Status:** 200 OK
- **Model Selected:** `models/classifier/runs/tomato-potato-2026-11-17-b/efficientnet_b0_best.pt`
- **Model Version Reported:** `efficientnet_b0_tomato_potato_2026_11_17_b`
- **Predicted Class:** `tomato_early_blight`
- **Confidence:** `0.999995` (99.9995%)
- **Top Probabilities:**
  - `tomato_early_blight`: 99.9995%
  - `tomato_late_blight`: 0.0004%
  - `potato_early_blight`: 0.0001%
- **Prediction Status:** `accepted`
- **Recommendation Status:** `available`
- **History Record ID:** `361f1c0a-af6b-45bf-b796-4ed643961637`

### 4.2 Potato Workflow
- **Input Sample:** `data/PlantVillage/Potato___Early_blight/001187a0-57ab-4329-baff-e7246a9edeb0___RS_Early.B 8178.JPG`
- **Crop Selected:** `potato`
- **Location:** `Shimla`
- **HTTP Status:** 200 OK
- **Model Selected:** `models/classifier/runs/tomato-potato-2026-11-17-b/efficientnet_b0_best.pt`
- **Model Version Reported:** `efficientnet_b0_tomato_potato_2026_11_17_b`
- **Predicted Class:** `potato_early_blight`
- **Confidence:** `0.999991` (99.9991%)
- **Top Probabilities:**
  - `potato_early_blight`: 99.9991%
  - `tomato_late_blight`: 0.0006%
  - `potato_late_blight`: 0.0001%
- **Prediction Status:** `accepted`
- **Recommendation Status:** `available`
- **History Record ID:** `372744aa-6c33-4f01-9450-2b059cd29596`

### 4.3 Grape Workflow
- **Input Sample:** `data/PlantVillage-Grape/Grape___Black_rot/00090b0f-c140-4e77-8d20-d39f67b75fcc___FAM_B.Rot 0376.JPG`
- **Crop Selected:** `grape`
- **Location:** `Nashik`
- **HTTP Status:** 200 OK
- **Model Selected:** `models/classifier/runs/grape-2026-11-17-a/efficientnet_b0_best.pt`
- **Model Version Reported:** `efficientnet_b0_grape_2026_11_17_a`
- **Predicted Class:** `grape_black_rot`
- **Confidence:** `0.997126` (99.7126%)
- **Top Probabilities:**
  - `grape_black_rot`: 99.7126%
  - `grape_isariopsis_leaf_blight`: 0.1952%
  - `grape_esca`: 0.0922%
- **Prediction Status:** `accepted`
- **Recommendation Status:** `available`
- **History Record ID:** `18ad580a-c50c-40c2-a851-60d13572ff1b`

---

## 5. End-to-End Pipeline Verification

### 5.1 Grad-CAM Generation
- **Target Layer:** Final convolutional feature map (`features[-1]` in EfficientNet-B0).
- **Fix Applied:** In `backend/app/prediction_service.py`, cached models are loaded with `with torch.inference_mode(mode=False):` and `_default_predictor` uses `@torch.no_grad()` to prevent model parameters from becoming frozen "inference tensors", allowing autograd backward passes during Grad-CAM generation.
- **Heatmap Data URL:** Valid base64 JPEG data URL generated for all crops (e.g. 7,859–8,235 bytes).
- **Overlay Data URL:** Valid base64 JPEG data URL blending original leaf and activation map (e.g. 17,119–27,059 bytes).
- **Explainability Status:** `available` across Tomato, Potato, and Grape live workflows.

### 5.2 Severity Estimation
- **Without Mask:** Returns `"status": "not_requested"`, `"estimate": null`. The UI cleanly renders "Severity needs an aligned lesion mask. Upload an optional PNG mask with the leaf image to request an estimate."
- **With Aligned PNG Mask:** Tested with an aligned 256×256 lesion mask:
  - **Status:** `"estimated"`
  - **Severity Percentage:** `11.19%`
  - **Category:** `"Moderate"`
  - **Diseased Leaf Area:** 4,096 pixels
  - **Estimated Leaf Area:** 36,604 pixels
  - **Method:** `hsv_green_foreground_with_lesion_mask`

### 5.3 Disease Knowledge Base Lookup
- All predicted classes mapped directly to knowledge base records:
  - `tomato_early_blight` → "Early blight" (7 general guidance items, source citations to extension guides).
  - `potato_early_blight` → "Early blight" (5 general guidance items, source citations to extension guides).
  - `grape_black_rot` → "Grape black rot" (6 general guidance items, source citations to OSU Extension PLPATH-FRU-24 & UC IPM).
- **Grape Coverage:** Replaced prior `unsupported_disease` fallback with full knowledge-base resolution and active guidance.

### 5.4 Weather Context & Recommendations
- **Available Context:** Live Open-Meteo API query for Pune, Shimla, and Nashik returned structured weather measurements (temperature, relative humidity, precipitation, wind speed).
- **Unrequested Context:** When location is omitted, weather status defaults to `not_requested` and guidance continues without weather rules.
- **Unavailable Context:** When given an invalid location (`NonExistentPlaceXYZ123456789`), the service safely returns structured unavailable context without failing the prediction.
- **Grape Esca Isolation:** Verified that Esca predictions intentionally receive no weather rules (trunk disease symptom expression is decoupled from short-term weather).

### 5.5 Prediction History Persistence
- Every prediction was committed to SQLite via `PredictionRepository`.
- Verified record retrieval: `GET /predictions?limit=10` lists all historical records newest-first.
- Verified individual retrieval: `GET /predictions/{record_id}` retrieves full metadata, stored probabilities, and recommendation traceability.

---

## 6. Error & Edge-Case Testing

The automated end-to-end error suite in `tests/test_e2e_verification.py` verified the following conditions:

| Test Case | Request Input | Expected Code | Observed Status | Detail Code | Status |
|---|---|---|---|---|---|
| **Missing Crop** | Image provided without `crop` field | 422 | 422 Unprocessable | `invalid_crop` | ✅ Passed |
| **Invalid Crop** | `crop="banana"` | 422 | 422 Unprocessable | `invalid_crop` | ✅ Passed |
| **Missing Image** | Multipart request without `image` | 422 | 422 Unprocessable | Standard validation error | ✅ Passed |
| **Unsupported Image** | `test.gif` (GIF media type) | 415 | 415 Unsupported Media | `unsupported_image_type` | ✅ Passed |
| **Corrupted Image** | Corrupt bytes with JPEG extension | 400 | 400 Bad Request | `invalid_image` | ✅ Passed |
| **Oversized Image** | 11 MiB payload (>10 MiB limit) | 413 | 413 Payload Too Large | `upload_too_large` | ✅ Passed |
| **Missing Location** | Valid image + crop, no location | 200 | 200 OK | `weather_context.status: not_requested` | ✅ Passed |
| **Weather Fallback** | Non-existent location query | 200 | 200 OK | `weather_context.status: unavailable` | ✅ Passed |

---

## 7. Frontend Visual Verification (Browser Subagent)

Visual UI verification was executed using the built-in browser agent directly interacting with the live application at `http://127.0.0.1:5173/`:

- **Host-Verified Navigation Origin:** `http://127.0.0.1:5173`
- **Blocked Origins:** None
- **Recorded Screenshot:** `browser_evidence/71e3c763-5058-4c77-957d-b53acf6595ac/final_step_10.png`

### Observed Behaviors:
1. **Crop Selector Visibility & Semantics:**
   - Crop selector group rendered clearly with "Tomato", "Potato", and "Grape".
   - "Tomato" radio was selected by default on initial page load.
2. **Crop Selection Switching:**
   - Clicking "Grape" unselected Tomato and Potato, visually highlighting the Grape option (`crop-option-selected`).
   - Clicking "Potato" updated state cleanly to Potato.
   - Clicking "Tomato" returned selection to Tomato.
3. **Prediction History View:**
   - Clicking "Prediction history" in the sidebar transitioned view smoothly.
   - Analytics summary displayed current page record counts and class distributions.
   - History table populated with previous live test runs with columns for Date, Predicted class, Confidence, Severity, Weather, and Model version.
4. **Detail Drawer:**
   - Clicking "Open result" on a history row opened the right-side detail drawer.
   - Rendered saved class name, confidence, severity status, disease description, symptoms, and extension sources.
5. **Sidebar Navigation:**
   - Navigating back to "Leaf analysis" restored the upload workspace and crop selector in default ready state.

---

## 8. Complete Regression Testing Suite

| Suite | Scope | Tests Run | Result | Notes |
|---|---|---|---|---|
| **Backend API Regression** | `tests/test_prediction_api.py`, `tests/test_persistence.py`, `tests/test_recommendations.py`, `tests/test_weather.py` | 82 passed | ✅ 100% | Pytest under `retail-forecast` env |
| **Domain Library** | `tests/test_knowledge_base.py`, `tests/test_classifier_splits.py`, `tests/test_classifier_grouped_splits.py`, `tests/test_classifier_training_safety.py`, `tests/test_explainability.py`, `tests/test_severity.py`, `tests/test_deployment_config.py` | 31 passed | ✅ 100% | Pytest under `mlenv` env |
| **Automated E2E Suite** | `tests/test_e2e_verification.py` | 3 test suites (history, 7 edge cases, weather fallback) | ✅ 100% | Live HTTP integration suite |
| **Frontend Vitest** | `frontend/src/api.test.js`, `frontend/src/App.test.jsx` | 52 passed | ✅ 100% | Vitest under jsdom |
| **Frontend Production Build** | `npm run build` | 17 modules | ✅ 100% | Vite client bundle generated in 302ms |
| **Ruff Code Linter** | `backend/app/`, `backend/app/prediction_service.py`, `tests/test_e2e_verification.py` | All files | ✅ Clean | All checks passed, 0 errors |

---

## 9. Code Modifications in Stage 35

In accordance with strict preservation guidelines, only the minimal targeted adjustments necessary for end-to-end operation were made:

1. **`backend/app/prediction_service.py` (2-line fix):**
   - Wrapped `model_loader` in `with torch.inference_mode(mode=False):` within `get_loaded_model()` and replaced `@torch.inference_mode()` with `@torch.no_grad()` on `_default_predictor`.
   - **Reason:** Resolved PyTorch autograd conflict where model weights cached during inference mode threw `RuntimeError: Inference tensors cannot be saved for backward` during subsequent Grad-CAM generation.
2. **`tests/test_e2e_verification.py` (New file):**
   - Automated end-to-end test script covering live database persistence, HTTP error mapping, and weather fallbacks.
3. **`data/crop_health_local.sqlite3` (Local database):**
   - Created and migrated local SQLite development database to revision `0002_prediction_result_metadata` to support live persistence testing.

---

## 10. Strict Preservation Audit

All protected assets remain byte-for-byte identical to baseline SHA-256 hashes:

| Protected File | Baseline SHA-256 | Verified SHA-256 | Audit Status |
|---|---|---|---|
| `models/classifier/runs/tomato-potato-2026-11-17-b/efficientnet_b0_best.pt` | `ff89f20e59c8475481d3da56ceec93e3586eedcf984663ff26a88d6362ed8a27` | `ff89f20e59c8475481d3da56ceec93e3586eedcf984663ff26a88d6362ed8a27` | ✅ Verified Unmodified |
| `models/classifier/runs/grape-2026-11-17-a/efficientnet_b0_best.pt` | `fdd8497e8ec7ac40de2f0aefd4eb498c2b83de4573e8e5e167c9cb88b0e17ae3` | `fdd8497e8ec7ac40de2f0aefd4eb498c2b83de4573e8e5e167c9cb88b0e17ae3` | ✅ Verified Unmodified |
| `models/classifier/runs/tomato-potato-2026-11-17-b/class_mapping.json` | `1fd3233d017fe622281cbefbbd70db4e5c01b820fa8a585b515707e315ee423a` | `1fd3233d017fe622281cbefbbd70db4e5c01b820fa8a585b515707e315ee423a` | ✅ Verified Unmodified |
| `models/classifier/runs/grape-2026-11-17-a/class_mapping.json` | `39aa1f0d0b781b83c586897b79afa8ff49a627aea21fda17f48014b4ffb0a5c7` | `39aa1f0d0b781b83c586897b79afa8ff49a627aea21fda17f48014b4ffb0a5c7` | ✅ Verified Unmodified |
| `reports/grape_preparation/grape_classifier_split.csv` | `9978dff163509824a5af1457f5a597503cebbd284eaf928b62ccfa8066cafcb1` | `9978dff163509824a5af1457f5a597503cebbd284eaf928b62ccfa8066cafcb1` | ✅ Verified Unmodified |
| `src/crop_health/knowledge_base/diseases.json` | `e3be2fdb8b179b03b05c120ed20a2d8bb77dece3dbdef2d964a8f1bb49b39997` | `e3be2fdb8b179b03b05c120ed20a2d8bb77dece3dbdef2d964a8f1bb49b39997` | ✅ Verified Unmodified |
| `configs/recommendation_config.yaml` | `ab83dd6500534d713fb48ae066f130499f622624f3891ca4ff97d5a3fc4aeee1` | `ab83dd6500534d713fb48ae066f130499f622624f3891ca4ff97d5a3fc4aeee1` | ✅ Verified Unmodified |

---

## 11. Remaining Issues & Manual Verification Notes

1. **Production PostgreSQL Deployment:** The local development and test suite utilizes SQLite via Alembic. In a containerized or cloud production deployment, `DATABASE_URL` should target PostgreSQL with `psycopg` as documented in `docs/database.md`.
2. **Third-Party Geocoding Limits:** The weather context relies on Open-Meteo's public API. In high-frequency production use, an API key or dedicated weather proxy should be configured to prevent upstream rate limiting.
3. **No Remaining Functional Blockers:** All endpoints, model routing, explainability, severity estimation, and frontend components operate as specified.

---

## 12. Conclusion

Stage 35 (End-to-End Application Testing) is **COMPLETE**. All services, pipelines, and UI flows have been thoroughly verified across Tomato, Potato, and Grape crops. Execution is halted awaiting user instruction.
