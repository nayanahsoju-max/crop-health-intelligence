@echo off
setlocal
set "REPO_ROOT=%~dp0.."
pushd "%REPO_ROOT%"
if errorlevel 1 exit /b 1

if not defined CROP_HEALTH_PYTHON set "CROP_HEALTH_PYTHON=python"
if not defined API_HOST set "API_HOST=0.0.0.0"
if not defined API_PORT set "API_PORT=8000"
if not defined API_WORKERS set "API_WORKERS=1"
if not defined API_LOG_LEVEL set "API_LOG_LEVEL=info"

"%CROP_HEALTH_PYTHON%" -m uvicorn backend.app.main:app --host "%API_HOST%" --port "%API_PORT%" --workers "%API_WORKERS%" --log-level "%API_LOG_LEVEL%"
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
