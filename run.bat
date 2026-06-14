@echo off
title Smart English Trainer Launcher

echo ===================================================
echo   Smart English Trainer Launcher
echo ===================================================
echo.

:: Check if Flask is installed
echo [1/3] Checking dependencies (Flask, edge-tts)...
python -c "import flask, edge_tts" 2>nul
if %errorlevel% neq 0 (
    echo [*] Dependencies are missing. Installing from requirements.txt...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [!] Error: Failed to install dependencies. Please run "pip install flask edge-tts" manually.
        pause
        exit /b
    )
) else (
    echo [*] All dependencies are already installed.
)

echo.
:: Open the browser
echo [2/3] Opening browser at http://localhost:8000 ...
start "" "http://localhost:8000"

echo.
:: Launch the backend server
echo [3/3] Starting Flask Local Server...
echo       (You can close this window to stop the server)
echo ===================================================
echo.
python app.py
pause
