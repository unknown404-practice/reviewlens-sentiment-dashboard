@echo off
title ReviewLens Full-Stack Launcher (FastAPI + Next.js)
echo ========================================================
echo    ReviewLens Full Stack: FastAPI Backend + Next.js UI
echo ========================================================

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000...
start "ReviewLens FastAPI Backend" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

echo Waiting 3 seconds for API backend to initialize...
timeout /t 3 /nobreak >nul

echo [2/2] Starting Next.js Premium Dashboard on http://localhost:3000...
cd /d "%~dp0frontend-next"
start "" "http://localhost:3000"
npm run dev

pause
