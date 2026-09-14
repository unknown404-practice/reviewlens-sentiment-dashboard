@echo off
title ReviewLens Sentiment API Launcher
echo ===================================================
echo Starting ReviewLens Sentiment API Server...
echo ===================================================

cd /d "C:\Users\RANADEEP\Documents\reviewlens-sentiment-dashboard"

:: Start Uvicorn server in a separate background window
start "ReviewLens API Server" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

echo Waiting for API to initialize...
timeout /t 3 /nobreak >nul

echo Launching API documentation and health endpoints in browser...
start http://127.0.0.1:8000/docs
start http://127.0.0.1:8000/redoc
start http://127.0.0.1:8000/health
start http://127.0.0.1:8000/api/v1/demo/summary

echo ===================================================
echo ReviewLens API is active at http://127.0.0.1:8000
echo ===================================================
pause
