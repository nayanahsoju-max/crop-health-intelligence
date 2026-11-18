# React frontend

The Vite/React client provides a crop-image analysis workflow and prediction history. It consumes the existing FastAPI contract; the backend remains responsible for inference, severity, weather context, source-traceable recommendations, Grad-CAM, and persistence.

## Run locally

From `frontend/`, install packages and start the Vite development server:

```powershell
npm.cmd install
npm.cmd run dev
```

By default, Vite proxies `/health`, `/predict`, `/predictions`, `/weather`, and `/recommendations` to `http://127.0.0.1:8000`. Set `VITE_API_BASE_URL` in `frontend/.env` to use a different API origin. The backend must allow that origin through its CORS configuration when the browser calls it directly. `VITE_MAX_UPLOAD_BYTES` configures the client-side byte limit (default 10 MiB); the backend independently enforces its own configured limit, which remains authoritative. `frontend/.env.example` lists these settings.

For a production frontend build, set `VITE_API_BASE_URL` to the deployed backend origin at build time. Configure that exact frontend origin in the backend's `CORS_ALLOWED_ORIGINS`; see [deployment instructions](deployment.md). Vite build-time variables are public and must not contain secrets.

Run the frontend tests and production build with `npm.cmd test` and `npm.cmd run build`.

## Workflow and response display

The analysis view accepts JPEG, PNG, and WEBP images, checks MIME/extension and file size, and previews the selected image. A location and PNG lesion mask are optional; the mask supports the backend's existing severity estimator. While a request is in progress the submit action is disabled. The app sends multipart fields `image`, optional `location`, and optional `lesion_mask` to `POST /predict`.

The result view renders the predicted class, confidence, probabilities when present, model version, severity status/result, disease information, general guidance, weather context, weather-specific guidance, recommendation message, Grad-CAM heatmap/overlay, and prediction-history ID. Grad-CAM data URLs are restricted to bounded base64 JPEG data URLs before rendering. Weather absence is displayed as unavailable context while disease-based results remain visible.

The history view calls `GET /predictions` with the backend's `limit`, `offset`, and optional `class_id` parameters. It displays 20 rows per page and requests one extra row to determine whether a next page exists; the backend does not return a total count. The list shows timestamp, class, confidence, severity, weather availability, and model version. Class filtering uses the exact class ID supported by the backend. The backend orders newest records first.

The analytics panel summarizes only the currently displayed page: record count, unique classes, average confidence, and class/severity distributions. It labels the scope and shows an empty state when no rows or severity estimates are available; it does not imply a full-database aggregate.

Opening a row calls `GET /predictions/{record_id}` and displays the stored prediction metadata, severity status/category/percentage when available, disease description and symptoms, general guidance, weather status/context, recommendation message, and source/rule traceability. Missing optional fields receive a concise unavailable/not-recorded state.

Backend error codes are translated into clear messages, including `model_unavailable`, `database_unavailable`, `persistence_failed`, invalid/unsupported/oversized image, and invalid lesion mask. In particular, a missing production model is shown as unavailable: the frontend never fabricates a result and the backend does not substitute its smoke-test checkpoint. See [Prediction API](prediction_api.md) for server-side prerequisites and limitations.

Successful prediction responses are checked at the API boundary for required class/confidence/probability, model, severity, weather, guidance, explainability, and history-ID fields. Stored source links are only rendered for absolute HTTP(S) URLs without embedded credentials. This is lightweight contract validation rather than a duplicate of the backend Pydantic schema.

The static production files are written to `frontend/dist`. The API URL is embedded at build time from `VITE_API_BASE_URL`; it is public browser configuration and must not contain secrets. Confidence is the model's class probability; Grad-CAM visualizes influential regions and does not confirm disease. When no lesion mask is supplied, severity is `not_requested`. Missing optional values are shown as unavailable/not recorded rather than filled with sample predictions.

## Tests

Vitest and Testing Library cover file validation, successful response rendering, model-unavailable and invalid-upload errors, result content, history pagination/filtering, detail loading/not-found, missing fields, malformed responses, analytics calculations, and empty/error states. They mock API responses and do not need a production classifier or live backend.
