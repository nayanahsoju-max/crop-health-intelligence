# Software quality checks

Run the complete local quality gate from the project root in Windows PowerShell:

```powershell
.\scripts\quality_check.cmd
```

The script runs, in order:

1. In-memory Python syntax compilation for project Python sources (no bytecode output).
2. Ruff checks using the project's conservative E4/E7/E9/F rule selection.
3. The full backend pytest suite, including Alembic upgrades against temporary SQLite databases.
4. Frontend Vitest tests.
5. The Vite production build.

Each command is required and a non-zero result stops the gate. The script selects the existing Miniconda `retail-forecast` interpreter under the current user's profile by default. Set `CROP_HEALTH_PYTHON` to select a different interpreter. Dependencies are declared in `requirements.txt` and `frontend/package.json`.

Individual checks can also be run from the root:

```powershell
C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe scripts/check_python_syntax.py
C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe -m ruff check backend src tests alembic scripts
C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe -m pytest -q
Push-Location frontend
npm.cmd test -- --run
npm.cmd run build
Pop-Location
```

The active `retail-forecast` environment used for Stage 16 did not have `pytest-cov` or `coverage` installed, even though `pytest-cov` is declared in the project requirements. Coverage was therefore not measured, and no percentage is reported. In an environment with the declared plugin installed, an optional measurement command is:

```powershell
python -m pytest --cov=src/crop_health --cov=backend.app --cov-report=term-missing -q
```

The test fixtures use temporary files/databases, deterministic inference doubles, and mocked weather responses. They do not contact Open-Meteo, require PostgreSQL, or load a production checkpoint. JSON POST bodies to `/predictions` and `/recommendations/current` are limited to 1 MiB; multipart `/predict` continues to use the existing streamed upload limits.

The quality gate validates software behavior, boundary contracts, and integration. It does **not** establish production classifier accuracy, agricultural diagnosis validity, or deployment readiness. The controlled classifier outputs in tests are fixtures only.

The backend suite currently emits two third-party deprecation warnings from Starlette's TestClient compatibility path with httpx and AnyIO. They originate in installed dependencies; the project does not suppress them.
