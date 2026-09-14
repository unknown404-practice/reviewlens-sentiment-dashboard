@echo off
title ReviewLens Full-Stack Launcher (FastAPI + Streamlit)
echo ========================================================
echo    ReviewLens Sentiment Dashboard - Full Stack Launcher
echo ========================================================

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000...
start "ReviewLens FastAPI Backend" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

echo Waiting 3 seconds for API backend to initialize...
timeout /t 3 /nobreak >nul

echo [2/2] Starting Streamlit Dashboard on http://localhost:8501...
set "API_BASE_URL=http://127.0.0.1:8000"
python -m streamlit run app.py --server.port 8501

pause
