# Current limitations

This page separates implemented software behavior from evidence and infrastructure that are still missing. The system is educational decision support, not a validated agricultural diagnostic service.

## Classifier and datasets

- No trained production classifier checkpoint or production class mapping is available. Full EfficientNet-B0 training has not been run. Real production image inference remains unavailable and `POST /predict` returns `model_unavailable`.
- The existing one-epoch smoke model used 28 images (four per class) and a 14/7/7 train/validation/test split. Its 7-example test metrics (accuracy 0.1429 and macro-F1 0.0476) validate pipeline execution only; they are not production performance or useful generalization estimates.
- Development and smoke checks used a CPU-only environment. Suitable compute and reproducible full-run resources have not yet been established.
- The class scope is seven configured Tomato/Potato labels. Healthy classes are PlantVillage-only; the Potato healthy class is underrepresented in the audited data. PlantDoc is used only for external evaluation, and its mapped test subset is small. Label noise/compatibility and duplicate-tree leakage require continued care.

## Severity and explainability

- Severity estimation requires an aligned PNG lesion mask. Without it, the API returns `not_requested`; no severity estimate is produced.
- The current severity baseline approximates the leaf-area denominator using HSV/morphology foreground rules. Thresholds are configurable demonstration values, not universal thresholds.
- No expert-scored field severity dataset validates the estimator, percentage, or Mild/Moderate/Severe categories.
- Grad-CAM visualizes regions influencing a model class score. It is not proof of biological causality, a validated lesion mask, or evidence that the predicted class is correct. Grad-CAM failure is nonfatal.
- Class confidence is a model probability and has not been calibrated/validated for field use. It is distinct from Grad-CAM.

## Knowledge, advice, and weather

- Knowledge-base entries cover only configured supported classes. Unsupported classes return safe fallback content rather than invented disease details.
- Agricultural recommendations are deterministic summaries of sourced knowledge and configured contextual rules, but still require domain/expert validation and local geographic adaptation before operational use.
- The system does not recommend pesticide products, dosages, or treatment schedules.
- Weather is supplied by an external Open-Meteo service, is optional/contextual, and is not an input to the disease classifier or proof of disease cause. Provider calls were tested with mocks; no live-provider verification is claimed.

## Infrastructure and frontend

- PostgreSQL is the intended deployed persistence service, but a live PostgreSQL deployment was not verified. Automated migrations use temporary SQLite tests; SQLite is not a substitute production deployment target.
- Docker is unavailable in the checked environment. No Docker files or Docker deployment verification exist.
- No cloud deployment, reverse-proxy deployment, or production hosting was performed.
- API authentication, authorization, and per-user history isolation are not implemented. CORS is a browser-origin policy, not authentication; the unauthenticated write/history routes need a trusted network boundary or later access-control design before public exposure.
- History analytics are scoped to the currently loaded page because the history API has no total-count field.
- Prediction records keep metadata and SHA-256 but do not store uploaded image bytes.
- Automated software tests and integration mocks validate software contracts only. They do not establish production classifier accuracy, diagnosis validity, agricultural outcomes, or production readiness.
