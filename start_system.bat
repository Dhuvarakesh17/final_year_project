@echo off
title AgroVision AI System Launcher
echo =======================================================
echo            AgroVision AI System Launcher
echo =======================================================
echo.
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "AgroVision Backend (Port 8000)" cmd /k "cd /d D:\final_year_project && .\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting React + Vite Frontend on http://localhost:3000 ...
start "AgroVision Frontend (Port 3000)" cmd /k "cd /d D:\final_year_project\frontend && npm run dev"

echo.
echo =======================================================
echo Both services are launching in their own terminal windows!
echo When ready, open your browser at: http://localhost:3000
echo API Documentation is at:        http://127.0.0.1:8000/api/v1/docs
echo =======================================================
pause
