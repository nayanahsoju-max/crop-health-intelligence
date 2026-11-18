# Stage 32: Multi-Crop Model Routing Report

**Date:** 2026-11-17  
**Status:** Completed and Verified  
**Scope:** Crop-specific classifier routing across Tomato, Potato, and Grape in the FastAPI backend without retraining or modifying existing model weights, manifests, or evaluations.

---

## 1. Executive Summary

In Stage 32, crop-specific routing was implemented in the AI-Powered Crop Health Intelligence System. The system now dispatches incoming prediction requests to either the 7-class Tomato-Potato classifier or the 3-class Grape classifier based on a required `crop` parameter.

Both trained models, checkpoints, class mappings, and split manifests remain strictly isolated and unmodified. An in-memory model cache was introduced to eliminate redundant disk weight reloads, and the endpoint enforces strict request validation returning HTTP 422 for missing or invalid crops.

---

## 2. Model Routing & Asset Isolation

The two models remain completely decoupled:

| Attribute | Tomato-Potato Route (`tomato_potato`) | Grape Route (`grape`) |
| :--- | :--- | :--- |
| **Supported Crops** | `tomato`, `potato` | `grape` |
| **Run ID** | `tomato-potato-2026-11-17-b` | `grape-2026-11-17-a` |
| **Model Architecture** | EfficientNet-B0 (7 classes) | EfficientNet-B0 (3 classes) |
| **Checkpoint Path** | `models/classifier/runs/tomato-potato-2026-11-17-b/efficientnet_b0_best.pt` | `models/classifier/runs/grape-2026-11-17-a/efficientnet_b0_best.pt` |
| **Checkpoint SHA-256** | `ff89f20e59c8475481d3da56ceec93e3586eedcf984663ff26a88d6362ed8a27` | `fdd8497e8ec7ac40de2f0aefd4eb498c2b83de4573e8e5e167c9cb88b0e17ae3` |
| **Class Mapping Path** | `models/classifier/runs/tomato-potato-2026-11-17-b/class_mapping.json` | `models/classifier/runs/grape-2026-11-17-a/class_mapping.json` |
| **Class Mapping SHA-256** | `1fd3233d017fe622281cbefbbd70db4e5c01b820fa8a585b515707e315ee423a` | `39aa1f0d0b781b83c586897b79afa8ff49a627aea21fda17f48014b4ffb0a5c7` |
| **Classes** | `tomato_healthy`, `tomato_bacterial_spot`, `tomato_early_blight`, `tomato_late_blight`, `potato_healthy`, `potato_early_blight`, `potato_late_blight` | `grape_black_rot: 0`, `grape_esca: 1`, `grape_isariopsis_leaf_blight: 2` |
| **Model Version** | `efficientnet_b0_tomato_potato_2026_11_17_b` | `efficientnet_b0_grape_2026_11_17_a` |

---

## 3. Implementation Details

### 3.1. Prediction Configuration (`configs/prediction_config.yaml`)
- Added structured `models` section declaring route entries for `tomato_potato` and `grape`.
- Preserved legacy top-level keys (`checkpoint_path`, `class_mapping_path`, `model_version`) for backward compatibility.

### 3.2. Prediction Service (`backend/app/prediction_service.py`)
- **Route Resolution (`get_route`)**: Trims and normalizes crop strings to lowercase. Validates against configured crops (`grape, potato, tomato`). Raises `UploadValidationError(422, "invalid_crop", ...)` on missing or unsupported crops.
- **Model Caching (`get_loaded_model`)**: Maintains `self._model_cache` keyed by `(checkpoint_path, class_mapping_path, device)`. `load_classifier` is called once per checkpoint and subsequent inference/Grad-CAM passes reuse the cached model.
- **Grad-CAM Integration**: `_default_gradcam` runs activation analysis directly on the cached evaluation model, eliminating duplicate model loads on every request.
- **Readiness Checking (`ensure_model_available`)**: Checks the specific route when a crop is specified, or verifies all configured routes when called without arguments (for `/health/ready`).
- **History & Metadata**: Persists `crop` and `model_route` in `result_metadata`, sets `model_version` per route, and exposes `crop` in the return payload.

### 3.3. FastAPI API (`backend/app/main.py`)
- **Endpoint Signature**: Updated `POST /predict` to accept `crop: str | None = Form(default=None)`.
- **Validation**: Enforces non-blank crop input, raising HTTP 422 with `{"code": "invalid_crop", "message": "Crop is required and must be one of: grape, potato, tomato."}` when missing or invalid.
- **Response Schema**: Added `crop: str | None = None` to `PredictionResponse` Pydantic model.

### 3.4. Test Suite (`tests/test_prediction_api.py`)
- Added default `crop="tomato"` to `post_image` helper so existing test cases continue to test end-to-end flows.
- Updated `make_workflow` mocks to dynamically return Grape or Tomato-Potato class predictions depending on the routed checkpoint and mapping.
- Added comprehensive unit tests:
  1. `test_routing_tomato_routes_to_tomato_potato_model`: Verifies Tomato routes to 7-class checkpoint.
  2. `test_routing_potato_routes_to_tomato_potato_model`: Verifies Potato routes to 7-class checkpoint.
  3. `test_routing_grape_routes_to_grape_model`: Verifies Grape routes to 3-class checkpoint and safely triggers fallback recommendation (`unsupported_disease`).
  4. `test_crop_parameter_case_and_whitespace_tolerance`: Verifies case-insensitivity and trimming (`"  GrApE  "` -> `"grape"`).
  5. `test_invalid_crop_returns_422`: Verifies HTTP 422 with code `"invalid_crop"` for unsupported crops.
  6. `test_missing_crop_returns_422`: Verifies HTTP 422 with code `"invalid_crop"` for omitted crop field.
  7. `test_model_caching_loads_weights_only_once`: Verifies spy loader is called only once per model path.
  8. `test_crop_saved_in_history_metadata`: Verifies persistence records include crop and model route.

---

## 4. Verification and Test Results

### 4.1. Test Suites
- **`tests/test_prediction_api.py`**: 32 passed (100%).
- **`tests/test_persistence.py`**: 15 passed (100%).
- **`tests/test_recommendations.py`**: 13 passed (100%).
- **`tests/test_weather.py`**: 17 passed (100%).
- **Domain Tests (`mlenv`)**: 29 passed (100%) across splits, training safety, Grad-CAM, severity, knowledge base, and deployment configuration.
- **Total Tests Passing**: 106 tests passed, 0 failures.

### 4.2. Static Code Analysis (Ruff)
- Checked `backend/app/prediction_service.py`, `backend/app/main.py`, and `tests/test_prediction_api.py`.
- **Result:** `All checks passed!` (0 lint errors).

### 4.3. Asset Integrity Verification
All reference files, checkpoints, mappings, and split manifests were verified via SHA-256:
- `reports/grape_preparation/grape_classifier_split.csv`: `9978dff163509824a5af1457f5a597503cebbd284eaf928b62ccfa8066cafcb1` (UNMODIFIED)
- `reports/classification/runs/tomato-potato-2026-11-17-b/split_manifest.csv`: `40b08f14a9085b26004633fb9123159766ba795892bc6afc483a3f4e76de64bc` (UNMODIFIED)
- `models/classifier/runs/tomato-potato-2026-11-17-b/efficientnet_b0_best.pt`: `ff89f20e59c8475481d3da56ceec93e3586eedcf984663ff26a88d6362ed8a27` (UNMODIFIED)
- `models/classifier/runs/grape-2026-11-17-a/efficientnet_b0_best.pt`: `fdd8497e8ec7ac40de2f0aefd4eb498c2b83de4573e8e5e167c9cb88b0e17ae3` (UNMODIFIED)
- `src/crop_health/knowledge_base/diseases.json`: `4081894b66a8b3ba5bbb51dc9dfaa34c1e8375a896050bd18bbc66302b07a5d1` (UNMODIFIED)

---

## 5. Scope Boundary Compliance

- No models were retrained.
- No model weights or checkpoints were modified.
- No class mappings were merged or altered.
- Knowledge base (`diseases.json`) and recommendation configs remain untouched.
- Frontend files remain untouched.
- Grape predictions safely return `"status": "safe_fallback"` and `"prediction_status": "unsupported_disease"`, awaiting Knowledge Base expansion in Stage 33.
