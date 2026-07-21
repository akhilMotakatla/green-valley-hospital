# Green Valley Hospital — Security Guide

---

## Authentication

### JWT Bearer Tokens

The application uses **JSON Web Tokens (JWT)** for authentication. Every protected endpoint requires a valid JWT in the `Authorization: Bearer <token>` header.

**Token lifecycle**:
1. Client sends `POST /api/auth/login` with `{email, password}`.
2. Server verifies credentials and issues a signed JWT containing `{sub: user_id, role, exp}`.
3. Client stores the token in memory (via `AuthContext`) and attaches it to every subsequent request.
4. Token expires after `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 60 minutes). The client must log in again after expiry.

**Token signing**: HMAC-SHA256 (`HS256`) using the `SECRET_KEY` environment variable. Change this key to a long random string (32+ bytes) in any non-development environment.

### Password Storage

Passwords are hashed with **bcrypt** before storage. The plaintext password is never stored or logged. The `security.py` module handles hashing and verification.

### Password Policy

Enforced server-side on signup and password change (mirrored client-side for UX):
- Minimum **8 characters**
- At least **one letter**
- At least **one number**

### Login Security

- Wrong credentials return a **generic error** that does not reveal whether the email exists (prevents user enumeration).
- Deactivated accounts return **403 Forbidden** with reason "account inactive" — no JWT is issued.
- There is no account lockout mechanism in this build (out of scope; see `docs/requirements.md` Section 4).

---

## Authorization

### Role-Based Access Control (RBAC)

Every authenticated endpoint checks the role claim from the JWT. The five roles are:

| Role | Description |
|---|---|
| `Admin` | Full system administration access |
| `Doctor` | Clinical access limited to own patients |
| `Patient` | Self-service access to own data only |
| `Staff` | Front-desk access (appointments + demographics) |
| `Lab` | Lab order queue and result upload only |

Role checks are enforced in FastAPI **dependency injectors** (`deps.py`). The frontend hiding a UI control is never a substitute for backend enforcement.

### Row-Level Authorization

Role alone is not sufficient. Every clinical and personal data endpoint also enforces **ownership and relationship checks**:

- **Patient data**: a patient can only access rows where `patient_id` equals their own. Requests for another patient's data return **403 Forbidden**.
- **Doctor access**: a doctor can only access clinical data for patients with whom they have at least one appointment record (past or present). No appointment relationship returns **403 Forbidden**.
- **Staff**: can read/write appointments and demographic data for any patient, but cannot write clinical content.
- **Lab**: can only see the minimum patient fields needed to process an order — never full medical history, prescriptions, or billing.
- **Admin**: cannot author clinical content (visit notes, prescriptions, lab orders). Admin's role is account/data administration only.

### Signup Role Enforcement

`POST /api/auth/signup` always creates an account with `role = Patient`, regardless of any role field in the request body. Other roles can only be created by an existing Admin via `POST /api/admin/users`.

### CORS

The backend is configured to allow requests only from the frontend origin (`http://localhost:5173` in development). In production, update the `CORS_ORIGINS` setting in `config.py` to the deployed frontend URL.

---

## Access Control Matrix

| Resource | Admin | Doctor | Patient | Staff | Lab |
|---|---|---|---|---|---|
| User accounts (CRUD) | Full | — | Self profile | Create Patient only | — |
| Departments | Full CRUD | Read | Read | Read | Read |
| Appointments | All (read/write) | Own (as assigned doctor) | Own (as patient) | All (create/edit) | — |
| Visit notes / diagnoses | Read (no create) | Own patients (create/read) | Own (read-only) | Read limited subset | — |
| Prescriptions | Read | Own patients (create/read) | Own (read-only) | Read-only | — |
| Lab orders | Read | Own patients (create/read) | Own (read-only) | Read-only | Assigned queue |
| Lab results | Read | Own patients (read) | Own (read-only) | Read-only | Create / edit until finalized |
| Billing / invoices | Full | — | Own (read-only) | Create/edit | — |
| Blog articles | Full CRUD + publish | — | Read published only | — | — |
| Contact messages | Full (read/resolve) | — | Submit via public form | Read/resolve | — |
| Site content (home/about) | Full PATCH | — | Read | — | — |
| Patient vitals | — | — | — | Create/read | — |
| Audit log | Read | — | — | — | — |

---

## Sensitive Data Handling

- **Passwords**: bcrypt-hashed, never returned in any API response.
- **JWT secret**: read from environment variable only; never committed to source control.
- **Lab result attachments**: stored in the `uploads/` directory on the local filesystem, not in the database. The path is stored in `lab_results.file_attachment_path`.
- **Profile photos**: stored as static files in `src/frontend/public/images/`; the path is stored in `doctors.profile_photo_path`. Paths are relative and served as static assets — no authentication is required to fetch image files.
- **Contact form data**: stored in the database with no automatic deletion policy. Admin and Staff can review and resolve messages.

---

## Out of Scope (Not Implemented)

The following security features are explicitly excluded from this demo build:

- Multi-factor authentication (MFA)
- OAuth / SSO login
- Account lockout after failed login attempts
- Rate limiting on login or any endpoint
- Full HIPAA / GDPR compliance audit
- Granular field-level audit logging for clinical reads (only account/role admin actions are logged)
- Content Security Policy (CSP) headers
- Virus scanning for uploaded lab result attachments
- HTTPS / TLS configuration (assumed to be handled by a reverse proxy in production)
