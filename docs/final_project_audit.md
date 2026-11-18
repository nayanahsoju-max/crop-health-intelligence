# Final Project Audit

**Audit date:** 2026-09-30  
**Scope:** Stages 0–18 implementation and documentation, reviewed for the Stage 19 final audit.  
**Conclusion:** The repository contains a software-integrated crop-health prototype with a tested prediction workflow, but no production classifier artifact. Real production image inference is unavailable. Software tests do not establish agricultural validity or classifier performance.

## Audit status vocabulary

- **COMPLETE / TEST-VERIFIED:** implementation and relevant automated checks were found and passed. This does not imply scientific or field validation.
- **IMPLEMENTED / NOT VALIDATED:** implementation exists, but real-world, production, or external-service validation is absent.
- **PARTIAL:** some stated capability exists, with material implementation or evidence gaps.
- **NOT COMPLETE:** the objective is not currently delivered.

“Demonstrated” means a local build, controlled test, or other reproducible artifact was inspected. It does not mean a live production service was operated.

## Requirement traceability

| Requirement | Implementation location | Test/evidence inspected | Status | Limitation |
|---|---|---|---|---|
| Disease classification | `src/crop_health/classification/`, `configs/classification_config.yaml` | Training/inference tests, class mapping, smoke evaluation artifact | **PARTIAL** | Training and inference pipeline exist; production checkpoint is absent, so production inference is unavailable. |
| Severity estimation | `src/crop_health/severity/`, `configs/severity_config.yaml` | Unit/API tests for mask, bounds, category, missing/invalid mask, persistence | **IMPLEMENTED / NOT VALIDATED** | Requires an aligned PNG lesion mask; thresholds and estimator lack expert-field validation. |
| Grad-CAM | `src/crop_health/explainability/` | Tests cover association and nonfatal unavailability; smoke artifacts provide a pipeline demonstration | **IMPLEMENTED / NOT VALIDATED** | Explanatory visualization is not evidence of biological causality or model validity. |
| Disease knowledge base | `src/crop_health/knowledge_base/`, knowledge-base configuration/data | Record/source validation and recommendation tests | **COMPLETE / TEST-VERIFIED** | Coverage and geographic applicability are limited; local expert review remains necessary. |
| Weather integration | `src/crop_health/weather/`, weather configuration | Mocked tests for valid, invalid, timeout, provider-error, and unavailable cases | **IMPLEMENTED / NOT VALIDATED** | Live Open-Meteo behavior was not verified; weather is contextual, not a classifier input or causal proof. |
| Weather-aware recommendations | `src/crop_health/recommendations/`, `configs/recommendation_config.yaml` | Deterministic tests for confidence gate, weather context, safe fallbacks, rule/source traceability | **COMPLETE / TEST-VERIFIED** | Agricultural recommendations require domain/geographic validation. No product, dose, or treatment schedule is prescribed. |
| PostgreSQL persistence | `backend/app/models/`, repositories, Alembic migrations | SQLite-isolated persistence, repository/API tests, migrations exercised on temporary SQLite | **IMPLEMENTED / NOT VALIDATED** | PostgreSQL is the production target, but no live PostgreSQL deployment was tested. Uploaded image bytes are not stored. |
| FastAPI backend | `backend/app/` | Full pytest suite and endpoint contract tests | **COMPLETE / TEST-VERIFIED** | Runtime integration was tested locally and with controlled dependencies; public production operation is not established. |
| React frontend | `frontend/src/` | Vitest suite and production Vite build | **COMPLETE / TEST-VERIFIED** | Production build is verified; no live hosted frontend/backend deployment was performed. |
| Prediction history | Prediction routes/repository and frontend history views | Create/list/detail, pagination/filter, and frontend tests | **COMPLETE / TEST-VERIFIED** | History endpoints have no authentication or per-user isolation. |
| Analytics | Frontend history/analytics components | Tests for calculated summary, class/severity distributions, empty state | **COMPLETE / TEST-VERIFIED** | Metrics are calculated from the current page returned by the API; there is no global count endpoint. |
| Upload validation/security | Prediction API upload handling and frontend validation | Tests cover size/type/content/corrupt image and lesion-mask validation | **COMPLETE / TEST-VERIFIED** | Limits reduce application-level risk but are not a penetration/security assessment. |
| Health/readiness | FastAPI health routes | Endpoint tests and code inspection | **COMPLETE / TEST-VERIFIED** | `/health/ready` checks database connectivity and model-asset presence; it does not load weights, validate a complete production artifact, or prove inference readiness. |
| Deployment configuration | `scripts/`, environment examples, `docs/deployment.md` | Quality gate/build and local checks documented; no Docker or PostgreSQL deployment | **PARTIAL** | Infrastructure instructions/configuration exist. Docker, cloud hosting, and live PostgreSQL were not verified. |
| Automated quality checks | `scripts/quality_check.cmd`, Python and frontend test configuration | Quality gate run for this audit (results below) | **COMPLETE / TEST-VERIFIED** | No coverage percentage was established; test success is not model accuracy. |
| Documentation | `README.md`, `docs/`, `PROJECT_STATUS.md` | Link check and source-to-doc review; this audit records discrepancies/limits | **COMPLETE / TEST-VERIFIED** | Documentation describes a prototype and its gaps; external provider and deployment claims remain unverified. |

## Model readiness

- `models/classifier/production/` is absent. The configured seven class labels are `tomato_healthy`, `tomato_bacterial_spot`, `tomato_early_blight`, `tomato_late_blight`, `potato_healthy`, `potato_early_blight`, and `potato_late_blight`.
- Smoke-only checkpoint/mapping artifacts are under `models/classifier/smoke/`. The inference workflow rejects smoke-path artifacts and requires the configured production checkpoint and mapping. No smoke fallback is present.
- When the production artifact is missing, `POST /predict` returns the established `503 model_unavailable` response; it does not fabricate a class or confidence.
- Training, evaluation, preprocessing, deterministic stratified split, inference loading, class-map checks, and Grad-CAM compatibility code are implemented. Full EfficientNet-B0 training has not been performed.
- The smoke artifact describes 28 images (4 per class), one epoch, 14/7/7 train/validation/test, accuracy 0.1429 and macro-F1 0.0476. These are tiny pipeline-verification results only and must not be reported as classifier performance.
- The classifier is **partially implemented; production inference is unavailable and the classifier is not production-ready**. No real production predictions, accuracy, or diagnosis validity are established.
- Training defaults to a candidate output directory distinct from inference’s production path. The handoff describes a deliberate review/promotion step; operators must not copy a smoke artifact into production.

## Dataset integrity and scope

The configured class scope is seven labels listed above. Dataset roles documented in the repository are PlantVillage for the configured classification scope, PlantSeg for lesion-segmentation data/metadata, and PlantDoc as an external-only compatibility source for five supported disease classes. PlantDoc does not supply the two healthy classes in this scope.

The deterministic split implementation is stratified and seeded. Leakage remains a dataset risk if near-duplicate or related images are split across subsets. The dataset documentation flags the repeated/nested PlantVillage tree and class imbalance, including relatively few potato healthy examples; this audit did not re-hash the full image corpus or recompute dataset-wide statistics. PlantDoc compatibility is constrained by small per-class counts and domain differences. The configured validator was run and reported: seven configured classes matched on-disk labels/counts; 11,458 PlantSeg metadata rows had non-empty labels and valid splits with zero invalid rows; five disease classes mapped to PlantDoc, which remains external-only. These checks do not establish annotation quality or representativeness.

No dataset sizes, provenance, splits, or performance beyond existing repository evidence are inferred here.

## Severity, weather, recommendations, and traceability

Severity uses the provided lesion mask and estimated leaf foreground. The recorded calculation is diseased pixels divided by estimated leaf area, multiplied by 100 and bounded to 0–100; category boundaries are configuration-driven. The API requires an aligned PNG lesion mask; without one, status is `not_requested`. Invalid/misaligned masks are rejected safely, and tests exercise result propagation/persistence. Severity is **implemented but unvalidated against expert-scored field data**; it is not a validated agricultural severity measure.

The Open-Meteo adapter uses configurable geocoding/current-weather URLs and timeout. Invalid locations, provider errors, malformed responses, and timeouts become explicit unavailable outcomes. Automated tests mock provider calls. Weather is not passed into classification. The deterministic recommendation engine combines supported knowledge-base records with confidence and optional weather context, applies the configured confidence gate (default 0.5), and returns safe fallbacks for unsupported/low-confidence cases. Rule IDs and knowledge-base sources are retained. Weather does not establish disease cause; no LLM advice or pesticide products/doses/schedules were found in the implementation reviewed.

## API and frontend contract

The implemented routes inspected are `GET /health`, `GET /health/ready`, `GET /weather/current`, `POST /recommendations/current`, `POST /predictions`, `GET /predictions`, `GET /predictions/{record_id}`, and `POST /predict`. Pydantic schemas and route behavior support the documented JSON and multipart workflows. Prediction errors include model-unavailable, validation, persistence/database, and not-found cases as applicable. History detail retains the saved prediction/recommendation/weather/source metadata; timestamps and optional values are handled in the UI.

The frontend obtains its API origin from `VITE_API_BASE_URL`, validates uploads client-side and relies on backend validation, presents the structured prediction response, checks Grad-CAM data URLs, and supports history, class filtering, pagination, and page-scoped analytics. The initial UI does not include fabricated prediction records; deterministic sample values appear only in tests. Vite production build and frontend tests passed. The API contract is software-tested, not verified against a running production model.

## Database and deployment

SQLAlchemy models, repository operations, and ordered Alembic migrations are present. The application does not automatically create/migrate production tables on startup. Migration behavior was exercised against temporary SQLite; PostgreSQL remains the intended production database. No live PostgreSQL server was used for this audit.

Deployment documentation covers environment configuration, Uvicorn, frontend build, CORS, health/readiness, and migration ordering. Docker was unavailable/not verified; cloud deployment was not performed. A frontend build configured with an API base URL was previously reported as passing. Infrastructure configuration does not establish model readiness or diagnosis validity.

## Security and repository integrity observations

- Backend image and lesion-mask limits, decoded-image bounds, MIME/content checks, basename handling, and temporary-directory cleanup are present. JSON-only write routes have a 1 MiB body limit.
- CORS is environment-configured; wildcard origins are rejected. CORS is not authentication.
- Source links are constrained to HTTP(S); database integrity details are redacted from API errors. Environment examples use placeholders. A lightweight credential-pattern scan over relevant source/config paths found no hits; this is not a secret-management certification.
- **Access control is missing:** prediction write/history routes are unauthenticated and history is not partitioned by user. Do not expose the API publicly without a trusted access-control boundary and an appropriate privacy/security design.
- Generated caches and dependency output directories are ignored by `.gitignore`. This checkout did not contain a readable `.git` directory, so tracked/untracked state and commit hygiene could not be audited. No files were deleted during this audit.

## Verification performed

The existing quality gate `cmd.exe /c scripts\quality_check.cmd` passed:

- Python syntax validation: 56 files passed.
- Ruff: passed.
- Backend pytest: **89 passed**.
- Frontend Vitest: **30 passed**.
- Vite production build: passed.
- Quality gate: passed.

The configured dataset validation command also passed with the counts described above. Two existing third-party FastAPI/Starlette test-client deprecation warnings remain (httpx compatibility path and AnyIO `BlockingPortal` alias); they were not suppressed. Coverage was not measured. Live weather, live PostgreSQL, Docker, and cloud deployment were not tested.

## Final audit outcome and remaining work

Stages 0–19 are documented complete as project stages, with Stage 19 recording this audit. This does not mean every original system capability is scientifically validated or production-ready. The main outstanding work is production EfficientNet training/evaluation using a finalized, leakage-reviewed dataset; expert and geographic validation of severity and recommendations; a trusted access-control design before public exposure; and actual infrastructure/provider verification if deployment is pursued. Stage 19 makes no claim that those tasks have been completed.

### Stage 20 follow-up finding (2026-09-30)

The subsequent Stage 20 pre-training audit refined the earlier dataset limitation: SHA-256 checks over 8,779 selected PlantVillage images found 14 exact-duplicate groups, with seven crossing the generated train/validation/test boundaries. The existing split is therefore not suitable for independent evaluation. Training stopped before the sanity batch. The full dataset validator decoded 41,276 PlantVillage files, 814 PlantDoc images, and all 11,458 PlantSeg image/mask pairs; it found no unreadable files or missing pairs and zero oriented-size mismatches. It did not establish byte identity of the full nested tree or rule out perceptual near-duplicates. See the [Stage 20 report](stage20_classifier_training_report.md); no production model or metrics were produced.

### Stage 20B follow-up

The nested tree has since been hash-audited: it contains 20,638 files, including exact matches for all 8,779 selected records. A deterministic group-aware manifest was generated and independently verified; the near-duplicate check remains conservative and incomplete. Stage 20B did not train or evaluate a classifier. Details are in the [Stage 20B report](stage20b_leakage_safe_split_report.md).
