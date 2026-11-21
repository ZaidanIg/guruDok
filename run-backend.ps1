Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Menjalankan GuruDok Backend (FastAPI) - Port 8000" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Set-Location $PSScriptRoot
& .\backend\.venv\Scripts\python.exe run-backend.py
