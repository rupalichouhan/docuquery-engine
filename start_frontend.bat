@echo off
echo ========================================================
echo Starting DocuQuery Engine Frontend (Next.js on Port 3000)...
echo ========================================================
cd frontend
set NEXT_TELEMETRY_DISABLED=1
set NEXT_DISABLE_VERSION_CHECK=1
npm run dev
