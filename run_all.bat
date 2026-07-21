@echo off
REM Green Valley Hospital — Start both servers in separate windows.
REM Run this from the project root.

echo Starting backend (uvicorn on port 8000) ...
start "GVH Backend" cmd /k "%~dp0run_backend.bat"

echo Starting frontend (Vite on port 5173) ...
start "GVH Frontend" cmd /k "%~dp0run_frontend.bat"

echo.
echo Both servers are starting.
echo   Backend API : http://localhost:8000
echo   API Docs    : http://localhost:8000/docs
echo   Frontend    : http://localhost:5173
echo.
echo Close the two opened terminal windows to stop the servers.
