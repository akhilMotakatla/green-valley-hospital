@echo off
REM Green Valley Hospital — Frontend dev server
REM Runs Vite dev server on port 5173 (proxies /api/* to localhost:8000).

cd /d "%~dp0src\frontend"
npm run dev
