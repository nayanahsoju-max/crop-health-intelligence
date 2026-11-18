# Project guide

## Problem and objective

Crop leaf symptoms can be difficult to interpret from an image alone. This project builds an educational decision-support application that joins a configured image-classification pipeline with optional severity estimation, visual explanation, cited disease information, contextual weather, and traceable management guidance. It does not replace field diagnosis or local agricultural extension advice.

The objective is a connected software workflow with safe behavior when evidence or services are missing. The software pipeline is implemented; the production classifier is not trained or available.

## System architecture

```mermaid
flowchart TB
  Person[Grower / demonstrator] --> UI[React + Vite]
  UI -->|POST /predict: multipart image, optional location/mask| API[FastAPI]
  API --> VALIDATE[Bounded upload validation + preprocessing]
  VALIDATE --> MODEL[EfficientNet-B0 inference adapter]
  MODEL --> SEVERITY[Optional aligned lesion-mask severity]
  MODEL --> CAM[Class-specific Grad-CAM]
  MODEL --> ENGINE[Recommendation engine]
  SEVERITY --> ENGINE
  ENGINE --> KB[Structured cited disease KB]
  ENGINE --> WEATHER[Open-Meteo, optional context]
  API --> REPO[SQLAlchemy repository]
  REPO --> DB[(PostgreSQL deployment / SQLite isolated development tests)]
  API --> UI
  UI -->|GET /predictions and /predictions/{id}| API
```

The main pieces are:

- `src/crop_health/`: reusable domain logic and data adapters.
- `backend/app/`: HTTP contracts, prediction orchestration, database lifecycle, and persistence integration.
- `frontend/`: upload/result experience and backend-backed history/analytics.
- `configs/`: explicit class mappings, model/training settings, thresholds, provider values, and upload limits.
- `alembic/`: versioned database schema changes.

## End-to-end data flow

1. The browser validates a selected JPEG, PNG, or WEBP file, shows a preview, and submits multipart `image`, optional `location`, and optional PNG `lesion_mask` fields to `POST /predict`.
2. FastAPI validates filename extension, declared media type and decoded image content; enforces byte and dimension bounds; and writes uploads only into a temporary directory that is cleaned after the request.
3. The prediction workflow checks for both configured production artifacts. It reuses the shared EXIF-aware classification preprocessing and inference service. If model assets are absent or point to smoke artifacts, the API returns `model_unavailable`; no class result is fabricated.
4. When a real model is available, the predicted class/confidence/probabilities feed the recommendation engine. An aligned lesion mask can also be processed by the current severity estimator. Grad-CAM is requested for the predicted class, but a Grad-CAM failure is nonfatal.
5. For supported class/confidence input, the deterministic recommendation engine retrieves the exact disease entry. When a location is provided it requests current weather; weather is optional and contextual. Rule IDs and knowledge-base source references are retained.
6. The repository persists the returned prediction and metadata. The API responds with the result and saved history ID; the browser displays the fields it received.
7. History uses `GET /predictions` with pagination and exact class filtering. Selecting a record uses `GET /predictions/{record_id}`. The frontend analytics summarize only the currently loaded page because the endpoint does not provide a total-count field.

## Component responsibilities and limits

### Classification

The configured classification scope contains seven labels: `tomato_healthy`, `tomato_bacterial_spot`, `tomato_early_blight`, `tomato_late_blight`, `potato_healthy`, `potato_early_blight`, and `potato_late_blight`. The training module uses torchvision EfficientNet-B0 with pretrained ImageNet weights and a replacement class head. **Full configured production training has not been run.** The existing one-epoch smoke artifact validates code paths only; it is deliberately rejected by API inference.

### Severity

The current deterministic baseline requires an aligned PNG lesion mask. It estimates visible leaf area with an HSV/morphology foreground approximation, counts disease-mask pixels, and computes `diseased leaf area / estimated leaf area × 100`. Configured categories currently use the demonstration thresholds in `configs/severity_config.yaml`. With no mask, the API returns `severity.status: "not_requested"`. Neither the leaf-area estimate nor category cutoffs have expert-field validation.

### Confidence and Grad-CAM

Confidence is the classifier's probability for the selected class. Grad-CAM is a class-specific visualization of image regions influencing that class score. They communicate different information. A heatmap does not prove that a highlighted region is a biological symptom or that the class is correct; if Grad-CAM cannot be produced, prediction may continue with `explainability.status: "unavailable"`.

### Knowledge base and recommendations

`src/crop_health/knowledge_base/diseases.json` provides structured disease/status descriptions, symptoms, prevention and general management, weather associations, and cited sources for the configured classes. `RecommendationEngine` applies a configurable confidence gate (default `0.5`), returns safe fallback output for unsupported/low-confidence input, and attaches knowledge-base/rule provenance to guidance. It does not use an LLM to invent advice and does not provide pesticide product, dosage, or schedule recommendations. Content and geographic suitability still need domain validation.

### Weather

The Open-Meteo adapter geocodes the optional place name and fetches current conditions with configurable URLs and timeout. A failure, unknown place, malformed response, or timeout returns unavailable status. Weather is used only as optional context by recommendations; it is neither fed into disease classification nor evidence of causation. Automated tests mock the provider; no live service check is claimed.

### Persistence and frontend

SQLAlchemy maps prediction history records, while Alembic controls schema changes. PostgreSQL is the intended deployed database; test migrations use temporary SQLite. Rows retain class/confidence, optional severity, weather, recommendation/source/rule snapshots, model version, image filename/type/hash metadata, and timestamp. Image bytes are not stored.

The React interface supports upload, optional context/mask, structured result display, safe Grad-CAM data URLs, history/detail, filtering, pagination, and page-scoped analytics. It maps backend errors to readable messages and does not ship hardcoded prediction examples.

## API and deployment

The main routes are `GET /health`, `GET /health/ready`, `GET /weather/current`, `POST /recommendations/current`, `POST /predict`, and prediction history create/list/detail under `/predictions`. Consult the [API reference](prediction_api.md) for request schemas and error codes.

Deployment configuration separates a Uvicorn API service from a static Vite build, configures origins with `CORS_ALLOWED_ORIGINS`, and applies Alembic before traffic. PostgreSQL and Docker deployment were not verified on the development machine. Infrastructure readiness does not imply model readiness, classifier performance, or agricultural diagnosis validity. See [deployment](deployment.md) and [limitations](limitations.md).
