# Green Valley Hospital — REST API Contract

Status: Draft v1.2  (updated for Section 8: BillingSpecialist role, performance, email notifications, billing portal)
Owner: Solution Architect stage
Consumers: Backend developer agent, Frontend developer agent (single source of truth — build against this exactly)
Companion docs: `docs/architecture.md` (auth flow, ER diagram, resolved open items), `db/schema.sql` (DDL)

## Conventions

- Base path: `/api`.
- All request/response bodies are JSON, `snake_case` field names, matching `db/schema.sql` columns 1:1 wherever a field is a direct pass-through.
- Timestamps: ISO-8601 strings (`"2026-07-18T14:30:00"`).
- Money: JSON responses express amounts as `total_amount_cents` (integer) to match storage; frontend formats for display.
- Auth: `Authorization: Bearer <jwt>` header on every non-public endpoint.
- Standard error shape: `{"detail": "<message>"}` (FastAPI default), optionally `{"detail": [...]}` for validation errors (FastAPI/Pydantic 422 format).
- Standard status codes used throughout: `200 OK`, `201 Created`, `204 No Content`, `400 Bad Request` (malformed input), `401 Unauthorized` (missing/invalid/expired token), `403 Forbidden` (role or ownership check failed — see `docs/architecture.md` §4.2 for the 403-vs-404 policy), `404 Not Found` (resource genuinely doesn't exist), `409 Conflict` (double-booking, cancellation-window violation), `422 Unprocessable Entity` (validation errors).
- Pagination: list endpoints accept `?page=1&page_size=20` (defaults shown). `page_size` max is 100 (silently clamped; `page_size > 100` returns 100 items). `page=0` or negative values return 400. Response envelope: `{"items": [...], "total": <int>, "page": <int>, "page_size": <int>, "total_pages": <int>}` where `total_pages = ceil(total / page_size)` (0 when total is 0). **All 13 affected list endpoints** were updated in v1.2 to return this exact five-field envelope. See Section 8.2.2 for the full list of affected endpoints.
- "Required role" of `Any authenticated` means any of Admin/Doctor/Patient/Staff/Lab, still subject to row-level checks noted per endpoint.

---

## 1. Auth

| Method | Path | Required role | Request | Response |
|---|---|---|---|---|
| POST | `/api/auth/signup` | Public | `{email, password, full_name, phone, date_of_birth}` | `201` `{id, email, role: "Patient", full_name, phone, is_active, created_at}` |
| POST | `/api/auth/login` | Public | `{email, password}` | `200` `{access_token, token_type: "bearer", expires_in, role, user_id}` |
| GET | `/api/auth/me` | Any authenticated | — | `200` `{id, email, role, full_name, phone, is_active, created_at}` |

Notes:
- `/auth/signup` request schema has **no `role` field** — server always sets `role = "Patient"` (AC-AUTH-1). Password validated server-side against SEC-1 (min 8 chars, ≥1 letter, ≥1 number) → `422` on failure. Any attempt to pass `role=BillingSpecialist` (or any non-Patient role) in the request body → `400 Bad Request` (BILL-ROLE-2, AC-BILL-ROLE-1). The server ignores or rejects any `role` field in the signup body.
- `/auth/login`: wrong email or password → `401` generic `{"detail": "Invalid email or password"}` (AUTH-5). Correct credentials but `is_active = false` → `403` `{"detail": "Account is inactive"}` (AUTH-6, AC-AUTH-3).
- **JWT payload (v1.2 extension — Section 8.2.4):** The issued access token now contains five claims: `sub` (user_id, integer), `role` (role string), `email` (user's email address), `full_name` (user's full name from `users.full_name`), `exp` (Unix epoch expiry). This applies to all roles without exception (AC-JWT-FIELDS). The `create_access_token` function must include `email` and `full_name` when minting the token. The frontend `AuthContext` reads these claims from the decoded JWT at login and stores them in context state (no additional `/auth/me` call required for the sidebar display).
- This is distinct from **Staff-initiated patient registration**, which is `POST /api/staff/patients` (§6) — that endpoint requires the Staff role and returns full patient + user records including a generated temporary password, whereas `/auth/signup` is self-service.

---

## 2. Public (no auth required)

| Method | Path | Required role | Request | Response |
|---|---|---|---|---|
| GET | `/api/public/home` | Public | — | `200` `{tagline, highlights: [...], featured_departments: [{department_id, name, description, first_doctor: {doctor_id, full_name, specialty, profile_photo_path}\|null}], recent_articles: [{article_id, title, slug, summary, author_name, published_at, cover_image_path}]}` |
| GET | `/api/public/about` | Public | — | `200` `{mission, history, facilities, accreditations}` |
| GET | `/api/public/departments` | Public | — | `200` `{items: [{department_id, name, description}]}` (active departments only) |
| GET | `/api/public/departments/{department_id}/doctors` | Public | — | `200` `{department: {department_id, name, description}, items: [{doctor_id, full_name, specialty, qualifications, years_experience, profile_photo_path}]}` |
| GET | `/api/public/doctors/{doctor_id}` | Public | — | `200` `{doctor_id, full_name, specialty, department: {department_id, name}, qualifications, bio, years_experience, consultation_hours, profile_photo_path}` (no schedule internals, no patient data — PUB-DEPT-3) |
| GET | `/api/public/contact-info` | Public | — | `200` `{address, general_phone, emergency_phone}` |
| POST | `/api/public/contact-messages` | Public | `{name, email, phone?, subject, message}` | `201` `{message_id, status: "New", created_at}` — missing required field → `422`, no row created (AC-CONTACT-2) |
| GET | `/api/public/blog` | Public | query: `page`, `page_size` | `200` `{items: [{article_id, title, slug, summary, author_name, cover_image_path, published_at}], total, page, page_size}` — Published only (PUB-BLOG-3) |
| GET | `/api/public/blog/{slug}` | Public | — | `200` `{article_id, title, slug, body, author_name, cover_image_path, published_at}`; Draft or unknown slug → `404` (AC-BLOG-1) |

### Section 6 backend changes — notes for Pavan

**`GET /api/public/home` — `recent_articles` field (VI-HOME-7):**
The home endpoint now includes a `recent_articles` array (up to 3 items, most recently published first). Each item shape: `{article_id, title, slug, summary, author_name, published_at, cover_image_path}`. Only Published articles are included. This is the canonical approach — the frontend does NOT make a separate `GET /public/blog?limit=3` call for the home page; it reads from the home payload. If `recent_articles` is empty (no published articles yet), return an empty array, not null.

**`GET /api/public/home` — `featured_departments.first_doctor` (VI-HOME-5):**
Each element of the `featured_departments` array gains a `first_doctor` field: the first (lowest `doctor_id`) doctor record belonging to that department, or `null` if the department has no active doctors. Shape: `{doctor_id, full_name, specialty, profile_photo_path}`. This allows the "Meet Our Specialists" teaser on the home page to render doctor cards without a second API call.

**`GET /api/public/departments/{department_id}/doctors` — `department` wrapper (VI-DDOC-1):**
The response is now a JSON object with two top-level keys: `department` (the department record) and `items` (the doctors array). Previously the response was only the items array wrapper. The `department` object carries `{department_id, name, description}`. This is needed so the Department Doctors page can render its header banner with the department name without a separate lookup.

**`profile_photo_path` on `Doctor` (VI-HOME-5, VI-DDOC-2, VI-DOCPROF-1):**
The `doctors` table gains a nullable `profile_photo_path TEXT` column (see `db/schema.sql`). This field is now included in every endpoint that returns a doctor record (public listing, department doctors, public profile, doctor-me, patients doctor browse, staff directory). The value is a filesystem path relative to the static assets root (e.g., `/images/doctors/dr-smith.jpg`). It is set via `PATCH /api/doctor/me` (doctor self-updates their own photo path) or `PATCH /api/admin/users/{user_id}` (admin sets it). The frontend renders it as a static asset `<img src={profile_photo_path} />` — no separate image-serving API endpoint needed (VI-IMG-3).

---

## 3. Admin

Role required: `Admin` on every endpoint below (`require_role("Admin")`), enforcing ADM-1..ADM-10 / AUTHZ-5.

### 3.1 User & account management
| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/admin/users` | query: `role?`, `is_active?`, `page`, `page_size` | `200` `{items: [{id, email, role, full_name, phone, is_active, created_at}], total, page, page_size}` |
| POST | `/api/admin/users` | `{email, password, role: "Doctor"\|"Staff"\|"Lab"\|"Admin", full_name, phone, department_id?, ...role_specific_fields}` | `201` created user + role-profile record; writes an `audit_log_entries` row (`action: "user_created"`) |
| GET | `/api/admin/users/{user_id}` | — | `200` full user record + role-profile sub-object |
| PATCH | `/api/admin/users/{user_id}` | `{full_name?, phone?, department_id?, specialty?, ...}` (role-profile fields) | `200` updated user record |
| PATCH | `/api/admin/users/{user_id}/status` | `{is_active: bool}` | `200` `{id, is_active}`; writes an audit entry (`action: "user_deactivated"` or `"user_reactivated"`) |
| PATCH | `/api/admin/users/{user_id}/role` | `{role, department_id?}` | `200` updated user; writes an audit entry (`action: "role_changed"`, `details`: old→new role) — AUTHZ-5 |

### 3.2 Departments
| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/admin/departments` | — | `200` `{items: [{department_id, name, description, is_active}]}` |
| POST | `/api/admin/departments` | `{name, description}` | `201` `{department_id, name, description, is_active: true}` |
| PATCH | `/api/admin/departments/{department_id}` | `{name?, description?}` | `200` updated department |
| PATCH | `/api/admin/departments/{department_id}/status` | `{is_active: bool}` | `200` `{department_id, is_active}` |

### 3.3 Appointments (system-wide view)
| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/admin/appointments` | query: `department_id?`, `doctor_id?`, `date?`, `status?`, `page`, `page_size` | `200` `{items: [{appointment_id, patient_id, patient_name, doctor_id, doctor_name, department_name, scheduled_at, status, reason}], total, page, page_size}` |

### 3.4 Billing (system-wide view)
| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/admin/invoices` | query: `patient_id?`, `status?`, `page`, `page_size` | `200` `{items: [{invoice_id, patient_id, patient_name, appointment_id, total_amount_cents, status, created_at}], total, page, page_size}` |

### 3.5 Blog administration
| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/admin/blog` | query: `status?`, `page`, `page_size` | `200` all articles (Draft + Published) |
| POST | `/api/admin/blog` | multipart: `{title, summary, body, cover_image?: file}` | `201` `{article_id, ..., status: "Draft", slug}` (slug auto-generated from title) |
| PATCH | `/api/admin/blog/{article_id}` | `{title?, summary?, body?}` or multipart with `cover_image?` | `200` updated article |
| PATCH | `/api/admin/blog/{article_id}/publish` | — | `200` `{article_id, status: "Published", published_at}` (AC-BLOG-2) |
| PATCH | `/api/admin/blog/{article_id}/unpublish` | — | `200` `{article_id, status: "Draft", published_at: null}` |
| DELETE | `/api/admin/blog/{article_id}` | — | `204` |

### 3.6 Contact messages
| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/admin/contact-messages` | query: `status?`, `page`, `page_size` | `200` `{items: [{message_id, name, email, phone, subject, message, status, created_at}], total, page, page_size}` |
| PATCH | `/api/admin/contact-messages/{message_id}/status` | `{status: "Reviewed"\|"Resolved"}` | `200` `{message_id, status}` |

### 3.7 Dashboard & audit
| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/admin/dashboard/summary` | — | `200` `{patient_count, doctor_count, appointments_today, pending_lab_orders}` (ADM-8) |
| GET | `/api/admin/audit-log` | query: `actor_user_id?`, `target_user_id?`, `page`, `page_size` | `200` `{items: [{log_id, actor_user_id, actor_name, action, target_user_id, target_name, details, created_at}], total, page, page_size}` (ADM-9) |

### 3.8 Public site content (About/Home copy)
| Method | Path | Request | Response |
|---|---|---|---|
| PATCH | `/api/admin/site-content/home` | `{tagline?, highlights?}` | `200` updated home content |
| PATCH | `/api/admin/site-content/about` | `{mission?, history?, facilities?, accreditations?}` | `200` updated about content |

Note: Admin explicitly cannot write to visit-note/prescription/lab-result creation endpoints (ADM-10) — those are Doctor/Lab-only by role check; Admin's read access to clinical data is via `GET /api/admin/appointments` (metadata only, no diagnosis/prescription body) plus whatever the Doctor/Patient-facing read endpoints would show if Admin were added to their role list, which it deliberately is not. Admin has no clinical-content read endpoint beyond appointment metadata in this build.

---

## 4. Doctor

Role required: `Doctor` on every endpoint below, plus the ownership rule from AUTHZ-2 ("Doctor can only access clinical data for a patient with whom they have at least one appointment record, past or present") enforced on every patient-scoped read/write.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/doctor/me` | — | `200` `{doctor_id, full_name, department: {department_id, name}, specialty, qualifications, bio, years_experience, consultation_hours, profile_photo_path}` |
| PATCH | `/api/doctor/me` | `{bio?, qualifications?, consultation_hours?, profile_photo_path?}` | `200` updated profile (DOC-1 — public-facing fields only; `specialty` and `department_id` remain Admin-managed) |
| GET | `/api/doctor/me/appointments` | query: `status?`, `from?`, `to?`, `page`, `page_size` | `200` `{items: [{appointment_id, patient_id, patient_name, scheduled_at, status, reason}], total, page, page_size}` (DOC-2) |
| PATCH | `/api/doctor/appointments/{appointment_id}/status` | `{status: "Completed"\|"NoShow"\|"Cancelled"}` | `200` `{appointment_id, status}`; `403` if `appointment.doctor_id` != current doctor (DOC-4) |
| GET | `/api/doctor/patients/{patient_id}/records` | — | `200` `{visit_notes: [...], prescriptions: [...], lab_results: [...]}`; `403` if no appointment relationship exists (AUTHZ-2, AC-DOC-1) |
| POST | `/api/doctor/appointments/{appointment_id}/visit-notes` | `{diagnosis?, notes}` | `201` `{record_id, appointment_id, patient_id, doctor_id, diagnosis, notes, created_at}`; `403` if appointment not owned by this doctor (DOC-4) |
| POST | `/api/doctor/appointments/{appointment_id}/prescriptions` | `{medicines: [{name, dosage, frequency, duration}], instructions?}` | `201` `{prescription_id, appointment_id, patient_id, doctor_id, medicines, instructions, created_at}`; `403` if appointment not owned by this doctor (DOC-5, AC-DOC-2) |
| POST | `/api/doctor/patients/{patient_id}/lab-orders` | `{test_type: "Lab"\|"XRay"\|"Scan", test_subtype?, notes?, appointment_id?}` | `201` `{order_id, patient_id, doctor_id, test_type, test_subtype, status: "Pending", notes, created_at}`; `403` if no appointment relationship (DOC-6, AC-LAB-1) |
| GET | `/api/doctor/lab-orders/{order_id}/results` | — | `200` `{order_id, status, results: [{result_id, result_data, file_attachment_path, version, is_finalized, finalized_at}]}`; `403` if `order.doctor_id` != current doctor (DOC-7, AC-LAB-2) |

---

## 5. Patient

Role required: `Patient` on every endpoint below, plus row-level ownership: `patient_id` must equal the current user's own linked `patient_id` (AUTHZ-1). Any request naming another patient's id returns `403 Forbidden` (AC-PAT-1) per the resolved 403-vs-404 policy in `docs/architecture.md` §4.2.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/patients/me` | — | `200` `{patient_id, full_name, email, phone, date_of_birth, gender, address, emergency_contact_name, emergency_contact_phone}` |
| PATCH | `/api/patients/me` | `{phone?, address?, emergency_contact_name?, emergency_contact_phone?, date_of_birth?}` | `200` updated profile (PAT-1 — cannot change `role`/`is_active`, not accepted by this schema) |
| GET | `/api/patients/doctors` | query: `department_id?` | `200` `{items: [{doctor_id, full_name, specialty, department_name, years_experience, profile_photo_path}]}` (PAT-2 search/browse) |
| GET | `/api/patients/doctors/{doctor_id}/availability` | query: `date` | `200` `{doctor_id, date, available_slots: ["09:00", "09:30", ...]}` |
| POST | `/api/patients/me/appointments` | `{doctor_id, scheduled_at, reason?}` | `201` `{appointment_id, patient_id, doctor_id, scheduled_at, status: "Scheduled", reason, created_at}`; slot already booked → `409 Conflict` (AC-APT-1, AC-APT-2) |
| GET | `/api/patients/me/appointments` | query: `status?`, `page`, `page_size` | `200` `{items: [{appointment_id, doctor_id, doctor_name, scheduled_at, status, reason}], total, page, page_size}` — only own rows (AC-PAT-2) |
| DELETE | `/api/patients/me/appointments/{appointment_id}` | — | `200` `{appointment_id, status: "Cancelled"}`; within the 2-hour notice window → `409 Conflict` `{"detail": "Appointments can only be cancelled at least 2 hours before the scheduled time"}` (PAT-4, AC-APT-3, `docs/architecture.md` §4.1); not own appointment → `403` |
| GET | `/api/patients/me/records` | — | `200` `{visit_notes: [...], prescriptions: [...], lab_results: [...]}` — own records only, read-only (PAT-5) |
| GET | `/api/patients/{patient_id}/records` | — | Same shape as above but explicit-id form used only by other roles' equivalent per-role endpoints; for a Patient calling this with any `patient_id` other than their own → `403 Forbidden` (AC-PAT-1). Patients should use `/api/patients/me/records` instead. |
| GET | `/api/patients/me/invoices` | query: `status?`, `page`, `page_size` | `200` `{items: [{invoice_id, appointment_id, total_amount_cents, status, created_at}], total, page, page_size}` (PAT-6, AC-BILL-1) |

Note: `POST /api/patients/{id}/prescriptions`, lab-order creation, etc. are **not exposed** under `/api/patients/*` at all (PAT-8 — read-only by omission, not by a role check that could be bypassed).

---

## 6. Staff

Role required: `Staff` on every endpoint below (AUTHZ-3 — read/write appointments and demographics for any patient; read-only on clinical content; no clinical-content writes, no Admin functions).

| Method | Path | Request | Response |
|---|---|---|---|
| POST | `/api/staff/patients` | `{full_name, email, phone, date_of_birth, gender?, address?, emergency_contact_name?, emergency_contact_phone?}` | `201` `{patient_id, user_id, full_name, email, temporary_password}` — front-desk registration, distinct from public signup (STF-2); server generates a temporary password the patient is expected to change on first login |
| GET | `/api/staff/patients/{patient_id}` | — | `200` `{patient_id, full_name, email, phone, date_of_birth, upcoming_appointments: [...]}` — basic demographic + appointment info only (STF-3) |
| GET | `/api/staff/patients` | query: `search?`, `page`, `page_size` | `200` `{items: [{patient_id, full_name, email, phone}], total, page, page_size}` |
| POST | `/api/staff/appointments` | `{patient_id, doctor_id, scheduled_at, reason?}` | `201` appointment record — front-desk booking on behalf of any patient (STF-1); slot conflict → `409` |
| GET | `/api/staff/appointments` | query: `patient_id?`, `doctor_id?`, `date?`, `status?`, `page`, `page_size` | `200` `{items: [...], total, page, page_size}` |
| PATCH | `/api/staff/appointments/{appointment_id}` | `{scheduled_at?, doctor_id?, status?, reason?}` | `200` updated appointment — no notice-window restriction (front-desk override; see `docs/architecture.md` §4.1) |
| POST | `/api/staff/patients/{patient_id}/vitals` | `{height_cm?, weight_kg?, blood_pressure?, temperature_c?, pulse_bpm?, recorded_for_appointment_id?}` | `201` `{vitals_id, patient_id, ..., recorded_by_user_id, created_at}` (STF-4) |
| GET | `/api/staff/patients/{patient_id}/prescriptions` | — | `200` `{items: [...]}` — read-only (STF-5, AUTHZ-3) |
| GET | `/api/staff/patients/{patient_id}/lab-results` | — | `200` `{items: [...]}` — read-only (STF-5, AUTHZ-3) |
| GET | `/api/staff/contact-messages` | query: `status?`, `page`, `page_size` | `200` `{items: [...], total, page, page_size}` (STF-6) |
| PATCH | `/api/staff/contact-messages/{message_id}/status` | `{status: "Reviewed"\|"Resolved"}` | `200` `{message_id, status}` |
| GET | `/api/staff/directory` | query: `department_id?` | `200` `{items: [{doctor_id, full_name, specialty, department_name, consultation_hours, profile_photo_path}]}` — includes schedule info to assist booking (STF-7) |

Note: no `POST` endpoints for prescriptions, lab orders, or diagnoses exist under `/api/staff/*` (STF-8 enforced by omission, mirroring the Patient section's approach) — attempting to reuse a Doctor or Lab endpoint as Staff fails the `require_role` check with `403`.

Vitals table: `staff_members` records vitals via a new `vitals` table not explicitly listed in `db/schema.sql`'s original entity list from requirements — **added to schema as a lightweight addition**: see note in §7 below. (STF-4 requires persistence and the requirements doc's entity list didn't enumerate a vitals table explicitly; this is a minor schema extension, documented here rather than silently added.)

---

## 7. Lab

Role required: `Lab` on every endpoint below, restricted to the assigned queue and minimal patient fields (AUTHZ-4, LAB-5).

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/lab/orders` | query: `test_type?`, `status?`, `page`, `page_size` | `200` `{items: [{order_id, patient_name, patient_dob, ordering_doctor_name, test_type, test_subtype, status, notes, created_at}], total, page, page_size}` — minimal patient fields only, no full medical history/prescriptions/billing (LAB-1, AUTHZ-4) |
| PATCH | `/api/lab/orders/{order_id}/status` | `{status: "InProgress"\|"Completed"}` | `200` `{order_id, status}` (LAB-2) |
| POST | `/api/lab/orders/{order_id}/results` | multipart: `{result_data, file?: file}` | `201` `{result_id, order_id, result_data, file_attachment_path, version: 1, is_finalized: true, finalized_at}` (LAB-3) |
| POST | `/api/lab/orders/{order_id}/results/amend` | multipart: `{result_data, file?: file}` | `201` new `lab_results` row with `version = previous_max + 1`; previous version(s) remain retrievable, unchanged (LAB-4, AC-LAB-3) — only callable if a prior finalized version exists for this `order_id` |
| GET | `/api/lab/orders/{order_id}/results` | — | `200` `{order_id, results: [{result_id, result_data, file_attachment_path, version, is_finalized, finalized_at}]}` — all versions |
| GET | `/api/lab/results/{result_id}/file` | — | `200` binary file stream (the authenticated download route referenced in `docs/architecture.md` §4.3); `403` unless requester is the ordering Doctor, the owning Patient, Lab, or Admin |

Note: `/api/lab/*` has no endpoints for appointments, prescriptions, or diagnoses (LAB-6 enforced by omission).

---

## 8. Cross-Check Summary (requirements → endpoint/schema mapping)

| Requirement area | Endpoint(s) | Schema table(s) |
|---|---|---|
| PUB-HOME, PUB-ABOUT | `/api/public/home`, `/api/public/about` | (static content, not persisted — see note below) |
| PUB-DEPT-1..3 | `/api/public/departments`, `/api/public/departments/{id}/doctors`, `/api/public/doctors/{id}` | `departments`, `doctors`, `users` |
| PUB-CONTACT-1..3 | `/api/public/contact-info`, `/api/public/contact-messages` | `contact_messages` |
| PUB-BLOG-1..3 | `/api/public/blog`, `/api/public/blog/{slug}` | `blog_articles` |
| PUB-AUTH-1..3 | `/api/auth/login`, `/api/auth/signup` | `users` |
| ADM-1, ADM-2, AUTHZ-5 | `/api/admin/users`, `/api/admin/users/{id}/status`, `/api/admin/users/{id}/role` | `users`, `doctors`/`staff_members`/`lab_technicians`, `audit_log_entries` |
| ADM-3 | `/api/admin/departments` | `departments` |
| ADM-4 | `/api/admin/appointments` | `appointments` |
| ADM-5 | `/api/admin/invoices` | `invoices` |
| ADM-6 | `/api/admin/blog/*` | `blog_articles` |
| ADM-7 | `/api/admin/contact-messages/*` | `contact_messages` |
| ADM-8 | `/api/admin/dashboard/summary` | `patients`, `doctors`, `appointments`, `lab_orders` |
| ADM-9 | `/api/admin/audit-log` | `audit_log_entries` |
| ADM-10 | (no write endpoints granted to Admin for clinical tables) | `visit_notes`, `prescriptions`, `lab_results` — no Admin-role write path |
| DOC-1..9 | `/api/doctor/*` | `doctors`, `appointments`, `visit_notes`, `prescriptions`, `lab_orders`, `lab_results` |
| PAT-1..8 | `/api/patients/*` | `patients`, `appointments`, `visit_notes`, `prescriptions`, `lab_orders`, `lab_results`, `invoices` |
| STF-1..8 | `/api/staff/*` | `appointments`, `patients`, `vitals` (new — see §6 note), `prescriptions` (read), `lab_results` (read), `contact_messages`, `doctors` |
| LAB-1..6 | `/api/lab/*` | `lab_orders`, `lab_results` |
| AUTH-1..6 | `/api/auth/*` | `users` |
| SEC-1 | `/api/auth/signup` validation | `users.password_hash` |
| AUTHZ-1..6 | enforced per-endpoint via `get_current_user` + `require_role` + ownership checks | n/a (application logic) |

Static public content (`home` tagline/highlights, `about` mission/history/facilities/accreditations) is intentionally **not** modeled as its own schema table in this draft — it's small, low-churn, single-tenant copy. Recommended implementation: a simple `site_content` key-value table (`key TEXT PRIMARY KEY, value_json TEXT, updated_at TEXT`) so `PATCH /api/admin/site-content/{page}` has somewhere to persist to; add this table to `db/schema.sql` during backend implementation if the developer agent prefers persistence over a hardcoded config file. Flagged here rather than silently decided, since requirements.md's entity list (§3.4) didn't enumerate it.

**Two minor schema extensions beyond the requirements doc's explicit entity list**, both flagged rather than silently added:
1. `vitals` table (supports STF-4) — not in requirements.md §3.4's entity list. Suggested columns: `vitals_id, patient_id (FK), recorded_by_user_id (FK), appointment_id (FK, optional), height_cm, weight_kg, blood_pressure, temperature_c, pulse_bpm, created_at`. Add to `db/schema.sql` during backend implementation.
2. `site_content` table (supports ADM's "edit About/Home copy" row in the authz matrix) — optional; a config file is an acceptable alternative if the backend agent prefers to avoid the extra table for static copy.

**Schema changes added in v1.1 (Section 6 visual requirements):**
3. `doctors.profile_photo_path TEXT` — nullable column added to `db/schema.sql` directly. No new table or migration; Pavan adds this column when running the DDL against a fresh database, or issues `ALTER TABLE doctors ADD COLUMN profile_photo_path TEXT;` against an existing database file.

**Schema changes added in v1.2 (Section 8 — BillingSpecialist, performance, email notifications):**
4. `users.role` CHECK extended to include `'BillingSpecialist'`. Pavan must update the ORM `CheckConstraint` in `models.py` accordingly.
5. `billing_specialists` table added (see `db/schema.sql` §1).
6. `invoices.has_insurance_claim INTEGER NOT NULL DEFAULT 0` column added; all invoice create/read/update endpoints return and accept this field. Default value is `0` when not supplied.
7. `email_notifications` table added (see `db/schema.sql` §6).
8. 12 new performance indexes added across `invoices`, `appointments`, `visit_notes`, `prescriptions`, `lab_orders`, `lab_results`, `blog_articles`, `contact_messages`, and `email_notifications` (see `db/schema.sql` inline comments). Two indexes that were listed in Section 8.2.1 as "Add" (`invoices.patient_id`, `invoices.status`) already existed in v1.0 — not duplicated. Two "Verify" entries (`patients.user_id`, `users.email`) are covered by existing `UNIQUE` constraints which create implicit SQLite indexes — no additional `CREATE INDEX` needed.
9. `invoices.total_amount_cents` was already `INTEGER` in v1.0 (not a float) — no migration needed for this field.

---

## 9. Billing Specialist Endpoints

Role required: `BillingSpecialist` on every endpoint in this section unless otherwise stated. All role checks are enforced server-side (AUTHZ-10). A BillingSpecialist JWT is issued only after Admin creates the account — self-signup is blocked (BILL-ROLE-2).

**Base path for this section: `/api/billing`**

**Scope boundaries (BILL-DENY-1 through BILL-DENY-6):** A BillingSpecialist receives `403 Forbidden` from any endpoint under `/api/doctor/*`, `/api/patients/{id}/records`, `/api/patients/{id}/prescriptions`, `/api/lab/*`, `/api/admin/*`. These are enforced by the `require_role` dependency — no special handling needed per endpoint.

---

### 9.1 Auth — BillingSpecialist Self-Registration Blocked

| Method | Path | Required role | Request | Response |
|---|---|---|---|---|
| POST | `/api/auth/signup` | Public | `{email, password, full_name, phone, date_of_birth}` | Any `role` field in the request body is rejected: `400 Bad Request` `{"detail": "Self-registration is available for Patient role only"}` if a non-Patient role is supplied. Normal Patient signup proceeds per §1. |

This is an additive note on the existing endpoint — no new endpoint is introduced.

---

### 9.2 Dashboard

| Method | Path | Required role | Request | Response |
|---|---|---|---|---|
| GET | `/api/billing/dashboard` | BillingSpecialist | — | `200` `{outstanding_invoices, awaiting_claims, collected_this_month_cents, total_patients_billed}` |

Response shape:
```json
{
  "outstanding_invoices": 42,
  "awaiting_claims": 7,
  "collected_this_month_cents": 384500,
  "total_patients_billed": 318
}
```

Backend queries (Section 8.4.3):
- `outstanding_invoices`: `SELECT COUNT(*) FROM invoices WHERE status = 'Pending'`
- `awaiting_claims`: `SELECT COUNT(*) FROM invoices WHERE status = 'Pending' AND has_insurance_claim = 1`
- `collected_this_month_cents`: `SELECT COALESCE(SUM(total_amount_cents), 0) FROM invoices WHERE status = 'Paid' AND created_at >= {start_of_current_month_UTC}`
- `total_patients_billed`: `SELECT COUNT(DISTINCT patient_id) FROM invoices`

All four values are returned in a single response to avoid four separate page-load calls (AC-DASH-TILES).

---

### 9.3 Invoices

| Method | Path | Required role | Request | Response |
|---|---|---|---|---|
| GET | `/api/billing/invoices` | BillingSpecialist | query: `status?`, `has_insurance_claim?` (0 or 1), `search?`, `page`, `page_size` | `200` pagination envelope (see below) |
| GET | `/api/billing/invoices/{invoice_id}` | BillingSpecialist | — | `200` full invoice detail (see below) |
| POST | `/api/billing/invoices` | BillingSpecialist | `{patient_id, appointment_id?, line_items: [{description, amount_cents}], total_amount_cents, has_insurance_claim?}` | `201` invoice object |
| PATCH | `/api/billing/invoices/{invoice_id}` | BillingSpecialist | `{status?, has_insurance_claim?, line_items?, total_amount_cents?}` | `200` updated invoice object; if `status` changed → triggers email notification synchronously (Section 8.3) |
| DELETE | `/api/billing/invoices/{invoice_id}` | BillingSpecialist | — | `204`; invoice `status != 'Pending'` → `409 Conflict` `{"detail": "Only Pending invoices may be deleted"}` (BILL-4) |
| POST | `/api/billing/invoices/{invoice_id}/resend-notification` | BillingSpecialist | — | `201` `{notification_id, status, sent_at}`; writes a new `email_notifications` row with `trigger_event = 'manual_resend'` (BILL-8) |

**`GET /api/billing/invoices` — query parameters:**
- `?status=Pending|Paid|Waived` — server-side filter on `invoices.status`. Omit for all statuses.
- `?has_insurance_claim=1` — server-side filter; returns only invoices with `has_insurance_claim = 1`. Omit or `0` for no filter.
- `?search={term}` — case-insensitive LIKE filter on `patients.full_name` (`%term%`) OR exact `invoice_id` match (if `term` is a pure integer). Applied server-side (AC-LEDGER-SEARCH).
- `?page=N&page_size=M` — pagination per Conventions section. Default `page=1`, `page_size=20`, max `page_size=100`.

**`GET /api/billing/invoices` — response envelope:**
```json
{
  "items": [
    {
      "invoice_id": 1042,
      "patient_id": 7,
      "patient_name": "Alice Patel",
      "appointment_id": 55,
      "appointment_date": "2026-07-10T09:30:00",
      "total_amount_cents": 15000,
      "status": "Pending",
      "has_insurance_claim": 0,
      "created_at": "2026-07-10T10:00:00"
    }
  ],
  "total": 35,
  "page": 1,
  "page_size": 20,
  "total_pages": 2
}
```

`patient_name` is resolved by join (`users.full_name` via `patients.user_id`). `appointment_date` is `appointments.scheduled_at` joined on `invoices.appointment_id`; `null` if no linked appointment. These joined fields are never stored denormalized — always resolved at query time (PERF-CONS-2).

**`GET /api/billing/invoices/{invoice_id}` — full detail response:**
```json
{
  "invoice_id": 1042,
  "patient_id": 7,
  "patient_name": "Alice Patel",
  "appointment_id": 55,
  "appointment_date": "2026-07-10T09:30:00",
  "doctor_name": "Dr. Ravi Sharma",
  "department_name": "Cardiology",
  "line_items": [{"description": "Consultation", "amount_cents": 10000}, {"description": "ECG", "amount_cents": 5000}],
  "total_amount_cents": 15000,
  "status": "Pending",
  "has_insurance_claim": 0,
  "created_by_user_id": 3,
  "created_at": "2026-07-10T10:00:00"
}
```

`line_items` is the parsed form of `invoices.line_items_json` (JSON array in DB → array in response). `doctor_name` and `department_name` are joined from `appointments → doctors → departments` when `appointment_id` is not null; both are `null` otherwise.

**`POST /api/billing/invoices` — request body:**
```json
{
  "patient_id": 7,
  "appointment_id": 55,
  "line_items": [{"description": "Consultation", "amount_cents": 10000}],
  "total_amount_cents": 10000,
  "has_insurance_claim": 0
}
```
`appointment_id` is optional. `has_insurance_claim` defaults to `0` if omitted. `line_items_json` stored as JSON string in DB. `created_by_user_id` set to the authenticated BillingSpecialist's `user_id`. Response: created invoice in same shape as full detail above.

**`PATCH /api/billing/invoices/{invoice_id}` — email notification side-effect:**
If `status` is present in the request body AND differs from the current `invoices.status`, the server:
1. Captures `old_status` before the update.
2. Applies the update (commits to DB).
3. Constructs and writes the HTML email file to `uploads/email_log/{timestamp}_{patient_id}_invoice_{invoice_id}.html` (Section 8.3.2).
4. Inserts a row into `email_notifications` (`trigger_event = 'invoice_status_change'`).
5. Returns `200` with the updated invoice regardless of whether the file write succeeded or failed (NOTIFY-3).

If `status` is absent from the request body (partial update with no status change), no notification is triggered.

---

### 9.4 Read-Only Patient List (Billing Context)

| Method | Path | Required role | Request | Response |
|---|---|---|---|---|
| GET | `/api/billing/patients` | BillingSpecialist | query: `search?`, `page`, `page_size` | `200` pagination envelope |

Response item shape (AUTHZ-9 — restricted fields only):
```json
{
  "patient_id": 7,
  "full_name": "Alice Patel",
  "date_of_birth": "1990-04-15",
  "phone": "+1 (555) 123-4567",
  "email": "alice.patel@example.com"
}
```

Fields **not** returned: `address`, `gender`, `emergency_contact_name`, `emergency_contact_phone`. The join goes through `patients → users` to resolve `full_name`, `email`, and `phone`.

`?search={term}` — case-insensitive LIKE on `full_name` (`%term%`). Default `page=1`, `page_size=20`.

---

### 9.5 Read-Only Appointment List (Billing Reference)

| Method | Path | Required role | Request | Response |
|---|---|---|---|---|
| GET | `/api/billing/appointments` | BillingSpecialist | query: `patient_id?`, `status?`, `page`, `page_size` | `200` pagination envelope |

Response item shape (AUTHZ-8 — no clinical data):
```json
{
  "appointment_id": 55,
  "patient_id": 7,
  "patient_name": "Alice Patel",
  "scheduled_at": "2026-07-10T09:30:00",
  "status": "Completed",
  "doctor_name": "Dr. Ravi Sharma",
  "department_name": "Cardiology"
}
```

Fields **not** returned: `reason`, `diagnosis`, visit notes, prescriptions, or any clinical content. `created_by_user_id` is also excluded. Only the listed fields are available to BillingSpecialist. The backend enforces this at the query/serialization layer — a SELECT that explicitly names only the allowed columns.

---

### 9.6 Email Notification Log

| Method | Path | Required role | Request | Response |
|---|---|---|---|---|
| GET | `/api/billing/notifications` | BillingSpecialist, Admin | query: `page`, `page_size` | `200` pagination envelope — `body_html` excluded from list items |
| GET | `/api/billing/notifications/{notification_id}` | BillingSpecialist, Admin | — | `200` full notification including `body_html` |

**`GET /api/billing/notifications` — list item shape:**
```json
{
  "notification_id": 8,
  "recipient_user_id": 12,
  "recipient_name": "Alice Patel",
  "subject": "Invoice #1042 Status Update — Green Valley Hospital",
  "sent_at": "2026-07-10T10:05:00",
  "trigger_event": "invoice_status_change",
  "related_invoice_id": 1042,
  "status": "Sent"
}
```
`body_html` is intentionally excluded from list responses to keep payload size manageable (Section 8.3.5). Default sort: descending `sent_at`. Default `page=1`, `page_size=20`.

**`GET /api/billing/notifications/{notification_id}` — full detail adds:**
```json
{
  "notification_id": 8,
  "recipient_user_id": 12,
  "recipient_name": "Alice Patel",
  "subject": "Invoice #1042 Status Update — Green Valley Hospital",
  "body_html": "<!DOCTYPE html>...",
  "sent_at": "2026-07-10T10:05:00",
  "trigger_event": "invoice_status_change",
  "related_invoice_id": 1042,
  "status": "Sent"
}
```

Staff, Doctor, Patient, and Lab roles receive `403 Forbidden` from both notification endpoints (BILL-7, Section 8.3.5).

---

### 9.7 Pagination Envelope Reminder (All Billing Endpoints)

Every list endpoint in Section 9 returns the standard five-field envelope:
```json
{ "items": [...], "total": <int>, "page": <int>, "page_size": <int>, "total_pages": <int> }
```
`total_pages = ceil(total / page_size)`. If `total = 0`, `total_pages = 0`. `page_size` is clamped to 100 server-side if the caller supplies a value above 100 (`page_size` in the response reflects the clamped value — AC-PAGINATE-2).

---

### 9.8 Section 8 Cross-Check (Requirements → Endpoints → Schema)

| Requirement | Endpoint(s) | Schema |
|---|---|---|
| BILL-ROLE-1 (Admin creates BillingSpecialist) | `POST /api/admin/users` with `role: "BillingSpecialist"` | `users.role` CHECK extended; `billing_specialists` table |
| BILL-ROLE-2 (no self-signup) | `POST /api/auth/signup` → 400 if role supplied | No schema change |
| BILL-ROLE-3 (profile entity) | — (created by `POST /api/admin/users`) | `billing_specialists` table |
| BILL-1 (view all invoices) | `GET /api/billing/invoices` | `invoices` JOIN `patients`, `appointments` |
| BILL-2 (create invoice) | `POST /api/billing/invoices` | `invoices` |
| BILL-3 (edit invoice) | `PATCH /api/billing/invoices/{id}` | `invoices` |
| BILL-4 (delete pending only) | `DELETE /api/billing/invoices/{id}` | `invoices.status` check |
| BILL-5 (read patient demographics) | `GET /api/billing/patients` | `patients` JOIN `users` (limited fields) |
| BILL-6 (read appointments for billing) | `GET /api/billing/appointments` | `appointments` JOIN `doctors`, `departments` (limited fields) |
| BILL-7 (view notification log) | `GET /api/billing/notifications` | `email_notifications` |
| BILL-8 (manual resend) | `POST /api/billing/invoices/{id}/resend-notification` | `email_notifications` |
| NOTIFY-1..3 (file-sink notifications) | `PATCH /api/billing/invoices/{id}` (side-effect) | `email_notifications` |
| Section 8.2.2 (pagination) | All 13 list endpoints; see Conventions | No schema change |
| Section 8.2.4 (JWT claims) | `POST /api/auth/login` (token minting) | No schema change |
| Section 8.4.2 (has_insurance_claim) | All invoice endpoints | `invoices.has_insurance_claim` |
| Section 8.4.3 (dashboard tiles) | `GET /api/billing/dashboard` | Aggregate queries on `invoices` |
