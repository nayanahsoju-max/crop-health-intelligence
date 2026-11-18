# Tests

Run the backend tests with:

```powershell
C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe -m pytest -q
```

The tests use mocked inference and weather services plus temporary files and SQLite databases migrated with Alembic. They do not require a production classifier checkpoint, Open-Meteo, PostgreSQL, or internet access.

Run the complete Windows quality gate with scripts/quality_check.cmd. It also runs Python syntax validation, Ruff, frontend Vitest, and the Vite production build. See [quality check documentation](../docs/quality_checks.md). Passing tests validates software behavior and integration; it does not establish classifier accuracy or agricultural diagnosis validity.
