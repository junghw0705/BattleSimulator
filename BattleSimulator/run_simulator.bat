@echo off
setlocal
cd /d "%~dp0"

title Siecletrain Battle Simulator
cls
echo ===================================================
echo   Siecletrain Battle Simulator Launcher
echo ===================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10 or higher and check "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo [INFO] Checking required packages (PyQt6, openpyxl)...
python -c "import PyQt6, openpyxl" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing required packages from requirements.txt...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install packages. Please check internet connection.
        pause
        exit /b 1
    )
    echo.
)

echo [INFO] Starting Siecletrain Battle Simulator...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with error code %errorlevel%.
    pause
    exit /b %errorlevel%
)
