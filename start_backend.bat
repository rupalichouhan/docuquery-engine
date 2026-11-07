@echo off
echo ========================================================
echo Starting DocuQuery Engine Backend (FastAPI on Port 8000)...
echo ========================================================
set PYTHONPATH=backend
.\venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
