@echo off
title GuruDok - Backend (FastAPI)
echo ========================================================
echo   Menjalankan GuruDok Backend (FastAPI) - Port 8000
echo ========================================================
cd /d "%~dp0"
.\backend\.venv\Scripts\python.exe run-backend.py
