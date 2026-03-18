@echo off
title ARES — Launch

echo ============================================================
echo   ARES — Adaptive Risk ^& Escalation Simulator
echo   [MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE]
echo ============================================================

echo.
echo [1/2] Starting Python API server on http://localhost:8000 ...
start "ARES Python API" cmd /k "cd /d %~dp0ares && py -3 server.py"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Next.js UI on http://localhost:3000 ...
start "ARES Next.js UI" cmd /k "cd /d %~dp0ares-ui && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo  Open: http://localhost:3000
echo  API:  http://localhost:8000/api/health
echo.
start http://localhost:3000
