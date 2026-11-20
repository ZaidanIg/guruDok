Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Menjalankan GuruDok Staging / Development Environment" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '=== BACKEND GURUDOK (FASTAPI) ===' -ForegroundColor Cyan; cd '$PSScriptRoot'; .\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '=== FRONTEND GURUDOK (VITE + REACT) ===' -ForegroundColor Green; cd '$PSScriptRoot\frontend'; npm run dev"

Write-Host ""
Write-Host "Kedua service telah dibuka di jendela terminal mandiri!" -ForegroundColor Green
Write-Host "- Backend:  http://127.0.0.1:8000"
Write-Host "- Frontend: http://localhost:5173"
