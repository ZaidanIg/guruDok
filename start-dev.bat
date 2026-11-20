@echo off
title GuruDok Development Launcher
echo ========================================================
echo   Menjalankan GuruDok Staging / Development
echo ========================================================
echo.

echo 1. Menjalankan Backend FastAPI di port 8000...
start "GuruDok - Backend (FastAPI)" cmd /k "cd /d %~dp0 && .\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload"

echo 2. Menjalankan Frontend Vite di port 5173...
start "GuruDok - Frontend (Vite + React)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Kedua service telah dibuka di jendela terminal mandiri!
echo - Backend:  http://127.0.0.1:8000
echo - Frontend: http://localhost:5173
echo ========================================================
