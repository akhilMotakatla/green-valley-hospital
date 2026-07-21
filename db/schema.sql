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
    -- Batch 2 (OI-7): set server-side (UTC) when status changes to 'Paid'.
    -- Used for accurate revenue analytics (GET /admin/analytics/revenue collected series).
    paid_at                  TEXT,
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

-- ============================================================
-- BATCH 2 (2026-07-20): REQ-01 through REQ-12
-- See docs/technical-design.md §4.1 for full rationale.
-- ============================================================

-- OI-7: paid_at column added inline to invoices CREATE TABLE above.
-- Index is defined here (after the invoices block) for the batch 2 schema section clarity.
CREATE INDEX idx_invoices_paid_at ON invoices(paid_at);

-- ============================================================
-- 7. DOCTOR AVAILABILITY (REQ-01)
-- ============================================================

-- Weekly recurring schedule: one row per (doctor, day-of-week, start_time) window.
-- day_of_week: 0=Monday, 6=Sunday.
-- Multiple windows per day allowed (e.g. 9am-12pm and 2pm-5pm).
CREATE TABLE doctor_availability_schedules (
    schedule_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id       INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    day_of_week     INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time      TEXT NOT NULL,   -- HH:MM 24-hour format
    end_time        TEXT NOT NULL,   -- HH:MM 24-hour format
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (doctor_id, day_of_week, start_time)
);

CREATE INDEX idx_avail_schedules_doctor ON doctor_availability_schedules(doctor_id);

-- Slot duration configuration: one row per doctor.
-- Default slot_duration_minutes = 30. Created on first PUT by doctor or admin.
CREATE TABLE doctor_slot_configs (
    config_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id               INTEGER NOT NULL UNIQUE REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    slot_duration_minutes   INTEGER NOT NULL DEFAULT 30
                                CHECK (slot_duration_minutes IN (10, 15, 20, 30, 45, 60)),
    updated_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- One-off date blocks overriding the weekly schedule.
-- Full-day block: start_time IS NULL AND end_time IS NULL.
-- Partial block: both start_time and end_time must be non-null (enforced at app layer).
CREATE TABLE doctor_availability_blocks (
    block_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id   INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    block_date  TEXT NOT NULL,   -- YYYY-MM-DD
    start_time  TEXT,            -- HH:MM or NULL
    end_time    TEXT,            -- HH:MM or NULL; must match nullability of start_time
    reason      TEXT,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_avail_blocks_doctor ON doctor_availability_blocks(doctor_id);
CREATE INDEX idx_avail_blocks_date   ON doctor_availability_blocks(block_date);

-- ============================================================
-- 8. IN-APP NOTIFICATIONS (REQ-02)
-- ============================================================

-- Per-user in-app notification inbox.
-- Separate from email_notifications (Section 6) which handles billing file-sink only.
CREATE TABLE notifications (
    notification_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type          TEXT NOT NULL,
    title               TEXT NOT NULL CHECK (LENGTH(title) <= 120),
    body                TEXT NOT NULL CHECK (LENGTH(body) <= 500),
    related_entity_type TEXT,    -- nullable: 'appointment','invoice','lab_result','referral','survey','waitlist_entry'
    related_entity_id   INTEGER, -- nullable: FK to related entity (app-layer enforced, not DDL)
    is_read             INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0, 1)),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- (recipient_user_id, is_read) compound index: required for O(1) unread-count queries (NOTIFNFR-1).
CREATE INDEX idx_notifications_recipient_read ON notifications(recipient_user_id, is_read);
CREATE INDEX idx_notifications_created_at     ON notifications(created_at);

-- Deferred notification triggers (poll-on-login pattern; OI-2 decision).
-- Used for: appointment_reminder (24h before appointment), survey_available (24h after completion).
-- survey_id is a soft FK to satisfaction_surveys (defined below); DDL FK omitted
-- because satisfaction_surveys is defined after this table. Enforce at app layer.
CREATE TABLE notification_schedules (
    schedule_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id  INTEGER REFERENCES appointments(appointment_id) ON DELETE CASCADE,
    survey_id       INTEGER,  -- soft FK -> satisfaction_surveys.survey_id
    trigger_type    TEXT NOT NULL
                        CHECK (trigger_type IN ('appointment_reminder', 'survey_available')),
    trigger_at      TEXT NOT NULL,  -- ISO 8601 UTC timestamp
    is_fired        INTEGER NOT NULL DEFAULT 0 CHECK (is_fired IN (0, 1)),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Compound index for poll-on-login: unfired schedules at or before now.
CREATE INDEX idx_notif_schedules_poll ON notification_schedules(trigger_at, is_fired);

-- ============================================================
-- 9. INTAKE FORMS (REQ-03)
-- ============================================================

-- 1:1 with appointments. Created automatically (as empty/draft) when an appointment is booked.
-- submitted_at is NULL while in draft state; set on first full patient submission.
-- Read-only once appointment.status = 'Completed' (enforced at app layer).
CREATE TABLE intake_forms (
    intake_form_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id      INTEGER NOT NULL UNIQUE REFERENCES appointments(appointment_id) ON DELETE CASCADE,
    patient_id          INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    chief_complaint     TEXT,
    symptom_duration    TEXT,
    allergies           TEXT,
    current_medications TEXT,
    pain_scale          INTEGER CHECK (pain_scale BETWEEN 1 AND 10),
    additional_notes    TEXT,
    submitted_at        TEXT,   -- NULL = draft; ISO 8601 timestamp when first fully submitted
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_intake_forms_appointment ON intake_forms(appointment_id);
CREATE INDEX idx_intake_forms_patient     ON intake_forms(patient_id);

-- ============================================================
-- 10. VITALS (REQ-04 / STF-4 schema gap resolution — Section 9.14)
-- ============================================================

-- Resolves the STF-4 schema gap: vital signs recording by Staff was in scope
-- since Section 2.4 but had no backing table. appointment_id is nullable (vitals
-- may be taken outside a specific appointment context).
CREATE TABLE vitals (
    vital_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id              INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    appointment_id          INTEGER REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    recorded_by_user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    systolic_bp             INTEGER,      -- mmHg; 40-300; must be paired with diastolic_bp (app-layer)
    diastolic_bp            INTEGER,      -- mmHg; 40-300; must be paired with systolic_bp
    weight_kg               REAL,         -- kg; must be > 0 if provided
    pulse_bpm               INTEGER,      -- bpm; 20-300 if provided
    temperature_celsius     REAL,         -- °C; 30.0-45.0 if provided
    height_cm               REAL,         -- cm; must be > 0 if provided
    recorded_at             TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vitals_patient     ON vitals(patient_id);
CREATE INDEX idx_vitals_appointment ON vitals(appointment_id);
CREATE INDEX idx_vitals_recorded_at ON vitals(recorded_at);  -- for trend query ordering

-- ============================================================
-- 11. REFERRALS (REQ-05)
-- ============================================================

-- Inter-department referrals. Status lifecycle per REFFR-1:
-- Pending -> Accepted -> AppointmentBooked -> Completed
-- Pending -> Declined (terminal, per OI-5 architectural decision)
CREATE TABLE referrals (
    referral_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    referring_doctor_id     INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    receiving_department_id INTEGER NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT,
    receiving_doctor_id     INTEGER REFERENCES doctors(doctor_id) ON DELETE SET NULL,
    patient_id              INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    reason                  TEXT NOT NULL,
    urgency                 TEXT NOT NULL CHECK (urgency IN ('Routine', 'Urgent')),
    status                  TEXT NOT NULL DEFAULT 'Pending'
                                CHECK (status IN ('Pending', 'Accepted', 'Declined',
                                                  'AppointmentBooked', 'Completed')),
    receiving_doctor_note   TEXT,
    referred_appointment_id INTEGER REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    created_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_referrals_patient      ON referrals(patient_id);
CREATE INDEX idx_referrals_referring    ON referrals(referring_doctor_id);
CREATE INDEX idx_referrals_recv_dept    ON referrals(receiving_department_id);
CREATE INDEX idx_referrals_status       ON referrals(status);
-- Composite for FIFO queue: department + status + urgency (Urgent first) + time
CREATE INDEX idx_referrals_dept_queue   ON referrals(receiving_department_id, status, urgency, created_at);

-- ============================================================
-- 12. SYMPTOM TAGS (REQ-07)
-- ============================================================

-- Department-level symptom/condition tags for public search enrichment.
-- Case-insensitive uniqueness per department enforced at application layer (SQLite
-- does not support functional indexes with LOWER() for UNIQUE constraints natively).
-- Admin can configure up to 50 tags per department (enforced at app layer).
CREATE TABLE department_symptom_tags (
    tag_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id   INTEGER NOT NULL REFERENCES departments(department_id) ON DELETE CASCADE,
    tag_text        TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_symptom_tags_department ON department_symptom_tags(department_id);
CREATE INDEX idx_symptom_tags_text       ON department_symptom_tags(tag_text);

-- ============================================================
-- 13. WAITLIST (REQ-09)
-- ============================================================

-- Per OI-12 documented assumption: waitlist is per-doctor-per-date.
-- preferred_date is NOT NULL (patient specifies a date when joining).
-- Uniqueness rule: one active ('Waiting' or 'Notified') entry per (patient_id, doctor_id, preferred_date).
-- Enforced at application layer (not DDL partial-index due to multi-value IN clause).
--
-- held_slot_time: set when a cancellation triggers this entry's 'Notified' status;
-- records which specific HH:MM slot is held for this patient. Used to exclude the
-- slot from the public slot-availability query (WLFR-4).
CREATE TABLE waitlist_entries (
    entry_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id              INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id               INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    preferred_date          TEXT NOT NULL,   -- YYYY-MM-DD
    status                  TEXT NOT NULL DEFAULT 'Waiting'
                                CHECK (status IN ('Waiting', 'Notified', 'Confirmed', 'Expired', 'Removed')),
    notified_at             TEXT,            -- ISO 8601; set when status -> Notified
    confirmation_deadline   TEXT,            -- ISO 8601; notified_at + confirmation_hours
    held_slot_time          TEXT,            -- HH:MM of the specific slot held for this patient
    removed_reason          TEXT,            -- set by Staff when manually removing a patient
    created_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- FIFO queue index: for a given doctor + date, find the first Waiting entry.
CREATE INDEX idx_waitlist_doctor_date_queue ON waitlist_entries(doctor_id, preferred_date, status, created_at);
CREATE INDEX idx_waitlist_patient           ON waitlist_entries(patient_id);

-- System-wide configuration key-value store.
-- Initial row: ('waitlist_confirmation_hours', '4') — inserted by seed script.
CREATE TABLE system_config (
    config_key      TEXT PRIMARY KEY,
    config_value    TEXT NOT NULL,
    updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 14. DISCHARGE SUMMARIES (REQ-10)
-- ============================================================

-- 1:1 with completed appointments. Immutable after creation (DSFR-8).
-- follow_up_appointment_id references a new Scheduled appointment created atomically
-- with the summary (OI-8 decision: atomic single transaction).
CREATE TABLE discharge_summaries (
    summary_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id              INTEGER NOT NULL UNIQUE REFERENCES appointments(appointment_id) ON DELETE RESTRICT,
    patient_id                  INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id                   INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    key_findings                TEXT NOT NULL,
    patient_instructions        TEXT,
    activity_restrictions       TEXT,
    medication_reminders        TEXT,    -- free text; not linked to prescriptions table
    follow_up_appointment_id    INTEGER REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    created_at                  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_discharge_patient ON discharge_summaries(patient_id);
CREATE INDEX idx_discharge_doctor  ON discharge_summaries(doctor_id);

-- ============================================================
-- 15. SATISFACTION SURVEYS (REQ-11)
-- ============================================================

-- 1:1 with completed appointments. Created when appointment transitions to Completed.
-- Never created for Cancelled or NoShow appointments (SURVFR-6).
-- trigger_after = completed_at + 24h; expires_at = trigger_after + 7 days.
-- notification_sent flag supports poll-on-login deferred notification (OI-2 / SURVFR-2).
CREATE TABLE satisfaction_surveys (
    survey_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id          INTEGER NOT NULL UNIQUE REFERENCES appointments(appointment_id) ON DELETE RESTRICT,
    patient_id              INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id               INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    trigger_after           TEXT NOT NULL,   -- ISO 8601: completed_at + 24h
    expires_at              TEXT NOT NULL,   -- ISO 8601: trigger_after + 7 days
    notification_sent       INTEGER NOT NULL DEFAULT 0 CHECK (notification_sent IN (0, 1)),
    submitted_at            TEXT,            -- NULL = pending; ISO 8601 when submitted
    doctor_star_rating      INTEGER CHECK (doctor_star_rating BETWEEN 1 AND 5),
    overall_star_rating     INTEGER CHECK (overall_star_rating BETWEEN 1 AND 5),
    comment                 TEXT CHECK (comment IS NULL OR LENGTH(comment) <= 1000),
    is_comment_removed      INTEGER NOT NULL DEFAULT 0 CHECK (is_comment_removed IN (0, 1))
);

CREATE INDEX idx_surveys_patient ON satisfaction_surveys(patient_id);
CREATE INDEX idx_surveys_doctor  ON satisfaction_surveys(doctor_id);
-- Poll-on-login compound index: pending, unnotified, matured surveys for a patient
CREATE INDEX idx_surveys_poll ON satisfaction_surveys(patient_id, notification_sent, submitted_at);

-- ============================================================
-- 16. CORPORATE HEALTH PACKAGES (REQ-12)
-- ============================================================

-- B2B health package tiers. Soft delete via is_active (deactivated packages
-- remain referenced by existing inquiries).
CREATE TABLE corporate_packages (
    package_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    TEXT NOT NULL,
    tier_order              INTEGER NOT NULL,
    description             TEXT NOT NULL,
    included_services_json  TEXT NOT NULL,   -- JSON array of service strings
    price_range_display     TEXT NOT NULL,   -- marketing copy, e.g. "$500-$800 per employee"
    is_active               INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_corp_packages_active ON corporate_packages(is_active, tier_order);

-- Corporate inquiry pipeline (CRM-lite).
-- Inquiries are never deleted; status advances through defined lifecycle.
CREATE TABLE corporate_inquiries (
    inquiry_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name        TEXT NOT NULL,
    contact_name        TEXT NOT NULL,
    email               TEXT NOT NULL,
    phone               TEXT,
    headcount           INTEGER CHECK (headcount > 0),
    package_id          INTEGER REFERENCES corporate_packages(package_id) ON DELETE SET NULL,
    preferred_schedule  TEXT,
    status              TEXT NOT NULL DEFAULT 'New'
                            CHECK (status IN ('New', 'Contacted', 'ProposalSent', 'ClosedWon', 'ClosedLost')),
    notes               TEXT,
    deal_value_cents    INTEGER CHECK (deal_value_cents >= 0),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_corp_inquiries_status     ON corporate_inquiries(status);
CREATE INDEX idx_corp_inquiries_created_at ON corporate_inquiries(created_at);
