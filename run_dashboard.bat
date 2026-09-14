@echo off
title ReviewLens Streamlit Dashboard Launcher
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

set "API_BASE_URL=http://127.0.0.1:8000"

echo ========================================================
echo Starting ReviewLens Streamlit Dashboard (Port 8501)...
echo Expected Backend API: %API_BASE_URL%
echo ========================================================

python -m streamlit run app.py --server.port 8501
pause
