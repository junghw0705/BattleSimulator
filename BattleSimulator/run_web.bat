@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Siecletrain Web Battle Simulator Launcher

echo =================================================================
echo [Siecletrain Web Battle Simulator (Streamlit)]
echo =================================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b 1
)

echo [1/2] Checking required packages (streamlit, plotly, pandas, openpyxl)...
python -m pip install --quiet -r requirements.txt

echo [2/2] Launching Web Simulator in your default browser...
echo.
echo URL: http://localhost:8501
echo (Press Ctrl+C in this terminal to stop the web server)
echo.

python -m streamlit run app.py

pause
