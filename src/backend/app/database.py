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
