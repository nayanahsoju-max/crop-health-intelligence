# PostgreSQL persistence

The API stores prediction history in the `prediction_records` table through SQLAlchemy 2.x. PostgreSQL with the `psycopg` driver is the intended production database. SQLite is supported as a local development/test backend; it does not replace the PostgreSQL deployment target. No database credentials or URL are embedded in source code. The application reads `DATABASE_URL` from the process environment; it does not load `.env` automatically.

## Schema

Each row stores the predicted class ID and confidence, optional severity category/percentage plus the full severity payload, optional weather context, the complete recommendation result (including source/rule traceability), inference result metadata (class probabilities and explainability/severity statuses), model version, optional image filename/media type/SHA-256/storage URI, and a server-generated timestamp. Image bytes are not stored. JSON payloads use PostgreSQL `JSONB` in production and portable JSON in SQLite. The second Alembic revision adds `result_metadata` for the Stage 12 inference workflow.

Constraints enforce confidence in `[0, 1]`, supported severity categories, severity percentage in `[0, 100]`, and 64-character image hashes. Indexes support newest-first history and class-filtered history. The disease/class ID is stored as a string snapshot instead of a foreign key to the knowledge-base JSON: this keeps historical predictions readable if the supported class catalog changes. The recommendation JSON retains the knowledge-base record IDs, cited sources, and weather rule IDs used at prediction time.

## Configuration and migrations

Set a private `DATABASE_URL` in the environment. For PostgreSQL:

```text
DATABASE_URL=postgresql+psycopg://<user>:<password>@<host>:5432/<database>
```

For local SQLite development, an example is `sqlite:///./data/crop_health_local.sqlite3`. `.env.example` is a template only; copy settings to a private environment or `.env` file and load them in your shell/process manager.

Schema creation is migration-only. Do not use `Base.metadata.create_all()` in the application. Apply the checked-in Alembic migration after setting `DATABASE_URL`:

For deployment, apply and verify the Alembic revision as a release step before routing traffic. Application startup does not run migrations. See [deployment instructions](deployment.md) for the production sequence and rollback caution.

```powershell
python -m alembic -c alembic.ini upgrade head
```

Inspect the current revision with `python -m alembic -c alembic.ini current`; roll back one revision with `python -m alembic -c alembic.ini downgrade -1`. Application startup does not run migrations automatically. When no database URL is configured, non-persistence API features start normally and history routes respond with HTTP 503.

## History API

- `POST /predictions` persists a prediction/result payload and returns its generated record ID.
- `GET /predictions?limit=50&offset=0&class_id=tomato_early_blight` returns newest-first history (maximum page size 200).
- `GET /predictions/{record_id}` retrieves one record or returns 404.

The create body accepts `class_id`, `confidence`, optional `severity`, `weather_context`, `recommendation_result`, `result_metadata`, `model_version`, and `image_reference`. The persistence API stores already-produced pipeline outputs; use `/predict` for image inference orchestration.

## Tests

`tests/test_persistence.py` applies the Alembic migration to a per-test SQLite file in pytest's temporary directory. It does not connect to PostgreSQL or reuse a developer database. Tests cover creation, retrieval, ordering/filter/pagination, provenance and image metadata, required fields, database constraints, API validation, and the API's no-database response.
