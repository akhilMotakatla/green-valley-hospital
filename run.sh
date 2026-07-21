#!/usr/bin/env bash
# Green Valley Hospital — unified dev launcher (bash / macOS / Linux / WSL)
# Run from the project root: bash run.sh
# Requires: Python 3.11+ and Node.js 18+ on PATH.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/src/backend"
FRONTEND="$ROOT/src/frontend"
VENV="$BACKEND/venv"

# ---------------------------------------------------------------------------
# 1. Backend virtual environment + dependencies
# ---------------------------------------------------------------------------
if [ ! -f "$VENV/bin/python" ] && [ ! -f "$VENV/Scripts/python.exe" ]; then
    echo "[DevOps] Creating Python virtual environment at src/backend/venv ..."
    python3 -m venv "$VENV"
fi

# Resolve python / pip inside the venv (handles Windows Git-Bash paths too)
if [ -f "$VENV/Scripts/python.exe" ]; then
    PYTHON="$VENV/Scripts/python.exe"
    UVICORN="$VENV/Scripts/uvicorn.exe"
else
    PYTHON="$VENV/bin/python"
    UVICORN="$VENV/bin/uvicorn"
fi

echo "[DevOps] Ensuring backend Python dependencies are up to date ..."
"$PYTHON" -m pip install --quiet --upgrade pip
"$PYTHON" -m pip install --quiet -r "$BACKEND/requirements.txt"

# ---------------------------------------------------------------------------
# 2. Database seed (idempotent)
# ---------------------------------------------------------------------------
echo "[DevOps] Seeding database ..."
"$PYTHON" "$ROOT/db/seed/seed.py"

# ---------------------------------------------------------------------------
# 3. Frontend npm dependencies
# ---------------------------------------------------------------------------
if [ ! -d "$FRONTEND/node_modules" ]; then
    echo "[DevOps] Installing frontend npm dependencies ..."
    (cd "$FRONTEND" && npm install)
fi

# ---------------------------------------------------------------------------
# 4. Start backend and frontend in the background
# ---------------------------------------------------------------------------
echo "[DevOps] Starting backend (uvicorn) on http://localhost:8000 ..."
(cd "$BACKEND" && "$UVICORN" app.main:app --reload --port 8000) &
BACKEND_PID=$!

echo "[DevOps] Starting frontend (Vite) on http://localhost:5173 ..."
(cd "$FRONTEND" && npm run dev) &
FRONTEND_PID=$!

# ---------------------------------------------------------------------------
# 5. Summary and wait
# ---------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "  Green Valley Hospital — servers running"
echo "=========================================="
echo "  Frontend app  : http://localhost:5173"
echo "  Backend API   : http://localhost:8000"
echo "  Swagger docs  : http://localhost:8000/docs"
echo ""
echo "  Demo login    : http://localhost:5173/login"
echo "  Admin         : admin@greenvalleyhospital.com  / Admin123!"
echo "  Doctor        : doctor@greenvalleyhospital.com / Doctor123!"
echo "  Patient       : patient@greenvalleyhospital.com / Patient123!"
echo "  Staff         : staff@greenvalleyhospital.com  / Staff123!"
echo "  Lab           : lab@greenvalleyhospital.com    / Lab123!"
echo "  Billing       : billing@greenvalleyhospital.com / Billing123!"
echo ""
echo "Press Ctrl+C to stop both servers."

# Wait for either process to exit; kill both on Ctrl+C.
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait $BACKEND_PID $FRONTEND_PID
