from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL, DB_DIR

DB_DIR.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create the SQLite file and all tables from the models on first run
    (schema mirrors db/schema.sql).

    Also applies any additive ALTER TABLE / CREATE INDEX migrations for
    columns and indexes added after the initial schema was deployed, so
    existing DB files keep working without a full re-creation.

    v1.1 additions: doctors.profile_photo_path
    v1.2 additions: invoices.has_insurance_claim, billing_specialists table,
                    email_notifications table, 12 new performance indexes
    """
    # Import models so they're registered on Base.metadata before create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    if not DATABASE_URL.startswith("sqlite"):
        return

    import sqlalchemy as _sa

    with engine.connect() as conn:
        # ---- v1.1: doctors.profile_photo_path --------------------------------
        result = conn.execute(_sa.text("PRAGMA table_info(doctors)"))
        existing_cols = {row[1] for row in result.fetchall()}
        if "profile_photo_path" not in existing_cols:
            conn.execute(_sa.text("ALTER TABLE doctors ADD COLUMN profile_photo_path TEXT"))
            conn.commit()

        # ---- v1.2: invoices.has_insurance_claim ------------------------------
        result = conn.execute(_sa.text("PRAGMA table_info(invoices)"))
        existing_cols = {row[1] for row in result.fetchall()}
        if "has_insurance_claim" not in existing_cols:
            conn.execute(
                _sa.text(
                    "ALTER TABLE invoices ADD COLUMN has_insurance_claim INTEGER NOT NULL DEFAULT 0"
                )
            )
            conn.commit()

        # ---- v1.2: users.role CHECK constraint — add BillingSpecialist ---------
        # SQLite does not support ALTER TABLE ... MODIFY COLUMN, so we must
        # detect the old constraint and recreate the table when BillingSpecialist
        # is absent.  Foreign-keys are disabled for the duration of the DDL
        # (the pragma only affects the current connection, not the session).
        result = conn.execute(_sa.text("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"))
        users_ddl = (result.fetchone() or ("",))[0] or ""
        if "'BillingSpecialist'" not in users_ddl:
            conn.execute(_sa.text("PRAGMA foreign_keys = OFF"))
            conn.execute(_sa.text("""
                CREATE TABLE users_new (
                    id INTEGER NOT NULL,
                    email VARCHAR NOT NULL,
                    password_hash VARCHAR NOT NULL,
                    role VARCHAR NOT NULL,
                    full_name VARCHAR NOT NULL,
                    phone VARCHAR,
                    is_active INTEGER NOT NULL,
                    created_at VARCHAR NOT NULL,
                    PRIMARY KEY (id),
                    CONSTRAINT ck_users_role CHECK (role IN ('Admin','Doctor','Patient','Staff','Lab','BillingSpecialist')),
                    CONSTRAINT ck_users_is_active CHECK (is_active IN (0,1)),
                    UNIQUE (email)
                )
            """))
            conn.execute(_sa.text("INSERT INTO users_new SELECT * FROM users"))
            conn.execute(_sa.text("DROP TABLE users"))
            conn.execute(_sa.text("ALTER TABLE users_new RENAME TO users"))
            conn.execute(_sa.text("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)"))
            conn.execute(_sa.text("PRAGMA foreign_keys = ON"))
            conn.commit()

        # ---- v1.2: 12 new performance indexes --------------------------------
        # CREATE INDEX IF NOT EXISTS is idempotent — safe to run every startup.
        new_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_invoices_created_at ON invoices(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_has_insurance_claim ON invoices(has_insurance_claim)",
            "CREATE INDEX IF NOT EXISTS idx_appointments_scheduled_at ON appointments(scheduled_at)",
            "CREATE INDEX IF NOT EXISTS idx_appointments_created_at ON appointments(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_visit_notes_created_at ON visit_notes(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_prescriptions_created_at ON prescriptions(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_lab_orders_created_at ON lab_orders(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_lab_results_created_at ON lab_results(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_blog_articles_published_at ON blog_articles(published_at)",
            "CREATE INDEX IF NOT EXISTS idx_contact_messages_created_at ON contact_messages(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_email_notifications_recipient ON email_notifications(recipient_user_id)",
            "CREATE INDEX IF NOT EXISTS idx_email_notifications_sent_at ON email_notifications(sent_at)",
        ]
        for ddl in new_indexes:
            conn.execute(_sa.text(ddl))
        conn.commit()

        # ---- Batch 2 (2026-07-20): invoices.paid_at (OI-7) ------------------
        result = conn.execute(_sa.text("PRAGMA table_info(invoices)"))
        existing_cols = {row[1] for row in result.fetchall()}
        if "paid_at" not in existing_cols:
            conn.execute(_sa.text("ALTER TABLE invoices ADD COLUMN paid_at TEXT"))
            conn.execute(_sa.text(
                "CREATE INDEX IF NOT EXISTS idx_invoices_paid_at ON invoices(paid_at)"
            ))
            conn.commit()

        # ---- Batch 2: vitals table schema upgrade ----------------------------
        # The pre-Batch-2 Vitals model used different column names (vitals_id PK,
        # blood_pressure TEXT, temperature_c). The Batch 2 schema uses vital_id,
        # systolic_bp/diastolic_bp, temperature_celsius, recorded_at.
        # Detect the old schema by checking for vitals_id and recreate if needed.
        result = conn.execute(_sa.text("PRAGMA table_info(vitals)"))
        vitals_cols = {row[1] for row in result.fetchall()}
        if "vitals_id" in vitals_cols:
            # Old schema present — drop and recreate with Batch 2 schema.
            conn.execute(_sa.text("PRAGMA foreign_keys = OFF"))
            conn.execute(_sa.text("DROP TABLE IF EXISTS vitals"))
            conn.execute(_sa.text("""
                CREATE TABLE vitals (
                    vital_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
                    appointment_id INTEGER REFERENCES appointments(appointment_id) ON DELETE SET NULL,
                    recorded_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
                    systolic_bp INTEGER,
                    diastolic_bp INTEGER,
                    weight_kg REAL,
                    pulse_bpm INTEGER,
                    temperature_celsius REAL,
                    height_cm REAL,
                    recorded_at VARCHAR NOT NULL
                )
            """))
            conn.execute(_sa.text("PRAGMA foreign_keys = ON"))
            conn.commit()

        # ---- Batch 2: new indexes (idempotent) --------------------------------
        batch2_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_vitals_patient ON vitals(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_vitals_appointment ON vitals(appointment_id)",
            "CREATE INDEX IF NOT EXISTS idx_vitals_recorded_at ON vitals(recorded_at)",
            "CREATE INDEX IF NOT EXISTS idx_avail_schedules_doctor ON doctor_availability_schedules(doctor_id)",
            "CREATE INDEX IF NOT EXISTS idx_avail_blocks_doctor ON doctor_availability_blocks(doctor_id)",
            "CREATE INDEX IF NOT EXISTS idx_avail_blocks_date ON doctor_availability_blocks(block_date)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_recipient_read ON notifications(recipient_user_id, is_read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_notif_schedules_poll ON notification_schedules(trigger_at, is_fired)",
            "CREATE INDEX IF NOT EXISTS idx_intake_forms_appointment ON intake_forms(appointment_id)",
            "CREATE INDEX IF NOT EXISTS idx_intake_forms_patient ON intake_forms(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_waitlist_doctor_date_queue ON waitlist_entries(doctor_id, preferred_date, status, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_waitlist_patient ON waitlist_entries(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_discharge_patient ON discharge_summaries(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_discharge_doctor ON discharge_summaries(doctor_id)",
            "CREATE INDEX IF NOT EXISTS idx_surveys_patient ON satisfaction_surveys(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_surveys_doctor ON satisfaction_surveys(doctor_id)",
            "CREATE INDEX IF NOT EXISTS idx_surveys_poll ON satisfaction_surveys(patient_id, notification_sent, submitted_at)",
            "CREATE INDEX IF NOT EXISTS idx_corp_packages_active ON corporate_packages(is_active, tier_order)",
            "CREATE INDEX IF NOT EXISTS idx_corp_inquiries_status ON corporate_inquiries(status)",
            "CREATE INDEX IF NOT EXISTS idx_corp_inquiries_created_at ON corporate_inquiries(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_symptom_tags_department ON department_symptom_tags(department_id)",
            "CREATE INDEX IF NOT EXISTS idx_symptom_tags_text ON department_symptom_tags(tag_text)",
            "CREATE INDEX IF NOT EXISTS idx_referrals_patient ON referrals(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_referrals_referring ON referrals(referring_doctor_id)",
            "CREATE INDEX IF NOT EXISTS idx_referrals_recv_dept ON referrals(receiving_department_id)",
            "CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status)",
            "CREATE INDEX IF NOT EXISTS idx_referrals_dept_queue ON referrals(receiving_department_id, status, urgency, created_at)",
        ]
        for ddl in batch2_indexes:
            conn.execute(_sa.text(ddl))
        conn.commit()
