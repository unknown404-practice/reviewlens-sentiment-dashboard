@echo off
title ReviewLens Next.js Frontend Launcher
echo ========================================================
echo    ReviewLens Next.js Frontend Dashboard (Port 3000)
echo ========================================================

cd /d "%~dp0frontend-next"

if not exist "node_modules" (
    echo Installing node dependencies...
    call npm install
)

echo Starting Next.js development server...
start "" "http://localhost:3000"
npm run dev

pause
