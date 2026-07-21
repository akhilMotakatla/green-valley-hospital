# Green Valley Hospital — Deployment Guide

This guide covers everything needed to get the application running locally for development or review.

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Python | 3.11 |
| Node.js | 18.x |
| npm | 9.x |
| Git | any |

---

## 1. Clone / open the project

```
Green Valley Hospital/   ← project root
├── src/backend/         ← FastAPI app (Python)
├── src/frontend/        ← React + Vite (TypeScript)
├── db/                  ← SQLite database + seed script
├── run_backend.bat      ← convenience launcher
├── run_frontend.bat     ← convenience launcher
└── run_all.bat          ← starts both in separate windows
```

---

## 2. Backend setup

A virtual environment is pre-created at `src/backend/venv`. If it is missing, recreate it:

```cmd
cd src\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

If the venv is already present (as it is in this repo), no extra installation is needed.

---

## 3. Frontend setup

Node modules are pre-installed. If `node_modules` is absent:

```cmd
cd src\frontend
npm install
```

---

## 4. Seed the database

Run once (safe to re-run — idempotent):

```cmd
src\backend\venv\Scripts\python.exe db\seed\seed.py
```

This creates `db/green_valley.db` (if not already present) and inserts:

- One demo account per role (Admin, Doctor, Patient, Staff, Lab)
- Four extra doctor accounts covering Cardiology, Pediatrics, Orthopedics, and Neurology
- Four departments
- A demo appointment (Patient booked with Dr. Heart, 3 days from seed date)
- Four published blog articles

---

## 5. Starting the servers

### Option A — PowerShell (recommended)

From the project root in PowerShell:

```powershell
.\run.ps1
```

This seeds the database (idempotent), then opens two new terminal windows — one for the backend and one for the frontend.

### Option B — bash / WSL / macOS

```bash
bash run.sh
```

Both servers run in the foreground (backgrounded via `&`); press `Ctrl+C` to stop both at once.

### Option C — legacy batch files

Double-click `run_all.bat` or from a cmd prompt:

```cmd
run_all.bat
```

### Option D — separate terminals

**Terminal 1 — Backend:**

```cmd
cd src\backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**

```cmd
cd src\frontend
npm run dev
```

---

---

## 6. URLs

| Service | URL |
|---------|-----|
| Frontend (app) | http://localhost:5173 |
| Backend root | http://localhost:8000 |
| Swagger / OpenAPI docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

The Vite dev server proxies all `/api/*` requests to `http://localhost:8000`, so the frontend only ever talks to port 5173 — no CORS concerns in the browser during development.

---

## 7. Demo login credentials

Navigate to `http://localhost:5173/login` and use any of the accounts below.

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@greenvalleyhospital.com | Admin123! |
| Doctor (primary) | doctor@greenvalleyhospital.com | Doctor123! |
| Doctor | dr.patel@greenvalleyhospital.com | Doctor123! |
| Doctor | dr.nguyen@greenvalleyhospital.com | Doctor123! |
| Doctor | dr.martinez@greenvalleyhospital.com | Doctor123! |
| Patient | patient@greenvalleyhospital.com | Patient123! |
| Staff | staff@greenvalleyhospital.com | Staff123! |
| Lab | lab@greenvalleyhospital.com | Lab123! |
| Billing | billing@greenvalleyhospital.com | Billing123! |

Each account lands on its role-specific dashboard immediately after login.

---

## 8. Stopping the servers

- If started via `run_all.bat`: close the two terminal windows that were opened.
- If started manually: press `Ctrl+C` in each terminal.

---

## 9. Re-seeding / resetting the database

To reset to a clean seed state, delete the SQLite file and re-seed:

```cmd
del db\green_valley.db
src\backend\venv\Scripts\python.exe db\seed\seed.py
```

The database is re-created automatically by `init_db()` on the next backend startup (or by the seed script itself, whichever runs first).

---

## 10. Environment variables

Both servers work with zero configuration out of the box. A root-level `.env.example` documents every available override. If you need to change defaults, copy it to `src/backend/.env` and edit as required.

**Backend** (`src/backend/.env`):

```env
SECRET_KEY=change-me-to-a-long-random-string
DATABASE_URL=sqlite:///./greenvalley.db
CORS_ORIGINS=http://localhost:5173
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**Frontend** (`src/frontend/.env.development`):

```env
VITE_API_BASE_URL=/api
```

The frontend `.env.development` is already present and correctly configured.

---

## 11. File upload directory

Lab result file attachments are stored in `uploads/lab_results/`. Blog cover images go to `uploads/blog_covers/`. Both directories are created automatically on backend startup. They are excluded from version control via `.gitignore`.

---

## 12. Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: app` | Run uvicorn from `src/backend/`, not the project root |
| Port 8000 already in use | Stop the existing process or change `--port` |
| Port 5173 already in use | Vite will auto-increment to 5174 — update the backend CORS_ORIGINS if needed |
| `greenvalley.db` locked error | Another process has the DB open; stop it first |
| 401 on all API calls | JWT expired (60-minute TTL) — log out and log back in |
| Doctor photos show placeholder | Place real images in `src/frontend/public/images/doctors/` |
