@echo off
REM Green Valley Hospital — Backend dev server
REM Activates the venv and starts uvicorn with hot-reload on port 8000.

cd /d "%~dp0src\backend"
call venv\Scripts\activate.bat
uvicorn app.main:app --reload --port 8000
