Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting DocuQuery Engine Backend (FastAPI on Port 8000)..." -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
$env:PYTHONPATH = "backend"
.\venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
