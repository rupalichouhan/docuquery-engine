@echo off
echo ========================================================
echo Launching DocuQuery Engine Modular Monolith Workspace
echo ========================================================
start "DocuQuery Backend" cmd /k "start_backend.bat"
start "DocuQuery Frontend" cmd /k "start_frontend.bat"
echo Services launched!
echo - Backend API:  http://localhost:8000/docs
echo - Frontend UI:  http://localhost:3000
