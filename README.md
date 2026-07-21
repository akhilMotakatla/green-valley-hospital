# Green Valley Hospital

A full-stack hospital management web application with a public marketing/blog site and six role-guarded dashboards (Admin, Doctor, Patient, Staff, Lab, BillingSpecialist). Features include appointment booking with slot availability management, medical records, prescriptions, lab orders/results, billing, in-app notifications, and a health blog. Built end-to-end as a simulated SDLC with specialized AI agents.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2.x, Pydantic v2 |
| Auth | `python-jose` (JWT HS256, 60-min TTL), `passlib[bcrypt]` |
| Frontend | React 19, Vite, TypeScript, React Router v7, Axios, Recharts |
| Database | SQLite — single file at `db/green_valley.db` |
| PDF Export | WeasyPrint (REQ-08, Group C — requires GTK system libs on Windows; see note below) |
| Testing | pytest (backend), Vitest + React Testing Library (frontend) |

---

## Prerequisites

- Python 3.11 or newer
- Node.js 18.x or newer (npm 9.x+)

### WeasyPrint on Windows (optional — only needed for PDF export)

WeasyPrint pip-installs cleanly but needs GTK native DLLs (`libgobject-2.0-0`, `libpango-1.0-0`, etc.) to render PDFs. PDF export (REQ-08) is a Group C feature not yet implemented; the app boots and all Group A/B endpoints work without GTK installed. To enable PDF export later, install the [GTK3 runtime for Windows](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases) and ensure the DLLs are on `PATH`.

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

Run once (safe to re-run — fully idempotent):

```cmd
cd src\backend
venv\Scripts\python.exe seed.py
```

Or equivalently from the repo root:

```cmd
src\backend\venv\Scripts\python.exe db\seed\seed.py
```

This creates `db/green_valley.db` and inserts:
- One demo account per role (Admin, Doctor, Patient, Staff, Lab, BillingSpecialist)
- 10 departments (Cardiology, Pediatrics, Orthopedics, Neurology, Oncology, Radiology, Emergency Medicine, Ophthalmology, Gynecology, Dermatology)
- 10 doctors — one per department with full profiles
- A demo appointment (Patient with Dr. David Heart, 3 days in the future)
- 8 published blog articles
- 2 corporate health package tiers (Wellness Basic, Executive Health)
- System config rows (`waitlist_confirmation_hours = 4`, `survey_delay_hours = 24`)

---

## Running Both Dev Servers

### Option A — Bash / macOS / Linux / WSL (recommended)

```bash
bash run.sh
```

Seeds the database, installs missing dependencies, then starts backend and frontend in the background.

### Option B — Windows batch scripts

```cmd
run_all.bat
```

Opens two separate terminal windows: backend on port 8000, frontend on port 5173.

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
| Doctor | dr.chen@greenvalleyhospital.com | Doctor123! |
| Doctor | dr.singh@greenvalleyhospital.com | Doctor123! |
| Doctor | dr.brown@greenvalleyhospital.com | Doctor123! |
| Doctor | dr.kim@greenvalleyhospital.com | Doctor123! |
| Doctor | dr.rodriguez@greenvalleyhospital.com | Doctor123! |
| Doctor | dr.osei@greenvalleyhospital.com | Doctor123! |
| Patient | patient@greenvalleyhospital.com | Patient123! |
| Staff | staff@greenvalleyhospital.com | Staff123! |
| Lab | lab@greenvalleyhospital.com | Lab123! |
| BillingSpecialist | billing@greenvalleyhospital.com | Billing123! |

---

## Running Tests

```cmd
REM Backend (45 tests — Group A: REQ-01 availability + REQ-02 notifications)
src\backend\venv\Scripts\pytest.exe src\backend\tests -v

REM Frontend
cd src\frontend && npm test
```

---

## Batch 2 Features (Group A — implemented and QA-cleared)

- **REQ-01 Doctor Availability & Slot Management**: Doctors set weekly schedules and date blocks; patients book from real available slots; 19 API endpoints under `/api/doctors/`, `/api/doctor/availability/`, `/api/admin/doctors/{id}/availability/`.
- **REQ-02 In-App Notification Center**: Fan-out notifications on appointment events (confirmed, cancelled, noshow), lab results, invoice creation, contact form submissions, and account changes. Bell badge with 60s poll, paginated inbox at `/notifications` for all roles. Endpoints: `/api/notifications/unread-count`, `/api/notifications`, `/api/notifications/{id}/read`, `/api/notifications/mark-all-read`.

---

## Project Docs

| Document | Description |
|----------|-------------|
| `docs/requirements.md` | User stories, roles, RBAC matrix, acceptance criteria |
| `docs/architecture.md` | System architecture, auth model, data flow |
| `docs/api-spec.md` | Full API endpoint reference (86 endpoints) |
| `docs/technical-design.md` | Batch 2 UX journeys and technical design (REQ-01 through REQ-12) |
| `docs/delivery-plan.md` | 30-task delivery plan with milestones and risk register |
| `docs/deployment-guide.md` | Step-by-step deployment and seeding instructions |

---

## SDLC Pipeline

Built by a team of specialized Claude Code sub-agents under `.claude/agents/`, each owning one SDLC stage:

| Agent | Role | Deliverables |
|-------|------|-------------|
| Akhil | Orchestrator | Coordinates the pipeline |
| Lavanya | Requirements + PM | `docs/requirements.md`, `docs/delivery-plan.md` |
| Sagar | Architecture + Review | `docs/architecture.md`, `db/schema.sql`, `docs/api-spec.md`, Phase 7 code review |
| Chintu | Full-Stack Dev | `src/backend`, `src/frontend` |
| Gopal | QA Engineer | `src/backend/tests/`, QA reports |
| Indra | DevOps | `run_*.bat`, `run.sh`, `db/seed/seed.py`, `.claude/launch.json`, `README.md` |
| Sunny | Scrum | Daily standups, `docs/delivery-plan.md` milestone tracking |
| Krishna | Client / Product Owner | Requirements batches |

`.claude/launch.json` defines the dev server configs used by the preview tooling to launch both the backend and frontend.
