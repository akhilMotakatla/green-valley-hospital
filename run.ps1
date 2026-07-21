# Green Valley Hospital — unified dev launcher (PowerShell)
# Run from the project root: .\run.ps1
# Requires: Python 3.11+ and Node.js 18+ on PATH.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$BACKEND = Join-Path $ROOT "src\backend"
$FRONTEND = Join-Path $ROOT "src\frontend"
$VENV      = Join-Path $BACKEND "venv"
$PYTHON    = Join-Path $VENV "Scripts\python.exe"
$UVICORN   = Join-Path $VENV "Scripts\uvicorn.exe"

# ---------------------------------------------------------------------------
# 1. Backend virtual environment + dependencies
# ---------------------------------------------------------------------------
if (-not (Test-Path $PYTHON)) {
    Write-Host "[DevOps] Creating Python virtual environment at src\backend\venv ..." -ForegroundColor Cyan
    python -m venv $VENV
}

Write-Host "[DevOps] Ensuring backend Python dependencies are up to date ..." -ForegroundColor Cyan
& $PYTHON -m pip install --quiet --upgrade pip
& $PYTHON -m pip install --quiet -r (Join-Path $BACKEND "requirements.txt")

# ---------------------------------------------------------------------------
# 2. Database seed (idempotent)
# ---------------------------------------------------------------------------
Write-Host "[DevOps] Seeding database ..." -ForegroundColor Cyan
& $PYTHON (Join-Path $ROOT "db\seed\seed.py")

# ---------------------------------------------------------------------------
# 3. Frontend npm dependencies
# ---------------------------------------------------------------------------
$NM = Join-Path $FRONTEND "node_modules"
if (-not (Test-Path $NM)) {
    Write-Host "[DevOps] Installing frontend npm dependencies ..." -ForegroundColor Cyan
    Push-Location $FRONTEND
    npm install
    Pop-Location
}

# ---------------------------------------------------------------------------
# 4. Start backend (uvicorn) in a new window
# ---------------------------------------------------------------------------
Write-Host "[DevOps] Starting backend (uvicorn) on http://localhost:8000 ..." -ForegroundColor Green
$backendJob = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$BACKEND'; & '$UVICORN' app.main:app --reload --port 8000"
) -PassThru

# ---------------------------------------------------------------------------
# 5. Start frontend (Vite) in a new window
# ---------------------------------------------------------------------------
Write-Host "[DevOps] Starting frontend (Vite) on http://localhost:5173 ..." -ForegroundColor Green
$frontendJob = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$FRONTEND'; npm run dev"
) -PassThru

# ---------------------------------------------------------------------------
# 6. Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "  Green Valley Hospital — servers running" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "  Frontend app  : http://localhost:5173"
Write-Host "  Backend API   : http://localhost:8000"
Write-Host "  Swagger docs  : http://localhost:8000/docs"
Write-Host ""
Write-Host "  Demo login    : http://localhost:5173/login"
Write-Host "  Admin         : admin@greenvalleyhospital.com  / Admin123!"
Write-Host "  Doctor        : doctor@greenvalleyhospital.com / Doctor123!"
Write-Host "  Patient       : patient@greenvalleyhospital.com / Patient123!"
Write-Host "  Staff         : staff@greenvalleyhospital.com  / Staff123!"
Write-Host "  Lab           : lab@greenvalleyhospital.com    / Lab123!"
Write-Host "  Billing       : billing@greenvalleyhospital.com / Billing123!"
Write-Host ""
Write-Host "Close the two opened terminal windows to stop the servers." -ForegroundColor Gray
