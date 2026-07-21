# Green Valley Hospital

A full-stack hospital management web application with a public marketing/blog site and five role-guarded dashboards (Admin, Doctor, Patient, Staff, Lab). Features include appointment booking, medical records, prescriptions, lab orders/results, billing, and a health blog. Built end-to-end as a simulated SDLC with specialized AI agents.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2.x, Pydantic v2 |
| Auth | `python-jose` (JWT HS256, 60-min TTL), `passlib[bcrypt]` |
| Frontend | React 19, Vite, TypeScript, React Router v7, Axios |
| Database | SQLite — single file at `db/green_valley.db` |
| Testing | pytest (backend), Vitest + React Testing Library (frontend) |

---

## Prerequisites

- Python 3.11 or newer
- Node.js 18.x or newer (npm 9.x+)

---

## Installation

### Backend dependencies

A virtual environment is pre-created at `src/backend/venv`. If it is absent, recreate it:

```cmd
cd src\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend dependencies

`node_modules` is pre-installed. If absent:

```cmd
cd src\frontend
npm install
```

---

## Seeding the Database

Run once from the project root (safe to re-run — idempotent):

```cmd
src\backend\venv\Scripts\python.exe db\seed\seed.py
```

This creates `db/green_valley.db` and inserts demo accounts for every role, four departments, doctor profiles, a demo appointment, and four published blog articles.

---

## Running Both Dev Servers

### Option A — PowerShell (recommended)

```powershell
.\run.ps1
```

Seeds the database, then opens two terminal windows: backend on port 8000, frontend on port 5173.

### Option B — bash / WSL / macOS

```bash
bash run.sh
```

### Option C — separate terminals (manual)

**Terminal 1 — Backend** (from `src/backend`):

```cmd
venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

**Terminal 2 — Frontend** (from `src/frontend`):

```cmd
npm run dev
```

### URLs

| Service | URL |
|---------|-----|
| App (frontend) | http://localhost:5173 |
| Backend API root | http://localhost:8000 |
| Swagger / API docs | http://localhost:8000/docs |

The Vite dev server proxies all `/api/*` requests to the backend, so no cross-origin issues occur during development.

---

## Demo Login Credentials

Go to `http://localhost:5173/login` and sign in with any account below:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@greenvalleyhospital.com | Admin123! |
| Doctor | doctor@greenvalleyhospital.com | Doctor123! |
| Doctor | dr.patel@greenvalleyhospital.com | Doctor123! |
| Doctor | dr.nguyen@greenvalleyhospital.com | Doctor123! |
| Doctor | dr.martinez@greenvalleyhospital.com | Doctor123! |
| Patient | patient@greenvalleyhospital.com | Patient123! |
| Staff | staff@greenvalleyhospital.com | Staff123! |
| Lab | lab@greenvalleyhospital.com | Lab123! |
| Billing | billing@greenvalleyhospital.com | Billing123! |

---

## Running Tests

```cmd
REM Backend (53 tests)
src\backend\venv\Scripts\pytest.exe tests\backend -v

REM Frontend (13 tests)
cd src\frontend && npm test
```

---

## Project Docs

| Document | Description |
|----------|-------------|
| `docs/requirements.md` | User stories, roles, RBAC matrix, acceptance criteria |
| `docs/architecture.md` | System architecture, auth model, data flow |
| `docs/api-spec.md` | Full API endpoint reference |
| `docs/developer-guide.md` | Local setup details and common issues |
| `docs/deployment-guide.md` | Step-by-step deployment and seeding instructions |
| `docs/qa-report.md` | QA test coverage and results |

---

## SDLC Pipeline

Built by a team of specialized Claude Code sub-agents under `.claude/agents/`, each owning one SDLC stage:

| Agent | Role | Deliverables |
|-------|------|-------------|
| Akhil | Orchestrator | Coordinates the pipeline |
| Lavanya | Requirements | `docs/requirements.md` |
| Sagar | Architecture | `docs/architecture.md`, `db/schema.sql`, `docs/api-spec.md` |
| Pavan | Backend Dev | `src/backend` |
| Chintu | Frontend Dev | `src/frontend` |
| Gopal | QA Engineer | `tests/`, `docs/qa-report.md` |
| Indra | DevOps | `run_*.bat`, `db/seed/seed.py`, `.claude/launch.json`, `docs/deployment-guide.md` |

`.claude/launch.json` defines the dev server configs used by the preview tooling to launch both the backend and frontend.
