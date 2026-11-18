@echo off
setlocal enabledelayedexpansion

title Crop Health Intelligence Launcher

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"

:: Configured Python environment
if not defined CROP_HEALTH_PYTHON (
    set "CROP_HEALTH_PYTHON=C:\Users\ASUS\miniconda3\envs\mlenv\python.exe"
)

:: Project-specific database URL and PYTHONPATH
set "PYTHONPATH=%PROJECT_ROOT%;%PROJECT_ROOT%\src"
set "DATABASE_URL=sqlite:///%PROJECT_ROOT:\=/%/data/crop_health_local.sqlite3"

echo ======================================================================
echo           AI-Powered Crop Health Intelligence System
echo ======================================================================
echo.
echo [1/5] Checking environment and dependencies...

:: Verify essential project directories
if not exist "src\crop_health" (
    echo [ERROR] Project source directory 'src\crop_health' not found!
    echo Ensure START_CROP_HEALTH.bat is run from the project root directory.
    echo.
    if /i not "%1"=="/nopause" if /i not "%2"=="/nopause" pause
    exit /b 1
)
if not exist "frontend" (
    echo [ERROR] Frontend directory 'frontend' not found!
    echo.
    if /i not "%1"=="/nopause" if /i not "%2"=="/nopause" pause
    exit /b 1
)
if not exist "data" mkdir "data"

:: Check for existing listening services on ports 8000 and 5173
powershell -NoProfile -Command "$b = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue; $f = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue; if ($b -or $f) { exit 1 } else { exit 0 }"
if errorlevel 1 (
    echo [WARNING] Port 8000 or 5173 is already in use!
    echo Another instance of the application may already be running.
    echo Run STOP_CROP_HEALTH.bat first if you want to restart the system.
    echo.
    if /i not "%1"=="/nopause" if /i not "%2"=="/nopause" pause
    exit /b 1
)

:: Check Node.js and npm
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not found in PATH!
    echo Please install Node.js version 18 or newer to run the frontend.
    echo.
    if /i not "%1"=="/nopause" if /i not "%2"=="/nopause" pause
    exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is not found in PATH!
    echo.
    if /i not "%1"=="/nopause" if /i not "%2"=="/nopause" pause
    exit /b 1
)
if not exist "frontend\node_modules" (
    echo [ERROR] Frontend dependencies are missing in frontend\node_modules!
    echo Please run 'npm install' inside the frontend directory.
    echo.
    if /i not "%1"=="/nopause" if /i not "%2"=="/nopause" pause
    exit /b 1
)

:: Check Python interpreter and fallback to verified environment if needed
if not exist "%CROP_HEALTH_PYTHON%" (
    if exist "C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe" (
        echo [INFO] Configured Python not found at %CROP_HEALTH_PYTHON%.
        echo [INFO] Using available environment: C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe
        set "CROP_HEALTH_PYTHON=C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe"
    ) else (
        echo [ERROR] Python executable not found at: %CROP_HEALTH_PYTHON%
        echo.
        if /i not "%1"=="/nopause" if /i not "%2"=="/nopause" pause
        exit /b 1
    )
)

:: Test if Python interpreter has required web and ML packages
"%CROP_HEALTH_PYTHON%" -c "import fastapi, uvicorn, alembic, sqlalchemy" >nul 2>&1
if errorlevel 1 (
    if exist "C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe" (
        "C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe" -c "import fastapi, uvicorn, alembic, sqlalchemy, torch" >nul 2>&1
        if not errorlevel 1 (
            echo [INFO] Target environment is missing web packages.
            echo [INFO] Automatically using verified runtime: C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe
            set "CROP_HEALTH_PYTHON=C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe"
        )
    )
)

"%CROP_HEALTH_PYTHON%" -c "import fastapi, uvicorn, alembic, sqlalchemy, torch, torchvision, PIL, yaml, requests" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Missing required Python packages in %CROP_HEALTH_PYTHON%!
    echo Required: fastapi, uvicorn, alembic, sqlalchemy, torch, torchvision, pillow, pyyaml, requests
    echo.
    if /i not "%1"=="/nopause" if /i not "%2"=="/nopause" pause
    exit /b 1
)
echo Python environment verified: %CROP_HEALTH_PYTHON%

echo.
echo [2/5] Verifying database and applying migrations...
"%CROP_HEALTH_PYTHON%" -m alembic upgrade head
if errorlevel 1 (
    echo [ERROR] Database migration failed!
    echo Check database connection and alembic.ini configuration.
    echo.
    if /i not "%1"=="/nopause" if /i not "%2"=="/nopause" pause
    exit /b 1
)
echo Database is up to date at head revision.

echo.
echo [3/5] Starting FastAPI backend on port 8000...
set "BACKEND_PID_FILE=%PROJECT_ROOT%\data\crop_health_backend.pid"
if exist "%BACKEND_PID_FILE%" del /f /q "%BACKEND_PID_FILE%"

powershell -NoProfile -Command ^
  "$env:DATABASE_URL = '%DATABASE_URL%';" ^
  "$env:PYTHONPATH = '%PYTHONPATH%';" ^
  "$p = Start-Process cmd.exe -ArgumentList '/k', 'title Crop Health Intelligence - Backend [Port 8000] && cd /d \"%PROJECT_ROOT%\" && set \"DATABASE_URL=%DATABASE_URL%\" && set \"PYTHONPATH=%PYTHONPATH%\" && \"%CROP_HEALTH_PYTHON%\" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --log-level info' -PassThru;" ^
  "$p.Id | Out-File -FilePath '%BACKEND_PID_FILE%' -Encoding ascii"

echo Waiting for backend readiness probe [http://127.0.0.1:8000/health/ready]...
set /a ATTEMPTS=0
:WAIT_BACKEND
ping -n 2 127.0.0.1 >nul
set /a ATTEMPTS+=1
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health/ready' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo Backend is ready!
    goto BACKEND_READY
)
if !ATTEMPTS! geq 60 (
    echo [ERROR] Backend failed to become ready within 60 seconds!
    echo Check the Backend terminal window for error details.
    call "%PROJECT_ROOT%\STOP_CROP_HEALTH.bat" /quiet >nul 2>&1
    echo.
    if /i not "%1"=="/nopause" if /i not "%2"=="/nopause" pause
    exit /b 1
)
goto WAIT_BACKEND

:BACKEND_READY

echo.
echo [4/5] Starting React/Vite frontend on port 5173...
set "FRONTEND_PID_FILE=%PROJECT_ROOT%\data\crop_health_frontend.pid"
if exist "%FRONTEND_PID_FILE%" del /f /q "%FRONTEND_PID_FILE%"

powershell -NoProfile -Command ^
  "$p = Start-Process cmd.exe -ArgumentList '/k', 'title Crop Health Intelligence - Frontend [Port 5173] && cd /d \"%PROJECT_ROOT%\frontend\" && npm run dev -- --host 127.0.0.1 --port 5173' -PassThru;" ^
  "$p.Id | Out-File -FilePath '%FRONTEND_PID_FILE%' -Encoding ascii"

echo Waiting for frontend to respond [http://127.0.0.1:5173]...
set /a ATTEMPTS=0
:WAIT_FRONTEND
ping -n 2 127.0.0.1 >nul
set /a ATTEMPTS+=1
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:5173' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo Frontend is ready!
    goto FRONTEND_READY
)
if !ATTEMPTS! geq 60 (
    echo [ERROR] Frontend failed to respond within 60 seconds!
    echo Check the Frontend terminal window for error details.
    call "%PROJECT_ROOT%\STOP_CROP_HEALTH.bat" /quiet >nul 2>&1
    echo.
    if /i not "%1"=="/nopause" if /i not "%2"=="/nopause" pause
    exit /b 1
)
goto WAIT_FRONTEND

:FRONTEND_READY

echo.
echo [5/5] Opening Crop Health Intelligence in default browser...
start http://127.0.0.1:5173

echo.
echo ======================================================================
echo           CROP HEALTH INTELLIGENCE IS READY!
echo ======================================================================
echo.
echo   Frontend: http://127.0.0.1:5173
echo   Backend:  http://127.0.0.1:8000
echo   API Docs: http://127.0.0.1:8000/docs
echo.
echo To stop the application, double-click STOP_CROP_HEALTH.bat
echo or close the individual service terminal windows.
echo ======================================================================
echo.
if /i "%1"=="/nopause" exit /b 0
if /i "%2"=="/nopause" exit /b 0
pause
