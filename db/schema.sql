-- Green Valley Hospital — SQLite DDL
-- Status: Draft v1.1 (updated for Section 8: BillingSpecialist role, performance indexes, email notifications)
-- Owner: Solution Architect stage
-- Consumers: Backend developer agent
-- Companion docs: docs/architecture.md (ER diagram + rationale), docs/api-spec.md (endpoint contract)
--
-- Conventions:
--   - snake_case for every table/column name (matches JSON field names in docs/api-spec.md).
--   - Every table has a single-column integer primary key.
--   - Booleans stored as INTEGER (0/1), enforced via CHECK.
--   - Timestamps stored as TEXT in ISO-8601 ("YYYY-MM-DDTHH:MM:SS"), default CURRENT_TIMESTAMP.
--   - Enums modeled as TEXT + CHECK constraint (SQLite has no native enum type).
--   - Money stored as INTEGER cents to avoid floating-point rounding (total_amount_cents).

PRAGMA foreign_keys = ON;

-- ============================================================
-- 1. USERS & ROLE PROFILES
-- ============================================================

CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    -- Section 8.1.2 (BILL-ROLE-1): BillingSpecialist added as sixth role.
    role            TEXT NOT NULL CHECK (role IN ('Admin', 'Doctor', 'Patient', 'Staff', 'Lab', 'BillingSpecialist')),
    full_name       TEXT NOT NULL,
    phone           TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_role ON users(role);

CREATE TABLE departments (
    department_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    description     TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

-- 1:1 with users where role = 'Patient'
CREATE TABLE patients (
    patient_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                     INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    date_of_birth               TEXT NOT NULL,
    gender                      TEXT,
    address                     TEXT,
    emergency_contact_name      TEXT,
    emergency_contact_phone     TEXT
);

-- 1:1 with users where role = 'Doctor'
CREATE TABLE doctors (
    doctor_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    department_id       INTEGER NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT,
    specialty           TEXT NOT NULL,
    qualifications      TEXT,
    bio                 TEXT,
    years_experience    INTEGER NOT NULL DEFAULT 0 CHECK (years_experience >= 0),
    consultation_hours  TEXT,
    -- Nullable filesystem path to the doctor's public profile photo.
    -- Set via Admin/Doctor profile edit (plain text path input).
    -- Served as a static asset by the frontend dev server / Vite build (VI-IMG-4).
    profile_photo_path  TEXT
);

CREATE INDEX idx_doctors_department ON doctors(department_id);

-- 1:1 with users where role = 'Staff'
CREATE TABLE staff_members (
    staff_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    department_id   INTEGER REFERENCES departments(department_id) ON DELETE SET NULL
);

-- 1:1 with users where role = 'Lab'
CREATE TABLE lab_technicians (
    lab_user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE
);

-- 1:1 with users where role = 'BillingSpecialist'
-- Section 8.1.2 (BILL-ROLE-3): BillingSpecialist profile entity.
-- employee_id is an optional internal HR reference (nullable).
CREATE TABLE billing_specialists (
    billing_specialist_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                 INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    employee_id             TEXT,
    created_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. CLINICAL WORKFLOW
-- ============================================================

CREATE TABLE appointments (
    appointment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id          INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id           INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    scheduled_at         TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'Scheduled'
                            CHECK (status IN ('Scheduled', 'Completed', 'Cancelled', 'NoShow')),
    reason               TEXT,
    created_by_user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_scheduled_at ON appointments(scheduled_at); -- Section 8.2.1
CREATE INDEX idx_appointments_created_at ON appointments(created_at);     -- Section 8.2.1
-- Prevents double-booking the same doctor at the same instant (AC-APT-2).
CREATE UNIQUE INDEX uq_appointments_doctor_slot
    ON appointments(doctor_id, scheduled_at)
    WHERE status IN ('Scheduled', 'Completed');

CREATE TABLE visit_notes (
    record_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id  INTEGER NOT NULL REFERENCES appointments(appointment_id) ON DELETE CASCADE,
    patient_id      INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id       INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    diagnosis       TEXT,
    notes           TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_visit_notes_patient ON visit_notes(patient_id);
CREATE INDEX idx_visit_notes_doctor ON visit_notes(doctor_id);
CREATE INDEX idx_visit_notes_appointment ON visit_notes(appointment_id);
CREATE INDEX idx_visit_notes_created_at ON visit_notes(created_at); -- Section 8.2.1

CREATE TABLE prescriptions (
    prescription_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id      INTEGER NOT NULL REFERENCES appointments(appointment_id) ON DELETE CASCADE,
    patient_id          INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id           INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    -- JSON array of {name, dosage, frequency, duration} objects.
    medicines_json       TEXT NOT NULL,
    instructions         TEXT,
    created_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prescriptions_patient ON prescriptions(patient_id);
CREATE INDEX idx_prescriptions_doctor ON prescriptions(doctor_id);
CREATE INDEX idx_prescriptions_appointment ON prescriptions(appointment_id);
CREATE INDEX idx_prescriptions_created_at ON prescriptions(created_at); -- Section 8.2.1

CREATE TABLE lab_orders (
    order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id       INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    lab_user_id     INTEGER REFERENCES lab_technicians(lab_user_id) ON DELETE SET NULL,
    test_type       TEXT NOT NULL CHECK (test_type IN ('Lab', 'XRay', 'Scan')),
    test_subtype    TEXT,
    status          TEXT NOT NULL DEFAULT 'Pending'
                        CHECK (status IN ('Pending', 'InProgress', 'Completed')),
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lab_orders_patient ON lab_orders(patient_id);
CREATE INDEX idx_lab_orders_doctor ON lab_orders(doctor_id);
CREATE INDEX idx_lab_orders_lab_user ON lab_orders(lab_user_id);
CREATE INDEX idx_lab_orders_status ON lab_orders(status);
CREATE INDEX idx_lab_orders_created_at ON lab_orders(created_at); -- Section 8.2.1

-- LAB-4 / AC-LAB-3: finalized results are immutable; a correction inserts a new
-- row with an incremented `version` for the same order_id rather than an UPDATE.
CREATE TABLE lab_results (
    result_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id                 INTEGER NOT NULL REFERENCES lab_orders(order_id) ON DELETE CASCADE,
    result_data               TEXT NOT NULL,
    file_attachment_path      TEXT,
    version                   INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    recorded_by_user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    is_finalized               INTEGER NOT NULL DEFAULT 0 CHECK (is_finalized IN (0, 1)),
    finalized_at               TEXT,
    created_at                 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (order_id, version)
);

CREATE INDEX idx_lab_results_order ON lab_results(order_id);
CREATE INDEX idx_lab_results_created_at ON lab_results(created_at); -- Section 8.2.1

-- ============================================================
-- 3. BILLING
-- ============================================================

CREATE TABLE invoices (
    invoice_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id            INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    appointment_id         INTEGER REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    -- JSON array of {description, amount_cents} objects.
    line_items_json         TEXT NOT NULL,
    total_amount_cents       INTEGER NOT NULL CHECK (total_amount_cents >= 0),
    status                   TEXT NOT NULL DEFAULT 'Pending'
                                CHECK (status IN ('Pending', 'Paid', 'Waived')),
    -- Section 8.4.2: boolean flag for insurance claim filing. 0 = no claim, 1 = claim filed.
    has_insurance_claim      INTEGER NOT NULL DEFAULT 0
                                CHECK (has_insurance_claim IN (0, 1)),
    created_by_user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at               TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes: patient_id and status existed in v1.0; created_at and has_insurance_claim are new (Section 8.2.1).
CREATE INDEX idx_invoices_patient ON invoices(patient_id);
CREATE INDEX idx_invoices_appointment ON invoices(appointment_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_created_at ON invoices(created_at);                  -- Section 8.2.1
CREATE INDEX idx_invoices_has_insurance_claim ON invoices(has_insurance_claim); -- Section 8.2.1

-- ============================================================
-- 4. PUBLIC SITE CONTENT
-- ============================================================

CREATE TABLE blog_articles (
    article_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title                  TEXT NOT NULL,
    slug                    TEXT NOT NULL UNIQUE,
    summary                 TEXT,
    body                     TEXT NOT NULL,
    author_user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status                   TEXT NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Published')),
    cover_image_path         TEXT,
    published_at             TEXT,
    created_at               TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_blog_articles_status ON blog_articles(status);
CREATE INDEX idx_blog_articles_slug ON blog_articles(slug);
CREATE INDEX idx_blog_articles_published_at ON blog_articles(published_at); -- Section 8.2.1

CREATE TABLE contact_messages (
    message_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL,
    phone           TEXT,
    subject         TEXT NOT NULL,
    message         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'New' CHECK (status IN ('New', 'Reviewed', 'Resolved')),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contact_messages_status ON contact_messages(status);
CREATE INDEX idx_contact_messages_created_at ON contact_messages(created_at); -- Section 8.2.1

-- ============================================================
-- 5. AUDIT
-- ============================================================

-- ADM-9: audits account creation/deactivation and role changes only
-- (not general clinical reads/writes — see requirements.md Out of Scope).
CREATE TABLE audit_log_entries (
    log_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    action                TEXT NOT NULL,
    target_user_id        INTEGER REFERENCES users(id) ON DELETE SET NULL,
    details               TEXT,
    created_at             TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_actor ON audit_log_entries(actor_user_id);
CREATE INDEX idx_audit_log_target ON audit_log_entries(target_user_id);

-- ============================================================
-- 6. EMAIL NOTIFICATIONS  (Section 8.3 — file-sink delivery)
-- ============================================================

-- Records every invoice-status-change notification and manual resend attempt.
-- Delivery is a local file written to uploads/email_log/; this row is the audit record.
-- status = 'Sent'   → file was written successfully.
-- status = 'Failed' → file write failed; invoice change still committed (NOTIFY-3).
-- status = 'Queued' → reserved for future async delivery; not used in this build.
CREATE TABLE email_notifications (
    notification_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    subject             TEXT NOT NULL,
    body_html           TEXT NOT NULL,
    sent_at             TEXT NOT NULL,
    trigger_event       TEXT NOT NULL
                            CHECK (trigger_event IN ('invoice_status_change', 'manual_resend')),
    related_invoice_id  INTEGER REFERENCES invoices(invoice_id) ON DELETE SET NULL,
    status              TEXT NOT NULL
                            CHECK (status IN ('Queued', 'Sent', 'Failed'))
);

-- Section 8.2.1: indexes on recipient_user_id and sent_at for paginated notification log.
CREATE INDEX idx_email_notifications_recipient ON email_notifications(recipient_user_id);
CREATE INDEX idx_email_notifications_sent_at   ON email_notifications(sent_at);
