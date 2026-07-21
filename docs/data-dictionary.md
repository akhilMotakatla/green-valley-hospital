# Green Valley Hospital — Data Dictionary

All entities are defined in `src/backend/app/models.py` (SQLAlchemy ORM) and `db/schema.sql` (canonical DDL). SQLite is the database engine. All timestamps are stored as ISO 8601 strings in UTC.

---

## users

Central identity table. Every person in the system has exactly one row here.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement | Surrogate key |
| `email` | TEXT | NOT NULL, UNIQUE | Login credential; used as username |
| `password_hash` | TEXT | NOT NULL | bcrypt hash of the user's password; never stored plaintext |
| `role` | TEXT | NOT NULL, CHECK | One of: `Admin`, `Doctor`, `Patient`, `Staff`, `Lab` |
| `full_name` | TEXT | NOT NULL | Display name |
| `phone` | TEXT | nullable | Contact phone number |
| `is_active` | INTEGER | NOT NULL, default 1 | `1` = active (can log in); `0` = deactivated |
| `created_at` | TEXT | NOT NULL | ISO 8601 UTC timestamp of account creation |

**Indexes**: `idx_users_role` on `role`.

---

## departments

Hospital departments and specialties.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `department_id` | INTEGER | PK, autoincrement | Surrogate key |
| `name` | TEXT | NOT NULL, UNIQUE | Department display name (e.g., "Cardiology") |
| `description` | TEXT | nullable | Optional longer description |
| `is_active` | INTEGER | NOT NULL, default 1 | `1` = visible on public site; `0` = hidden/deactivated |

---

## patients

Extended profile for users with role `Patient`. One-to-one with `users`.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `patient_id` | INTEGER | PK, autoincrement | Surrogate patient key |
| `user_id` | INTEGER | FK → users.id, UNIQUE | Links to the patient's user account |
| `date_of_birth` | TEXT | NOT NULL | ISO 8601 date string (YYYY-MM-DD) |
| `gender` | TEXT | nullable | Free-text or enum value |
| `address` | TEXT | nullable | Mailing/home address |
| `emergency_contact_name` | TEXT | nullable | Name of emergency contact person |
| `emergency_contact_phone` | TEXT | nullable | Phone of emergency contact person |

---

## doctors

Extended profile for users with role `Doctor`. One-to-one with `users`.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `doctor_id` | INTEGER | PK, autoincrement | Surrogate doctor key |
| `user_id` | INTEGER | FK → users.id, UNIQUE | Links to the doctor's user account |
| `department_id` | INTEGER | FK → departments.department_id | The department this doctor belongs to |
| `specialty` | TEXT | NOT NULL | Clinical specialty (e.g., "Interventional Cardiology") |
| `qualifications` | TEXT | nullable | Degrees, certifications (free text) |
| `bio` | TEXT | nullable | Public-facing biography |
| `years_experience` | INTEGER | NOT NULL, default 0 | Years of clinical practice |
| `consultation_hours` | TEXT | nullable | Schedule string (e.g., "Mon–Fri 9am–5pm") |
| `profile_photo_path` | TEXT | nullable | Relative path to photo served from `public/images/` (e.g., `/images/doctors/dr-smith.jpg`) |

**Indexes**: `idx_doctors_department` on `department_id`.

---

## staff_members

Extended profile for users with role `Staff` (nurses and receptionists).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `staff_id` | INTEGER | PK, autoincrement | Surrogate staff key |
| `user_id` | INTEGER | FK → users.id, UNIQUE | Links to the staff user account |
| `department_id` | INTEGER | FK → departments.department_id, nullable | Optional department assignment |

---

## lab_technicians

Extended profile for users with role `Lab`.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `lab_user_id` | INTEGER | PK, autoincrement | Surrogate lab tech key |
| `user_id` | INTEGER | FK → users.id, UNIQUE | Links to the lab user account |

---

## appointments

Core scheduling entity. Links a patient to a doctor at a specific date/time.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `appointment_id` | INTEGER | PK, autoincrement | Surrogate key |
| `patient_id` | INTEGER | FK → patients.patient_id | The patient attending |
| `doctor_id` | INTEGER | FK → doctors.doctor_id | The assigned doctor |
| `scheduled_at` | TEXT | NOT NULL | ISO 8601 UTC datetime of the appointment |
| `status` | TEXT | NOT NULL, CHECK | One of: `Scheduled`, `Completed`, `Cancelled`, `NoShow` |
| `reason` | TEXT | nullable | Patient-entered reason for the visit |
| `created_by_user_id` | INTEGER | FK → users.id | The user who booked (patient self-booked or staff) |
| `created_at` | TEXT | NOT NULL | Row creation timestamp |

**Unique constraint**: `(doctor_id, scheduled_at)` for rows where status is `Scheduled` or `Completed` — prevents double-booking.

**Indexes**: `patient_id`, `doctor_id`, `status`.

---

## visit_notes

Clinical notes written by a doctor after an appointment.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `record_id` | INTEGER | PK, autoincrement | Surrogate key |
| `appointment_id` | INTEGER | FK → appointments.appointment_id | The appointment this note belongs to |
| `patient_id` | INTEGER | FK → patients.patient_id | Denormalized for efficient patient record queries |
| `doctor_id` | INTEGER | FK → doctors.doctor_id | Authoring doctor |
| `diagnosis` | TEXT | nullable | Clinical diagnosis text |
| `notes` | TEXT | NOT NULL | Full consultation / visit notes |
| `created_at` | TEXT | NOT NULL | Row creation timestamp |

**Indexes**: `patient_id`, `doctor_id`, `appointment_id`.

---

## prescriptions

Medication prescriptions created by a doctor for a patient.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `prescription_id` | INTEGER | PK, autoincrement | Surrogate key |
| `appointment_id` | INTEGER | FK → appointments.appointment_id | Associated appointment |
| `patient_id` | INTEGER | FK → patients.patient_id | Owning patient |
| `doctor_id` | INTEGER | FK → doctors.doctor_id | Prescribing doctor |
| `medicines_json` | TEXT | NOT NULL | JSON array of `{name, dosage, frequency, duration}` objects |
| `instructions` | TEXT | nullable | Additional instructions (e.g., "take with food") |
| `created_at` | TEXT | NOT NULL | Row creation timestamp |

---

## lab_orders

Requests for lab tests, X-rays, or scans, created by a doctor.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `order_id` | INTEGER | PK, autoincrement | Surrogate key |
| `patient_id` | INTEGER | FK → patients.patient_id | Patient to be tested |
| `doctor_id` | INTEGER | FK → doctors.doctor_id | Ordering doctor |
| `lab_user_id` | INTEGER | FK → lab_technicians.lab_user_id, nullable | Lab tech assigned to process the order |
| `test_type` | TEXT | NOT NULL, CHECK | One of: `Lab`, `XRay`, `Scan` |
| `test_subtype` | TEXT | nullable | Specific test (e.g., "Complete Blood Count", "MRI Brain") |
| `status` | TEXT | NOT NULL, CHECK | One of: `Pending`, `InProgress`, `Completed` |
| `notes` | TEXT | nullable | Ordering doctor's instructions |
| `created_at` | TEXT | NOT NULL | Row creation timestamp |

**Indexes**: `patient_id`, `doctor_id`, `lab_user_id`, `status`.

---

## lab_results

Results uploaded by the Lab role for a specific lab order. Supports versioning for amendments.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `result_id` | INTEGER | PK, autoincrement | Surrogate key |
| `order_id` | INTEGER | FK → lab_orders.order_id | The order this result belongs to |
| `result_data` | TEXT | NOT NULL | Result text or values |
| `file_attachment_path` | TEXT | nullable | Path to an uploaded attachment (stored in `uploads/`) |
| `version` | INTEGER | NOT NULL, default 1 | Version number; increments on amendment |
| `recorded_by_user_id` | INTEGER | FK → users.id | Lab user who entered the result |
| `is_finalized` | INTEGER | NOT NULL, default 0 | `1` = finalized; editing creates a new version instead |
| `finalized_at` | TEXT | nullable | Timestamp when result was finalized |
| `created_at` | TEXT | NOT NULL | Row creation timestamp |

**Unique constraint**: `(order_id, version)` — each order can have multiple versions but no two rows share the same order+version pair.

---

## invoices

Billing records linking a patient to charges for a visit.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `invoice_id` | INTEGER | PK, autoincrement | Surrogate key |
| `patient_id` | INTEGER | FK → patients.patient_id | Billed patient |
| `appointment_id` | INTEGER | FK → appointments.appointment_id, nullable | Associated appointment if applicable |
| `line_items_json` | TEXT | NOT NULL | JSON array of `{description, amount_cents}` objects |
| `total_amount_cents` | INTEGER | NOT NULL | Total in cents (avoids floating-point errors) |
| `status` | TEXT | NOT NULL, CHECK | One of: `Pending`, `Paid`, `Waived` |
| `created_by_user_id` | INTEGER | FK → users.id | Staff or Admin who created the invoice |
| `created_at` | TEXT | NOT NULL | Row creation timestamp |

---

## blog_articles

Health articles published by Admin on the public blog.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `article_id` | INTEGER | PK, autoincrement | Surrogate key |
| `title` | TEXT | NOT NULL | Article headline |
| `slug` | TEXT | NOT NULL, UNIQUE | URL-safe identifier (e.g., `understanding-hypertension`) |
| `summary` | TEXT | nullable | Short excerpt shown on the blog list page |
| `body` | TEXT | NOT NULL | Full article content (plain text or markdown) |
| `author_user_id` | INTEGER | FK → users.id | Admin author |
| `status` | TEXT | NOT NULL, CHECK | One of: `Draft`, `Published` |
| `cover_image_path` | TEXT | nullable | Relative path to cover image in `public/images/` |
| `published_at` | TEXT | nullable | Timestamp set when status changes to Published |
| `created_at` | TEXT | NOT NULL | Row creation timestamp |

**Indexes**: `status`, `slug`.

---

## contact_messages

Submissions from the public contact form.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `message_id` | INTEGER | PK, autoincrement | Surrogate key |
| `name` | TEXT | NOT NULL | Submitter's name |
| `email` | TEXT | NOT NULL | Submitter's email |
| `phone` | TEXT | nullable | Optional phone number |
| `subject` | TEXT | NOT NULL | Message subject |
| `message` | TEXT | NOT NULL | Full message body |
| `status` | TEXT | NOT NULL, CHECK | One of: `New`, `Reviewed`, `Resolved` |
| `created_at` | TEXT | NOT NULL | Submission timestamp |

---

## audit_log_entries

Immutable record of account management actions for compliance (ADM-9).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `log_id` | INTEGER | PK, autoincrement | Surrogate key |
| `actor_user_id` | INTEGER | FK → users.id | The user who performed the action |
| `action` | TEXT | NOT NULL | Short action label (e.g., `create_user`, `deactivate_user`, `change_role`) |
| `target_user_id` | INTEGER | FK → users.id, nullable | The user the action was performed on (if applicable) |
| `details` | TEXT | nullable | JSON or free-text with additional context |
| `created_at` | TEXT | NOT NULL | Timestamp of the event |

**Indexes**: `actor_user_id`, `target_user_id`.

---

## vitals

Patient vitals recorded by Staff before a doctor consultation (STF-4).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `vitals_id` | INTEGER | PK, autoincrement | Surrogate key |
| `patient_id` | INTEGER | FK → patients.patient_id | Patient measured |
| `recorded_by_user_id` | INTEGER | FK → users.id | Staff member who took the readings |
| `recorded_for_appointment_id` | INTEGER | FK → appointments.appointment_id, nullable | Associated appointment |
| `height_cm` | REAL | nullable | Height in centimetres |
| `weight_kg` | REAL | nullable | Weight in kilograms |
| `blood_pressure` | TEXT | nullable | Free text (e.g., "120/80 mmHg") |
| `temperature_c` | REAL | nullable | Temperature in Celsius |
| `pulse_bpm` | INTEGER | nullable | Pulse in beats per minute |
| `created_at` | TEXT | NOT NULL | Recording timestamp |

---

## site_content

Key-value store for Admin-editable home/about page copy. Persists marketing text across restarts.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `key` | TEXT | PK | Identifies the content block (e.g., `home.tagline`, `about.mission`) |
| `value_json` | TEXT | NOT NULL | JSON-encoded content value |
| `updated_at` | TEXT | NOT NULL | Timestamp of last edit |

---

## Entity Relationship Summary

```
users ──< patients ──< appointments >── doctors >── departments
                  ──< visit_notes
                  ──< prescriptions
                  ──< lab_orders >── lab_results
                  ──< invoices
                  ──< vitals

users ──< doctors (1:1)
users ──< staff_members (1:1)
users ──< lab_technicians (1:1)

blog_articles >── users (author)
contact_messages (standalone)
audit_log_entries >── users (actor + target)
site_content (standalone key-value)
```
