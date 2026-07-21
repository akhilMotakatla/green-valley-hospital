# Green Valley Hospital — Developer Guide

## Overview

Green Valley Hospital is a full-stack hospital management web application with:

- **Backend**: Python 3.11+ · FastAPI · SQLAlchemy 2.x · SQLite · JWT auth
- **Frontend**: React 19 · Vite · TypeScript · React Router · Lucide Icons
- **Database**: SQLite (single file, no separate DB server required)

---

## Project Structure

```
Green Valley Hospital/
├── src/
│   ├── backend/
│   │   └── app/
│   │       ├── main.py            # FastAPI app entry point, CORS, router registration
│   │       ├── models.py          # SQLAlchemy ORM models
│   │       ├── schemas.py         # Pydantic request/response schemas
│   │       ├── database.py        # DB engine, session factory, init_db()
│   │       ├── security.py        # JWT creation/verification, password hashing
│   │       ├── deps.py            # FastAPI dependency injectors (get_db, current_user)
│   │       ├── config.py          # App settings (env vars / defaults)
│   │       ├── utils.py           # Shared utility functions
│   │       └── routers/
│   │           ├── auth.py        # POST /api/auth/login, /signup
│   │           ├── public.py      # GET /api/public/* (no auth required)
│   │           ├── admin.py       # /api/admin/* (Admin role only)
│   │           ├── doctor.py      # /api/doctor/* (Doctor role only)
│   │           ├── patient.py     # /api/patients/* (Patient role only)
│   │           ├── staff.py       # /api/staff/* (Staff role only)
│   │           └── lab.py         # /api/lab/* (Lab role only)
│   └── frontend/
│       └── src/
│           ├── App.tsx            # Route definitions
│           ├── auth/              # AuthContext, RequireAuth guard
│           ├── layouts/           # PublicLayout, AppShell (authenticated)
│           ├── components/        # Shared components (Logo, SkeletonBlock, etc.)
│           ├── pages/
│           │   ├── public/        # Public site pages (no login)
│           │   ├── admin/         # Admin dashboard pages
│           │   ├── doctor/        # Doctor portal pages
│           │   ├── patient/       # Patient portal pages
│           │   ├── staff/         # Staff portal pages
│           │   └── lab/           # Lab portal pages
│           └── utils/             # deptIcons.tsx (department → Lucide icon map)
├── db/
│   ├── schema.sql                 # Canonical DDL (source of truth for DB structure)
│   └── seed/
│       └── seed.py                # Demo data seeding script
├── docs/                          # All project documentation
├── tests/                         # Automated test suite
└── uploads/                       # Local file storage for lab result attachments
```

---

## Prerequisites

| Tool | Minimum version |
|---|---|
| Python | 3.11 |
| Node.js | 18.x |
| npm | 9.x |
| Git | any |

---

## Backend Setup

### 1. Create and activate a virtual environment

```bash
cd src/backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment variables

Create `src/backend/.env` (or set environment variables directly). The app reads from `app/config.py`:

```env
SECRET_KEY=change-me-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=sqlite:///./greenvalley.db
UPLOAD_DIR=../../../uploads
```

- `SECRET_KEY`: used to sign JWT tokens — change this in any shared environment
- `DATABASE_URL`: SQLite path relative to where the app runs; defaults to `greenvalley.db` in the backend folder
- `UPLOAD_DIR`: path for lab result file uploads; defaults to the `uploads/` folder at project root

### 4. Initialize the database

The database is created automatically when the app starts via `init_db()` in `database.py`. To seed demo data:

```bash
cd db/seed
python seed.py
```

The seed script is idempotent — running it multiple times does not create duplicates.

### 5. Run the backend

```bash
cd src/backend
uvicorn app.main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`.

Interactive API docs (Swagger UI): `http://localhost:8000/docs`

---

## Frontend Setup

### 1. Install dependencies

```bash
cd src/frontend
npm install
```

### 2. Environment variables

Create `src/frontend/.env.development`:

```env
VITE_API_URL=http://localhost:8000
```

### 3. Run the development server

```bash
npm run dev
```

The frontend is available at `http://localhost:5173`.

### 4. Build for production

```bash
npm run build
```

Output goes to `src/frontend/dist/`. Serve with any static file server or Nginx.

---

## Image Assets

Static images live in `src/frontend/public/images/`. They are served directly by Vite at dev time and included in the production build.

See `docs/requirements.md` Section 6.18 for the full list of required image filenames and dimensions. For local development, SVG placeholder files with colored backgrounds are sufficient.

---

## Demo Accounts (after seeding)

| Role | Email | Password |
|---|---|---|
| Admin | admin@greenvalley.demo | Admin123! |
| Doctor | dr.heart@greenvalley.demo | Doctor123! |
| Doctor | dr.patel@greenvalley.demo | Doctor123! |
| Doctor | dr.nguyen@greenvalley.demo | Doctor123! |
| Doctor | dr.martinez@greenvalley.demo | Doctor123! |
| Patient | patient@greenvalley.demo | Patient123! |
| Staff | staff@greenvalley.demo | Staff123! |
| Lab | lab@greenvalley.demo | Lab123! |

---

## Running Tests

```bash
cd tests
pytest -v
```

Tests use `httpx.AsyncClient` against a fresh in-memory SQLite instance spun up per test session. No external services required.

---

## Common Issues

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: app` | Run uvicorn from `src/backend/`, not from the project root |
| `CORS error` in browser | Check `main.py` CORS origins include `http://localhost:5173` |
| `greenvalley.db` locked | Another process has the DB open; stop it before re-seeding |
| `profile_photo_path` images 404 | Place image files in `src/frontend/public/images/` |
| JWT token expired immediately | Check system clock; `ACCESS_TOKEN_EXPIRE_MINUTES` defaults to 60 |
