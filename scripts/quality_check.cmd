@echo off
setlocal
set "REPO_ROOT=%~dp0.."
pushd "%REPO_ROOT%"
if errorlevel 1 goto failure

if not defined CROP_HEALTH_PYTHON set "CROP_HEALTH_PYTHON=%USERPROFILE%\miniconda3\envs\retail-forecast\python.exe"
if not exist "%CROP_HEALTH_PYTHON%" (
    echo Python interpreter not found: "%CROP_HEALTH_PYTHON%"
    echo Set CROP_HEALTH_PYTHON to the project's Python interpreter.
    goto failure
)

echo == Python syntax ==
call "%CROP_HEALTH_PYTHON%" scripts/check_python_syntax.py
if errorlevel 1 goto failure

echo == Ruff lint ==
call "%CROP_HEALTH_PYTHON%" -m ruff check backend src tests alembic scripts
if errorlevel 1 goto failure

echo == Backend pytest ==
call "%CROP_HEALTH_PYTHON%" -m pytest -q
if errorlevel 1 goto failure

pushd frontend
if errorlevel 1 goto failure

echo == Frontend Vitest ==
call npm.cmd test -- --run
if errorlevel 1 goto frontend_failure

echo == Frontend production build ==
call npm.cmd run build
if errorlevel 1 goto frontend_failure

popd
popd
echo All software quality checks passed.
exit /b 0

:frontend_failure
popd
:failure
echo Quality gate failed.
popd
exit /b 1
