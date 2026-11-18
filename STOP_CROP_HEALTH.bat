@echo off
setlocal enabledelayedexpansion

title Stop Crop Health Intelligence

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"

set "BACKEND_PID_FILE=%PROJECT_ROOT%\data\crop_health_backend.pid"
set "FRONTEND_PID_FILE=%PROJECT_ROOT%\data\crop_health_frontend.pid"

echo ======================================================================
echo           Stopping Crop Health Intelligence System
echo ======================================================================
echo.

set "STOPPED_COUNT=0"

:: Stop Backend if PID file exists
if exist "%BACKEND_PID_FILE%" (
    set /p BACKEND_PID=<"%BACKEND_PID_FILE%"
    if defined BACKEND_PID (
        set "BACKEND_PID=!BACKEND_PID: =!"
        echo Stopping Backend process tree [PID !BACKEND_PID!]...
        powershell -NoProfile -Command "if (Get-Process -Id !BACKEND_PID! -ErrorAction SilentlyContinue) { taskkill /F /T /PID !BACKEND_PID! | Out-Null }"
        set /a STOPPED_COUNT+=1
    )
    del /f /q "%BACKEND_PID_FILE%" >nul 2>&1
)

:: Stop Frontend if PID file exists
if exist "%FRONTEND_PID_FILE%" (
    set /p FRONTEND_PID=<"%FRONTEND_PID_FILE%"
    if defined FRONTEND_PID (
        set "FRONTEND_PID=!FRONTEND_PID: =!"
        echo Stopping Frontend process tree [PID !FRONTEND_PID!]...
        powershell -NoProfile -Command "if (Get-Process -Id !FRONTEND_PID! -ErrorAction SilentlyContinue) { taskkill /F /T /PID !FRONTEND_PID! | Out-Null }"
        set /a STOPPED_COUNT+=1
    )
    del /f /q "%FRONTEND_PID_FILE%" >nul 2>&1
)

:: Clean up any leftover PID files
if exist "%BACKEND_PID_FILE%" del /f /q "%BACKEND_PID_FILE%" >nul 2>&1
if exist "%FRONTEND_PID_FILE%" del /f /q "%FRONTEND_PID_FILE%" >nul 2>&1

echo.
if !STOPPED_COUNT! gtr 0 (
    echo [SUCCESS] Crop Health Intelligence services stopped successfully.
) else (
    echo [INFO] No running launcher services found to stop.
)
echo.

if /i "%1"=="/quiet" exit /b 0
if /i "%2"=="/quiet" exit /b 0
if /i "%1"=="/nopause" exit /b 0
if /i "%2"=="/nopause" exit /b 0
pause
