# Green Valley Hospital — Requirements Specification

Status: Draft v1.0
Owner: Requirements Analyst stage
Consumers: Architecture agent, Development agents, QA agent

Tech stack (already decided): Python (FastAPI) backend, React (Vite + TypeScript) frontend, SQLite database.

Roles (already decided): Admin, Doctor, Patient, Staff (Nurse + Receptionist combined), Lab.

---

## 1. Public Site (no login required)

The public site is served to anonymous visitors. No public page may display any authenticated user's personal data.

### 1.1 Home
- PUB-HOME-1: As a visitor, I can view a landing page summarizing the hospital (name, tagline, highlights, featured departments, call-to-action to book/login).
- PUB-HOME-2: As a visitor, I can navigate from the home page to About, Departments, Contact, Blog, and Login/Signup.

### 1.2 About
- PUB-ABOUT-1: As a visitor, I can view hospital background information (mission, history, facilities, accreditations — static content).

### 1.3 Departments / Specialties with Doctor Listings
- PUB-DEPT-1: As a visitor, I can view a list of departments/specialties (e.g., Cardiology, Pediatrics, Orthopedics).
- PUB-DEPT-2: As a visitor, I can select a department and view the list of doctors belonging to it, showing name, specialty, qualification, and years of experience.
- PUB-DEPT-3: As a visitor, I can view an individual doctor's public profile (bio, specialty, department, qualifications) without seeing their schedule internals or any patient data.

### 1.4 Contact
- PUB-CONTACT-1: As a visitor, I can view the hospital's physical address, general phone number, and a distinct emergency contact number.
- PUB-CONTACT-2: As a visitor, I can submit a contact form (name, email, phone [optional], subject, message) which is stored for Staff/Admin follow-up.
- PUB-CONTACT-3: As a visitor, after submitting the contact form, I see an on-screen confirmation. No real email/SMS is sent (see Out of Scope).

### 1.5 Health Blog / Articles
- PUB-BLOG-1: As a visitor, I can view a list of published health blog articles (title, summary, author, publish date, cover image optional).
- PUB-BLOG-2: As a visitor, I can open an individual article and read its full content.
- PUB-BLOG-3: Only articles with status "Published" are visible publicly; draft articles are never returned by public endpoints.

### 1.6 Login / Signup Entry Point
- PUB-AUTH-1: As a visitor, I can navigate to a Login page and authenticate with email + password.
- PUB-AUTH-2: As a visitor, I can navigate to a Signup page and self-register as a Patient only. Staff, Doctor, Lab, and Admin accounts are never self-registrable (see 3.1).
- PUB-AUTH-3: As a visitor, signup requires: full name, email (unique), password (meets policy — see 3.2), phone number, date of birth.

---

## 2. Role-by-Role User Stories

### 2.1 Admin
- ADM-1: As an Admin, I can create, edit, and deactivate user accounts for Doctor, Staff, Lab, and Admin roles (Patients self-register; Admin can also deactivate Patient accounts).
- ADM-2: As an Admin, I can assign/change a user's role and department.
- ADM-3: As an Admin, I can create, edit, and deactivate Department/specialty records.
- ADM-4: As an Admin, I can view all appointments across the hospital, filterable by department, doctor, date, and status.
- ADM-5: As an Admin, I can view all billing records/invoices across the hospital.
- ADM-6: As an Admin, I can create, edit, publish, unpublish, and delete blog/article content.
- ADM-7: As an Admin, I can view submitted Contact form messages and mark them as reviewed/resolved.
- ADM-8: As an Admin, I can view system-wide summary metrics (counts of patients, doctors, appointments today, pending lab orders) on a dashboard.
- ADM-9: As an Admin, I can view an audit trail of account creation/deactivation and role changes (who did what, when).
- ADM-10: An Admin cannot edit another user's clinical data (medical records, prescriptions, lab results) directly — only Doctors/Lab create clinical content; Admin's role is account/data administration, not clinical authorship.

### 2.2 Doctor
- DOC-1: As a Doctor, I can view my own profile and edit my public-facing bio, qualifications, and consultation hours.
- DOC-2: As a Doctor, I can view my list of upcoming and past appointments.
- DOC-3: As a Doctor, I can view the medical history (past visits, diagnoses, prescriptions, lab results) of a patient only if that patient has (or has had) an appointment assigned to me.
- DOC-4: As a Doctor, I can update the status of my appointment (Scheduled -> Completed / No-show / Cancelled) and add visit notes/diagnosis.
- DOC-5: As a Doctor, I can create a prescription (medicines, dosage, instructions, duration) tied to a specific patient and appointment.
- DOC-6: As a Doctor, I can create a lab/x-ray/scan order for a patient, specifying test type and notes for the Lab role.
- DOC-7: As a Doctor, I can view lab/x-ray/scan results once the Lab role has uploaded them, for my own patients only.
- DOC-8: As a Doctor, I cannot view or modify the medical records of a patient with whom I have no appointment relationship.
- DOC-9: As a Doctor, I cannot access Admin-only functions (user management, department management, billing administration).

### 2.3 Patient
- PAT-1: As a Patient, I can view and edit my own profile (contact info, emergency contact, date of birth) but not my own role or account status.
- PAT-2: As a Patient, I can search/browse doctors by department and book an appointment by selecting a doctor, date, and available time slot.
- PAT-3: As a Patient, I can view my own upcoming and past appointments, including status.
- PAT-4: As a Patient, I can cancel my own upcoming appointment before it occurs (subject to a minimum notice rule, e.g. no cancellation within 1 hour of start time — exact threshold defined by Architecture stage but must be enforced server-side).
- PAT-5: As a Patient, I can view my own medical records: visit notes/diagnoses, prescriptions, and lab/x-ray/scan results.
- PAT-6: As a Patient, I can view my own billing records/invoices and their payment status.
- PAT-7: As a Patient, I cannot view any other patient's appointments, medical records, prescriptions, lab results, or billing data under any circumstance.
- PAT-8: As a Patient, I cannot create prescriptions, lab orders, or clinical notes — these are read-only to me.

### 2.4 Staff (Nurse + Receptionist combined)
- STF-1: As Staff, I can create, view, and edit appointments on behalf of any patient (front-desk booking/rescheduling), including for walk-in/phone bookings.
- STF-2: As Staff, I can register a new Patient account on behalf of a walk-in patient (front-desk registration flow, distinct from public self-signup).
- STF-3: As Staff, I can view a patient's basic demographic and appointment info to assist with front-desk duties.
- STF-4: As Staff, I can record vital signs (height, weight, blood pressure, temperature, pulse) for a patient ahead of a doctor's consultation (nurse duty).
- STF-5: As Staff, I can view (but not edit) a patient's prescriptions and lab results to assist with coordination (e.g., confirming a test was ordered).
- STF-6: As Staff, I can view and update the status of Contact form submissions (mark reviewed/resolved) and respond to general inbound queries.
- STF-7: As Staff, I can view the department/doctor directory including doctor schedules to help book appointments.
- STF-8: As Staff, I cannot create prescriptions, diagnoses, or lab orders — these require a Doctor role. I cannot access Admin-only account/role management or billing administration.

### 2.5 Lab
- LAB-1: As Lab, I can view a queue of pending lab/x-ray/scan orders assigned to my role, filterable by test type and status.
- LAB-2: As Lab, I can update an order's status (Pending -> In Progress -> Completed).
- LAB-3: As Lab, I can upload/enter the result for a lab/x-ray/scan order (result text/values, optional file attachment, completion date).
- LAB-4: As Lab, once a result is marked Completed, I can no longer edit it without it being reflected as "amended" (immutability of finalized results — a correction creates a new versioned entry rather than silently overwriting).
- LAB-5: As Lab, I can view only the minimal patient info needed to perform/report a test (name, DOB, ordering doctor, test type) — not the patient's full medical history, prescriptions, or billing.
- LAB-6: As Lab, I cannot create appointments, prescriptions, or diagnoses, and cannot access Admin-only functions.

---

## 3. Cross-Cutting Requirements

### 3.1 Authentication
- AUTH-1: Authentication uses JWT bearer tokens. On successful login, the backend issues an access token containing at minimum: user id, role, and expiry.
- AUTH-2: Passwords are never stored in plaintext; they are hashed (e.g., bcrypt/argon2) server-side.
- AUTH-3: Public self-signup (PUB-AUTH-2) can only create accounts with role = Patient. Accounts with role Doctor, Staff, Lab, or Admin are created only by an existing Admin (ADM-1) or, for Patient walk-ins, by Staff (STF-2).
- AUTH-4: A JWT must be presented on every request to a role-protected endpoint; missing/expired/invalid tokens receive 401 Unauthorized.
- AUTH-5: Login failure (wrong credentials) returns a generic error that does not reveal whether the email exists.
- AUTH-6: Deactivated accounts (see ADM-1) cannot log in even with correct credentials; login returns 403 Forbidden with an "account inactive" reason.

### 3.2 Password Policy
- SEC-1: Minimum 8 characters, at least one letter and one number. Exact complexity rules are enforced server-side and mirrored in frontend validation.

### 3.3 Authorization Rules (role-based access control)
General principle: every authenticated endpoint enforces both (a) role membership and (b) row-level ownership/relationship checks. Role alone is never sufficient for clinical or personal data.

| Resource | Admin | Doctor | Patient | Staff | Lab |
|---|---|---|---|---|---|
| User accounts (create/deactivate/role-assign) | Full | None | Self profile only | Create Patient only | None |
| Departments | Full (CRUD) | Read | Read | Read | Read |
| Appointments | Full (all) | Own (as assigned doctor) | Own (as patient) only | Full (create/edit for any patient) | None |
| Medical records / visit notes | Read (no author) | Own patients only (create/read) | Own records only (read-only) | Read own-patient-visible subset (no edit) | None |
| Prescriptions | Read | Own patients only (create/read) | Own only (read-only) | Read only | None |
| Lab/x-ray/scan orders | Read | Own patients only (create/read) | Own only (read-only) | Read only | Assigned queue (read/update status) |
| Lab/x-ray/scan results | Read | Own patients only (read) | Own only (read-only) | Read only | Create/edit until finalized |
| Billing/invoices | Full | None | Own only (read-only) | Create/edit (front-desk billing) | None |
| Blog/articles | Full (CRUD, publish) | None | Read published only | None | None |
| Contact messages | Full (read/resolve) | None | None (submits via public form) | Read/resolve | None |
| Public site content | Full (edit About/Home copy) | None | Read | None | None |

Explicit rule statements:
- AUTHZ-1: A Patient can only ever access appointment, medical record, prescription, lab result, and billing rows where `patient_id` equals their own linked patient record. Any request for another patient's `patient_id` returns 403 Forbidden (not 404, to keep behavior consistent and avoid ambiguity — Architecture stage may downgrade to 404 for record-existence privacy, documented explicitly if changed).
- AUTHZ-2: A Doctor can only access clinical data for a patient with whom they have at least one appointment record (past or present). No appointment relationship => 403 Forbidden.
- AUTHZ-3: Staff can read/write appointments and demographic data for any patient, but cannot write clinical content (diagnosis, prescriptions, lab orders/results).
- AUTHZ-4: Lab can only see the minimum patient fields necessary (name, DOB, ordering doctor, order/test detail) — never full medical history, prescriptions, or billing.
- AUTHZ-5: Only Admin can change a user's role or activation status.
- AUTHZ-6: All role checks are enforced server-side on every request; the frontend hiding a UI control is not a substitute for backend enforcement.

### 3.4 Data Entities (implied by the stories above)

- **User**: id, email (unique), password_hash, role (enum: Admin/Doctor/Patient/Staff/Lab), full_name, phone, is_active, created_at.
- **Patient** (1:1 with User where role=Patient): patient_id, user_id (FK), date_of_birth, gender, address, emergency_contact_name, emergency_contact_phone.
- **Doctor** (1:1 with User where role=Doctor): doctor_id, user_id (FK), department_id (FK), specialty, qualifications, bio, years_experience, consultation_hours.
- **StaffMember** (1:1 with User where role=Staff): staff_id, user_id (FK), department_id (FK, optional).
- **LabTechnician** (1:1 with User where role=Lab): lab_user_id, user_id (FK).
- **Department**: department_id, name, description, is_active.
- **Appointment**: appointment_id, patient_id (FK), doctor_id (FK), scheduled_at, status (enum: Scheduled/Completed/Cancelled/NoShow), reason, created_by_user_id (Patient self-booked or Staff-booked), created_at.
- **VisitNote / MedicalRecord**: record_id, appointment_id (FK), patient_id (FK), doctor_id (FK), diagnosis, notes, created_at.
- **Prescription**: prescription_id, appointment_id (FK), patient_id (FK), doctor_id (FK), medicines (list: name/dosage/frequency/duration), instructions, created_at.
- **LabOrder**: order_id, patient_id (FK), doctor_id (FK, ordering), lab_user_id (FK, assigned/actioned), test_type (enum: Lab/X-ray/Scan + subtype), status (enum: Pending/InProgress/Completed), notes, created_at.
- **LabResult**: result_id, order_id (FK), result_data (text/values), file_attachment_path (optional), version (int, for amendments), finalized_at.
- **Invoice/Billing**: invoice_id, patient_id (FK), appointment_id (FK, optional), line_items, total_amount, status (enum: Pending/Paid/Waived), created_by_user_id, created_at.
- **BlogArticle**: article_id, title, slug, summary, body, author_user_id (FK), status (enum: Draft/Published), cover_image_path (optional), published_at.
- **ContactMessage**: message_id, name, email, phone (optional), subject, message, status (enum: New/Reviewed/Resolved), created_at.
- **AuditLogEntry** (supports ADM-9): log_id, actor_user_id, action, target_user_id (optional), details, created_at.

### 3.5 Acceptance Criteria (representative, per feature area — QA to expand into full test case suite)

**Authentication**
- AC-AUTH-1: Given an unauthenticated visitor submits valid signup data, when the account is created, then the role is always "Patient" regardless of any role field sent in the request payload.
- AC-AUTH-2: Given a user with role Staff logs in with correct credentials, when authentication succeeds, then the returned JWT's role claim is "Staff" and expires within the configured TTL.
- AC-AUTH-3: Given a deactivated user, when they attempt login with correct credentials, then the response is 403 Forbidden and no JWT is issued.

**Patient data isolation**
- AC-PAT-1: Given Patient A is logged in, when they call GET /patients/{B_patient_id}/records for Patient B, then the response is 403 Forbidden and no record data from B is present in the response body.
- AC-PAT-2: Given Patient A is logged in, when they call GET /patients/me/appointments, then only appointments with patient_id = A's own id are returned.

**Doctor-patient relationship**
- AC-DOC-1: Given Doctor X has never had an appointment with Patient Z, when Doctor X requests Patient Z's medical records, then the response is 403 Forbidden.
- AC-DOC-2: Given Doctor X has a completed appointment with Patient Z, when Doctor X creates a prescription for Patient Z, then the prescription is persisted with doctor_id = X and patient_id = Z and is retrievable by both X (as author) and Z (as owner).

**Appointment booking**
- AC-APT-1: Given a Patient selects a doctor, date, and an available time slot, when they submit the booking, then an Appointment row is created with status "Scheduled" and is visible in the Patient's own appointment list and the Doctor's appointment list.
- AC-APT-2: Given a Patient attempts to book a time slot already booked for that doctor, when they submit, then the request is rejected (409 Conflict) and no duplicate Appointment row is created.
- AC-APT-3: Given a Patient's appointment is scheduled to start within the minimum cancellation notice window, when they attempt to cancel, then the request is rejected with an explanatory error.

**Lab workflow**
- AC-LAB-1: Given a Doctor creates a lab order for a Patient, when the order is saved, then it appears in the Lab role's pending queue with status "Pending".
- AC-LAB-2: Given a Lab user marks an order "Completed" with a result, when the Doctor who ordered it queries results, then the result is visible to that Doctor and to the owning Patient, but not to unrelated Doctors.
- AC-LAB-3: Given a finalized (Completed) LabResult, when the Lab user attempts to edit it, then the system creates a new versioned entry rather than overwriting the original, and both versions remain retrievable.

**Blog**
- AC-BLOG-1: Given an article has status "Draft", when an anonymous visitor requests the public blog list or the article by slug, then it is not returned (404 or excluded from list).
- AC-BLOG-2: Given an Admin publishes a Draft article, when a visitor subsequently requests the public blog list, then the article appears with its published_at timestamp set.

**Contact form**
- AC-CONTACT-1: Given a visitor submits the contact form with valid required fields, when submitted, then a ContactMessage row is created with status "New" and the visitor sees an on-screen success confirmation (no real email is sent).
- AC-CONTACT-2: Given a visitor submits the contact form missing a required field, when submitted, then the request is rejected client-side and server-side with a validation error, and no ContactMessage row is created.

**Billing**
- AC-BILL-1: Given Staff creates an invoice for a Patient's completed appointment, when saved, then the invoice is visible to that Patient (read-only) and to Admin, but not to any other Patient.

---

## 4. Out of Scope

The following are explicitly excluded from this build to keep it a functional demo, not a production hospital system:
- Real payment gateway integration (Stripe/PayPal/etc.) — billing status changes (Paid/Waived) are manually set by Staff/Admin, no real money moves.
- Real email or SMS delivery — signup confirmation, appointment reminders, and contact-form acknowledgements are shown/stored in-app only, not dispatched via an external provider.
- Insurance claims processing/eligibility verification.
- Telemedicine / video consultation.
- Multi-hospital / multi-tenant support — single hospital instance only.
- Native mobile apps (iOS/Android) — web (responsive) only.
- Real-time chat between Patient and Doctor/Staff.
- Advanced scheduling optimization (auto-suggested slots, doctor leave/absence calendars) — booking is manual slot selection against a simple availability list.
- Electronic prescription transmission to external pharmacies (e-prescribing standards, e.g., NCPDP).
- HL7/FHIR interoperability with external health systems.
- Full HIPAA/regulatory compliance certification — access controls follow the rules in this document but no formal compliance audit is in scope.
- Granular field-level audit logging for every clinical read (only account/role admin actions are audited per ADM-9).
- Multi-factor authentication, SSO/OAuth login.
- File storage integration beyond local disk/simple storage for lab result attachments and blog cover images (no cloud CDN, virus scanning, etc.).
- General data export/interoperability tools beyond the patient medical record PDF (REQ-08, Section 9.8) and the admin analytics CSV (REQ-06, Section 9.6) — such as HL7/FHIR feeds, bulk data exports, and CSV export of raw clinical records.
- ~~Waitlist management for fully booked doctors~~ — now in scope as REQ-09 (Section 9.9).
- Internationalization / multi-language support.

---

## 5. Open Items for Architecture Stage
- Exact minimum-notice threshold for appointment cancellation (PAT-4 / AC-APT-3) — placeholder of 1 hour proposed, confirm or adjust.
- Whether 403 vs 404 is used for cross-tenant record access attempts (AUTHZ-1) — 403 assumed here for explicitness; Architecture may choose 404 for stricter existence-privacy and should document the change here if so.
- File storage mechanism for lab result attachments and blog images (local filesystem path assumed given SQLite/simple-stack scope).

---

## 6. Visual & UI Enhancement Requirements

Status: Draft v1.1 — added after initial skeleton review.
Consumers: Frontend Developer (Chintu — primary owner), Solution Architect (Sagar — CSS architecture decisions), Backend Developer (Pavan — no backend changes required unless noted).

The current build is a functional skeleton with a plain teal/green color scheme, no images, no icons, bare cards, and no visual components beyond tables and basic grids. This section defines the full-detail visual and UI requirements to make the site look and feel like a real, professional hospital website. These are pure frontend changes unless a specific backend note is called out.

---

### 6.1 Image Strategy

All images required for the demo shall be sourced from Unsplash (free, no API key required for direct URL embedding) and stored as static assets inside `src/frontend/public/images/`. This keeps the demo self-contained and offline-capable after initial placement.

**VI-IMG-1**: Create the directory `src/frontend/public/images/` and populate it with the following curated image files before frontend visual work begins. Image descriptions, filenames, and minimum dimensions are specified per section below. Images must be compressed (WebP format preferred; JPEG acceptable) with a maximum file size of 300 KB per image for fast load.

**VI-IMG-2**: Every `<img>` element must carry a descriptive `alt` attribute. Images that are purely decorative (backgrounds, overlays) must use `alt=""` so screen readers skip them.

**VI-IMG-3**: Images are never loaded from external URLs at runtime in the final frontend build. All image references use relative paths from `/images/`. This means Pavan does not need to add any new image-serving endpoints to the backend; the frontend dev server and Vite build serve them as static assets.

**VI-IMG-4**: The existing `cover_image_path` field on `BlogArticle` and the `Doctor` public profile already exist in the data model (see section 3.4). The backend already returns these fields; the frontend must now actually render them as `<img>` elements wherever applicable (blog cards, blog article header, doctor profile).

---

### 6.2 Color Scheme and Typography

The existing CSS variable set in `src/frontend/src/index.css` is the single source of truth for design tokens. The following changes update and extend it.

**VI-COLOR-1: Refined color palette.** Update `:root` in `index.css` with the following token additions/changes. Existing variable names must be preserved to avoid breaking existing code; new tokens are additive.

```
/* Updated primary — slightly warmer teal, hospital-grade */
--color-primary:        #0e8a7a;
--color-primary-dark:   #096b5d;
--color-primary-light:  #e6f5f2;

/* New accent — used for emergency numbers, urgent CTAs */
--color-accent:         #e05c2a;
--color-accent-light:   #fdf0eb;

/* Extended neutrals */
--color-bg:             #f4f7f6;
--color-surface:        #ffffff;
--color-surface-alt:    #f0f5f3;
--color-border:         #d8e3e0;
--color-border-dark:    #b3c8c2;

/* Text */
--color-text:           #1a2422;
--color-text-muted:     #536560;
--color-text-light:     #8fa8a2;

/* Semantic */
--color-danger:         #c0392b;
--color-warn:           #b7791f;
--color-ok:             #1e8e5a;
--color-info:           #1f5aa8;

/* Shadows */
--shadow-sm:            0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
--shadow-md:            0 4px 12px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.06);
--shadow-lg:            0 10px 28px rgba(0,0,0,0.12), 0 4px 10px rgba(0,0,0,0.06);

/* Radii */
--radius-sm:            6px;
--radius-md:            10px;
--radius-lg:            16px;
--radius-xl:            24px;
```

**VI-COLOR-2**: The accent color (`--color-accent`, warm orange-red) is used exclusively for: the emergency phone number display, emergency-related badges, and any "book now" primary CTA buttons on the public marketing site. It must not be used for general UI elements to preserve its urgency signal.

**VI-FONT-1: Google Fonts — Inter.** Load the Inter typeface via a `<link>` in `src/frontend/index.html`. Use weights 400, 500, 600, and 700.
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```
Update `font-family` in `:root` to: `'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif`.

**VI-FONT-2: Heading scale.** Apply the following heading styles globally in `index.css`:
- `h1`: font-size 2rem; font-weight 700; line-height 1.2; letter-spacing -0.02em; color `--color-text`.
- `h2`: font-size 1.5rem; font-weight 700; line-height 1.3; color `--color-text`.
- `h3`: font-size 1.125rem; font-weight 600; color `--color-text`.
- Body: font-size 1rem; line-height 1.6.
- Small/muted text: font-size 0.875rem; line-height 1.5.

Remove the current rule that colors `h1, h2, h3` using `--color-primary-dark`. Headings on dark/hero backgrounds are explicitly overridden with `color: #fff` at the component level; headings on light backgrounds use `--color-text`.

**VI-FONT-3**: All buttons (`btn` class) use font-weight 600 and font-size 0.9375rem (15px). Button border-radius updates to `--radius-md` (10px). Padding becomes `0.625rem 1.375rem`.

---

### 6.3 Icon System

**VI-ICON-1**: Install `lucide-react` as a dependency (`npm install lucide-react`). Use Lucide icons throughout the UI. Lucide is MIT licensed, tree-shakeable, and provides consistent line-style SVG icons appropriate for a healthcare brand.

**VI-ICON-2**: The following icon assignments are required at a minimum. Frontend developer must not deviate from these assignments to keep visual language consistent:

| Usage location | Icon name (Lucide) |
|---|---|
| Departments — Cardiology | `Heart` |
| Departments — Pediatrics | `Baby` |
| Departments — Orthopedics | `Bone` |
| Departments — Neurology | `Brain` |
| Departments — Oncology | `Ribbon` |
| Departments — Emergency / General | `AlertCircle` |
| Departments — Radiology / Lab | `FlaskConical` |
| Departments — Ophthalmology | `Eye` |
| Departments — Dermatology | `Smile` |
| Departments — Gynecology / Women's Health | `Star` |
| Any department without a specific mapping | `Stethoscope` |
| Navigation — Home | `Home` |
| Navigation — About | `Info` |
| Navigation — Departments | `Building2` |
| Navigation — Blog | `BookOpen` |
| Navigation — Contact | `Phone` |
| Sidebar nav — Dashboard | `LayoutDashboard` |
| Sidebar nav — Appointments | `CalendarCheck` |
| Sidebar nav — Patients | `Users` |
| Sidebar nav — Records | `FileText` |
| Sidebar nav — Billing | `Receipt` |
| Sidebar nav — Profile | `UserCircle` |
| Sidebar nav — Lab Orders | `FlaskConical` |
| Sidebar nav — Blog (admin) | `BookOpen` |
| Sidebar nav — Users (admin) | `UserCog` |
| Sidebar nav — Contact Messages | `MessageSquare` |
| Sidebar nav — Audit Log | `ClipboardList` |
| Sidebar nav — Departments (admin) | `Building2` |
| Contact — address | `MapPin` |
| Contact — phone | `Phone` |
| Contact — emergency | `PhoneCall` |
| Contact — email | `Mail` |
| Stats — patients | `Users` |
| Stats — doctors | `UserCheck` |
| Stats — experience years | `Award` |
| Stats — departments | `Building2` |
| Logout button | `LogOut` |
| Book appointment CTA | `CalendarPlus` |

**VI-ICON-3**: All icon-text pairings in nav items use `display: flex; align-items: center; gap: 0.5rem`. Icons render at 18px (1.125rem) in nav contexts, 20px in cards, 28–36px in stat/feature cards.

---

### 6.4 Public Navigation Bar

**VI-NAV-1: Logo.** Replace the plain text brand in `.public-nav` with an SVG logo mark: a green circle containing a white plus/cross symbol, followed by the text "Green Valley Hospital" in two lines ("Green Valley" in bold, "Hospital" in regular weight). The logo mark SVG must be inline or a separate component at `src/frontend/src/components/Logo.tsx`. Size: 36px height for the icon mark, text at 1rem / 0.75rem stacked.

**VI-NAV-2: Emergency strip.** Add a narrow (36px tall) top bar above `.public-nav` with background `--color-primary-dark` and text: "Emergency: +1 (555) 000-9999  |  Open 24 hours, 7 days a week". The emergency number is styled in `--color-accent` with a `PhoneCall` icon. This strip is visible only on the public site (not inside the authenticated app shell).

**VI-NAV-3: Nav link style.** Public nav links receive a bottom border underline on hover (2px solid `--color-primary`) rather than color-only change. Active link has this underline permanently. Font-weight 500. Do not use background-color highlights on public nav links (reserved for sidebar).

**VI-NAV-4: Sticky shadow.** When the page is scrolled past 10px, add `box-shadow: var(--shadow-sm)` to `.public-nav` via a scroll-event listener that toggles a CSS class `.scrolled`. This gives visual depth as content scrolls under the nav.

**VI-NAV-5: "Book Appointment" CTA in nav.** Replace the plain "Sign Up" button in the nav auth area with a button labeled "Book Appointment" styled with `--color-accent` background (not primary teal). This is the primary conversion CTA on the public site. Keep "Login" as `btn-outline`.

**VI-NAV-6: Mobile hamburger menu.** At viewport width below 768px, hide the nav link list and auth buttons, and display a hamburger icon button (`Menu` icon from Lucide). Clicking it toggles a full-width dropdown showing all nav links and auth buttons stacked vertically. The dropdown overlays page content (z-index above main, below modal level). Close on outside click. No JavaScript animation library — use a CSS class toggle with `max-height` transition.

---

### 6.5 Public Footer

**VI-FOOTER-1: Three-column footer layout.** Replace the current two-element flex footer with a four-area footer:
- Column 1 (brand): Logo mark + hospital name + tagline "Compassionate care, every day." + social placeholder icons (Facebook, Twitter/X, LinkedIn using Lucide `Facebook`, `Twitter`, `Linkedin` — links go to `#` since social pages don't exist).
- Column 2 (Quick Links): About, Departments, Blog, Contact, Book Appointment (links to `/signup`).
- Column 3 (Services): List the top 6 departments by name as links to `/departments/{id}` — these are rendered from a static list if the API is unavailable, since the footer is a layout component.
- Column 4 (Contact Info): Address with `MapPin` icon, General phone with `Phone` icon, Emergency phone with `PhoneCall` icon and accent color, Email with `Mail` icon.
- Bottom bar: copyright text left, "Privacy Policy | Terms of Use" text right (links go to `#`).

**VI-FOOTER-2**: Footer background remains `--color-primary-dark`. Column headings use font-weight 700, color `#fff`. Links use `rgba(255,255,255,0.75)` with hover to `#fff`. The emergency phone number uses `--color-accent` color.

---

### 6.6 Home Page

**VI-HOME-1: Full-bleed hero section.** Replace the current padded hero box with a full-width (100vw, not constrained to `.public-main`) hero section. Requirements:
- Height: `min-height: 600px; max-height: 700px`.
- Background: a hospital exterior or medical team photograph at `/images/hero-banner.jpg` (minimum 1600x700px, subject: modern hospital building exterior at daytime, or doctors/nurses in a bright clinical corridor). Overlay: `linear-gradient(to right, rgba(9,107,93,0.88) 0%, rgba(9,107,93,0.55) 60%, rgba(9,107,93,0.15) 100%)`.
- Layout: two-column on desktop (text left, image right using `object-fit: cover`); stacked single-column on mobile.
- Left content: hospital name in white 2.5rem font-weight 800, tagline below in white 1.125rem, two CTA buttons: "Book an Appointment" (accent color) and "Explore Departments" (white outline). Buttons have 48px height, appropriate padding.
- The hero section sits immediately below the sticky nav and emergency strip, with no margin between them.
- The `.public-main` padding does NOT apply to the hero — the hero must break out of the container. Implement using a negative margin trick or restructure the layout so the hero is rendered outside `.public-main` as a direct child of `.site`.

**VI-HOME-2: Stats counter band.** Immediately below the hero, add a full-width stats band with background `--color-primary-light` (`#e6f5f2`), 64px vertical padding. It displays four stats in a flex row (wraps to 2x2 on mobile):

| Icon | Value | Label |
|---|---|---|
| `Users` (28px, primary) | 15,000+ | Patients Treated |
| `UserCheck` (28px, primary) | 80+ | Specialist Doctors |
| `Award` (28px, primary) | 25 | Years of Service |
| `Building2` (28px, primary) | 18 | Departments |

Values are displayed in 2.25rem font-weight 800 `--color-primary-dark`. Labels in 0.875rem `--color-text-muted`. These are static hardcoded values (not from API) since they represent marketing copy, not live data. A subtle count-up animation on scroll-into-view is required: use `IntersectionObserver` to trigger a JavaScript counter animation from 0 to the target value over 1.5 seconds when the band enters the viewport for the first time. No external animation library — plain `requestAnimationFrame`.

**VI-HOME-3: "Why Choose Us" section.** Redesign the existing highlights section. Layout: 3-column grid on desktop, 2-column on tablet, 1-column on mobile. Each card:
- Icon: one of `ShieldCheck` (Advanced Technology), `Heart` (Compassionate Care), `Clock` (24/7 Emergency), `Award` (Accredited Facility), `Users` (Expert Team), `Stethoscope` (Comprehensive Specialties) — assign by index of the highlights array; if fewer than 6 highlights, assign from the front of this list.
- Icon renders in a 56px circle with background `--color-primary-light`.
- Card: white background, `--shadow-sm`, `--radius-lg`, 24px padding, no border. On hover, lift to `--shadow-md` with `transform: translateY(-3px)` transition (200ms ease).
- Text: h3 heading (icon label from list above), then the highlight text from the API below it.

**VI-HOME-4: Featured Departments section.** Redesign the current plain card grid. Section header: centered "Our Departments" h2 with a 3px wide 48px colored underline in `--color-primary` below it. Department cards:
- 3-column on desktop, 2-column on tablet, 1-column on mobile.
- Each card: icon from VI-ICON-2 mapping (56px, in a circle), department name in h3, description in muted small text, a "Learn More" link-styled text with chevron-right icon, all inside a white rounded card with `--shadow-sm` hover lift.
- Clicking the card navigates to `/departments/{department_id}`.

**VI-HOME-5: "Meet Our Specialists" teaser.** Add a new section below Featured Departments titled "Meet Our Specialists". This section renders a horizontal scrollable row of up to 4 doctor cards pulled from the existing `content.featured_departments` data — specifically, for each featured department display the first doctor from that department if available. Each doctor card:
- Circular photo placeholder: if `doctor.profile_photo_path` is set, display it; else display a gradient circle with the doctor's initials in white 1.25rem font.
- Doctor name, specialty, department chip (small badge with `--color-primary-light` background).
- "View Profile" link to `/doctors/{doctor_id}`.
- Card: white, `--shadow-sm`, rounded-lg, padding 24px, text-center.

Note to backend developer (Pavan): the `Doctor` entity in the data model must expose a `profile_photo_path` field (nullable string, filesystem path). This field is already implied by the existing doctor profile editing (DOC-1) but is not explicitly listed in the data entity definition in section 3.4. Add it: `Doctor` gains `profile_photo_path` (nullable string). No API endpoint changes are needed — simply include this field in the existing doctor listing and profile response schemas.

**VI-HOME-6: Patient Testimonials section.** Add a testimonials section with a background of `--color-surface-alt`. Title: "What Our Patients Say" centered h2 with decorative underline. Display 3 testimonial cards in a 3-column grid (collapses to 1 column on mobile). These are static, hardcoded content — not stored in the database (testimonials are marketing copy, out of scope for dynamic CMS). Each card:
- Large opening quote mark (`"`) in `--color-primary-light`, font-size 4rem, line-height 0.5.
- Testimonial text in 1rem italic, 5–6 lines.
- Author name in 0.9rem font-weight 600.
- Author detail in 0.8rem `--color-text-muted` (e.g., "Patient since 2021").
- 5-star rating using 5 filled `Star` icons (Lucide) in `#f5a623`.
- Card: white, `--shadow-sm`, `--radius-lg`, 28px padding.

Hardcoded testimonials to use:
1. "The care I received at Green Valley was exceptional. The doctors took time to explain every step of my treatment. I felt genuinely heard and cared for." — Sarah M., Patient since 2019.
2. "After my surgery, the nursing team was attentive 24/7. The facilities are modern and the entire process from booking to discharge was smooth." — Rajesh K., Patient since 2022.
3. "I brought my daughter here for pediatric care and the doctors were so patient and gentle with her. Green Valley is our family's hospital." — Priya L., Patient since 2021.

**VI-HOME-7: Recent Blog Posts section.** Add a "Health Tips & News" section at the bottom of the home page (above footer). Render the 3 most recent published blog articles from the existing `getHome()` API response, or make a separate call to `getBlogList()` if the home API does not include recent articles.

Note to backend developer (Pavan): the `GET /public/home` endpoint should include a `recent_articles` array in its response payload — up to 3 articles with fields: `article_id`, `title`, `summary`, `author_name`, `published_at`, `cover_image_path`, `slug`. If this is too large a change for the home endpoint, the frontend may call `GET /public/blog?limit=3` instead — either approach is acceptable; Pavan must document which is implemented.

Each article card: cover image (top image, 200px height, `object-fit: cover`, `--radius-md` top corners only) or a placeholder gradient if no image; title; summary (2-line clamp); author + date; "Read More" link. 3-column grid, same card style as departments.

---

### 6.7 About Page

**VI-ABOUT-1: Page hero.** Add a page-level hero banner at the top of the About page (outside `.public-main` container, full-width). Height: 300px. Background image: `/images/about-hero.jpg` (subject: interior of a bright, modern hospital lobby or corridor, minimum 1400x400px). Overlay: `rgba(9,107,93,0.75)`. Text centered in the overlay: "About Green Valley Hospital" in 2.25rem white bold, subtitle "Serving our community with compassion since 1999" in 1rem white.

**VI-ABOUT-2: Mission/Vision/Values cards.** Replace the plain `<p>` paragraphs for Mission with a 3-column card row:
- Card 1 "Our Mission" — `Target` icon (Lucide), teal circle, content from `content.mission`.
- Card 2 "Our Vision" — `Eye` icon, content: "To be the most trusted healthcare partner in the region, setting the standard for clinical excellence and patient experience."
- Card 3 "Our Values" — `Heart` icon, content: a bulleted list — Compassion, Integrity, Excellence, Innovation, Community.
Cards: white background, `--shadow-sm`, `--radius-lg`, top icon with label, 28px padding.

**VI-ABOUT-3: Facility photo gallery.** Add a 3-column image grid (2 rows, 6 images) in the Facilities section. Images: `/images/facility-icu.jpg`, `/images/facility-er.jpg`, `/images/facility-lab.jpg`, `/images/facility-maternity.jpg`, `/images/facility-outpatient.jpg`, `/images/facility-pharmacy.jpg`. Each image: height 200px, `object-fit: cover`, `--radius-md`, `--shadow-sm`. Subjects: modern ICU, emergency room, clinical laboratory, maternity ward, outpatient waiting area, pharmacy counter — all bright and clean-looking. Below each image, a short label in `--color-text-muted` 0.875rem.

**VI-ABOUT-4: Accreditations strip.** Display accreditations as horizontally arranged logo-placeholder cards: grey-bordered rounded cards (100px x 80px) each containing the accreditation name in small centered text and a `Award` icon. These are static. The current `content.accreditations` text is reformatted to parse comma-separated values and render each as a separate badge card.

**VI-ABOUT-5: History timeline.** Replace the plain history paragraph with a vertical timeline component. The timeline has 4–5 milestones. The backend `content.history` text is used as the final paragraph; the preceding milestones are static:
- 1999: "Green Valley Hospital founded with 50 beds and 3 departments."
- 2005: "Expanded to 200 beds; Cardiology and Neurology centers established."
- 2012: "Achieved NABH accreditation; opened dedicated Cancer Care wing."
- 2019: "Launched 24/7 Emergency & Trauma center; added advanced MRI and CT facilities."
- Present: Content from `content.history`.

Timeline design: vertical line (2px `--color-border-dark`), alternating left/right cards on desktop, always right-aligned on mobile. Year shown in a circle on the line in `--color-primary`. Card: white, `--shadow-sm`, `--radius-md`.

---

### 6.8 Departments Page

**VI-DEPT-1: Page hero.** Full-width page hero, 240px height, background `/images/departments-hero.jpg` (subject: multi-specialist medical team), overlay `rgba(9,107,93,0.78)`, centered white text "Our Departments & Specialties" + subtitle "World-class care across 18 specialties".

**VI-DEPT-2: Department card redesign.** Each department card:
- Top area: full-width image slot, height 150px, `object-fit: cover`. Image file: `/images/dept-{slug}.jpg` where `{slug}` is the department name lowercased and hyphenated (e.g., `dept-cardiology.jpg`). If the image file is not found, fall back to a solid background using `--color-primary-light` with the department icon centered (56px).
- Below image: department icon (24px, `--color-primary`) + name in h3 + description 2-line clamp + "View Doctors" button (small, outline style).
- Card: white, `--shadow-sm` → `--shadow-md` on hover, `--radius-lg`, no border.
- 3-column grid on desktop, 2-column on tablet, 1 on mobile.

**VI-DEPT-3: Search filter.** Add a search input above the grid with a `Search` icon (Lucide) inside the input on the left side. Filter is client-side: as the user types, hide cards whose `name` or `description` do not match the query string (case-insensitive). No API call required. If no departments match, display "No departments match your search." in muted text.

---

### 6.9 Department Doctors Page

**VI-DDOC-1: Department header banner.** At the top of the Department Doctors page, display a full-width banner (200px height) with the department's `/images/dept-{slug}.jpg` as background, the same overlay as VI-DEPT-1, and centered white text: the department name as h1, "Meet our specialists" as subtitle. The department name must be fetched — if the existing `getDepartmentDoctors()` API call does not return the department name, Pavan must add it to the response payload.

Note to Pavan: `GET /public/departments/{id}/doctors` must return a `department` object with at minimum `name`, `description`, `department_id` alongside the doctors array. This aligns with PUB-DEPT-2 already in requirements.

**VI-DDOC-2: Doctor card redesign.** Each doctor card:
- Profile photo: 90px circle, `object-fit: cover`. If `profile_photo_path` is null, render a gradient circle (#0e8a7a to #096b5d) with the doctor's initials in white 1.25rem font.
- Doctor name in h3, specialty in 0.875rem `--color-text-muted`.
- Qualifications shown as a grey badge (`--color-surface-alt`, border `--color-border`, `--radius-sm`).
- Experience shown as "X yrs experience" with a small `Clock` icon.
- "View Full Profile" button (outline, full-width of card).
- Card: white, `--shadow-sm`, `--radius-lg`, centered text layout, 24px padding.

---

### 6.10 Doctor Profile Page

**VI-DOCPROF-1: Profile layout.** Replace the single plain card with a two-column layout:
- Left column (30%): large profile photo (200px circle, centered). If no photo, gradient circle with initials. Below photo: department badge, specialty tag.
- Right column (70%): doctor name as h1, specialty below in `--color-text-muted`, then sections: Bio, Qualifications, Experience, Consultation Hours — each with a small icon and a section divider (`--color-border` 1px horizontal rule).

**VI-DOCPROF-2: "Book an Appointment" CTA.** Below the profile content, add a full-width CTA strip with background `--color-primary-light`, `--radius-lg`, text "Ready to consult with {doctor.full_name}? Book your appointment today." and a `CalendarPlus`-icon button "Book Appointment" linking to `/signup` (or `/patient/book` if already logged in as a Patient). This is the primary conversion action on the doctor profile page.

---

### 6.11 Contact Page

**VI-CONTACT-1: Split layout.** Replace the stacked layout with a two-column grid (50/50 on desktop, stacked on mobile):
- Left column: contact information cards + map placeholder.
- Right column: the contact form.

**VI-CONTACT-2: Contact info cards.** Replace the plain `<p>` list with four styled info rows, each with an icon circle (56px, `--color-primary-light` background, icon `--color-primary`):
- Address (`MapPin`): "123 Green Valley Drive, Medical District, City, State 00000"
- General Phone (`Phone`): "+1 (555) 000-1234"
- Emergency (`PhoneCall`): "+1 (555) 000-9999" — the phone number text is styled in `--color-accent` with font-weight 700 and a small badge "24/7 Emergency" in red.
- Email (`Mail`): "info@greenvalleyhospital.demo"

These values are rendered from the API `getContactInfo()` response if available; the above are the fallback/demo defaults.

**VI-CONTACT-3: Map placeholder.** Below the contact info, add a static map image `/images/map-placeholder.jpg` (subject: a hospital location map screenshot or a generic city map pin image) inside a container: height 220px, `object-fit: cover`, `--radius-md`, border `1px solid --color-border`. Overlay text at bottom-left of the image: "Green Valley Hospital" in small white text on a semi-transparent dark strip. The map is not interactive (no Google Maps API — see Out of Scope section 4).

**VI-CONTACT-4: Form styling.** The contact form receives:
- White card background with `--shadow-md`, `--radius-lg`, 32px padding.
- Each input field gets 48px height, focus ring: `outline: 2px solid --color-primary; outline-offset: 1px`.
- The submit button is full-width, 48px height, accent color (`--color-accent`), with `Send Message` text and a `Send` icon (Lucide) on the right.
- Success state: replace the form with a success illustration using a large `CheckCircle` icon (64px, `--color-ok`) centered, "Message Sent!" in h2, and the confirmation text below, inside the same card.

---

### 6.12 Blog Pages

**VI-BLOG-1: Blog list page hero.** Add a 240px full-width page hero, background `/images/blog-hero.jpg` (subject: doctor reading or a medical library/research setting), overlay `rgba(9,107,93,0.75)`, centered white text "Health Blog & Articles" + subtitle.

**VI-BLOG-2: Article card redesign.** Each blog list card:
- Cover image: top of card, height 180px, `object-fit: cover`, rounded top corners. If `cover_image_path` is null, use a gradient placeholder (`--color-primary` to `--color-primary-dark`) with a centered `BookOpen` icon in white.
- Title in h3 (2-line clamp with `overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical`).
- Summary in 0.875rem `--color-text-muted`, 3-line clamp.
- Author + date row with a small author avatar placeholder (24px circle with initials) and `Calendar` icon before the date.
- "Read More" link with right arrow.
- Card: white, `--shadow-sm` → `--shadow-md` on hover, `--radius-lg`, no border.

**VI-BLOG-3: Article detail page.** The `BlogArticlePage` (not read in detail yet but follows standard structure) must be styled:
- Full-width article header: cover image (400px height max, `object-fit: cover`) or gradient fallback with same overlay used on heroes.
- Article title in 2rem bold white text overlaid at the bottom-left of the header image.
- Below header: article meta row (author avatar, author name, published date, estimated read time = `Math.ceil(word_count / 200)` minutes where `word_count` is derived client-side from `body.split(' ').length`).
- Article body: `max-width: 720px; margin: 0 auto;` for readability. Font-size 1.0625rem, line-height 1.75.
- "Back to Blog" link at top with `ArrowLeft` icon.

---

### 6.13 Login and Signup Pages

**VI-AUTH-1: Split-screen layout.** Replace the `center-box` card layout with a full-viewport-height two-column layout (visible only on desktop/tablet — collapses to centered card on mobile):
- Left panel (45% width): a hospital-themed image `/images/auth-panel.jpg` (subject: warm, welcoming hospital reception or a doctor with a reassuring expression), `object-fit: cover`, full height. Over the image: a dark gradient overlay from bottom, and at the bottom of the panel: hospital logo mark + name in white + tagline.
- Right panel (55% width): vertically centered auth card, max-width 400px, no border (no extra shadow since the panel itself is the frame).
- On mobile (< 768px): left panel hidden; right panel is full-width with the hospital logo at top of form.

**VI-AUTH-2: Form field improvements.**
- Each input: 48px height, `--radius-md`, focus ring, icon inside left of field: `Mail` for email, `Lock` for password, `User` for name, `Phone` for phone, `Calendar` for date of birth.
- Password field: toggle show/hide password with `Eye` / `EyeOff` icon button inside the field right side.
- The submit button: full-width, 48px height, `--color-accent` background for the primary action.

**VI-AUTH-3: Signup page role clarity.** At the top of the signup form (before the fields), add a small info banner using `--color-primary-light` background and `Info` icon: "Patient registration only. Doctor, staff, and admin accounts are created by hospital administration." This satisfies PUB-AUTH-2's constraint visually.

---

### 6.14 Authenticated App Shell (Sidebar)

**VI-SHELL-1: Sidebar logo.** Replace the plain "Green Valley" text brand in the sidebar with the `Logo` component from VI-NAV-1, white variant (white icon mark + white text). The logo links to the appropriate role home page, not to `/`.

**VI-SHELL-2: Nav item icons.** Every sidebar nav item must render its assigned icon from VI-ICON-2 to the left of the label text. Icon size 16px. Items use `display: flex; align-items: center; gap: 0.625rem`.

**VI-SHELL-3: User info in sidebar.** Replace the simple role badge with a user info block at the bottom of the sidebar (using `margin-top: auto` flex-push):
- Small avatar circle (36px) with user initials on `rgba(255,255,255,0.2)` background.
- User's full name in 0.875rem white font-weight 600.
- Role in 0.75rem `rgba(255,255,255,0.65)`.
- Logout button as an icon-only button (`LogOut` icon, 18px) to the right, tooltip "Log out".

**VI-SHELL-4: Topbar improvement.** The authenticated topbar currently shows only email + logout. Replace with:
- Left: current page title (either a prop or derived from the route match).
- Right: user full name + role badge + notification bell placeholder (`Bell` icon, Lucide, no functionality — visual only) + logout.

**VI-SHELL-5: Sidebar active state.** Active sidebar links use a white background at 15% opacity (`rgba(255,255,255,0.15)`) with a 3px left border in `--color-primary-light` (white at 60%). This is already partially implemented in the existing `.active` CSS — extend it with the left border.

---

### 6.15 Admin Dashboard

**VI-ADMIN-1: Stat card icons.** Each stat card on the Admin Dashboard (`AdminDashboardPage`) receives a Lucide icon appropriate to its metric (from VI-ICON-2 stats row), rendered at 36px inside a 64px circle with background `--color-primary-light` at the top of the card. The numeric value below, label below that.

**VI-ADMIN-2: Stat card color theming.** Each of the four stat cards gets a distinct left-border accent: patient count = `--color-primary`, doctor count = `--color-info`, appointments today = `--color-warn`, pending lab orders = `--color-accent`. Border: 4px solid on the left side of the card.

**VI-ADMIN-3: Quick-action buttons.** Below the stat grid on the admin dashboard, add a "Quick Actions" row with icon buttons: "Add User" (`UserPlus`), "New Department" (`Plus`), "View Appointments" (`CalendarCheck`), "View Messages" (`MessageSquare`). These are styled as medium outline buttons and navigate to the respective admin pages.

---

### 6.16 Patient Portal Pages

**VI-PAT-1: Patient dashboard greeting.** The patient appointments page (`PatientAppointmentsPage`) should display a greeting card at the top: "Good morning/afternoon/evening, {patient.full_name}" (time-of-day aware) with a subtle illustration or icon area using `--color-primary-light` background and a `CalendarCheck` icon (48px). Below: upcoming appointment count in a badge.

**VI-PAT-2: Empty states.** All patient pages (appointments, records, invoices) must replace the current "No X found." plain text with an illustrated empty-state: centered Lucide icon (80px, `--color-text-light`), h3 "No appointments yet", muted text, and a CTA button where applicable (e.g., "Book your first appointment" on the appointments page).

---

### 6.17 Shared UI Component Improvements

**VI-SHARED-1: Card hover states.** All `.card` instances that are clickable (wrapped in `<Link>`) must have hover styles: `transform: translateY(-2px); box-shadow: var(--shadow-md);` with `transition: transform 200ms ease, box-shadow 200ms ease`. Static (non-link) cards do not get hover lift.

**VI-SHARED-2: Table improvements.** All data tables receive:
- Zebra striping: odd rows `--color-surface`, even rows `--color-surface-alt`.
- Row hover: `background: --color-primary-light` on `tr:hover td`.
- Sticky header: `thead th { position: sticky; top: 0; z-index: 1; }` for long tables.

**VI-SHARED-3: Loading skeleton.** Replace all instances of `<p className="muted">Loading…</p>` with a skeleton loader: 3 placeholder bars of varying width (80%, 60%, 90%) animated with a shimmer (`background: linear-gradient(90deg, --color-surface-alt 25%, --color-border 50%, --color-surface-alt 75%)` animated `background-position`). Create a reusable `<SkeletonBlock>` component at `src/frontend/src/components/SkeletonBlock.tsx`.

**VI-SHARED-4: Page-level error state.** Replace all instances of plain `<p className="error-text">{error}</p>` at page level with an error card: `AlertCircle` icon (Lucide, 32px, `--color-danger`), error message, and a "Try again" button that re-calls the data fetch. Create a reusable `<PageError>` component at `src/frontend/src/components/PageError.tsx`.

**VI-SHARED-5: Back-to-top button.** On pages taller than the viewport (especially blog article, department doctors, about), render a floating "back to top" button in the bottom-right corner that appears after scrolling 400px. Uses `ChevronUp` icon (Lucide), 44x44px circle, `--color-primary` background, white icon. Smooth-scrolls to top on click. Create as `src/frontend/src/components/BackToTopButton.tsx`.

**VI-SHARED-6: Status badges.** The existing `.badge-*` classes are used in tables. Add a visual icon to each status badge: `Check` for Completed, `Clock` for Scheduled/Pending, `X` for Cancelled/NoShow, `Loader` for InProgress. Icons at 12px inline before the text.

---

### 6.18 Required Image Files

The following image files must be created in `src/frontend/public/images/` before frontend visual implementation begins. Chintu is responsible for sourcing these from Unsplash (https://unsplash.com) or Pexels (https://www.pexels.com) and converting to WebP (max 300 KB each). All images are under free-use licenses compatible with demo use.

| Filename | Dimensions | Subject / Search terms |
|---|---|---|
| `hero-banner.jpg` | 1600 x 700 | Modern hospital exterior, daytime, clear sky, architectural |
| `about-hero.jpg` | 1400 x 400 | Hospital lobby interior, bright, modern, welcoming |
| `departments-hero.jpg` | 1400 x 400 | Medical team group, diverse doctors in white coats |
| `blog-hero.jpg` | 1400 x 400 | Doctor reading tablet, medical journal, research |
| `auth-panel.jpg` | 800 x 1000 | Friendly doctor or reception desk, warm lighting |
| `map-placeholder.jpg` | 800 x 300 | City map with pin marker, generic |
| `facility-icu.jpg` | 600 x 300 | ICU patient room, modern equipment |
| `facility-er.jpg` | 600 x 300 | Emergency room corridor |
| `facility-lab.jpg` | 600 x 300 | Clinical laboratory with technician |
| `facility-maternity.jpg` | 600 x 300 | Maternity ward, newborn, gentle lighting |
| `facility-outpatient.jpg` | 600 x 300 | Hospital waiting area, comfortable seating |
| `facility-pharmacy.jpg` | 600 x 300 | Hospital pharmacy counter |
| `dept-cardiology.jpg` | 600 x 250 | Heart monitor, cardiologist, ECG |
| `dept-pediatrics.jpg` | 600 x 250 | Pediatrician with child patient |
| `dept-orthopedics.jpg` | 600 x 250 | X-ray bone, orthopedic procedure |
| `dept-neurology.jpg` | 600 x 250 | Brain scan, neurologist |
| `dept-oncology.jpg` | 600 x 250 | Cancer treatment, infusion therapy |
| `dept-radiology.jpg` | 600 x 250 | MRI scanner, radiology suite |
| `dept-emergency.jpg` | 600 x 250 | Emergency ambulance bay or ER entrance |
| `dept-ophthalmology.jpg` | 600 x 250 | Eye examination, slit lamp |
| `dept-gynecology.jpg` | 600 x 250 | Women's health consultation |
| `dept-dermatology.jpg` | 600 x 250 | Dermatology consultation, skin examination |

For departments not listed above, use `/images/dept-default.jpg` (600x250, generic stethoscope/medical background). Chintu must create this default image as well.

---

### 6.19 Responsive Breakpoints

All visual changes must respect the following breakpoints consistently:

| Breakpoint name | CSS min-width | Behavior |
|---|---|---|
| Mobile | (default, no min-width) | Single column layouts, hamburger nav, stacked cards |
| Tablet | 640px | 2-column grids begin |
| Desktop | 1024px | Full multi-column layouts, side-by-side panels |
| Wide | 1280px | Max-width container caps at 1200px centered |

The existing `.public-main` constraint of `max-width: 1100px` should be increased to `max-width: 1200px` and a `--content-max-width: 1200px` CSS variable added for reuse.

Full-bleed sections (hero banners, stats band, testimonials band) must use `width: 100vw; margin-left: calc(-50vw + 50%);` to break out of the constrained content container, or be rendered as siblings to `.public-main` (preferred approach).

---

### 6.20 Acceptance Criteria — Visual (QA)

**AC-VI-1**: Given the public home page loads, when a user views it on a 1280px-wide viewport, then the hero section is at least 600px tall, contains a visible background image (not a broken img tag), has the hospital name, tagline, and two CTA buttons visible without scrolling.

**AC-VI-2**: Given the home page loads, when the stats band scrolls into view for the first time, then the numeric counters animate from 0 to their target values within approximately 1.5 seconds; subsequent scroll-away and scroll-back does not re-trigger the animation.

**AC-VI-3**: Given the departments page loads, when the user types "card" into the search input, then only department cards whose name or description contains "card" (case-insensitive) remain visible; all others are hidden. When the search is cleared, all departments reappear.

**AC-VI-4**: Given the public navigation bar is visible and the page is scrolled more than 10px, then the nav bar has a visible drop shadow (box-shadow) that was not present at scroll position 0.

**AC-VI-5**: Given a viewport width of 767px or less, when the public site header is rendered, then the navigation link list is hidden and a hamburger/menu icon button is visible. When the hamburger is clicked, the navigation links become visible in a dropdown. When an outside click or navigation occurs, the dropdown closes.

**AC-VI-6**: Given the login page is viewed on a viewport 1024px or wider, then the split-screen layout renders with a visible left panel image and the form in the right panel. On a viewport below 768px, the left panel image is not rendered and the form is full-width centered.

**AC-VI-7**: Given any page with data loading state, when the API call is pending, then a skeleton loader (animated shimmer bars) is shown in place of the content, not a plain "Loading…" text string.

**AC-VI-8**: Given a department card on the Departments page, when the user hovers over it with a pointing device, then the card visibly lifts (translateY) and shadow deepens within 200ms.

**AC-VI-9**: Given the About page loads, then the page contains a visible page hero banner with background image, a 3-card Mission/Vision/Values row, an image gallery of 6 facility photos, and a vertical timeline with at least 4 milestone entries.

**AC-VI-10**: Given the Contact page loads, then: (a) the emergency phone number is visually distinct from the general phone (different color — accent/red), (b) each contact info row has an icon, (c) the form has at least 48px-tall input fields, and (d) the submit button is full-width.

**AC-VI-11**: Given the authenticated app shell renders, then every sidebar nav item has a Lucide icon to the left of its text label.

**AC-VI-12**: Given no images are available (network off, image files missing), then all `<img>` tags with broken sources display gracefully — either the fallback gradient with initials (doctor photos) or the primary-color gradient fallback (department cards, blog cards) rather than a broken image icon.

---

### 6.21 Out of Scope — Visual (Additions to Section 4)

The following visual/UI items are explicitly excluded from this build:

- Dark mode / theme toggle.
- CSS-in-JS libraries (styled-components, Emotion) — all styles remain in `index.css` plus inline style props as already established.
- Animation libraries (Framer Motion, GSAP) — all animations use CSS transitions and native Web APIs (IntersectionObserver, requestAnimationFrame) only.
- Interactive maps (Google Maps, Leaflet, Mapbox) — a static image placeholder is used for the contact page map (VI-CONTACT-3).
- Video backgrounds or embedded video content.
- Image upload / crop UI for doctor profile photos or blog covers — photos are added by placing files on the filesystem and updating the path field via the existing Admin/Doctor edit forms (plain text path input).
- Carousel/slider libraries (Swiper, Slick) — testimonials use a CSS grid, not a slider.
- Design tokens exported to Figma or any design file format.
- Accessibility audit beyond semantic HTML, `alt` text on images, and visible focus indicators — a full WCAG 2.1 audit is out of scope for this build.

---

## 7. Real Images and Scroll Animations

Status: Draft v1.2 — added per client enhancement request.
Consumers: Frontend Developer (Chintu — primary owner for all work in this section), Solution Architect (Sagar — review CSS architecture for Section 7.2 before Chintu begins implementation).

---

### 7.1 Real Image Requirements

#### 7.1.1 Current State and Problem

The `src/frontend/public/images/` directory contains files with both `.jpg` and `.svg` extensions. Every file in both sets is an SVG placeholder graphic — colored rectangles with text labels — not a photograph. The frontend source code references these files using the `.svg` extension (e.g., `src="/images/hero-banner.svg"`). All SVG placeholder files must be replaced with real photographs sourced from Unsplash or Pexels. The SVG placeholder files (`.svg`) may be left in place or deleted after download; they will simply be unused.

#### 7.1.2 Source Licensing

All images must be sourced from:
- **Unsplash** (https://unsplash.com) — free for commercial and demo use under the Unsplash License. No attribution required. No API key required for direct CDN URL downloading.
- **Pexels** (https://www.pexels.com) — free for commercial and demo use under the Pexels License. No attribution required.

Do not use Google Images, Shutterstock, Getty, iStock, or any other source.

#### 7.1.3 File Format and Size Constraints

- **Format**: `.jpg` (JPEG). Save every file with the `.jpg` extension regardless of the codec the CDN returns. Browsers read the Content-Type header, not the filename extension, so this is safe.
- **Maximum file size**: 500 KB per image. If the raw download exceeds 500 KB, compress using Squoosh (https://squoosh.app) at MozJPEG quality 75–80 before saving.
- **Minimum visual quality**: the image must be a recognisable, real photograph — no blurry, extreme-crop, or near-solid-colour results.

#### 7.1.4 Code Reference Update Required

The existing frontend TypeScript source files reference images using the `.svg` extension. After downloading the real `.jpg` files, Chintu must also update the image `src` attributes in each affected component file. The table below lists every file and what must change.

| Source file | Change required |
|---|---|
| `src/frontend/src/pages/public/HomePage.tsx` | `DeptCardImage` component: `src="/images/dept-${deptSlug}.svg"` → `.jpg`; hero background `<img src="/images/hero-banner.svg"` → `hero-banner.jpg` (also see Section 7.2.4 — the hero will switch from `<img>` to CSS `backgroundImage` for the parallax effect) |
| `src/frontend/src/pages/public/AboutPage.tsx` | Hero: `src="/images/about-hero.svg"` → `.jpg`; `FACILITIES` array: all 6 `.svg` filenames → `.jpg` |
| `src/frontend/src/pages/public/DepartmentsPage.tsx` | `DeptCardImage` component: `src="/images/dept-${slug}.svg"` → `.jpg` |
| `src/frontend/src/pages/public/ContactPage.tsx` | `MapPlaceholder` component: `src="/images/map-placeholder.svg"` → `.jpg` |
| `src/frontend/src/pages/public/DepartmentDoctorsPage.tsx` | Page hero background image reference when hero is added (see Section 7.2.5) |
| `src/frontend/src/pages/public/BlogListPage.tsx` | Page hero background image reference when hero is added (see Section 7.2.5) |
| `src/frontend/src/pages/public/LoginPage.tsx` | Auth panel: `src="/images/auth-panel.svg"` → `.jpg` |
| `src/frontend/src/pages/public/SignupPage.tsx` | Auth panel: `src="/images/auth-panel.svg"` → `.jpg` |

A scoped find-and-replace of `/images/` + `.svg"` → `.jpg"` across all `.tsx` files will catch most cases. Chintu must verify after the replace that no Lucide icon imports or inline `<svg>` elements are accidentally affected — the replace scope is only strings inside image `src` attributes.

#### 7.1.5 Complete Image File List

Total: 28 image files. All must reside in `src/frontend/public/images/` (doctor photos in the `doctors/` subdirectory).

**Hero and page-level images — 6 files**

| Filename | Save dimensions (w × h px) | Subject |
|---|---|---|
| `hero-banner.jpg` | 1600 × 700 | Modern hospital building exterior, daytime, architectural |
| `about-hero.jpg` | 1400 × 400 | Hospital lobby interior, bright, modern, welcoming |
| `departments-hero.jpg` | 1400 × 400 | Diverse group of doctors in white coats |
| `blog-hero.jpg` | 1400 × 400 | Doctor reading a tablet or medical journal |
| `auth-panel.jpg` | 800 × 1000 | Friendly doctor or welcoming reception desk, warm lighting |
| `map-placeholder.jpg` | 800 × 300 | City map with location pin marker |

**Facility images — 6 files**

| Filename | Save dimensions | Subject |
|---|---|---|
| `facility-icu.jpg` | 600 × 300 | ICU patient room, modern medical equipment |
| `facility-er.jpg` | 600 × 300 | Emergency room corridor or trauma bay |
| `facility-lab.jpg` | 600 × 300 | Clinical laboratory technician at work |
| `facility-maternity.jpg` | 600 × 300 | Maternity ward, newborn, gentle lighting |
| `facility-outpatient.jpg` | 600 × 300 | Hospital waiting area, comfortable seating |
| `facility-pharmacy.jpg` | 600 × 300 | Hospital pharmacy counter |

**Department images — 11 files**

| Filename | Save dimensions | Subject |
|---|---|---|
| `dept-cardiology.jpg` | 600 × 250 | Heart monitor, ECG trace, or cardiologist at work |
| `dept-pediatrics.jpg` | 600 × 250 | Pediatrician with young child patient |
| `dept-orthopedics.jpg` | 600 × 250 | X-ray of bones or orthopedic procedure |
| `dept-neurology.jpg` | 600 × 250 | Brain scan on a light box or neurologist |
| `dept-oncology.jpg` | 600 × 250 | Cancer treatment, infusion therapy setup |
| `dept-radiology.jpg` | 600 × 250 | MRI scanner or radiology suite |
| `dept-emergency.jpg` | 600 × 250 | Ambulance bay or emergency room entrance |
| `dept-ophthalmology.jpg` | 600 × 250 | Eye examination with slit lamp |
| `dept-gynecology.jpg` | 600 × 250 | Women's health consultation |
| `dept-dermatology.jpg` | 600 × 250 | Dermatology consultation or skin examination |
| `dept-default.jpg` | 600 × 250 | Generic stethoscope or medical background |

**Doctor photos — 5 files**

| Filename | Save dimensions | Subject |
|---|---|---|
| `doctor-placeholder.jpg` | 400 × 400 | Generic doctor in white coat, neutral/fallback |
| `doctors/dr-1.jpg` | 400 × 400 | Female doctor, professional headshot, smiling |
| `doctors/dr-2.jpg` | 400 × 400 | Male doctor, professional headshot |
| `doctors/dr-3.jpg` | 400 × 400 | Female doctor, diverse, professional portrait |
| `doctors/dr-4.jpg` | 400 × 400 | Male doctor, professional portrait |

#### 7.1.6 Search URLs and Direct Download URLs

For each file, a primary direct Unsplash CDN URL is provided. If a direct URL returns a 404 or an HTML/SVG error response, use the search URL to find an equivalent photograph, then copy the Unsplash CDN URL from the photo's download link (format: `https://images.unsplash.com/photo-{id}?...`).

**Unsplash CDN URL format:**
`https://images.unsplash.com/photo-{photo-id}?w={width}&h={height}&fit=crop&auto=format&q=80`

`hero-banner.jpg`
- Direct: `https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=1600&h=700&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/hospital-building-exterior

`about-hero.jpg`
- Direct: `https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1400&h=400&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/hospital-lobby-interior

`departments-hero.jpg`
- Direct: `https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=1400&h=400&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/medical-team-doctors-group

`blog-hero.jpg`
- Direct: `https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1400&h=400&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/doctor-reading-tablet-medical

`auth-panel.jpg`
- Direct: `https://images.unsplash.com/photo-1551601651-2a8555f1a136?w=800&h=1000&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/friendly-doctor-reception-desk

`map-placeholder.jpg`
- Direct: `https://images.unsplash.com/photo-1524661135-423995f22d0b?w=800&h=300&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/city-map-location-pin

`facility-icu.jpg`
- Direct: `https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=600&h=300&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/intensive-care-unit-hospital

`facility-er.jpg`
- Direct: `https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=600&h=300&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/emergency-room-corridor

`facility-lab.jpg`
- Direct: `https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=600&h=300&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/clinical-laboratory-technician

`facility-maternity.jpg`
- Direct: `https://images.unsplash.com/photo-1555252333-9f8e92e65df9?w=600&h=300&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/maternity-ward-newborn

`facility-outpatient.jpg`
- Direct: `https://images.unsplash.com/photo-1519494080410-f9aa76cb4283?w=600&h=300&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/hospital-waiting-area

`facility-pharmacy.jpg`
- Direct: `https://images.unsplash.com/photo-1576671081837-49000212a370?w=600&h=300&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/hospital-pharmacy-counter

`dept-cardiology.jpg`
- Direct: `https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=600&h=250&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/cardiology-ecg-heart

`dept-pediatrics.jpg`
- Direct: `https://images.unsplash.com/photo-1579208575657-c595a05383b7?w=600&h=250&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/pediatrician-child-patient

`dept-orthopedics.jpg`
- Direct: `https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=600&h=250&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/orthopedics-xray-bone

`dept-neurology.jpg`
- Direct: `https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=600&h=250&fit=crop&auto=format&q=80`
- Note: if this resolves to an emergency-room image (same as `facility-er.jpg`), use the search URL to pick a distinct brain-scan or neurology photo.
- Search fallback: https://unsplash.com/s/photos/neurology-brain-scan-mri

`dept-oncology.jpg`
- Direct: `https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=600&h=250&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/oncology-cancer-treatment

`dept-radiology.jpg`
- Direct: `https://images.unsplash.com/photo-1516549655169-df83a0774514?w=600&h=250&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/mri-scanner-radiology

`dept-emergency.jpg`
- Direct: `https://images.unsplash.com/photo-1612531385446-f7e6d131e1d0?w=600&h=250&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/ambulance-emergency-hospital

`dept-ophthalmology.jpg`
- Direct: `https://images.unsplash.com/photo-1559685440-8b1b8abc21a2?w=600&h=250&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/eye-examination-ophthalmology

`dept-gynecology.jpg`
- Direct: `https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=600&h=250&fit=crop&auto=format&q=80`
- Note: if this resolves to the same photo as `dept-oncology.jpg`, use the search URL to pick a distinct women's health consultation photo.
- Search fallback: https://unsplash.com/s/photos/womens-health-consultation

`dept-dermatology.jpg`
- Direct: `https://images.unsplash.com/photo-1631815588090-d1bcbe9b26e0?w=600&h=250&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/dermatology-skin-examination

`dept-default.jpg`
- Direct: `https://images.unsplash.com/photo-1584515933487-779824d29309?w=600&h=250&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/stethoscope-doctor-medical

`doctor-placeholder.jpg` and `doctors/dr-1.jpg`
- Direct: `https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&h=400&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/female-doctor-headshot-portrait

`doctors/dr-2.jpg`
- Direct: `https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&h=400&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/male-doctor-headshot-professional

`doctors/dr-3.jpg`
- Direct: `https://images.unsplash.com/photo-1594824476967-48c8b964273f?w=400&h=400&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/woman-doctor-portrait-diverse

`doctors/dr-4.jpg`
- Direct: `https://images.unsplash.com/photo-1612349317150-e413f6a422ed?w=400&h=400&fit=crop&auto=format&q=80`
- Search fallback: https://unsplash.com/s/photos/male-doctor-professional-portrait

#### 7.1.7 All-in-One Download Script

Chintu must save the following as `download-images.ps1` in `src/frontend/public/images/` and run it once from a PowerShell terminal opened at that directory (`cd` to `src/frontend/public/images/` first, then run `.\download-images.ps1`).

```powershell
# Run from: src/frontend/public/images/
# Purpose: Download all 28 real photograph files from Unsplash CDN.

$images = @(
  @{ url = "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=1600&h=700&fit=crop&auto=format&q=80";  out = "hero-banner.jpg" },
  @{ url = "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1400&h=400&fit=crop&auto=format&q=80";  out = "about-hero.jpg" },
  @{ url = "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=1400&h=400&fit=crop&auto=format&q=80";  out = "departments-hero.jpg" },
  @{ url = "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1400&h=400&fit=crop&auto=format&q=80";  out = "blog-hero.jpg" },
  @{ url = "https://images.unsplash.com/photo-1551601651-2a8555f1a136?w=800&h=1000&fit=crop&auto=format&q=80";    out = "auth-panel.jpg" },
  @{ url = "https://images.unsplash.com/photo-1524661135-423995f22d0b?w=800&h=300&fit=crop&auto=format&q=80";     out = "map-placeholder.jpg" },
  @{ url = "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=600&h=300&fit=crop&auto=format&q=80";  out = "facility-icu.jpg" },
  @{ url = "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=600&h=300&fit=crop&auto=format&q=80";     out = "facility-er.jpg" },
  @{ url = "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=600&h=300&fit=crop&auto=format&q=80";  out = "facility-lab.jpg" },
  @{ url = "https://images.unsplash.com/photo-1555252333-9f8e92e65df9?w=600&h=300&fit=crop&auto=format&q=80";     out = "facility-maternity.jpg" },
  @{ url = "https://images.unsplash.com/photo-1519494080410-f9aa76cb4283?w=600&h=300&fit=crop&auto=format&q=80";  out = "facility-outpatient.jpg" },
  @{ url = "https://images.unsplash.com/photo-1576671081837-49000212a370?w=600&h=300&fit=crop&auto=format&q=80";  out = "facility-pharmacy.jpg" },
  @{ url = "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=600&h=250&fit=crop&auto=format&q=80";  out = "dept-cardiology.jpg" },
  @{ url = "https://images.unsplash.com/photo-1579208575657-c595a05383b7?w=600&h=250&fit=crop&auto=format&q=80";  out = "dept-pediatrics.jpg" },
  @{ url = "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=600&h=250&fit=crop&auto=format&q=80";     out = "dept-orthopedics.jpg" },
  @{ url = "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=600&h=250&fit=crop&auto=format&q=80";     out = "dept-neurology.jpg" },
  @{ url = "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=600&h=250&fit=crop&auto=format&q=80";  out = "dept-oncology.jpg" },
  @{ url = "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=600&h=250&fit=crop&auto=format&q=80";  out = "dept-radiology.jpg" },
  @{ url = "https://images.unsplash.com/photo-1612531385446-f7e6d131e1d0?w=600&h=250&fit=crop&auto=format&q=80";  out = "dept-emergency.jpg" },
  @{ url = "https://images.unsplash.com/photo-1559685440-8b1b8abc21a2?w=600&h=250&fit=crop&auto=format&q=80";     out = "dept-ophthalmology.jpg" },
  @{ url = "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=600&h=250&fit=crop&auto=format&q=80";  out = "dept-gynecology.jpg" },
  @{ url = "https://images.unsplash.com/photo-1631815588090-d1bcbe9b26e0?w=600&h=250&fit=crop&auto=format&q=80";  out = "dept-dermatology.jpg" },
  @{ url = "https://images.unsplash.com/photo-1584515933487-779824d29309?w=600&h=250&fit=crop&auto=format&q=80";  out = "dept-default.jpg" },
  @{ url = "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&h=400&fit=crop&auto=format&q=80";     out = "doctor-placeholder.jpg" },
  @{ url = "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&h=400&fit=crop&auto=format&q=80";     out = "doctors/dr-1.jpg" },
  @{ url = "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&h=400&fit=crop&auto=format&q=80";  out = "doctors/dr-2.jpg" },
  @{ url = "https://images.unsplash.com/photo-1594824476967-48c8b964273f?w=400&h=400&fit=crop&auto=format&q=80";  out = "doctors/dr-3.jpg" },
  @{ url = "https://images.unsplash.com/photo-1612349317150-e413f6a422ed?w=400&h=400&fit=crop&auto=format&q=80";  out = "doctors/dr-4.jpg" }
)

foreach ($img in $images) {
  Write-Host "Downloading $($img.out) ..."
  try {
    Invoke-WebRequest -Uri $img.url -OutFile $img.out -ErrorAction Stop
    $sizeKB = [math]::Round((Get-Item $img.out).Length / 1KB, 1)
    # Verify it is not an SVG/HTML error response
    $first4 = Get-Content $img.out -TotalCount 1 -ErrorAction SilentlyContinue
    if ($first4 -and $first4.TrimStart().StartsWith('<')) {
      Write-Warning "  WARNING: $($img.out) appears to contain HTML/SVG, not a photo. Replace manually using the search URL."
    } else {
      Write-Host "  OK — $sizeKB KB"
    }
  } catch {
    Write-Warning "  FAILED: $($_.Exception.Message). Use search URL to download manually."
  }
}
Write-Host "All done. Open each file in Windows Photos to verify it shows a real photograph."
```

After running the script, open each downloaded file in Windows Photos or a browser tab. Any file that displays as a coloured rectangle with text is still an SVG placeholder — that URL failed silently. For those files, open the corresponding search URL from Section 7.1.6, choose a suitable photograph, right-click the download button and copy the image address, then re-run the `Invoke-WebRequest` line for that single file with the new URL.

#### 7.1.8 Duplicate Photo Check

After downloading, visually verify that the following pairs (which share the same direct CDN URL in the script above and may produce identical images) are replaced with distinct photographs:
- `dept-neurology.jpg` vs `facility-er.jpg` — must be different subjects.
- `dept-oncology.jpg` vs `dept-gynecology.jpg` — must be different subjects.
- `doctor-placeholder.jpg` vs `doctors/dr-1.jpg` — may be the same image; this is acceptable for a demo, but if four doctor photos are all distinct it is preferable.

For any duplicate found, visit the relevant search URL from Section 7.1.6 and manually download a different photo.

---

### 7.2 Scroll Animation Requirements

#### 7.2.1 Technology Constraint (Restatement of Section 6.21)

All scroll animations must use CSS keyframes, CSS class toggling, `IntersectionObserver`, and `requestAnimationFrame` only. No external animation library — no AOS, GSAP, ScrollReveal, Framer Motion, Animate.css, or any other package — may be added. This is a firm constraint already established in Section 6.21.

#### 7.2.2 CSS Keyframes and Utility Classes

Add the following block to `src/frontend/src/index.css`, inside a clearly delimited comment block `/* === Scroll Animation Utilities === */`. This block must appear after the existing design token `:root` block and before the first component class.

**Keyframes:**

```css
/* === Scroll Animation Utilities === */

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-50px); }
  to   { opacity: 1; transform: translateX(0); }
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(50px); }
  to   { opacity: 1; transform: translateX(0); }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.94); }
  to   { opacity: 1; transform: scale(1); }
}

@keyframes expandUnderline {
  from { transform: scaleX(0); opacity: 0; }
  to   { transform: scaleX(1); opacity: 1; }
}
```

**Base utility classes** — elements start invisible; the `.animated` class triggers the animation:

```css
.scroll-fade-up,
.scroll-fade,
.scroll-slide-left,
.scroll-slide-right,
.scroll-scale-in {
  opacity: 0;
}

.scroll-fade-up.animated     { animation: fadeInUp    0.6s ease forwards; }
.scroll-fade.animated        { animation: fadeIn      0.5s ease forwards; }
.scroll-slide-left.animated  { animation: slideInLeft 0.6s ease forwards; }
.scroll-slide-right.animated { animation: slideInRight 0.6s ease forwards; }
.scroll-scale-in.animated    { animation: scaleIn     0.5s ease forwards; }
```

**Section underline expansion** (applied to `.section-underline` elements — see Section 7.2.6):

```css
.section-underline {
  transform-origin: left center;
}

.section-underline.animated {
  animation: expandUnderline 0.5s ease forwards;
  animation-delay: 0.15s;
}
```

**Stagger delay helpers** — add alongside any `.scroll-*` class on sibling elements:

```css
.anim-delay-1 { animation-delay: 0.1s; }
.anim-delay-2 { animation-delay: 0.2s; }
.anim-delay-3 { animation-delay: 0.3s; }
.anim-delay-4 { animation-delay: 0.4s; }
.anim-delay-5 { animation-delay: 0.5s; }
.anim-delay-6 { animation-delay: 0.6s; }
```

**Reduced-motion override** — this rule is mandatory and must immediately follow the utility classes:

```css
@media (prefers-reduced-motion: reduce) {
  .scroll-fade-up,
  .scroll-fade,
  .scroll-slide-left,
  .scroll-slide-right,
  .scroll-scale-in,
  .section-underline {
    opacity: 1 !important;
    transform: none !important;
    animation: none !important;
  }
}
```

#### 7.2.3 Shared Hooks

Create two new hook files in `src/frontend/src/hooks/`.

**`useScrollReveal.ts`** — for containers of multiple children.

Specification:
- Accepts `options?: { threshold?: number; stagger?: boolean }`. Default threshold: `0.15`. Default stagger: `false`.
- Returns a `ref` (React `RefObject<HTMLElement>`) to attach to the container element.
- On mount, creates an `IntersectionObserver` with the given threshold.
- When the observed container intersects, iterates over all direct child elements that have the attribute `data-scroll` set to any value, and adds `"animated"` to each child's `classList`.
- If `stagger: true`, also adds `anim-delay-{i+1}` (where i = 0-indexed position among `data-scroll` children, capped at index 5, so max class is `anim-delay-6`) to each child before adding `"animated"`.
- Calls `observer.disconnect()` after firing once. The animation never re-triggers.
- Cleans up the observer in the `useEffect` return function.

**`useSingleScrollReveal.ts`** — for animating a single element.

Specification:
- Accepts `threshold?: number` (default `0.15`).
- Returns a `ref` to attach to a single element.
- When that element intersects, adds `"animated"` to its `classList` and disconnects the observer.
- Cleans up on unmount.

Usage pattern in a component:

```tsx
// Container with staggered children
const containerRef = useScrollReveal({ stagger: true });
return (
  <div ref={containerRef} className="grid-3-up">
    <div data-scroll className="card scroll-scale-in">...</div>
    <div data-scroll className="card scroll-scale-in">...</div>
    <div data-scroll className="card scroll-scale-in">...</div>
  </div>
);

// Single element
const headingRef = useSingleScrollReveal();
return <h2 ref={headingRef} className="scroll-fade-up">Our Departments</h2>;
```

#### 7.2.4 Hero Parallax Effect (Home Page Only)

The hero section in `HomePage.tsx` currently uses an `<img>` tag as the background image. To enable the parallax effect, replace the `<img>` background approach with a CSS `backgroundImage` on the `<section>` element directly, as follows:

- Remove the `<img src="/images/hero-banner.svg" ...>` element from the hero `<section>`.
- Add to the hero `<section>` inline styles: `backgroundImage: "url('/images/hero-banner.jpg')"`, `backgroundSize: 'cover'`, `backgroundPosition: 'center top'`, `willChange: 'background-position'`.
- Keep the existing gradient overlay `<div>` with `position: absolute; inset: 0` and the gradient value unchanged.

Inside `HomePage`, add a `useEffect` (no dependency array — runs on mount) that:

1. Checks `window.innerWidth >= 768`. If below 768px, does nothing (no parallax on mobile).
2. Gets a reference to the hero `<section>` element via a `useRef`.
3. Adds a `scroll` event listener to `window` using `requestAnimationFrame` throttling:
   ```typescript
   let ticking = false;
   function onScroll() {
     if (!ticking) {
       requestAnimationFrame(() => {
         if (heroRef.current) {
           heroRef.current.style.backgroundPositionY = `${window.scrollY * 0.4}px`;
         }
         ticking = false;
       });
       ticking = true;
     }
   }
   window.addEventListener('scroll', onScroll, { passive: true });
   return () => window.removeEventListener('scroll', onScroll);
   ```
4. Does not apply parallax if `window.matchMedia('(prefers-reduced-motion: reduce)').matches` is true.

This is the only page that receives a parallax effect. No other page hero uses parallax.

#### 7.2.5 Page-by-Page Animation Assignments

The following tables define exactly which CSS class goes on which element on each public page. Chintu must implement each row. "On mount" means the element is visible above the fold and must be animated by adding `"animated"` via `setTimeout` (300ms delay) inside a `useEffect`, not via `IntersectionObserver` (which would never fire for above-fold content). All other rows use `IntersectionObserver` via the hooks in Section 7.2.3.

---

**Home Page (`HomePage.tsx`)**

| Element / Section | CSS class(es) | Trigger | Notes |
|---|---|---|---|
| Hero h1 | `scroll-fade-up` | On mount, 300ms delay | Above fold; add `animated` via setTimeout |
| Hero tagline `<p>` | `scroll-fade-up anim-delay-1` | On mount, 300ms delay | |
| Hero CTA buttons container | `scroll-fade-up anim-delay-2` | On mount, 300ms delay | |
| Each `StatItem` in `StatsBand` | `scroll-fade-up` + stagger delays 1–4 | Existing IntersectionObserver in `StatsBand`; add class toggle alongside `setTriggered(true)` | Do not replace the existing counter logic; add the CSS class toggle to the same observer callback |
| "Why Choose Us" section `<h2>` | `scroll-fade-up` | `useSingleScrollReveal` | |
| "Why Choose Us" `.section-underline` | `section-underline` | Same observer as h2 | Add `animated` to underline div when h2 observer fires |
| "Why Choose Us" card grid container | `useScrollReveal({ stagger: true })` ref | — | Each card `<div>` gets `data-scroll` attribute and `scroll-scale-in` class |
| "Our Departments" section `<h2>` | `scroll-fade-up` | `useSingleScrollReveal` | |
| "Our Departments" `.section-underline` | `section-underline` | Same observer | |
| "Our Departments" card grid container | `useScrollReveal({ stagger: true })` ref | — | Each card link wrapper gets `data-scroll` + `scroll-fade-up` |
| "Meet Our Specialists" section `<h2>` | `scroll-fade-up` | `useSingleScrollReveal` | |
| "Meet Our Specialists" `.section-underline` | `section-underline` | Same observer | |
| "Meet Our Specialists" scrollable row container | `useScrollReveal({ stagger: true })` ref | — | Each doctor card `<div>` gets `data-scroll` + `scroll-scale-in` |
| "What Our Patients Say" section `<h2>` | `scroll-fade-up` | `useSingleScrollReveal` | |
| Testimonial card 1 | `scroll-slide-left` | `useSingleScrollReveal` | |
| Testimonial card 2 | `scroll-fade-up` | `useSingleScrollReveal` | |
| Testimonial card 3 | `scroll-slide-right` | `useSingleScrollReveal` | |
| "Health Tips & News" section `<h2>` | `scroll-fade-up` | `useSingleScrollReveal` | |
| Blog article card grid container (`RecentBlogSection`) | `useScrollReveal({ stagger: true })` ref | — | Each card link wrapper gets `data-scroll` + `scroll-fade-up` |

---

**About Page (`AboutPage.tsx`)**

| Element / Section | CSS class(es) | Trigger | Notes |
|---|---|---|---|
| Hero `<h1>` | `scroll-fade-up` | On mount, 200ms delay | Above fold |
| Hero subtitle `<p>` | `scroll-fade-up anim-delay-1` | On mount, 200ms delay | |
| "Our Purpose" `<h2>` | `scroll-fade-up` | `useSingleScrollReveal` | |
| "Our Purpose" `.section-underline` | `section-underline` | Same observer | |
| Mission/Vision/Values card grid | `useScrollReveal({ stagger: true })` ref | — | Each card `<div>` gets `data-scroll` + `scroll-scale-in anim-delay-{1,2,3}` |
| "Our Facilities" `<h2>` | `scroll-fade-up` | `useSingleScrollReveal` | |
| "Our Facilities" `.section-underline` | `section-underline` | Same observer | |
| Facility photo grid | `useScrollReveal({ stagger: true })` ref | — | Each `<FacilityImg>` wrapper gets `data-scroll` + `scroll-fade-up` |
| "Accreditations" `<h2>` | `scroll-fade-up` | `useSingleScrollReveal` | |
| Accreditation badge flex container | `useScrollReveal({ stagger: true })` ref | — | Each badge `<div>` gets `data-scroll` + `scroll-scale-in` |
| "Our History" `<h2>` | `scroll-fade-up` | `useSingleScrollReveal` | |
| Each timeline card (left-aligned, even index) | `scroll-slide-left` | `useSingleScrollReveal` per card | Apply `useSingleScrollReveal` inside the `Timeline` component per milestone card |
| Each timeline card (right-aligned, odd index) | `scroll-slide-right` | `useSingleScrollReveal` per card | |

---

**Departments Page (`DepartmentsPage.tsx`)**

| Element / Section | CSS class(es) | Trigger | Notes |
|---|---|---|---|
| Hero `<h1>` | `scroll-fade-up` | On mount, 200ms delay | |
| Hero subtitle | `scroll-fade-up anim-delay-1` | On mount, 200ms delay | |
| Search input wrapper | `scroll-fade` | `useSingleScrollReveal({ threshold: 0.5 })` | Gentle fade |
| Department card grid container | `useScrollReveal({ stagger: true })` ref | — | Each card link wrapper gets `data-scroll` + `scroll-fade-up`; stagger caps at 6 — do not apply delay beyond `anim-delay-6` for cards beyond index 5 |

---

**Contact Page (`ContactPage.tsx`)**

The contact page currently has no page hero. Add a 200px full-width hero above the two-column content layout, matching the `page-hero` pattern used on About and Departments pages. Background image: `/images/departments-hero.jpg` (reuse). Overlay `rgba(9,107,93,0.75)`. Centered white text: "Contact Us" as `<h1>`, "We're here to help" as subtitle `<p>`.

| Element / Section | CSS class(es) | Trigger | Notes |
|---|---|---|---|
| Hero `<h1>` "Contact Us" | `scroll-fade-up` | On mount, 200ms delay | |
| Hero subtitle | `scroll-fade-up anim-delay-1` | On mount, 200ms delay | |
| Left column wrapper | `scroll-slide-left` | `useSingleScrollReveal` | The entire left column slides in from left |
| Each contact info row (4 rows) within left column | `scroll-fade-up anim-delay-{1,2,3,4}` | After left column observer fires, add `animated` to each row with staggered delays via `useScrollReveal({ stagger: true })` on the info container | |
| Map placeholder | `scroll-fade` | `useSingleScrollReveal` | |
| Right column (form card) | `scroll-slide-right` | `useSingleScrollReveal` | Entire form card slides in from right; threshold 0.2 |

---

**Blog List Page (`BlogListPage.tsx`)**

| Element / Section | CSS class(es) | Trigger | Notes |
|---|---|---|---|
| Hero `<h1>` | `scroll-fade-up` | On mount, 200ms delay | The blog list page already has a hero per VI-BLOG-1 |
| Hero subtitle | `scroll-fade-up anim-delay-1` | On mount, 200ms delay | |
| Article card grid container | `useScrollReveal({ stagger: true })` ref | — | Each card link wrapper gets `data-scroll` + `scroll-fade-up` |

---

**Department Doctors Page (`DepartmentDoctorsPage.tsx`)**

| Element / Section | CSS class(es) | Trigger | Notes |
|---|---|---|---|
| Hero `<h1>` (department name) | `scroll-fade-up` | On mount, 200ms delay | |
| Hero subtitle | `scroll-fade-up anim-delay-1` | On mount, 200ms delay | |
| Doctor card grid container | `useScrollReveal({ stagger: true })` ref | — | Each doctor card `<div>` gets `data-scroll` + `scroll-scale-in` |

---

**Doctor Profile Page (`DoctorProfilePage.tsx`)**

| Element / Section | CSS class(es) | Trigger | Notes |
|---|---|---|---|
| Left column (photo + dept badge) | `scroll-slide-left` | `useSingleScrollReveal` | |
| Right column (name, bio, details) | `scroll-slide-right` | `useSingleScrollReveal` | |
| "Book an Appointment" CTA strip | `scroll-fade-up` | `useSingleScrollReveal` | |

---

**Blog Article Page (`BlogArticlePage.tsx`)**

| Element / Section | CSS class(es) | Trigger | Notes |
|---|---|---|---|
| Article header image/gradient block | `scroll-fade` | On mount, 150ms delay | Full-width header; gentle fade in on load |
| Article meta row (author, date, read time) | `scroll-fade-up` | `useSingleScrollReveal` | |
| Article body `<div>` | No animation | — | Body text must never animate; content must be immediately readable. This is an explicit exclusion. |

#### 7.2.6 Section Header Reveal Pattern (All Pages)

Every `<div className="section-header">` block on every public page contains an `<h2>` and a `<div className="section-underline" />`. The reveal pattern is:

1. Attach `useSingleScrollReveal` to the `.section-header` container `<div>`.
2. When the observer fires, add `"animated"` to the `<h2>` (class `scroll-fade-up`) and to the `.section-underline` div (class `section-underline`) in the same callback.
3. The CSS `animation-delay: 0.15s` on `.section-underline.animated` means the underline expands 150ms after the h2 fades in.

Since the `.section-header` pattern is used on every public page and authenticated dashboard, create a wrapper component `src/frontend/src/components/SectionHeader.tsx` that encapsulates this behaviour, accepting `title: string` and optionally `subtitle?: string` as props. This avoids duplicating the observer logic across 10+ page files.

`SectionHeader` component spec:
- Renders a `<div className="section-header">` container.
- Inside: `<h2 className="scroll-fade-up">` and `<div className="section-underline">`.
- Uses `useSingleScrollReveal` internally on the container div.
- On intersection, adds `"animated"` to both children.
- If `subtitle` is provided, renders a `<p>` below the underline with `scroll-fade-up anim-delay-1`.

#### 7.2.7 Counter Animation Verification Checklist

The stats counter in `StatsBand` on the Home page already implements IntersectionObserver + requestAnimationFrame. Chintu must verify each of the following points by inspection of the existing code before adding scroll classes, and fix anything that fails:

- The observer calls `obs.disconnect()` after the first intersection. (Existing code at line 102 of `HomePage.tsx` — confirmed correct.)
- The `animatedRef.current` boolean prevents re-animation on scroll-back. (Existing code at line 69 — confirmed correct.)
- The `scroll-fade-up` class is added to each `StatItem` wrapper div at the same moment `setTriggered(true)` is called, so the counter animation and the fade-in fire simultaneously.
- The `StatsBand` element starts with `opacity: 0` on the items (via the `scroll-fade-up` class) and becomes visible when `animated` is added.

If both the counter trigger and CSS class add are not happening in the same IntersectionObserver callback, consolidate them into one callback.

---

### 7.3 Acceptance Criteria — Images and Animations (QA)

**AC-IMG-1**: Given the public site loads with network access, when any page with a hero background image is viewed, then the hero section displays a real photograph (not an SVG rectangle or broken-image icon). Verify by inspecting the rendered `<img>` or `background-image` — the source must be a `.jpg` file from `/images/` that is a recognisable photographic image.

**AC-IMG-2**: Given the About page loads, when the "Our Facilities" gallery section is visible, then each of the 6 facility images renders as a real photograph. No facility image may be a solid-colour placeholder or SVG.

**AC-IMG-3**: Given the Departments page loads, when the department cards are visible, then each card's top image area shows a real photograph relevant to that department's subject. Where no department-specific photo exists, `dept-default.jpg` is shown — this must also be a real photograph (a stethoscope or medical image), not an SVG.

**AC-IMG-4**: Given a doctor record has a `profile_photo_path` value pointing to a file in `/images/doctors/`, when that doctor's card or profile page is viewed, then the circular photo area shows the real headshot photograph, not the initials fallback gradient.

**AC-IMG-5**: Given any image file is missing or returns an error (simulated by renaming a file), when the page renders, then the graceful fallback (gradient with initials for doctor photos; primary-color gradient with icon for department/blog cards) is shown — not a broken-image browser icon.

**AC-ANIM-1**: Given the Home page loads on a desktop viewport (>= 1024px), when the "Why Choose Us" section scrolls into view, then all 6 feature cards become visible via a staggered scale-in animation. Each card's animation begins approximately 100ms after the previous card's animation.

**AC-ANIM-2**: Given the About page loads, when the History timeline section scrolls into view, then even-indexed (left-aligned) timeline cards animate in from the left and odd-indexed (right-aligned) cards animate in from the right. Each card animates independently as it enters the viewport — they do not all fire at once.

**AC-ANIM-3**: Given the Contact page loads, when the two-column contact layout enters the viewport, then the left column (contact info cards) slides in from the left side and the right column (contact form) slides in from the right side simultaneously, creating a split-reveal effect.

**AC-ANIM-4**: Given the Home page hero is visible on a desktop viewport (>= 768px), when the user scrolls the page downward by 200px, then the hero background image has visibly shifted upward relative to its initial position — demonstrating the parallax depth effect.

**AC-ANIM-5**: Given a section with a `.section-header` block scrolls into view, when the `<h2>` fade-in begins, then approximately 150ms later the colored underline bar expands from left to right (width grows from 0 to full). The expansion must be visibly smooth, not instant.

**AC-ANIM-6**: Given any public page is viewed in a browser or OS with `prefers-reduced-motion: reduce` enabled (set via Windows Settings > Accessibility > Visual Effects > Animation effects = Off, or via browser developer tools), then no scroll animations occur. All page content is fully visible and in its final position immediately on page load, with no fade-in, slide-in, or scale-in effects.

**AC-ANIM-7**: Given the Home page hero loads, when the page renders (no scrolling required), then the hero heading, tagline, and CTA buttons are fully visible within 1 second of the page loading. The hero content must not be invisible or partially transparent on initial page load.

**AC-ANIM-8**: Given any animated section has fired its scroll animation once, when the user scrolls back up and then scrolls down through that section again, then the elements remain in their final (fully visible) animated state and the animation does not replay.

**AC-ANIM-9**: Given the Blog Article page is loaded and the article body is in view, then the article body text is immediately visible with no animation delay. There must be no fade-in, slide-in, or opacity transition on the article body `<div>` or its children.

**AC-ANIM-10**: Given the stats counter band on the Home page scrolls into view, when the IntersectionObserver fires, then both the numeric counter animation (0 to target value over 1.5 seconds) and the fade-up reveal of each stat item begin simultaneously. The stat items must not be invisible while the counter is counting.

---

### 7.4 Out of Scope — Images and Animations (Additions to Section 4)

- Lazy loading of images beyond the browser's native `loading="lazy"` attribute — no custom lazy-load library.
- Image CDN or optimised delivery pipeline (Cloudinary, Imgix, Next.js Image component) — images are served as static files from Vite's public directory.
- Animated page transitions between routes (e.g., fade-out current page, fade-in next page) — only within-page scroll animations are in scope.
- Scroll progress indicators (e.g., a progress bar at the top showing how far down the article the user has scrolled).
- Animated SVG illustrations — all animations use real photographs and CSS keyframes only.
- Skeleton loaders for images specifically — the existing `SkeletonBlock` component (Section 6.17) handles data loading, not image loading. Image loading uses the native browser placeholder until the photo loads.
- Infinite scroll or pagination animation for blog or department lists.

---

## 8. Billing Specialist Role, Performance, Email Notifications, and Portal UI

Status: Draft v1.3 — added per client requirements block.
Consumers: Solution Architect (Sagar — primary), Backend Developer (Pavan), Frontend Developer (Chintu).

---

### 8.1 New Role: BillingSpecialist

#### 8.1.1 Role Overview

`BillingSpecialist` is the sixth system role, distinct from all existing roles. It is not a subset of Staff or Admin. Its sole function is financial: creating, editing, and tracking patient invoices. It has no clinical read or write access whatsoever.

**JWT role claim value:** `BillingSpecialist` (exact casing, no spaces). The frontend must branch on this string to render the Billing Specialist portal. No view, page, or component from any other role's portal is shared with this role.

#### 8.1.2 Account Creation

- BILL-ROLE-1: BillingSpecialist accounts are created exclusively by an Admin via the existing user-management flow (ADM-1). The role enum in the `users` table must be extended from `Admin/Doctor/Patient/Staff/Lab` to `Admin/Doctor/Patient/Staff/Lab/BillingSpecialist`.
- BILL-ROLE-2: BillingSpecialist accounts cannot be self-registered via the public signup page. Any attempt to POST to `/auth/signup` with `role=BillingSpecialist` must be rejected with 400 Bad Request (same rule already enforced for Doctor/Staff/Lab/Admin).
- BILL-ROLE-3: A BillingSpecialist profile entity is required. Add a `BillingSpecialist` table: `billing_specialist_id` (PK), `user_id` (FK, UNIQUE, references `users`), `employee_id` (nullable text, for internal HR reference), `created_at`.

#### 8.1.3 Capabilities — What BillingSpecialist Can Do

- BILL-1: As a BillingSpecialist, I can view all invoices across all patients (read access — full list with filtering and search, not limited by patient ownership).
- BILL-2: As a BillingSpecialist, I can create a new invoice for any patient, linked optionally to an appointment.
- BILL-3: As a BillingSpecialist, I can edit an existing invoice: update line items, total amount, status (Pending / Paid / Waived), due date, and the `has_insurance_claim` flag.
- BILL-4: As a BillingSpecialist, I can delete an invoice, subject to the constraint that only invoices with status `Pending` may be deleted. Paid or Waived invoices cannot be deleted (they are financial records and must be retained).
- BILL-5: As a BillingSpecialist, I can read patient demographic information — specifically: full name, date of birth, phone number, email address — sufficient to identify the patient and confirm billing details. This is read-only.
- BILL-6: As a BillingSpecialist, I can read appointment records across all patients — specifically: appointment date/time, doctor name, department, and appointment status — sufficient to link an invoice to a clinical event. This is read-only.
- BILL-7: As a BillingSpecialist, I can view the email notification log for invoice status-change notifications (see 8.3) via `GET /billing/notifications`.
- BILL-8: As a BillingSpecialist, I can manually trigger a re-send of an invoice notification for a specific invoice via the "Resend Notification" action in the ledger (see 8.4). This writes a new `email_notifications` entry (file-sink delivery, same as automatic notifications).

#### 8.1.4 Capabilities — What BillingSpecialist Cannot Do

- BILL-DENY-1: A BillingSpecialist cannot read or write `visit_notes`, `medical_records`, `prescriptions`, `lab_orders`, or `lab_results` tables. Any request to endpoints under `/doctor/*`, `/patients/*/records`, `/patients/*/prescriptions`, `/lab/*` returns 403 Forbidden.
- BILL-DENY-2: A BillingSpecialist cannot create, edit, deactivate, or role-assign user accounts. Any request to `/admin/users/*` (create/edit/delete/role-change) returns 403 Forbidden.
- BILL-DENY-3: A BillingSpecialist cannot create, edit, or deactivate Department records. Any write request to `/admin/departments/*` returns 403 Forbidden. Read access to `/public/departments` is allowed (public endpoint, no restriction).
- BILL-DENY-4: A BillingSpecialist cannot access the Admin dashboard metrics endpoint (`GET /admin/dashboard`), the audit log (`GET /admin/audit-log`), or any `/admin/*` read endpoints. All return 403 Forbidden.
- BILL-DENY-5: A BillingSpecialist cannot read or write blog articles or contact form messages. Requests to `/admin/blog/*` or `/admin/contact-messages/*` return 403 Forbidden.
- BILL-DENY-6: A BillingSpecialist cannot change their own role or activation status.

---

### 8.2 System Capacity and Performance (4,000+ Patients)

This section defines the indexing, pagination, and consistency requirements needed to keep the system responsive at a data volume of 4,000+ patient records and their associated clinical and billing data.

#### 8.2.1 Database Index Requirements

The following indexes must be defined in the database schema (SQLite `CREATE INDEX` statements, or equivalent migration). Fields already covered by `UNIQUE` constraints carry an implicit index in SQLite and do not need a separate `CREATE INDEX`. The "Verify" note indicates the architect must confirm the index exists in the current schema before adding a duplicate.

| Table | Column(s) | Index type | Action |
|---|---|---|---|
| `invoices` | `patient_id` | Non-unique | Add |
| `invoices` | `status` | Non-unique | Add |
| `invoices` | `created_at` | Non-unique | Add |
| `invoices` | `has_insurance_claim` | Non-unique | Add (new field, see 8.4.2) |
| `appointments` | `scheduled_at` | Non-unique | Add |
| `appointments` | `created_at` | Non-unique | Add |
| `patients` | `user_id` | Unique | Verify (already UNIQUE per 3.4 entity — confirm index exists) |
| `users` | `email` | Unique | Verify (already UNIQUE per 3.4 — confirm index exists) |
| `visit_notes` | `created_at` | Non-unique | Add |
| `prescriptions` | `created_at` | Non-unique | Add |
| `lab_orders` | `created_at` | Non-unique | Add |
| `lab_results` | `created_at` | Non-unique | Add |
| `blog_articles` | `published_at` | Non-unique | Add |
| `contact_messages` | `created_at` | Non-unique | Add |
| `email_notifications` | `recipient_user_id` | Non-unique | Add (new table, see 8.3.3) |
| `email_notifications` | `created_at` (map to `sent_at`) | Non-unique | Add (new table) |

Sagar must document all `CREATE INDEX` statements in the data dictionary (`docs/data-dictionary.md`) alongside the schema changes for 8.1 and 8.4.

#### 8.2.2 Server-Side Pagination

Every list endpoint that can return more than 50 rows must support server-side pagination. No list endpoint may return an unbounded result set.

**Query parameter contract:**
- `?page=N` — 1-indexed page number. Default: `1`. Requests for `page=0` or negative values return 400 Bad Request.
- `?page_size=M` — number of items per page. Default: `20`. Maximum: `100`. Requests for `page_size` above 100 are silently clamped to 100. Requests for `page_size=0` or negative values return 400 Bad Request.

**Response envelope — all paginated endpoints must return exactly this shape:**
```json
{
  "items": [ /* array of result objects */ ],
  "total": 4217,
  "page": 1,
  "page_size": 20,
  "total_pages": 211
}
```
`total_pages` is computed as `ceil(total / page_size)`. If `total` is 0, `total_pages` is 0.

**Affected endpoints (minimum required set):**

| Endpoint | Role(s) |
|---|---|
| `GET /admin/users` | Admin |
| `GET /admin/appointments` | Admin |
| `GET /admin/invoices` | Admin |
| `GET /patients/me/appointments` | Patient |
| `GET /patients/me/records` | Patient |
| `GET /patients/me/invoices` | Patient |
| `GET /doctor/appointments` | Doctor |
| `GET /billing/invoices` | BillingSpecialist |
| `GET /billing/notifications` | BillingSpecialist |
| `GET /lab/orders` | Lab |
| `GET /staff/appointments` | Staff |
| `GET /public/blog` | Public (no auth) |
| `GET /public/doctors` | Public (no auth) |

**Frontend pagination requirement:**
Every list component bound to a paginated endpoint must render the existing `Pager` component located at `src/frontend/src/components/Pager.tsx`. Chintu must not implement custom pagination UI for any of these views — always use the shared component. The `Pager` component must receive: `page`, `totalPages`, and an `onPageChange` callback.

#### 8.2.3 Cross-Profile Data Consistency

The following consistency guarantees are server-side and must be enforced at the database query level, not via application-layer caching.

- PERF-CONS-1: When an invoice is updated (any field change: status, amount, line items, `has_insurance_claim`), the next `GET` request to any endpoint that returns that invoice (admin, billing, patient views) must reflect the updated values. No application-layer response caching is permitted on invoice endpoints. (SQLite does not have query caching by default; this rule is a reminder not to add one at the FastAPI layer without cache invalidation.)
- PERF-CONS-2: When a patient's profile is updated (name, phone, email via `PUT /patients/me/profile` or `PUT /admin/users/{id}`), any endpoint that joins patient data into invoice responses (e.g., the billing ledger patient name column) must return the updated patient name on the next request. Invoice records themselves do not store a denormalized patient name — they store `patient_id` (FK) and the patient name is always resolved by join at query time.
- PERF-CONS-3: Real-time WebSocket push for UI updates is explicitly out of scope (see Section 4). Standard HTTP request-response is sufficient. "On next load" means on the next page load or API call, not within an already-loaded page without user action.

#### 8.2.4 JWT Payload Extension

The current JWT payload contains only `sub` (user_id) and `role`. This is insufficient for the sidebar user block (VI-SHELL-3) which needs to display the user's full name and role without making an additional API call on every page load.

**New required JWT payload fields:**

| Claim | Type | Value |
|---|---|---|
| `sub` | string | `user_id` (already present) |
| `role` | string | Role enum value (already present) |
| `email` | string | User's email address |
| `full_name` | string | User's `full_name` from the `users` table |
| `exp` | integer | Unix epoch expiry timestamp (already present) |

**Backend change (Pavan):** The `create_access_token` function must be updated to include `email` and `full_name` in the token payload when issuing tokens on login or token refresh. No other endpoints need to change.

**Frontend change (Chintu):** The `AuthContext` (location: `src/frontend/src/contexts/AuthContext.tsx` or equivalent) must be updated to decode the JWT on login and store `email` and `full_name` alongside `role` and `user_id`. The sidebar user block and topbar display name must read from `AuthContext` state, not from a separate `/users/me` API call.

---

### 8.3 Automated Invoice Email Notifications

#### 8.3.1 Trigger

Whenever an invoice's `status` field changes — regardless of which role makes the change (BillingSpecialist, Admin, or Staff) — the system must generate an email notification addressed to the patient who owns the invoice.

Trigger conditions:
- `Pending` → `Paid`
- `Pending` → `Waived`
- Any other status transition that may be added in future (the handler checks for any `status` field change, not a specific set of transitions)
- Manual re-trigger via `POST /billing/invoices/{invoice_id}/resend-notification` (BillingSpecialist only)

#### 8.3.2 Delivery Implementation (File-Sink)

Real email delivery via SMTP or external provider is out of scope per Section 4. The email notification infrastructure must be built completely, but delivery is replaced with a local file-based sink:

- NOTIFY-1: When a notification is triggered, write the complete HTML email body to a file at: `uploads/email_log/{timestamp}_{patient_id}_invoice_{invoice_id}.html`. `{timestamp}` is formatted as `YYYYMMDD_HHMMSS` (UTC). The `uploads/email_log/` directory must be created at startup if it does not exist.
- NOTIFY-2: The notification handler runs synchronously within the invoice update request. There is no background task queue, Celery worker, or async job. The file write completes before the HTTP 200 response is returned to the caller.
- NOTIFY-3: If the file write fails (e.g., disk permission error), the invoice update must still succeed and commit to the database. The notification failure is recorded in `email_notifications.status = 'Failed'` but must not roll back the invoice change. The error is logged server-side.

#### 8.3.3 HTML Email Content

The HTML file written to the file sink must be a self-contained, fully inline-styled HTML document. No external CSS stylesheets or web fonts are referenced. All styles are applied as `style="..."` attributes on individual elements.

Required content sections (in order, top to bottom):
1. **Header**: Hospital logo text ("Green Valley Hospital" in a teal `#0e8a7a` rectangular header bar), centered, white text, 28px bold. No external image — text only.
2. **Greeting**: "Dear {patient.full_name}," in 16px dark text.
3. **Body paragraph**: "This is a notification regarding Invoice #{invoice_id} on your account. The status of your invoice has been updated."
4. **Status change block**: Two-row table or labeled section: "Previous Status: {old_status}" | "New Status: {new_status}". Status values are styled with inline background badges matching the CSS badge colors defined in 8.4.3 (Pending = amber `#fef3c7` background `#b7791f` text; Paid = green `#d1fae5` background `#1e8e5a` text; Waived = grey `#f3f4f6` background `#536560` text).
5. **Invoice summary row**: "Invoice Amount: {formatted total_amount}" and "Due Date: {due_date if set, else 'On receipt'}".
6. **Call-to-action button**: A centered link-styled button (inline `<a>` with `style="background:#0e8a7a; color:#fff; padding:12px 28px; border-radius:6px; text-decoration:none; font-weight:600; display:inline-block;"`) labeled "View Your Invoice". The `href` value is `#` for the demo (no deep-link URL is in scope).
7. **Footer**: Divider line, then "Green Valley Hospital | 123 Green Valley Drive, Medical District | Emergency: +1 (555) 000-9999 | info@greenvalleyhospital.demo" in 12px muted grey. Below that: "This is an automated notification. Please do not reply to this message."

#### 8.3.4 EmailNotification Data Entity

Add a new `email_notifications` table with the following columns:

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `notification_id` | INTEGER | PK, AUTOINCREMENT | |
| `recipient_user_id` | INTEGER | FK → `users.user_id`, NOT NULL | The patient's user_id |
| `subject` | TEXT | NOT NULL | e.g., "Invoice #42 Status Update — Green Valley Hospital" |
| `body_html` | TEXT | NOT NULL | Full HTML string (same content written to file) |
| `sent_at` | TEXT | NOT NULL | ISO 8601 UTC timestamp |
| `trigger_event` | TEXT | NOT NULL | Enum-like: `invoice_status_change`, `manual_resend` |
| `related_invoice_id` | INTEGER | FK → `invoices.invoice_id`, nullable | NULL only for non-invoice notifications (future-proofing) |
| `status` | TEXT | NOT NULL, CHECK IN ('Queued','Sent','Failed') | `Sent` = file written successfully; `Failed` = file write failed |

The `body_html` column stores the full HTML so the notification log can display a preview in the UI without re-reading the file. The file in `uploads/email_log/` is the delivery artifact; the database row is the audit record.

#### 8.3.5 Notification Log Endpoint

- `GET /billing/notifications` — accessible to BillingSpecialist and Admin only (Staff, Doctor, Patient, Lab receive 403).
- Returns paginated `email_notifications` rows in descending `sent_at` order.
- Response items include: `notification_id`, `recipient_user_id`, `recipient_name` (joined from `users.full_name`), `subject`, `sent_at`, `trigger_event`, `related_invoice_id`, `status`. The `body_html` field is excluded from list responses to keep payload size manageable.
- `GET /billing/notifications/{notification_id}` — returns the full record including `body_html`.

---

### 8.4 Billing Specialist Dashboard and Portal UI

#### 8.4.1 Portal Shell

The BillingSpecialist portal uses the existing `AppShell` layout (sidebar + topbar) identical in structure to the Admin, Doctor, Patient, Staff, and Lab portals. The shell is not rebuilt — the same CSS classes and layout components are reused.

The sidebar nav for BillingSpecialist contains exactly four items and no others:

| Nav item label | Lucide icon | Route |
|---|---|---|
| Overview | `LayoutDashboard` | `/billing` |
| Invoices | `Receipt` | `/billing/invoices` |
| Claims | `FileCheck` | `/billing/claims` |
| Records | `FileText` | `/billing/records` |

The `Claims` page is a filtered view of `GET /billing/invoices?has_insurance_claim=1`. The `Records` page is a read-only view of patient demographic records (name, DOB, contact) accessible under BILL-5. Both pages reuse the same master billing ledger table component described in 8.4.3.

The topbar displays the current page title on the left and the user's `full_name` + role badge + `Bell` icon + logout on the right, identical to the pattern in VI-SHELL-4.

#### 8.4.2 New Invoice Field: has_insurance_claim

Add the following column to the `invoices` table:

| Column | Type | Constraints | Default |
|---|---|---|---|
| `has_insurance_claim` | INTEGER | NOT NULL, CHECK(`has_insurance_claim` IN (0, 1)) | 0 |

This is a boolean flag (SQLite stores booleans as integers). A value of `1` means an insurance claim has been filed for this invoice. A value of `0` means no claim has been filed.

This field must be included in all invoice create (`POST`) and update (`PUT`) request/response schemas. All existing invoice endpoints must return this field. The field defaults to `0` on invoice creation if not supplied.

The `has_insurance_claim` index is specified in 8.2.1.

#### 8.4.3 Overview Page — Status Tiles

The Overview page (`/billing`) displays four summary tiles in a horizontal row at the top of the content area, collapsing to a 2×2 grid on viewports below 768px.

Each tile is backed by a distinct backend query. Sagar must add a `GET /billing/dashboard` endpoint that returns all four values in a single response to avoid four separate API calls on page load.

| Tile label | Backend query | Color theme |
|---|---|---|
| Outstanding Invoices | `SELECT COUNT(*) FROM invoices WHERE status = 'Pending'` | Warning amber |
| Awaiting Claims | `SELECT COUNT(*) FROM invoices WHERE status = 'Pending' AND has_insurance_claim = 1` | Info blue |
| Collected This Month | `SELECT COALESCE(SUM(total_amount_cents), 0) FROM invoices WHERE status = 'Paid' AND created_at >= {start_of_current_month_UTC}` | Success green |
| Total Patients Billed | `SELECT COUNT(DISTINCT patient_id) FROM invoices` | Primary teal |

`GET /billing/dashboard` response shape:
```json
{
  "outstanding_invoices": 42,
  "awaiting_claims": 7,
  "collected_this_month_cents": 384500,
  "total_patients_billed": 318
}
```

`collected_this_month_cents` is returned as an integer (cents) by the backend and formatted as a currency string by the frontend (e.g., `$3,845.00`). The `Invoice` entity stores `total_amount_cents` as an integer (cents) to avoid floating-point rounding errors.

Note to Pavan: if the existing `Invoice` entity currently stores `total_amount` as a float rather than an integer cents field, this is the point at which it must be migrated to `total_amount_cents` INTEGER. All existing invoice endpoints must be updated to accept and return `total_amount_cents` in place of `total_amount`. The frontend must be updated accordingly.

**Tile visual specification:**
Tiles follow the same pattern as the Admin stat cards (VI-ADMIN-2): white card background, `--shadow-sm`, `--radius-md`, 20px padding, and a 4px solid left-border in the theme accent color:

| Tile | Left-border color token | Icon |
|---|---|---|
| Outstanding Invoices | `--color-warn` (`#b7791f`) | `Clock` (Lucide, 28px) |
| Awaiting Claims | `--color-info` (`#1f5aa8`) | `FileCheck` (Lucide, 28px) |
| Collected This Month | `--color-ok` (`#1e8e5a`) | `TrendingUp` (Lucide, 28px) |
| Total Patients Billed | `--color-primary` (`#0e8a7a`) | `Users` (Lucide, 28px) |

All new tile styles go in `src/frontend/src/index.css` under the section comment `/* === Billing Specialist === */`, which Chintu must add if it does not already exist. Pure CSS Flexbox/Grid with semantic class names. No Tailwind or utility-first classes anywhere in this section.

#### 8.4.4 Master Billing Ledger

The ledger is the primary data table on both the Overview page (below the tiles) and the Invoices page. Both pages render the same `BillingLedger` component — on Overview it shows the most recent 20 records (first page); on the Invoices page it shows the full paginated dataset.

**Column specification:**

| Column header | Data source | Notes |
|---|---|---|
| Invoice ID | `invoice_id` | Display as `#` prefix, e.g. `#1042` |
| Patient Name | `patient.full_name` (joined) | Hyperlink to patient record detail |
| Appointment Date | `appointment.scheduled_at` (joined, nullable) | "—" if no linked appointment |
| Amount | `total_amount_cents` | Formatted as `$X,XXX.XX` |
| Status | `status` | Rendered as a styled badge (see below) |
| Insurance Claim | `has_insurance_claim` | Rendered as a badge: "Yes" (blue) or "—" |
| Created Date | `created_at` | Formatted as `MMM D, YYYY` |
| Actions | — | Three buttons: View, Edit Status, Resend Notification |

**Status badge colors (inline CSS, not class-based CSS variables, because these are dynamic):**
- `Pending`: `background-color: #fef3c7; color: #b7791f; border-radius: 4px; padding: 2px 8px; font-size: 0.8125rem; font-weight: 600;`
- `Paid`: background `#d1fae5`, color `var(--color-ok)`.
- `Waived`: background `var(--color-surface-alt)`, color `var(--color-text-muted)`.

**Insurance claim badge (when `has_insurance_claim = 1`):** background `#dbeafe`, color `var(--color-info)`, text "Claimed".

**Filtering and search:**
- **Status filter**: A `<select>` dropdown with options: All / Pending / Paid / Waived. Selecting a non-All value appends `?status={value}` to the API request. This is a server-side filter.
- **Insurance claim filter**: A checkbox labeled "Insurance claims only". When checked, appends `?has_insurance_claim=1` to the API request. Server-side filter.
- **Search bar**: A text input with a `Search` icon inside the left edge (same pattern as VI-DEPT-3). The search string is sent as `?search={term}` to the API (server-side). The backend must support `search` on `GET /billing/invoices` filtering by `patient.full_name` (case-insensitive LIKE) and by `invoice_id` (exact integer match). Client-side filtering of the current page is additionally acceptable as a UX enhancement but is not a substitute for the server-side `search` parameter.

**Actions column buttons:**
- `View`: navigates to `/billing/invoices/{invoice_id}` detail page.
- `Edit Status`: opens an inline modal or dropdown allowing the BillingSpecialist to change the invoice status. The modal contains a `<select>` (Pending / Paid / Waived), a text area for an optional internal note, and a Save button. On save, calls `PUT /billing/invoices/{invoice_id}` and refreshes the ledger row.
- `Resend Notification`: calls `POST /billing/invoices/{invoice_id}/resend-notification`. On success, shows a brief inline confirmation ("Notification sent.") in the Actions cell that auto-dismisses after 3 seconds.

**Pagination**: The ledger uses the `Pager` component (existing, at `src/frontend/src/components/Pager.tsx`) to navigate pages returned by the paginated `GET /billing/invoices` endpoint.

#### 8.4.5 CSS Rules for Billing Specialist Portal

All billing specialist styles are added to `src/frontend/src/index.css` under the section comment `/* === Billing Specialist === */`. The following rules are required at minimum:

- `.billing-tiles` — Flexbox row, `gap: 1rem`, flex-wrap on mobile (2 columns at 640px, 4 columns at 1024px).
- `.billing-tile` — white card, `--shadow-sm`, `--radius-md`, `padding: 1.25rem 1.5rem`, `border-left: 4px solid {see 8.4.3 per tile}`, `flex: 1 1 200px`.
- `.billing-tile__icon` — `width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 0.75rem;` with background set inline by component prop.
- `.billing-tile__value` — `font-size: 1.75rem; font-weight: 700; line-height: 1; margin-bottom: 0.25rem; color: var(--color-text);`.
- `.billing-tile__label` — `font-size: 0.8125rem; color: var(--color-text-muted); font-weight: 500;`.
- `.billing-ledger` — full-width table, `border-collapse: collapse`, same zebra-stripe pattern as VI-SHARED-2.
- `.billing-ledger th` — `position: sticky; top: 0; background: var(--color-surface); z-index: 1; padding: 0.75rem 1rem; text-align: left; font-size: 0.8125rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--color-text-muted); border-bottom: 2px solid var(--color-border);`.
- `.billing-ledger td` — `padding: 0.75rem 1rem; font-size: 0.9375rem; border-bottom: 1px solid var(--color-border);`.
- `.billing-filters` — Flexbox row, `gap: 0.75rem`, `align-items: center`, `margin-bottom: 1rem`, wraps on mobile.
- `.badge-insurance` — insurance claim badge style: `background: #dbeafe; color: var(--color-info); border-radius: 4px; padding: 2px 8px; font-size: 0.8125rem; font-weight: 600;`.

No Tailwind classes. No utility-first classes. No inline style props beyond dynamic values (color per tile, amount formatting).

---

### 8.5 Updated Role-Based Access Control

This section extends the RBAC table in Section 3.3 to include the `BillingSpecialist` role. The complete updated table (all six roles) replaces the original five-role table for clarity. Existing rules for Admin, Doctor, Patient, Staff, and Lab are unchanged from Section 3.3.

| Resource | Admin | Doctor | Patient | Staff | Lab | BillingSpecialist |
|---|---|---|---|---|---|---|
| User accounts (create/deactivate/role-assign) | Full | None | Self profile only | Create Patient only | None | None |
| Departments | Full (CRUD) | Read | Read | Read | Read | Read (public endpoint only) |
| Appointments | Full (all) | Own (as assigned doctor) | Own (as patient) only | Full (create/edit for any patient) | None | Read (all — for billing reference, date/doctor/status fields only) |
| Medical records / visit notes | Read (no author) | Own patients only (create/read) | Own records only (read-only) | Read own-patient-visible subset (no edit) | None | None |
| Prescriptions | Read | Own patients only (create/read) | Own only (read-only) | Read only | None | None |
| Lab orders / results | Read | Own patients only (create/read) | Own only (read-only) | Read only | Assigned queue (read/update status) | None |
| Billing / invoices | Full | None | Own only (read-only) | Create/edit (front-desk billing) | None | Full CRUD (all patients) |
| Blog / articles | Full (CRUD, publish) | None | Read published only | None | None | None |
| Contact messages | Full (read/resolve) | None | None (submits via public form) | Read/resolve | None | None |
| Public site content | Full (edit About/Home copy) | None | Read | None | None | None |
| Email notification log | Full (read) | None | None | None | None | Read (all notifications) |
| Patient demographics (name, DOB, contact) | Full | Own patients only | Own only | Read (any patient) | Minimal (name, DOB, order context) | Read (any patient — name, DOB, phone, email) |
| Audit log | Full (read) | None | None | None | None | None |

**New explicit rule statements (additive to AUTHZ-1 through AUTHZ-6 in Section 3.3):**

- AUTHZ-7: A BillingSpecialist can read invoice rows for any `patient_id` — there is no row-level ownership restriction for this role on the `invoices` table. This is by design: billing staff must see all outstanding invoices regardless of patient.
- AUTHZ-8: A BillingSpecialist's read access to the `appointments` table is limited to the fields: `appointment_id`, `scheduled_at`, `status`, `doctor.full_name`, `department.name`, `patient.full_name`. It does not extend to `visit_notes`, diagnosis fields, reason text, or any clinical data stored alongside the appointment.
- AUTHZ-9: A BillingSpecialist's read access to patient demographics is limited to: `full_name`, `date_of_birth`, `phone`, `email`. Address, emergency contact, and gender fields are not returned in BillingSpecialist-facing patient lookup responses.
- AUTHZ-10: All six role checks are enforced server-side on every request. The frontend hiding a Billing Specialist nav item or control is not a substitute for backend 403 enforcement (extends AUTHZ-6).

---

### 8.6 Acceptance Criteria

The following ten acceptance criteria cover the new features introduced in Section 8. QA must expand each into one or more executable test cases. Criteria are phrased in Given/When/Then format.

**AC-BILL-ROLE-1 (Account creation restriction)**
Given an unauthenticated visitor submits a POST to `/auth/signup` with `role=BillingSpecialist` in the request body, when the request is processed, then the response is 400 Bad Request and no user account is created in the database.

**AC-BILL-ROLE-2 (Clinical endpoint access denial)**
Given a BillingSpecialist is authenticated with a valid JWT (role claim = `BillingSpecialist`), when they send a GET request to any of `/patients/{id}/records`, `/patients/{id}/prescriptions`, `/lab/orders`, or `/doctor/appointments`, then the response is 403 Forbidden and no clinical data is present in the response body.

**AC-BILL-NOTIFY-1 (Email notification file creation)**
Given an invoice with `status = 'Pending'` exists, when an authenticated BillingSpecialist sends `PUT /billing/invoices/{id}` with `status = 'Paid'`, then: (a) the invoice row in the database has `status = 'Paid'`, (b) a file exists at `uploads/email_log/{timestamp}_{patient_id}_invoice_{id}.html`, (c) that file is valid HTML containing the patient's full name and the invoice ID, and (d) a row in `email_notifications` with `status = 'Sent'` and `related_invoice_id = {id}` exists.

**AC-BILL-NOTIFY-2 (File write failure does not roll back invoice)**
Given the `uploads/email_log/` directory is made temporarily unwritable (simulate by chmod or renaming in test), when an invoice status update is submitted, then the invoice status change commits successfully to the database and the corresponding `email_notifications` row has `status = 'Failed'`. The API response is still 200 OK with the updated invoice data (the notification failure is not surfaced as a 500 error to the caller).

**AC-JWT-FIELDS (JWT payload completeness)**
Given a user with role `BillingSpecialist` successfully logs in via `POST /auth/login`, when the JWT access token in the response is base64-decoded, then the payload contains the fields: `sub` (integer user_id), `role` (string `BillingSpecialist`), `email` (the user's registered email address), `full_name` (the user's full name), and `exp` (a future Unix timestamp). No other role combinations are exempt from this requirement — all roles must include `email` and `full_name`.

**AC-PAGINATE-1 (Pagination envelope shape)**
Given the `GET /billing/invoices?page=2&page_size=10` endpoint is called by an authenticated BillingSpecialist when the database contains 35 invoices, then the response body matches: `{ "items": [...], "total": 35, "page": 2, "page_size": 10, "total_pages": 4 }` and `items` contains exactly 10 records (records 11–20 by the default sort order).

**AC-PAGINATE-2 (Page size cap)**
Given the `GET /billing/invoices?page=1&page_size=500` request is sent, when the server processes it, then the response contains at most 100 items (the page_size is silently clamped to 100) and `page_size` in the response envelope is `100`, not `500`.

**AC-DASH-TILES (Dashboard tile accuracy)**
Given the database contains 12 invoices with `status = 'Pending'`, 3 of which also have `has_insurance_claim = 1`, and 5 invoices with `status = 'Paid'` created in the current calendar month with a combined `total_amount_cents` of 125000, when an authenticated BillingSpecialist calls `GET /billing/dashboard`, then the response is: `{ "outstanding_invoices": 12, "awaiting_claims": 3, "collected_this_month_cents": 125000, "total_patients_billed": <distinct patient count> }`.

**AC-LEDGER-SEARCH (Ledger search by patient name)**
Given the billing ledger has invoices for patients named "Alice Patel", "Bob Nguyen", and "Carol Smith", when an authenticated BillingSpecialist calls `GET /billing/invoices?search=pat`, then the response `items` array contains only the invoice(s) for "Alice Patel" (case-insensitive match on substring "pat"). Invoices for "Bob Nguyen" and "Carol Smith" are not returned.

**AC-INSURANCE-FLAG (has_insurance_claim field persistence)**
Given an invoice is created with `has_insurance_claim = 0`, when an authenticated BillingSpecialist calls `PUT /billing/invoices/{id}` with `{ "has_insurance_claim": 1 }`, then: (a) the database row has `has_insurance_claim = 1`, (b) a subsequent `GET /billing/invoices/{id}` returns `has_insurance_claim: 1`, and (c) the invoice appears in `GET /billing/invoices?has_insurance_claim=1` results.

**AC-BILL-ADMIN-DENY (BillingSpecialist cannot access Admin endpoints)**
Given a BillingSpecialist is authenticated, when they send GET requests to `/admin/dashboard`, `/admin/users`, and `/admin/audit-log`, then all three return 403 Forbidden. When they send a PUT request to `/admin/users/{any_user_id}`, then the response is also 403 Forbidden and no user record is modified.

---

### 8.7 Data Model Additions Summary

The following additions to the data model in Section 3.4 are required by Section 8. Sagar must include all of these in the updated data dictionary and migration scripts.

- **BillingSpecialist** (1:1 with User where role=BillingSpecialist): `billing_specialist_id` (PK), `user_id` (FK, UNIQUE, references `users`), `employee_id` (TEXT, nullable), `created_at` (TEXT, ISO 8601).
- **Invoice** entity gains: `has_insurance_claim` (INTEGER, NOT NULL, DEFAULT 0, CHECK IN (0,1)); `total_amount_cents` replaces `total_amount` if the field currently stores a float (see 8.4.3 note to Pavan).
- **EmailNotification** (new): `notification_id` (PK, AUTOINCREMENT), `recipient_user_id` (FK → users, NOT NULL), `subject` (TEXT, NOT NULL), `body_html` (TEXT, NOT NULL), `sent_at` (TEXT, NOT NULL, ISO 8601), `trigger_event` (TEXT, NOT NULL, values: `invoice_status_change` / `manual_resend`), `related_invoice_id` (INTEGER, FK → invoices, nullable), `status` (TEXT, NOT NULL, CHECK IN ('Queued','Sent','Failed')).
- **User.role enum** extended from `Admin/Doctor/Patient/Staff/Lab` to `Admin/Doctor/Patient/Staff/Lab/BillingSpecialist`.
- All indexes listed in 8.2.1 must be created via migration.

---

### 8.8 Out of Scope — Section 8 Additions

The following items are explicitly excluded from this build to keep scope bounded. These extend (and do not replace) the Out of Scope list in Section 4.

- Real SMTP or email API delivery (SendGrid, Mailgun, AWS SES, etc.) — the file-sink described in 8.3.2 is the only delivery mechanism for this build.
- Insurance eligibility verification or integration with any payer/clearinghouse API — `has_insurance_claim` is a manual boolean flag only.
- Invoice PDF generation or printing — status change and amount display are web-only.
- Multi-currency support — all amounts are in USD cents (single currency, single locale).
- Automated billing rules or charge-capture from clinical events — invoices are created manually by BillingSpecialist or Staff only.
- Role-level notification preferences (e.g., allow patients to opt out of invoice notifications) — all invoice status changes always trigger a notification in this build.
- Audit-log entries for billing changes — the audit log (ADM-9) covers account/role admin actions only; billing-specific change history is out of scope.
- Real-time dashboard tile refresh (WebSocket or polling) — tiles show data as of the last page load (standard HTTP, per PERF-CONS-3).
- Background job queue or retry mechanism for failed notifications — failures are recorded in `email_notifications.status = 'Failed'` and the BillingSpecialist may manually retry via the Resend Notification button (BILL-8).

---

## 9. Batch 2 Requirements — 2026-07-20 (12 New Requirements)

Status: Draft v2.0 — added 2026-07-20 by Lavanya (Phase 1 analysis + Phase 2 documentation).
Consumers: Solution Architect (Sagar — Phase 3 UX + Phase 4 Technical Design), Backend/Frontend (Chintu — Phase 6 Implementation), QA (Gopal — Phase 8).

This section documents all 12 requirements from Krishna's 2026-07-20 batch. Each requirement is confirmed as genuinely new — no overlap with Sections 1–8. Two previously out-of-scope items are now in scope (see Section 9.13). One pre-existing schema gap (vitals table) is also resolved here (see Section 9.14 and REQ-04).

**Requirement IDs** in this section use the prefix `REQ-` followed by a two-digit batch number. User story IDs extend the existing section-based scheme (e.g., AVL- for availability, NOTIF- for notifications).

**Dependency graph (blocking relationships):**
- REQ-01 (Availability) must be designed and schema-complete before REQ-09 (Waitlist) or REQ-10 (Follow-Up Scheduling) design begins.
- REQ-02 (Notification Center) must be designed and schema-complete before REQ-09, REQ-10, REQ-11 design begins.
- REQ-04 (Vitals Trend) requires the vitals table schema gap (Section 9.14) to be resolved first.
- All other requirements in this batch are independent of each other and of REQ-01 / REQ-02, unless otherwise noted per requirement.

---

### 9.1 REQ-01 — Doctor Availability & Slot Management (Critical)

**Description**: Replace the existing free-text `consultation_hours` field on the `doctors` table with a machine-readable weekly availability schedule per doctor, configurable slot durations, one-off date blocks, and real-time available-slot querying at booking time. This is the prerequisite foundation for REQ-09 (Waitlist) and REQ-10 (Follow-Up Scheduling).

**Affected roles**: Admin (configure on behalf of any doctor), Doctor (configure own schedule), Patient (queries slots during booking), Staff (queries slots during front-desk booking).

#### User Stories

- AVL-1: As an Admin or Doctor, I can define a weekly recurring availability schedule for a doctor: for each day of the week (Mon–Sun), I can set one or more time windows (start time, end time) during which appointments can be booked.
- AVL-2: As an Admin or Doctor, I can configure the slot duration (in minutes, e.g., 15, 20, 30, 45, 60) per doctor. The system uses this to divide available windows into discrete bookable slots.
- AVL-3: As an Admin or Doctor, I can create a one-off availability block for a specific date: either blocking the entire day or a specific time range (e.g., "Dr. Smith is unavailable 2–4pm on July 25"). Blocks override the weekly schedule for that date.
- AVL-4: As a Patient or Staff member performing a booking, when I select a doctor and a date, the system returns only the time slots that are (a) within the doctor's weekly schedule for that day, (b) not covered by a one-off block, and (c) not already booked by an existing Scheduled or Completed appointment.
- AVL-5: As a Patient or Staff member, if I attempt to book a slot that has become unavailable between my query and my submission, the booking is rejected with a conflict error (409 Conflict) and the available slots are refreshed.
- AVL-6: As a Doctor, I can view my own weekly schedule and one-off blocks in my portal.
- AVL-7: As an Admin, I can view and edit availability and blocks for any doctor.

#### Functional Requirements

- AVLFR-1: A doctor's weekly schedule is stored as day-of-week + start_time + end_time rows (one row per time window per day). Multiple windows per day are allowed (e.g., 9am–12pm and 2pm–5pm).
- AVLFR-2: Slot duration is stored per doctor (integer, minutes). Default: 30 minutes. Valid values: 10, 15, 20, 30, 45, 60. Requests outside these values are rejected with 400 Bad Request.
- AVLFR-3: One-off blocks store: doctor_id, block_date (YYYY-MM-DD), optional start_time (HH:MM), optional end_time (HH:MM). If start_time and end_time are both null, the entire day is blocked. If only one of start/end is present, the block is rejected with 400 Bad Request.
- AVLFR-4: The slot-query endpoint (`GET /doctors/{id}/available-slots?date=YYYY-MM-DD`) returns an ordered list of datetime strings representing the start time of each bookable slot. The list is empty if the doctor has no schedule for that day, if the entire day is blocked, or if all generated slots are already taken.
- AVLFR-5: The existing `consultation_hours` text field on the `doctors` table is retained for backward-compatibility (public profile display still uses it for a human-readable description) but is no longer the authoritative source of availability. The new schedule tables are authoritative for booking.
- AVLFR-6: Changes to a doctor's availability (schedule or blocks) do NOT retroactively affect existing booked appointments.
- AVLFR-7: The booking endpoint (`POST /appointments`) must validate slot availability in the same database transaction as the appointment insert. The existing unique index `uq_appointments_doctor_slot` remains in place as the last-line-of-defense conflict guard.

#### Non-Functional Requirements

- AVLNFR-1: The slot-query endpoint must return results within 500ms for a single date query even with 200+ existing appointments for a doctor in the database.
- AVLNFR-2: Availability configuration endpoints are role-guarded: Admin and Doctor (own record only) can write; Admin, Doctor (own), Patient, and Staff can read.

#### Acceptance Criteria

- AC-AVL-1: Given a doctor has a weekly schedule of Mon 9:00–12:00 with 30-minute slots, when `GET /doctors/{id}/available-slots?date=2026-07-27` (a Monday) is called and no appointments exist, then the response contains exactly 6 slots: 09:00, 09:30, 10:00, 10:30, 11:00, 11:30.
- AC-AVL-2: Given the same schedule and an existing Scheduled appointment at 09:30, when the slot query is called, then 09:30 is absent from the response and 5 slots are returned.
- AC-AVL-3: Given a one-off block exists for 2026-07-27 with no start/end time (full-day block), when the slot query is called for that date, then the response contains an empty list.
- AC-AVL-4: Given a Patient calls `POST /appointments` with a valid slot, and between the slot query and the booking POST another user books that same slot, then the second booking receives 409 Conflict and no duplicate appointment row is created.
- AC-AVL-5: Given a doctor has no weekly schedule configured for Wednesday, when the slot query is called for a Wednesday, then the response contains an empty list (not a 404 or 500).

#### Dependencies

- Prerequisite for REQ-09 (Waitlist) and REQ-10 (Follow-Up Scheduling within discharge summary).
- Integrates with existing Appointment booking flow (PAT-2, STF-1, AC-APT-1, AC-APT-2).

#### Priority: Critical

---

### 9.2 REQ-02 — In-App Notification Center (High)

**Description**: A persistent, role-aware notification inbox stored in the database. All six roles see a bell icon with an unread badge in the authenticated app shell. Notifications are generated server-side in response to defined events. No email or SMS delivery — in-app only. This is the notification foundation for REQ-09, REQ-10, and REQ-11.

**Note**: This is entirely separate from the existing `email_notifications` table (Section 8.3), which handles only billing invoice status changes via file-sink. The new `notifications` table serves in-app display only.

**Affected roles**: All six roles (Admin, Doctor, Patient, Staff, Lab, BillingSpecialist).

#### User Stories

- NOTIF-1: As any authenticated user, I can see a bell icon in the top navigation bar with a badge showing the count of unread notifications. If there are no unread notifications, the badge is hidden (not shown as "0").
- NOTIF-2: As any authenticated user, I can click the bell icon to open a notification panel showing my most recent notifications (most recent first), with unread items visually distinguished (e.g., bold or highlighted background).
- NOTIF-3: As any authenticated user, I can click an individual notification to mark it as read. If the notification is related to a specific entity (appointment, invoice, lab result), clicking it also navigates to the relevant page.
- NOTIF-4: As any authenticated user, I can mark all notifications as read in a single action.
- NOTIF-5: As any authenticated user, I can view a full notifications list page (not just the dropdown panel) with pagination.

#### Functional Requirements — Event Triggers

The following events must create notification rows server-side at the time the triggering action occurs. The "Recipient(s)" column defines which user account(s) receive the notification.

| Event type (stored in `notifications.event_type`) | Triggering action | Recipient(s) |
|---|---|---|
| `appointment_confirmed` | Appointment is created (any booking method) | Patient (owner), Doctor (assigned) |
| `appointment_reminder` | See NOTIFFR-3 below — deferred trigger | Patient (owner), Doctor (assigned) |
| `appointment_cancelled` | Appointment status set to Cancelled | Patient (owner), Doctor (assigned) |
| `appointment_noshow` | Appointment status set to NoShow | Patient (owner) |
| `lab_result_ready` | Lab result is marked finalized (is_finalized = 1) | Doctor (ordering), Patient (owner) |
| `invoice_created` | New invoice is created | Patient (owner) |
| `contact_form_received` | Public contact form submitted | All active Admin users, all active Staff users |
| `account_created` | New user account is created by Admin or Staff | The newly created user |
| `account_deactivated` | User account is deactivated | The deactivated user |
| `lab_order_assigned` | Lab order is created (enters the queue) | All active Lab users |
| `referral_received` | Doctor creates a referral (REQ-05) | Receiving doctor (if specified) or all doctors in receiving department |
| `referral_status_changed` | Referral is accepted or declined (REQ-05) | Referring doctor, Patient |
| `waitlist_slot_available` | Cancellation frees a slot (REQ-09) | First patient on waitlist (FIFO) |
| `discharge_summary_ready` | Doctor creates discharge summary (REQ-10) | Patient |
| `follow_up_booked` | Follow-up appointment booked from discharge panel (REQ-10) | Patient, Doctor |
| `survey_available` | Survey trigger record matures (REQ-11) | Patient |

- NOTIFFR-1: Each notification row stores: recipient_user_id, event_type, title (short text, max 120 chars), body (detail text, max 500 chars), related_entity_type (nullable text, e.g. 'appointment', 'invoice', 'lab_result', 'referral'), related_entity_id (nullable integer), is_read (boolean, default false), created_at.
- NOTIFFR-2: Notifications are per-user — a notification for "Doctor and Patient" creates two separate rows, one per recipient.
- NOTIFFR-3: `appointment_reminder` notifications cannot be generated synchronously since they must fire 24 hours before the appointment. Since the current stack has no background job scheduler, this implementation is deferred: a `notification_schedules` table records upcoming reminder triggers (appointment_id, trigger_at timestamp, is_fired boolean). The backend checks for unfired, matured triggers on each authenticated request by the recipient user and creates the notification row at that point. This is a poll-on-login pattern, not a true background job. Sagar must confirm this approach is architecturally acceptable before design is locked (see Section 9.18, Open Item OI-2).
- NOTIFFR-4: The notification panel in the UI shows at most 20 items. The full-page notification list is paginated (page_size=20 default).
- NOTIFFR-5: Unread badge count is returned by a dedicated lightweight endpoint (`GET /notifications/unread-count`) that returns `{ "unread_count": N }`. This endpoint is called on every authenticated page load to keep the badge current without polling.
- NOTIFFR-6: `GET /notifications` returns paginated notifications for the authenticated user, filtered to their own `recipient_user_id`. A user cannot request another user's notifications.
- NOTIFFR-7: `PATCH /notifications/{id}/read` marks a single notification as read (only if it belongs to the caller — 403 otherwise). `POST /notifications/mark-all-read` marks all of the caller's unread notifications as read.

#### Non-Functional Requirements

- NOTIFNFR-1: The unread count endpoint must respond within 200ms. It queries only `WHERE recipient_user_id = ? AND is_read = 0` with an index on (recipient_user_id, is_read).
- NOTIFNFR-2: Notification creation is synchronous (same request as the triggering action) and must not cause perceptible latency — notification inserts are a batch INSERT at the end of the triggering transaction, not nested queries.
- NOTIFNFR-3: No email or SMS is sent. In-app persistence only.

#### Acceptance Criteria

- AC-NOTIF-1: Given a Patient books an appointment, when the booking POST returns 200, then a notification row with event_type='appointment_confirmed' exists for the patient's user_id AND a separate row exists for the assigned doctor's user_id.
- AC-NOTIF-2: Given a Doctor has 3 unread notifications, when they call `GET /notifications/unread-count`, then the response is `{ "unread_count": 3 }`. After calling `POST /notifications/mark-all-read`, a subsequent call returns `{ "unread_count": 0 }`.
- AC-NOTIF-3: Given Patient A has 5 notifications, when Patient B (different user) calls `GET /notifications`, then Patient A's notifications are not in the response.
- AC-NOTIF-4: Given a Lab result is marked finalized, then notification rows are created for both the ordering doctor and the patient — not for any other user.
- AC-NOTIF-5: Given a public contact form is submitted, then notification rows are created for every active Admin user and every active Staff user currently in the database. No notification is created for Doctor, Patient, Lab, or BillingSpecialist users.

#### Dependencies

- REQ-05, REQ-09, REQ-10, REQ-11 all depend on this notification infrastructure being implemented first.
- Extends VI-SHELL-4 (the `Bell` placeholder icon already in the AppShell topbar must now be wired to NOTIFFR-5).

#### Priority: High

---

### 9.3 REQ-03 — Patient Pre-Visit Intake Form (High)

**Description**: A structured form linked 1:1 to an appointment. The patient fills it out before their visit. The doctor sees it inline in the appointment detail view. Once the appointment reaches Completed status, the form becomes permanently read-only for all roles.

**Affected roles**: Patient (fill/edit before appointment is Completed), Doctor (read-only at all times), Staff (read-only), Admin (read-only).

#### User Stories

- INTAKE-1: As a Patient, after booking an appointment, I can access a "Pre-Visit Form" for that appointment from my appointment detail view and fill in my chief complaint, symptom duration, current allergies, current medications, pain scale (1–10), and any additional notes.
- INTAKE-2: As a Patient, I can save the form as a draft (partial fill) and return to edit it later, as long as the appointment has not yet reached Completed status.
- INTAKE-3: As a Patient, once an appointment is marked Completed, the intake form for that appointment is permanently read-only and I can still view (but not edit) it.
- INTAKE-4: As a Doctor, I can see the patient's completed intake form within the appointment detail view for any of my appointments. If the patient has not yet submitted the form, I see a "Not yet submitted" state.
- INTAKE-5: As a Staff member, I can view (read-only) the intake form for any appointment, to assist with coordination.

#### Functional Requirements

- INTAKEFR-1: The intake form is linked 1:1 to an appointment (one form per appointment, unique constraint on appointment_id). It is created (as an empty/draft record) when the appointment is created.
- INTAKEFR-2: Form fields: `chief_complaint` (TEXT, required to mark as submitted), `symptom_duration` (TEXT, required), `allergies` (TEXT, nullable — "None" if patient reports none), `current_medications` (TEXT, nullable — "None" if no current meds), `pain_scale` (INTEGER, 1–10, nullable — only required for submissions, not drafts), `additional_notes` (TEXT, nullable), `submitted_at` (TEXT, ISO 8601 — null if draft, set on first full submission).
- INTAKEFR-3: A "submitted" form is one where `submitted_at` is not null. A patient can re-edit a submitted form and re-submit it (updating `submitted_at`) as long as the appointment is not yet Completed.
- INTAKEFR-4: When an appointment is transitioned to Completed status, the associated intake form becomes read-only system-wide. Any subsequent PATCH/PUT to the intake form endpoint for a Completed appointment returns 403 Forbidden.
- INTAKEFR-5: The patient can only access the intake form for appointments where they are the patient. The doctor can only access it for appointments assigned to them. Staff can access all.
- INTAKEFR-6: `pain_scale` must be validated server-side as an integer between 1 and 10 inclusive. Values outside this range return 400 Bad Request.

#### Non-Functional Requirements

- INTAKENF-1: Intake form data is included in the Patient Medical Record PDF export (REQ-08) for the relevant appointment.
- INTAKENF-2: The intake form is not visible to Lab or BillingSpecialist roles.

#### Acceptance Criteria

- AC-INTAKE-1: Given a Patient has a Scheduled appointment, when they submit the intake form with all required fields and `pain_scale=7`, then `submitted_at` is set to a non-null timestamp and the form is retrievable by the Doctor in the appointment detail view.
- AC-INTAKE-2: Given a Patient's appointment is marked Completed, when the Patient calls PATCH on that appointment's intake form, then the response is 403 Forbidden and the form data is unchanged.
- AC-INTAKE-3: Given a Patient submits `pain_scale=11`, then the response is 400 Bad Request with a validation error identifying the `pain_scale` field.
- AC-INTAKE-4: Given an appointment exists with patient_id=A, when a different Patient B calls GET on that appointment's intake form, then the response is 403 Forbidden.

#### Priority: High

---

### 9.4 REQ-04 — Vitals Trend Visualization (Medium)

**Description**: Time-series charts of key vitals (blood pressure systolic/diastolic, weight, pulse, temperature) plotted over appointment dates, visible to Doctors and Staff on the patient profile. This requirement also resolves a pre-existing schema gap: STF-4 (recording vital signs) was in scope since Section 2.4 but had no backing table in db/schema.sql. The vitals table defined here serves both STF-4 and the new visualization.

**Affected roles**: Staff (record vitals — existing STF-4), Doctor (view trend charts), Admin (view as part of patient record access).

#### User Stories

- VIT-1: As a Staff member, before a doctor's consultation, I can record vital signs for a patient appointment: systolic BP (mmHg), diastolic BP (mmHg), weight (kg), pulse (bpm), temperature (°C), and optionally height (cm). At least one vital field must be non-null to save a record.
- VIT-2: As a Doctor, I can view a vitals trend section on a patient's profile showing time-series charts for: (a) BP (systolic and diastolic as two lines on one chart), (b) weight, (c) pulse, (d) temperature. The x-axis is appointment date, the y-axis is the measurement value.
- VIT-3: As a Doctor, if a patient has fewer than 2 vitals records, the trend charts are replaced with an informational message ("Not enough data to display trend — at least 2 readings required").
- VIT-4: As a Doctor or Staff member, I can view individual vitals readings in a tabular list alongside the charts.
- VIT-5: Vitals data is read-only for Doctors. Only Staff (and Admin) can create vitals records.

#### Functional Requirements

- VITFR-1: Vitals are stored with: `patient_id` (FK), `appointment_id` (FK, nullable — a vitals record may be taken without being linked to a specific appointment, e.g. a standalone check), `recorded_by_user_id` (FK → users), `systolic_bp` (INTEGER, nullable), `diastolic_bp` (INTEGER, nullable), `weight_kg` (REAL, nullable), `pulse_bpm` (INTEGER, nullable), `temperature_celsius` (REAL, nullable), `height_cm` (REAL, nullable), `recorded_at` (TEXT, ISO 8601).
- VITFR-2: If both `systolic_bp` and `diastolic_bp` are provided, both must be integers ≥ 40 and ≤ 300. If only one is provided, the record is rejected with 400 Bad Request — both or neither.
- VITFR-3: Weight must be > 0 if provided. Temperature must be between 30.0 and 45.0 °C if provided. Pulse must be between 20 and 300 bpm if provided. These ranges are validated server-side.
- VITFR-4: The trend data endpoint (`GET /patients/{patient_id}/vitals`) returns all vitals records for the patient in ascending `recorded_at` order, suitable for rendering a chart. The response includes the raw records and no server-side aggregation.
- VITFR-5: Charts must not rely on color as the only means of distinguishing data series (accessibility). Each data point on BP chart must also use distinct line styles or symbols (e.g., dashed vs. solid) to distinguish systolic from diastolic.
- VITFR-6: Doctor access to vitals is subject to the existing AUTHZ-2 rule: a Doctor may only view vitals for patients with whom they have an appointment relationship.

#### Non-Functional Requirements

- VITNFR-1: The frontend chart library must be chosen by Sagar in Phase 4 and must be a standard, well-maintained library compatible with React 19 (e.g., Recharts, Chart.js via react-chartjs-2, Nivo). No D3 direct DOM manipulation.
- VITNFR-2: Vitals records are included in the Patient Medical Record PDF export (REQ-08).

#### Acceptance Criteria

- AC-VIT-1: Given a Staff member records systolic_bp=120, diastolic_bp=80, weight_kg=70.5, pulse_bpm=72, temperature_celsius=36.8 for Patient P linked to Appointment A, then a `vitals` row is created with all five fields set and `recorded_by_user_id` = Staff user's id.
- AC-VIT-2: Given `systolic_bp=120` is submitted without `diastolic_bp`, then the response is 400 Bad Request.
- AC-VIT-3: Given a patient has only 1 vitals record, when a Doctor views the trend section, then the chart is not rendered and the "not enough data" message is displayed.
- AC-VIT-4: Given Doctor X has no appointment with Patient Z, when Doctor X calls `GET /patients/{Z_patient_id}/vitals`, then the response is 403 Forbidden.

#### Priority: Medium

---

### 9.5 REQ-05 — Inter-Department Referral Management (Medium)

**Description**: A referring doctor creates a referral to another department (with optional specific receiving doctor), including reason and urgency level. The referral flows through a defined status lifecycle. The receiving doctor accepts or declines. On acceptance, the system facilitates appointment booking for the patient. Patients can see their referral status. Admin has full read access.

**Affected roles**: Doctor (create referrals; accept/decline received referrals), Patient (read own referral statuses), Admin (read all).

#### User Stories

- REF-1: As a Doctor, I can create a referral for one of my patients by specifying: receiving department (required), receiving doctor within that department (optional), clinical reason (required, free text), and urgency level (Routine or Urgent).
- REF-2: As a Doctor who has received a referral (either assigned directly or as any doctor in the receiving department), I can view pending referrals assigned to me or my department.
- REF-3: As a Doctor, I can accept a referral with an optional acceptance note, or decline it with a required decline reason.
- REF-4: As a Doctor, after accepting a referral, I can book an appointment for the referred patient from the referral detail page — the appointment booking form is pre-populated with: patient, doctor (me, as accepting doctor), and reason derived from the referral. Booking this appointment transitions the referral status to 'AppointmentBooked'.
- REF-5: As a Patient, I can view a list of referrals made for me, showing referring doctor, receiving department/doctor, urgency, current status, and (once available) the receiving doctor's note.
- REF-6: As an Admin, I can view all referrals across all patients, filterable by status, department, and date range.
- REF-7: A referral can be marked Completed by the receiving doctor once the referred consultation or appointment has concluded.

#### Functional Requirements

- REFFR-1: Referral status lifecycle: `Pending` (on creation) → `Accepted` (receiving doctor accepts) → `AppointmentBooked` (appointment created for the referral) → `Completed` (receiving doctor marks done). From `Pending`, the receiving doctor can also transition to `Declined`. No other status transitions are permitted.
- REFFR-2: If no specific receiving doctor is specified, the referral is visible to all active doctors in the receiving department. The first doctor to accept it claims it (optimistic locking: the first PATCH to accept sets the `receiving_doctor_id` and status atomically).
- REFFR-3: On acceptance, the system notifies the patient (via REQ-02 notification, event_type='referral_status_changed') with the accepting doctor's name and department.
- REFFR-4: On decline, the system notifies the patient and the referring doctor (event_type='referral_status_changed'). The referral returns to `Pending` if declined — it is not permanently closed, allowing another doctor in the department to accept it. This differs from "Declined by a specific doctor" — see Section 9.18 Open Item OI-5 for clarification needed from Krishna.
- REFFR-5: The referring doctor can only create referrals for patients with whom they have an appointment relationship (AUTHZ-2 applies).
- REFFR-6: A Patient may not cancel or decline a referral. Only the receiving doctor can decline.
- REFFR-7: Urgency is stored as `Routine` or `Urgent`. Urgent referrals appear at the top of the receiving department's referral queue regardless of creation time.

#### Non-Functional Requirements

- REFNFR-1: Referral data is not included in the Patient Medical Record PDF export (REQ-08) in this build. (Out of scope to avoid complexity — may be added in a future batch.)
- REFNFR-2: Admin read access to all referrals does not include clinical reason text — Admin sees department, doctor names, urgency, status, and dates only. This preserves clinical information access controls per ADM-10.

Actually, on reflection, the clinical reason is created by a Doctor and read by the receiving Doctor — Admin seeing it or not should be consistent with ADM-10. Flagging as Open Item OI-6 in Section 9.18.

#### Acceptance Criteria

- AC-REF-1: Given Doctor A (Cardiology) creates a referral for Patient P to Neurology, when the referral is saved, then a `referrals` row exists with status='Pending', referring_doctor_id=A, receiving_department_id=Neurology, patient_id=P, and a notification with event_type='referral_received' is created for all active Neurology doctors.
- AC-REF-2: Given a Neurology doctor B accepts the referral, when the PATCH is processed, then the referral status is 'Accepted', receiving_doctor_id=B, and notifications with event_type='referral_status_changed' are created for the Patient P and Doctor A.
- AC-REF-3: Given Doctor B accepts the referral and then books an appointment via the referral detail page, when the appointment is created, then the referral status transitions to 'AppointmentBooked' and the new appointment_id is stored on the referral row.
- AC-REF-4: Given Doctor C (also in Neurology) attempts to accept the same referral that Doctor B just accepted, then Doctor C's acceptance request returns 409 Conflict (or the referral is no longer in Pending status — the specific error is architecture's decision).
- AC-REF-5: Given Patient P calls `GET /patients/me/referrals`, then only referrals where patient_id = P's patient_id are returned.

#### Dependencies

- Notification infrastructure (REQ-02) is required before this can be fully implemented.
- Follow-up appointment booking uses REQ-01 availability query when scheduling the referred appointment.

#### Priority: Medium

---

### 9.6 REQ-06 — Advanced Analytics & Reporting Dashboard — Admin Only (High)

**Description**: A server-side-aggregated analytics dashboard accessible only to Admin. Shows appointment volume trends, no-show rates, revenue summary, department rankings, and patient acquisition trends over a configurable date range. CSV export available for each metric area. No other role has access to this dashboard.

**Affected roles**: Admin only.

#### User Stories

- ANLY-1: As an Admin, I can view a dashboard page showing aggregate analytics for the hospital, with a date range picker allowing me to select custom start/end dates or use presets: Last 7 days, Last 30 days, Last 3 months, Last 12 months, Year to date, All time.
- ANLY-2: As an Admin, I can view an appointment volume trend chart: total appointments per month (grouped by `scheduled_at` month) within the selected date range, broken down by status (Scheduled, Completed, Cancelled, NoShow) as stacked or grouped bars.
- ANLY-3: As an Admin, I can view a no-show rate trend: percentage of appointments with status='NoShow' out of total appointments (excluding Cancelled) per month.
- ANLY-4: As an Admin, I can view a revenue summary chart: per month — (a) total invoiced amount (sum of all invoice `total_amount_cents` created that month) and (b) total collected amount (sum of `total_amount_cents` where status='Paid' and payment/update occurred that month). Both lines on the same chart.
- ANLY-5: As an Admin, I can view a department volume ranking: a ranked bar chart or table showing each department's total appointment count within the date range, sorted descending.
- ANLY-6: As an Admin, I can view a patient acquisition trend: new patient registrations (new `patients` rows, by `users.created_at`) per month within the date range.
- ANLY-7: As an Admin, I can export the data for any single metric as a CSV file. The CSV includes the raw data rows (not a pre-rendered chart) suitable for import into Excel or Google Sheets.
- ANLY-8: No role other than Admin can access any analytics endpoint. All analytics endpoints return 403 Forbidden to any other role.

#### Functional Requirements

- ANLYFR-1: All aggregation is performed server-side via SQL aggregate queries. The frontend receives pre-aggregated data (e.g., `[{ month: "2026-05", total: 142, completed: 98, cancelled: 30, noshow: 14 }, ...]`) and renders it as charts. The frontend must not perform SUM, AVG, COUNT, or GROUP operations on raw data arrays.
- ANLYFR-2: The analytics API exposes separate endpoints per metric group to allow independent loading, using `from_date`/`to_date` query params (not `start`/`end`):
  - `GET /admin/analytics/appointments?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD&granularity=month`
  - `GET /admin/analytics/no-show-rate?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD&granularity=month`
  - `GET /admin/analytics/revenue?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD`
  - `GET /admin/analytics/department-volume?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD`
  - `GET /admin/analytics/patient-acquisition?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD`
- ANLYFR-3: CSV export is handled by a dedicated endpoint: `GET /api/admin/analytics/export-csv?metric=<name>&from_date=YYYY-MM-DD&to_date=YYYY-MM-DD`. Valid metric values: `appointments`, `no_show_rate`, `revenue`, `department_volume`, `patient_acquisition`. The backend returns `Content-Type: text/csv` with `Content-Disposition: attachment; filename="analytics_{metric}_{from_date}_{to_date}.csv"`. The `?format=csv` query parameter on individual metric endpoints is not supported.
- ANLYFR-4: Date range validation: `from_date` must be before or equal to `to_date`. If not, return 400 Bad Request. If `from_date` or `to_date` is missing, the default range is the last 30 days from today.
- ANLYFR-5: Revenue chart uses `invoices.created_at` for the "invoiced" series and (for the "collected" series) `invoices.created_at` where `status='Paid'` — both series grouped by the month of `created_at`. This is an approximation (it attributes payment to creation month, not the actual date status changed to Paid). This is a known simplification; a precise approach would require storing `paid_at` — this is an open item for Sagar (OI-7 in Section 9.18).
- ANLYFR-6: The chart type (bar, line) and library are Sagar's decision in Phase 3/4, subject to VITNFR-1's constraint (React 19-compatible, standard library).

#### Acceptance Criteria

- AC-ANLY-1: Given an Admin calls `GET /admin/analytics/appointments?from_date=2026-01-01&to_date=2026-06-30`, then the response contains `{"series": [...], "total": N}` where each series item covers one period with `count`, `completed`, `cancelled`, `no_show`, and `scheduled` fields derived from `appointments.scheduled_at`. No calculation is done client-side.
- AC-ANLY-2: Given a non-Admin user (Doctor, Patient, Staff, Lab, BillingSpecialist) calls any analytics endpoint, then the response is 403 Forbidden.
- AC-ANLY-3: Given an Admin calls `GET /api/admin/analytics/export-csv?metric=department_volume&from_date=2026-01-01&to_date=2026-12-31`, then the response has Content-Type: text/csv and the body is a valid CSV with `department_id`, `name`, and `count` columns.
- AC-ANLY-4: Given `from_date=2026-06-01&to_date=2026-01-01` (to_date before from_date), then the response is 400 Bad Request.

#### Priority: High

---

### 9.7 REQ-07 — Public Symptom / Condition Search (High)

**Description**: A search bar available on the public site (no login required) that matches user queries against department names/descriptions, doctor specialty/bio, and admin-curated symptom tags per department. Results are ranked (departments first, then individual doctors). Empty-result fallback is shown. Admin manages symptom tags from the admin portal.

**Affected roles**: Public (no auth — visitors), Admin (manage symptom tags).

#### User Stories

- SRCH-1: As a visitor on the public site, I can enter a symptom, condition, or keyword into a search bar and see ranked results showing which departments and doctors at Green Valley Hospital are relevant to my query.
- SRCH-2: As a visitor, search results show departments first (with their name, description snippet, and icon), followed by doctors (with name, specialty, department). Each result is a clickable link to the department page or doctor profile page.
- SRCH-3: As a visitor, if no results are found, I see a clear "No results found for '{query}'" message with a suggestion to contact the hospital or browse departments.
- SRCH-4: As an Admin, I can manage symptom tags for each department in the admin portal: add, edit, or remove free-text tags (e.g., "chest pain", "shortness of breath", "heart palpitations" for Cardiology). Tags are used to improve search matching beyond the department's name and description.
- SRCH-5: As an Admin, I can view which departments have symptom tags and how many tags each has.

#### Functional Requirements

- SRCHFR-1: The public search endpoint (`GET /public/search?q={query}`) performs case-insensitive substring matching against: (a) `departments.name`, (b) `departments.description`, (c) `department_symptom_tags.tag_text` for all tags belonging to each department, (d) `doctors.specialty`, (e) `doctors.bio`. Only active departments and active doctor accounts are searched.
- SRCHFR-2: Result ranking: departments appear before doctors in the response. Within departments, those matching on `name` rank above those matching on `description` or `tags`. Within doctors, those matching on `specialty` rank above those matching on `bio`. The ranking is determined server-side; the frontend renders in the order received.
- SRCHFR-3: The response shape separates departments and doctors: `{ "departments": [...], "doctors": [...], "query": "chest pain", "total": 5 }`.
- SRCHFR-4: Minimum query length: 2 characters. Queries shorter than 2 characters return 400 Bad Request with a validation message. Maximum query length: 200 characters. Queries longer than 200 characters are truncated server-side (not rejected).
- SRCHFR-5: Symptom tags are stored per department in a `department_symptom_tags` table. Each tag is a free-text string (max 100 chars). A department may have 0–50 tags (enforced server-side on admin CRUD). Duplicate tag text per department is rejected (case-insensitive unique constraint per department).
- SRCHFR-6: The admin symptom tag CRUD endpoints are: `GET /admin/departments/{id}/tags`, `POST /admin/departments/{id}/tags` (body: `{ "tag_text": "..." }`), `DELETE /admin/departments/{id}/tags/{tag_id}`, `PUT /admin/departments/{id}/tags/{tag_id}` (body: `{ "tag_text": "..." }`).
- SRCHFR-7: The public search bar is added to the public site navigation or home page. Its placement and visual design are Sagar's decision in Phase 3. It must be accessible without any page navigation (i.e., not requiring the visitor to go to a dedicated /search URL first, though a dedicated `/search` results page is acceptable after submission).

#### Acceptance Criteria

- AC-SRCH-1: Given Cardiology department has symptom tags ["chest pain", "shortness of breath"] and the query is "chest", then the Cardiology department appears in the response `departments` array.
- AC-SRCH-2: Given the query is "neuro", then the Neurology department appears in results (matched on department name). If a doctor has "neurology" in their bio, that doctor also appears in the `doctors` array. Departments appear before doctors in the combined results page.
- AC-SRCH-3: Given the query is "xyz123noresult", then the response is `{ "departments": [], "doctors": [], "query": "xyz123noresult", "total": 0 }` and the UI renders the fallback message.
- AC-SRCH-4: Given the query is "a" (1 character), then the response is 400 Bad Request.
- AC-SRCH-5: Given an Admin adds the tag "hair loss" to Dermatology, when a visitor searches for "hair", then Dermatology appears in results.

#### Priority: High

---

### 9.8 REQ-08 — Patient Medical Record Export (PDF) (Medium)

**Description**: On-demand server-generated PDF of a patient's full medical record, accessible only to the patient themselves. The PDF is not stored on the server. An optional date range filter narrows which visits are included. The PDF is watermarked. This requirement moves a previously out-of-scope item into scope (see Section 9.13).

**Affected roles**: Patient (own records only). No other role may trigger this export.

#### User Stories

- PDF-1: As a Patient, from my records page, I can request a PDF export of my medical records. The PDF downloads immediately (no email, no stored file).
- PDF-2: As a Patient, before generating the PDF, I can optionally filter the included visits by date range (start date, end date). If no filter is applied, all records are included.
- PDF-3: As a Patient, the generated PDF contains: (a) cover page, (b) patient demographics, (c) visit notes and diagnoses for each included appointment (ordered by date), (d) prescriptions, (e) completed lab results, (f) vitals recorded at each appointment. Each section is clearly headed.
- PDF-4: As a Patient, the PDF is watermarked on every page with: hospital name, patient full name, patient ID, and export timestamp (UTC).

#### Functional Requirements

- PDFFR-1: The PDF is generated server-side on each request. No file is written to disk. The endpoint streams the PDF bytes directly as the response body with `Content-Type: application/pdf` and `Content-Disposition: attachment; filename="GVH_MedicalRecord_{patient_id}_{YYYYMMDD}.pdf"`.
- PDFFR-2: Endpoint: `GET /patients/me/export-pdf?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` (date params are optional). Auth: Patient only. Any other role calling this endpoint receives 403 Forbidden.
- PDFFR-3: The date range filter applies to `appointments.scheduled_at`. Only appointments within the range (inclusive) are included, along with their associated visit notes, prescriptions, and lab results.
- PDFFR-4: The cover page must include: hospital name and logo (text-based, no external image), export date and time (UTC), patient full name, patient date of birth, patient ID, and date range applied (or "All records" if no filter).
- PDFFR-5: Watermark is rendered on every page as diagonal text at low opacity (e.g., 15% opacity, 45° angle), containing: "Green Valley Hospital | {patient_full_name} | ID:{patient_id} | Exported: {YYYY-MM-DD HH:MM UTC}". The watermark must not obscure the readable content.
- PDFFR-6: Lab result file attachments (images, scanned documents stored at `lab_results.file_attachment_path`) are NOT included in the PDF export (out of scope for this build — binary attachment embedding is deferred). The PDF includes only the text/values from `lab_results.result_data`.
- PDFFR-7: The PDF library choice is Sagar's decision in Phase 4 (see Section 9.18 Open Item OI-3). WeasyPrint and ReportLab are the two most likely candidates given the Python/FastAPI stack. The choice must be documented in `docs/architecture.md` before implementation begins.
- PDFFR-8: Generation must complete within 10 seconds for a patient with up to 100 appointment records. Requests exceeding 30 seconds should be aborted with 504 Gateway Timeout (this sets an expectation for the library/template approach chosen).

#### Acceptance Criteria

- AC-PDF-1: Given Patient P is authenticated and calls `GET /patients/me/export-pdf`, then the response has Content-Type: application/pdf, a non-empty body, and Content-Disposition: attachment with a filename containing the patient_id.
- AC-PDF-2: Given a non-Patient role (Doctor, Admin) calls `GET /patients/me/export-pdf`, then the response is 403 Forbidden and no PDF is generated.
- AC-PDF-3: Given the filter `?start_date=2026-01-01&end_date=2026-03-31` is applied and Patient P has appointments in Jan, Mar, and Jun 2026, then the PDF contains sections for Jan and Mar appointments only — the Jun appointment is absent.
- AC-PDF-4: Given the generated PDF is opened, then every page contains the watermark text including the patient's name, patient ID, and a date/time string. The watermark does not cover the primary text to the point of making it illegible.

#### Priority: Medium

---

### 9.9 REQ-09 — Appointment Waitlist System (Medium)

**Description**: When a patient attempts to book a slot with a doctor that has no available slots, they can join a FIFO waitlist for that doctor. On cancellation of an existing appointment, the first patient on the waitlist is notified via REQ-02. A configurable confirmation window (default 4 hours) gives the waitlisted patient time to confirm the slot. Non-response moves the patient to the back of the list (not removed). Staff can manage the waitlist. Admin sees fill-time statistics. This requirement removes "Waitlist management for fully booked doctors" from Section 4's Out of Scope list.

**Affected roles**: Patient (join waitlist), Staff (manage waitlist), Admin (view stats).

**Hard dependency**: REQ-01 (Availability & Slot Management) and REQ-02 (Notification Center) must be implemented before this requirement.

#### User Stories

- WL-1: As a Patient, when I select a doctor and date and no slots are available, I see a "Join Waitlist" option. Clicking it adds me to the doctor's waitlist with my preferred date noted (optional — I may be open to any date).
- WL-2: As a Patient, I can see my active waitlist entries in my appointments section, showing doctor name, department, my position in the queue, and the date I joined.
- WL-3: As a Patient, I can remove myself from a waitlist at any time before a slot is offered to me.
- WL-4: As a Patient, when a slot becomes available and I am first in the queue, I receive a notification (event_type='waitlist_slot_available') with a link to confirm the slot. I have 4 hours (configurable by Admin) to confirm. If I do not confirm within that window, I am moved to the back of the list and the next patient is notified.
- WL-5: As a Staff member, I can view the full waitlist for any doctor, see each patient's position and join date, and manually remove a patient from the waitlist with a recorded reason.
- WL-6: As an Admin, I can configure the global confirmation window duration (in hours, default 4, min 1, max 72) for all waitlists system-wide. Per-doctor configuration is out of scope for this build.
- WL-7: As an Admin, I can view waitlist fill-time statistics: average time from slot-available notification to confirmed booking, per doctor and across the hospital, for a selected date range.

#### Functional Requirements

- WLFR-1: The waitlist is per-doctor (not per-doctor-per-date). When a patient joins, they are placed at the end of that doctor's waitlist. FIFO ordering is maintained by `created_at` timestamp.
- WLFR-2: Waitlist entry statuses: `Waiting` (active in queue), `Notified` (slot offered, awaiting confirmation), `Confirmed` (patient accepted, appointment being created), `Expired` (confirmation window elapsed — patient moved to back of list, status of this entry is closed but patient remains on list as a new Waiting entry), `Removed` (patient or staff removed the entry).
- WLFR-3: "Moved to back" is implemented by creating a NEW `waitlist_entries` row with status='Waiting' and current `created_at`, while the old entry is set to status='Expired'. The patient's effective position is now last. There is no hard limit on how many times this can happen in this build.
- WLFR-4: The trigger for offering a slot is any appointment cancellation (status → Cancelled). On cancellation, the backend checks if the cancelled appointment's doctor has any `Waiting` waitlist entries. If yes, the first one (by `created_at`) is set to 'Notified' and a `waitlist_slot_available` notification is created (REQ-02). The freed slot is held for the confirmation window; it does not appear in the public slot query until the window expires without confirmation or the patient declines.
- WLFR-5: Slot confirmation is via `POST /waitlist/{entry_id}/confirm` (Patient only, own entry). This creates an appointment, sets the entry status to 'Confirmed', and removes the slot from the hold.
- WLFR-6: The global confirmation window is stored as a system configuration value (a `system_config` table with key='waitlist_confirmation_hours', value=TEXT). Admin reads/writes it via `GET /admin/config/waitlist` and `PUT /admin/config/waitlist` (body: `{ "confirmation_hours": 4 }`).
- WLFR-7: A patient may only have one active ('Waiting' or 'Notified') waitlist entry per doctor at a time. Attempting to join a doctor's waitlist twice returns 409 Conflict.

#### Acceptance Criteria

- AC-WL-1: Given Patient P joins Doctor D's waitlist and is the only entry, when Doctor D's only Scheduled appointment is cancelled, then within the same cancellation request: (a) a `waitlist_slot_available` notification is created for P, (b) P's waitlist entry status changes to 'Notified', (c) `notified_at` is set, (d) `confirmation_deadline` is set to `notified_at + 4 hours`.
- AC-WL-2: Given Patient P is 'Notified' and does not confirm within the confirmation window, when the expiry is checked (on P's next login), then P's entry status becomes 'Expired', a new 'Waiting' entry is created for P at the back of the list, and the next patient in queue (if any) is notified.
- AC-WL-3: Given Patient P is already on Doctor D's waitlist with status='Waiting', when P attempts to join Doctor D's waitlist again, then the response is 409 Conflict.
- AC-WL-4: Given the Admin sets confirmation_hours to 2, when a slot becomes available next, then the notification includes a confirmation deadline 2 hours from notification time.

#### Priority: Medium

---

### 9.10 REQ-10 — Discharge Summary & Follow-Up Scheduling (Medium)

**Description**: When a doctor marks an appointment Completed, an optional discharge summary panel allows them to record key findings, patient instructions, activity restrictions, and medication reminders. Optionally, they can book a follow-up appointment directly from this panel (using REQ-01 slot availability). The patient receives a notification (via REQ-02) and can view the discharge summary from their appointments page. Follow-up appointments appear in both the doctor's schedule and the patient's upcoming appointments.

**Affected roles**: Doctor (create discharge summary, book follow-up), Patient (read own discharge summaries).

**Hard dependencies**: REQ-01 (slot availability for follow-up booking), REQ-02 (notification to patient on summary creation).

#### User Stories

- DS-1: As a Doctor, when I mark an appointment as Completed, I am presented with an optional discharge summary panel (not mandatory — I can skip it).
- DS-2: As a Doctor, in the discharge summary panel, I can fill in: key findings (required if submitting the summary), patient instructions (nullable), activity restrictions (nullable), and medication reminders (nullable free text — distinct from the prescriptions workflow).
- DS-3: As a Doctor, within the same discharge summary panel, I can optionally book a follow-up appointment for the patient by selecting a date and available slot (using the REQ-01 availability API for my own schedule). The follow-up is created as a Scheduled appointment.
- DS-4: As a Patient, I receive a notification (event_type='discharge_summary_ready') when a discharge summary is created for my appointment. I can view the discharge summary from my appointment history page.
- DS-5: As a Patient, if a follow-up appointment was booked, it appears immediately in my upcoming appointments list and I receive a separate notification (event_type='follow_up_booked').
- DS-6: As a Doctor, the follow-up appointment booked from the discharge panel appears in my appointments list exactly as any other Scheduled appointment would.

#### Functional Requirements

- DSFR-1: Discharge summary is linked 1:1 to an appointment (unique on `appointment_id`). It can only be created for appointments with status='Completed'. Attempting to create a summary for a non-Completed appointment returns 400 Bad Request.
- DSFR-2: Fields: `appointment_id` (FK, UNIQUE), `patient_id` (FK), `doctor_id` (FK), `key_findings` (TEXT, required), `patient_instructions` (TEXT, nullable), `activity_restrictions` (TEXT, nullable), `medication_reminders` (TEXT, nullable — free text, not linked to the prescriptions table), `follow_up_appointment_id` (FK → appointments, nullable), `created_at`.
- DSFR-3: If `follow_up_appointment_id` is provided at summary creation time, the backend validates that the referenced appointment exists, has `doctor_id` matching the creating doctor, and has status='Scheduled'. If any condition fails, the summary creation request fails (400 Bad Request) — the doctor must book the follow-up first, then link it.
- DSFR-4: Alternatively (and preferably for UX), the discharge summary creation endpoint accepts an optional `follow_up` block in the request body (`{ "doctor_id": ..., "scheduled_at": "..." }`) and creates the follow-up appointment atomically in the same transaction. If slot validation fails (slot taken), the whole request fails. Sagar should decide between DSFR-3 and this atomic approach in Phase 4 (Open Item OI-8 in Section 9.18).
- DSFR-5: Patient read access: `GET /patients/me/discharge-summaries` and `GET /patients/me/appointments/{id}/discharge-summary`. Only the owning patient's summaries.
- DSFR-6: Doctor read access: `GET /doctor/appointments/{id}/discharge-summary` for appointments assigned to them.
- DSFR-7: Discharge summaries are included in the Patient Medical Record PDF export (REQ-08).
- DSFR-8: A discharge summary cannot be deleted after creation. It can be amended only once and must store both the original and amended text (amendment is out of scope for this build — if needed, raise a new requirement). In this build, discharge summaries are immutable after creation.

#### Acceptance Criteria

- AC-DS-1: Given Appointment A is Completed, when Doctor D creates a discharge summary with key_findings="Mild hypertension noted", then (a) a `discharge_summaries` row exists, (b) a notification with event_type='discharge_summary_ready' is created for the patient, (c) the patient can retrieve the summary via GET /patients/me/appointments/{A.id}/discharge-summary.
- AC-DS-2: Given Appointment A has status='Scheduled' (not Completed), when Doctor D attempts to create a discharge summary for it, then the response is 400 Bad Request.
- AC-DS-3: Given a discharge summary is created with a follow-up appointment slot, when the response is returned, then both the discharge summary row and the follow-up appointment row exist, the follow-up appears in the patient's upcoming appointments and in the doctor's schedule.
- AC-DS-4: Given Patient P calls `GET /patients/me/appointments/{A.id}/discharge-summary` for an appointment that belongs to Patient Q, then the response is 403 Forbidden.

#### Priority: Medium

---

### 9.11 REQ-11 — Patient Satisfaction Survey & Doctor Ratings (Medium)

**Description**: After an appointment is marked Completed (never Cancelled or NoShow), the system creates a pending survey record. The patient receives an in-app notification after 24 hours. The survey expires after 7 days if not responded to. Submissions are immutable. Doctors see their own aggregate rating. Admin sees all with patient identity. Admin can remove comment text without affecting star ratings.

**Affected roles**: Patient (submit survey), Doctor (view own aggregate + anonymized comments), Admin (view all, moderate comments).

**Hard dependency**: REQ-02 (Notification Center, for the survey availability notification).

#### User Stories

- SURV-1: As a Patient, approximately 24 hours after a Completed appointment, I receive an in-app notification (event_type='survey_available') inviting me to rate my experience.
- SURV-2: As a Patient, I can submit a rating with: doctor star rating (1–5 stars, required), overall experience star rating (1–5 stars, required), and an optional written comment (max 1,000 characters).
- SURV-3: As a Patient, once I submit a survey, it is permanently immutable — I cannot edit or delete it.
- SURV-4: As a Patient, I can only see whether I have submitted or not for each appointment — I cannot view the ratings I gave after submission (they are stored but not re-displayed to me, to prevent gaming or regret-editing).
- SURV-5: As a Doctor, I can view my aggregate rating dashboard: average doctor star rating across all submitted surveys, total submission count, and anonymized comment text (no patient name visible). Comments are listed in reverse chronological order.
- SURV-6: As an Admin, I can view all survey submissions with patient identity (name, patient ID) and the full comment text.
- SURV-7: As an Admin, I can remove the comment text from a specific submission (setting it to null or a placeholder "[Removed by admin]") without removing the star rating row. The star ratings always remain in the aggregate.
- SURV-8: A survey that has not been submitted 7 days after `trigger_after` is automatically expired and no longer accessible to the patient for submission.

#### Functional Requirements

- SURVFR-1: When an appointment is transitioned to status='Completed', a `satisfaction_surveys` row is created with: `appointment_id` (FK, UNIQUE), `patient_id`, `doctor_id`, `trigger_after` (TEXT, ISO 8601 = completed_at + 24 hours), `expires_at` (TEXT, ISO 8601 = trigger_after + 7 days), `submitted_at` (null), `doctor_star_rating` (null), `overall_star_rating` (null), `comment` (null), `is_comment_removed` (default false).
- SURVFR-2: Since the stack has no background job scheduler, the survey notification is dispatched using the same poll-on-login pattern as appointment reminders (REQ-02, NOTIFFR-3): on each authenticated request by the patient, the backend checks for any `satisfaction_surveys` rows where `patient_id=me AND submitted_at IS NULL AND trigger_after <= NOW() AND expires_at > NOW() AND notification_sent = false`. For each such row, a notification (event_type='survey_available') is created and `notification_sent` is set to true. The `notification_sent` column must be added to the `satisfaction_surveys` table (BOOLEAN, default false).
- SURVFR-3: Submission endpoint: `POST /patients/me/surveys/{survey_id}` (body: `{ "doctor_star_rating": 4, "overall_star_rating": 5, "comment": "..." }`). Validates: (a) survey belongs to calling patient, (b) `submitted_at` is null (not already submitted), (c) `expires_at > NOW()` (not expired), (d) both star ratings are integers 1–5. On success, sets `submitted_at = NOW()`.
- SURVFR-4: Doctor aggregate endpoint: `GET /doctor/ratings` — returns: `{ "average_doctor_rating": 4.3, "total_reviews": 47, "comments": [ { "comment": "...", "submitted_at": "..." }, ... ] }`. Patient name is never included in doctor-facing response.
- SURVFR-5: Admin view: `GET /admin/surveys` — paginated list of all submitted surveys with patient_id, patient_name (joined), doctor_id, doctor_name, ratings, comment, submitted_at. `GET /admin/surveys/{id}` — single record. `PATCH /admin/surveys/{id}/remove-comment` — sets comment to null and is_comment_removed to true. Is idempotent.
- SURVFR-6: A survey may only be created once per appointment (UNIQUE constraint on appointment_id). Surveys are never created for Cancelled or NoShow appointments — only Completed.
- SURVFR-7: If the appointment's doctor rating is requested by an unauthenticated visitor (public profile), only the aggregate average and total count are visible, not individual comments. This is Sagar's decision in Phase 3 whether to expose a public aggregate endpoint (Open Item OI-9 in Section 9.18).

#### Acceptance Criteria

- AC-SURV-1: Given Appointment A is marked Completed at 10:00 UTC on 2026-07-20, then a `satisfaction_surveys` row is created with `trigger_after = 2026-07-21T10:00:00` and `expires_at = 2026-07-28T10:00:00` and `submitted_at = null`.
- AC-SURV-2: Given Patient P logs in on 2026-07-21T11:00:00 (after trigger_after), when the backend checks pending surveys, then a notification with event_type='survey_available' is created for P and `notification_sent` is set to true. On P's next login, the notification is NOT created again for the same survey.
- AC-SURV-3: Given Patient P submits `doctor_star_rating=5, overall_star_rating=4, comment="Excellent care"`, then `submitted_at` is set and a subsequent POST to the same survey returns 409 Conflict (already submitted).
- AC-SURV-4: Given Admin calls `PATCH /admin/surveys/{id}/remove-comment`, then the survey's `comment` field becomes null and `is_comment_removed` becomes true. The star ratings are unchanged. A subsequent `GET /admin/surveys/{id}` shows is_comment_removed=true and comment=null.
- AC-SURV-5: Given a survey's `expires_at` has passed and `submitted_at` is null, when Patient P attempts to POST a submission, then the response is 403 Forbidden (or 400 Bad Request — Sagar to decide the appropriate code) and no submission is recorded.

#### Priority: Medium

---

### 9.12 REQ-12 — Corporate Health Check Packages (B2B) (Medium)

**Description**: A public-facing Corporate Health Packages section on the public site (no login required) showing tiered health check packages for businesses. Visitors can submit an inquiry form. Admin manages packages (create, edit, deactivate) and tracks the corporate inquiry pipeline (CRM-lite) with status, notes, and deal value.

**Affected roles**: Public visitor (view packages, submit inquiry), Admin (manage packages + inquiry pipeline).

#### User Stories

- CORP-1: As a visitor, I can view a "Corporate Health Packages" section on the public site listing 2–4 tiered packages, each with a name, tier order/badge, description, list of included services/tests, and displayed pricing range.
- CORP-2: As a visitor, I can submit a corporate inquiry form with: company name, contact person name, contact email, contact phone, estimated employee headcount, preferred package (dropdown of active packages), and preferred schedule (free text, e.g., "Q1 2027, weekends preferred").
- CORP-3: As a visitor, after submitting the inquiry form, I see an on-screen success confirmation. No email is sent.
- CORP-4: As an Admin, I can create, edit, and deactivate corporate packages. A deactivated package is hidden from the public site but remains in the database (referenced by existing inquiries).
- CORP-5: As an Admin, I can view all corporate inquiries in a pipeline view with filterable status: New, Contacted, Proposal Sent, Closed Won, Closed Lost.
- CORP-6: As an Admin, I can update the status of an inquiry, add internal notes, and set a deal value (in cents) for inquiries that progress to Closed Won.
- CORP-7: As an Admin, I can see the total revenue pipeline value: sum of `deal_value_cents` for all inquiries with status='Closed Won', displayed prominently on the pipeline page.

#### Functional Requirements

- CORPFR-1: Packages table fields: `package_id` (PK), `name` (TEXT, NOT NULL), `tier_order` (INTEGER, NOT NULL — used for display order), `description` (TEXT, NOT NULL), `included_services_json` (TEXT — JSON array of service strings), `price_range_display` (TEXT — a human-readable string, e.g., "$500–$800 per employee", stored as text, not as two integer fields; this is marketing copy), `is_active` (INTEGER, default 1). Only active packages (`is_active=1`) are returned by public endpoints.
- CORPFR-2: Package admin endpoints: `GET /admin/corporate/packages`, `POST /admin/corporate/packages`, `PUT /admin/corporate/packages/{id}`, `DELETE /admin/corporate/packages/{id}` (soft delete: sets `is_active=0`, does not delete the row). Public endpoint: `GET /public/corporate/packages` (returns active packages only, ordered by `tier_order`).
- CORPFR-3: Inquiry form fields: `company_name` (TEXT, required), `contact_name` (TEXT, required), `email` (TEXT, required, basic email format validation), `phone` (TEXT, nullable), `headcount` (INTEGER, nullable, must be > 0 if provided), `package_id` (FK → corporate_packages, nullable — visitor may not specify a package), `preferred_schedule` (TEXT, nullable), `status` (TEXT, default 'New', CHECK IN ('New','Contacted','ProposalSent','ClosedWon','ClosedLost')), `notes` (TEXT, nullable), `deal_value_cents` (INTEGER, nullable, ≥ 0), `created_at`, `updated_at`.
- CORPFR-4: Public inquiry submission endpoint: `POST /public/corporate/inquiries` (no auth required). On success, returns 201 Created with a confirmation message. No notification is created in the `notifications` table for this (Admin can see all inquiries via their pipeline view).
- CORPFR-5: Admin inquiry pipeline endpoints: `GET /admin/corporate/inquiries` (paginated, filterable by `?status=`), `GET /admin/corporate/inquiries/{id}`, `PATCH /admin/corporate/inquiries/{id}` (body: any subset of `{ status, notes, deal_value_cents }`). Inquiries cannot be deleted — only status can be advanced.
- CORPFR-6: Revenue pipeline total endpoint: included in the pipeline list response as a top-level field: `{ "items": [...], "total": N, "pipeline_total_cents": 1234500, ... }` where `pipeline_total_cents = SUM(deal_value_cents) WHERE status='ClosedWon'`.
- CORPFR-7: The corporate packages section location on the public site (new nav item? sub-section of About or Departments? standalone page?) is Sagar's decision in Phase 3 (Open Item OI-10 in Section 9.18). However, it must be reachable without login and must be indexed by the public nav in some form.

#### Non-Functional Requirements

- CORPNFR-1: The corporate inquiry pipeline is accessible to Admin only. Any non-Admin role calling `/admin/corporate/*` receives 403 Forbidden.
- CORPNFR-2: The public `/public/corporate/packages` and `/public/corporate/inquiries` (POST only) endpoints require no authentication — consistent with other public endpoints.

#### Acceptance Criteria

- AC-CORP-1: Given Admin creates a package with tier_order=1, name="Basic", is_active=1, when a visitor calls `GET /public/corporate/packages`, then the package appears in the response ordered by tier_order.
- AC-CORP-2: Given Admin deactivates a package (is_active=0), when a visitor calls `GET /public/corporate/packages`, then the deactivated package is absent from the response.
- AC-CORP-3: Given a visitor submits a valid inquiry form (company_name, contact_name, email), when the POST is processed, then a `corporate_inquiries` row exists with status='New' and the visitor sees a 201 response.
- AC-CORP-4: Given Admin updates inquiry status to 'ClosedWon' and sets deal_value_cents=500000, when `GET /admin/corporate/inquiries` is called, then `pipeline_total_cents` in the response includes this inquiry's deal value.
- AC-CORP-5: Given a non-Admin user calls `GET /admin/corporate/inquiries`, then the response is 403 Forbidden.
- AC-CORP-6: Given `headcount=-5` is submitted in the inquiry form, then the response is 400 Bad Request.

#### Priority: Medium

---

### 9.13 Out of Scope — Updates (Batch 2)

The following items previously listed in Section 4's Out of Scope list are now IN SCOPE as of this batch:

- ~~"Waitlist management for fully booked doctors"~~ — **Now in scope as REQ-09.** Remove from Section 4.
- ~~"Data export/interoperability tools (CSV/PDF export of records) beyond what's explicitly listed above"~~ — **Partially in scope: patient medical record PDF export (REQ-08) is now in scope. Admin analytics CSV export (REQ-06) is also now in scope.** The remaining items in that bullet (HL7/FHIR, general data portability tools) remain out of scope. Update Section 4 to narrow the exclusion to: "General data export/interoperability tools beyond the patient medical record PDF (REQ-08) and the admin analytics CSV (REQ-06), such as HL7/FHIR feeds, bulk data exports, and CSV export of clinical records."

Additionally, the following new out-of-scope clarifications apply to items introduced in this batch:

- Doctor public profile aggregate rating visibility (whether to show rating on the unauthenticated public doctor profile page) — deferred pending Open Item OI-9 resolution.
- Lab result file attachment (binary) embedding in the medical record PDF — out of scope (PDFFR-6). Text/values from result_data only.
- Per-doctor waitlist confirmation window configuration — out of scope (only global admin-configurable window in this build, per WLFR-6).
- Referral data in the patient medical record PDF — out of scope for this build (REFNFR-1).
- Discharge summary amendments after initial submission — out of scope (DSFR-8).
- A limit on the number of times a waitlist patient can be "moved to back" — out of scope; no removal policy in this build.
- Real background job processing for appointment reminders and survey notifications — out of scope (poll-on-login pattern used per NOTIFFR-3 and SURVFR-2).
- Survey data visible to patients after submission — out of scope (SURVFR-4; patients submit but cannot review their own submitted ratings).

---

### 9.14 Pre-Existing Schema Gap — Vitals Table (Resolved Here)

**Issue**: STF-4 (Section 2.4) has been in scope since the original requirements, allowing Staff to record vital signs (height, weight, blood pressure, temperature, pulse). No backing `vitals` table was defined in `db/schema.sql`. This gap is resolved as part of REQ-04.

**Resolution**: A `vitals` table must be added to `db/schema.sql` with the columns defined in VITFR-1 (Section 9.4). The existing `consultation_hours TEXT` column on `doctors` is unrelated (it is a doctor's stated hours, not patient vitals). No existing data is affected by adding the new table.

Sagar must include this table in the `db/schema.sql` update in Phase 4.

---

### 9.15 New Data Entities — Batch 2

The following entities are added to the data model (extending Section 3.4). Sagar must formalize these as SQL DDL in `db/schema.sql` and in `docs/architecture.md`.

- **DoctorAvailabilitySchedule**: `schedule_id` (PK), `doctor_id` (FK → doctors), `day_of_week` (INTEGER, 0=Mon, 6=Sun), `start_time` (TEXT, HH:MM), `end_time` (TEXT, HH:MM), `is_active` (INTEGER, default 1). Multiple rows per doctor per day allowed. UNIQUE constraint: (doctor_id, day_of_week, start_time).
- **DoctorSlotConfig**: `config_id` (PK), `doctor_id` (FK → doctors, UNIQUE), `slot_duration_minutes` (INTEGER, NOT NULL, default 30, CHECK IN (10,15,20,30,45,60)), `updated_at` (TEXT). One row per doctor.
- **DoctorAvailabilityBlock**: `block_id` (PK), `doctor_id` (FK → doctors), `block_date` (TEXT, YYYY-MM-DD), `start_time` (TEXT, HH:MM, nullable), `end_time` (TEXT, HH:MM, nullable), `reason` (TEXT, nullable), `created_at` (TEXT). Constraint: if start_time is non-null then end_time must also be non-null and vice versa.
- **Notification**: `notification_id` (PK), `recipient_user_id` (FK → users), `event_type` (TEXT, NOT NULL), `title` (TEXT, NOT NULL), `body` (TEXT, NOT NULL), `related_entity_type` (TEXT, nullable), `related_entity_id` (INTEGER, nullable), `is_read` (INTEGER, NOT NULL, default 0, CHECK IN (0,1)), `created_at` (TEXT).
- **NotificationSchedule** (for deferred triggers): `schedule_id` (PK), `appointment_id` (FK → appointments, nullable), `survey_id` (FK → satisfaction_surveys, nullable), `trigger_type` (TEXT, e.g. 'appointment_reminder', 'survey_available'), `trigger_at` (TEXT, ISO 8601), `is_fired` (INTEGER, default 0, CHECK IN (0,1)), `created_at` (TEXT).
- **IntakeForm**: `intake_form_id` (PK), `appointment_id` (FK → appointments, UNIQUE), `patient_id` (FK → patients), `chief_complaint` (TEXT, nullable), `symptom_duration` (TEXT, nullable), `allergies` (TEXT, nullable), `current_medications` (TEXT, nullable), `pain_scale` (INTEGER, nullable, CHECK BETWEEN 1 AND 10), `additional_notes` (TEXT, nullable), `submitted_at` (TEXT, nullable), `created_at` (TEXT).
- **Vitals**: `vital_id` (PK), `patient_id` (FK → patients), `appointment_id` (FK → appointments, nullable), `recorded_by_user_id` (FK → users), `systolic_bp` (INTEGER, nullable), `diastolic_bp` (INTEGER, nullable), `weight_kg` (REAL, nullable), `pulse_bpm` (INTEGER, nullable), `temperature_celsius` (REAL, nullable), `height_cm` (REAL, nullable), `recorded_at` (TEXT, NOT NULL).
- **Referral**: `referral_id` (PK), `referring_doctor_id` (FK → doctors), `receiving_department_id` (FK → departments), `receiving_doctor_id` (FK → doctors, nullable), `patient_id` (FK → patients), `reason` (TEXT, NOT NULL), `urgency` (TEXT, NOT NULL, CHECK IN ('Routine','Urgent')), `status` (TEXT, NOT NULL, CHECK IN ('Pending','Accepted','Declined','AppointmentBooked','Completed')), `receiving_doctor_note` (TEXT, nullable), `referred_appointment_id` (FK → appointments, nullable), `created_at` (TEXT), `updated_at` (TEXT).
- **DepartmentSymptomTag**: `tag_id` (PK), `department_id` (FK → departments), `tag_text` (TEXT, NOT NULL), `created_at` (TEXT). UNIQUE(department_id, LOWER(tag_text)) — case-insensitive uniqueness enforced application-side since SQLite's LOWER() in a UNIQUE index requires a functional index workaround; enforce in application layer.
- **WaitlistEntry**: `entry_id` (PK), `patient_id` (FK → patients), `doctor_id` (FK → doctors), `preferred_date` (TEXT, nullable), `status` (TEXT, NOT NULL, CHECK IN ('Waiting','Notified','Confirmed','Expired','Removed')), `notified_at` (TEXT, nullable), `confirmation_deadline` (TEXT, nullable), `created_at` (TEXT). Index on (doctor_id, status, created_at) for FIFO queue queries.
- **SystemConfig**: `config_key` (TEXT, PK), `config_value` (TEXT, NOT NULL), `updated_at` (TEXT). Single-row-per-key config store. Initial rows: ('waitlist_confirmation_hours', '4').
- **DischargeSummary**: `summary_id` (PK), `appointment_id` (FK → appointments, UNIQUE), `patient_id` (FK → patients), `doctor_id` (FK → doctors), `key_findings` (TEXT, NOT NULL), `patient_instructions` (TEXT, nullable), `activity_restrictions` (TEXT, nullable), `medication_reminders` (TEXT, nullable), `follow_up_appointment_id` (FK → appointments, nullable), `created_at` (TEXT).
- **SatisfactionSurvey**: `survey_id` (PK), `appointment_id` (FK → appointments, UNIQUE), `patient_id` (FK → patients), `doctor_id` (FK → doctors), `trigger_after` (TEXT, NOT NULL), `expires_at` (TEXT, NOT NULL), `notification_sent` (INTEGER, NOT NULL, default 0, CHECK IN (0,1)), `submitted_at` (TEXT, nullable), `doctor_star_rating` (INTEGER, nullable, CHECK BETWEEN 1 AND 5), `overall_star_rating` (INTEGER, nullable, CHECK BETWEEN 1 AND 5), `comment` (TEXT, nullable), `is_comment_removed` (INTEGER, NOT NULL, default 0, CHECK IN (0,1)).
- **CorporatePackage**: `package_id` (PK), `name` (TEXT, NOT NULL), `tier_order` (INTEGER, NOT NULL), `description` (TEXT, NOT NULL), `included_services_json` (TEXT, NOT NULL), `price_range_display` (TEXT, NOT NULL), `is_active` (INTEGER, NOT NULL, default 1, CHECK IN (0,1)), `created_at` (TEXT).
- **CorporateInquiry**: `inquiry_id` (PK), `company_name` (TEXT, NOT NULL), `contact_name` (TEXT, NOT NULL), `email` (TEXT, NOT NULL), `phone` (TEXT, nullable), `headcount` (INTEGER, nullable, CHECK(headcount > 0)), `package_id` (FK → corporate_packages, nullable), `preferred_schedule` (TEXT, nullable), `status` (TEXT, NOT NULL, DEFAULT 'New', CHECK IN ('New','Contacted','ProposalSent','ClosedWon','ClosedLost')), `notes` (TEXT, nullable), `deal_value_cents` (INTEGER, nullable, CHECK(deal_value_cents >= 0)), `created_at` (TEXT), `updated_at` (TEXT).

---

### 9.16 Updated Role-Based Access Control — Batch 2 Additions

The following rows extend (and do not replace) the RBAC tables in Sections 3.3 and 8.5.

| Resource | Admin | Doctor | Patient | Staff | Lab | BillingSpecialist |
|---|---|---|---|---|---|---|
| Doctor availability schedule & blocks | Full CRUD (all doctors) | Own only (CRUD) | Read (via slot query only) | Read (via slot query only) | None | None |
| In-app notifications | Read all (admin view — for audit if needed) | Own only | Own only | Own only | Own only | Own only |
| Intake forms | Read all (read-only) | Read (own patients only) | Own only (read/write until Completed) | Read all (read-only) | None | None |
| Vitals | Read all | Read (own patients only) | None (own vitals not directly queryable — included in PDF/record views) | Create + read all | None | None |
| Referrals | Read all (limited fields per REFNFR-2) | Create (for own patients) + accept/decline (own dept) + read own | Read own referrals (status only) | None | None | None |
| Analytics dashboard | Full access | None (403) | None (403) | None (403) | None (403) | None (403) |
| Symptom tags | Full CRUD | None | None | None | None | None |
| Public search | N/A (public) | N/A (public) | N/A (public) | N/A (public) | N/A (public) | N/A (public) |
| Patient PDF export | None (403) | None (403) | Own only | None (403) | None (403) | None (403) |
| Waitlist entries | Read all + delete any | None | Own only (create, view, remove self, confirm) | Read all + delete any | None | None |
| Discharge summaries | Read all | Create + read (own patients only) | Read own only | Read all | None | None |
| Satisfaction surveys | Read all + moderate comments | Read own aggregate + anonymized comments | Create (own, if triggered) + read own submission status | None | None | None |
| Corporate packages | Full CRUD | None | None | None | None | None |
| Corporate inquiries | Full pipeline management | None | None | None | None | None |

New explicit authorization rules (additive to AUTHZ-1 through AUTHZ-10):

- AUTHZ-11: Patient PDF export is strictly patient-self-service. No other role — including Admin or Doctor — may trigger a PDF export for a patient via the `/patients/me/export-pdf` endpoint. If Admin needs a patient record export, that is a separate future requirement.
- AUTHZ-12: Analytics endpoints under `/admin/analytics/*` are Admin-only. Role check at the router level returns 403 for all other roles before any database query is executed.
- AUTHZ-13: A Doctor may only accept/decline referrals directed to their own department. A Doctor in Department A cannot act on a referral directed to Department B.
- AUTHZ-14: Survey submissions are tied to the authenticated patient's own appointments only. A Patient cannot submit a survey for another patient's appointment.

---

### 9.17 Acceptance Criteria — Cross-Cutting (Batch 2)

These criteria apply across multiple requirements in this batch and are intended to be tested as integration scenarios.

- AC-BATCH2-1 (End-to-end booking with availability): Given a Doctor has a weekly schedule configured with 30-minute slots and no one-off blocks for a given Monday, when a Patient queries available slots for that Monday and books the first available slot, then the slot no longer appears in the available-slots response for that date, and an `appointment_confirmed` notification is created for both the Patient and the Doctor.
- AC-BATCH2-2 (Waitlist-to-booking pipeline): Given Patient A is #1 on Doctor D's waitlist, when an existing appointment with Doctor D is cancelled, then Patient A receives a 'waitlist_slot_available' notification within the same cancellation request, A's entry status changes to 'Notified', and if A confirms within the window, a new Scheduled appointment is created and A's entry moves to 'Confirmed'.
- AC-BATCH2-3 (Discharge-to-survey pipeline): Given Doctor D marks Appointment X as Completed and creates a discharge summary, then (a) a 'discharge_summary_ready' notification is created for the Patient, (b) a SatisfactionSurvey row is created with trigger_after = now + 24h, (c) when the Patient logs in 25 hours later, a 'survey_available' notification is created and notification_sent is set to true on the survey row.
- AC-BATCH2-4 (Role isolation on analytics): Given each of the six roles has a valid JWT, when each calls `GET /admin/analytics/appointments`, then only the Admin role receives a 200 response with data. All other roles receive 403 Forbidden.
- AC-BATCH2-5 (Notification unread count across events): Given a Patient has 0 notifications, when they book an appointment (creates appointment_confirmed), a lab result is finalized (creates lab_result_ready), and an invoice is created (creates invoice_created), then `GET /notifications/unread-count` returns `{ "unread_count": 3 }`.

---

### 9.18 Open Items for Architecture Stage (Batch 2)

The following items must be resolved by Sagar in Phase 3/4 before design is locked. Items marked with a Krishna escalation flag require a client decision, not just a technical decision — Sagar must route those to Akhil/Krishna before proceeding.

| ID | Requirement | Question | Escalate to Krishna? |
|---|---|---|---|
| OI-1 | REQ-01 | Can both Admin AND Doctor configure a doctor's availability? Or is it Admin-only (with doctor able to request changes via a workflow)? | Yes — Krishna must confirm who the owner of a doctor's schedule is |
| OI-2 | REQ-02 / REQ-11 | Poll-on-login pattern for deferred notifications: is this acceptable UX (notification appears on next login, not at the exact 24h mark)? | Yes — Krishna should confirm acceptable latency for reminders and survey notifications |
| OI-3 | REQ-08 | PDF library choice for FastAPI/Python: WeasyPrint (HTML-to-PDF, easier template) vs ReportLab (programmatic, more control)? | No — Sagar decides |
| OI-4 | REQ-04 | Chart library for React 19: Recharts vs react-chartjs-2 vs Nivo? | No — Sagar decides |
| OI-5 | REQ-05 | When a receiving doctor declines a referral, does it return to Pending (allowing another doctor in the department to accept) or does it stay Declined permanently? Krishna's requirement text implied a single Declined state but this may trap a referral | Yes — Krishna clarification needed |
| OI-6 | REQ-05 | Should Admin see the `reason` (clinical text) field on referrals, or only operational fields (dept, doctor, urgency, status)? | Yes — policy decision for Krishna |
| OI-7 | REQ-06 | Revenue "collected" series: use `invoices.created_at WHERE status='Paid'` (current simplification) or add a `paid_at` column to `invoices` for accurate month-of-payment reporting? | Yes — Krishna to decide if the approximation is acceptable |
| OI-8 | REQ-10 | Discharge summary + follow-up appointment: should the endpoint create them atomically in one transaction (better for integrity) or as two separate calls (simpler for the frontend to handle errors)? | No — Sagar decides; recommendation is atomic |
| OI-9 | REQ-11 | Should the doctor's aggregate star rating (average + count, no comments) be publicly visible on the unauthenticated doctor profile page? | Yes — Krishna must decide whether ratings are public-facing |
| OI-10 | REQ-12 | Where does the Corporate Packages section appear in the public site navigation? New top-level nav item? Sub-page of About? Separate footer link? | Yes — Sagar should propose in Phase 3 UX, then Krishna approves |
| OI-11 | REQ-02 | For `contact_form_received` notification — should it go to ALL active Admin+Staff users (could be a large fan-out), or only to Admin users? Or to a designated "contact" Staff role? | Yes — Krishna should clarify expected recipients |
| OI-12 | REQ-09 | Is the waitlist per-doctor only, or per-doctor-per-date (patient specifies a preferred date when joining, and is only notified when that specific date has a cancellation)? | Yes — Krishna clarification needed |
| OI-13 | REQ-01 | What happens to in-progress bookings (patient is on the slot-selection screen) when a doctor updates their availability mid-session? Is a session lock needed, or is the existing unique index sufficient? | No — Sagar decides; recommendation is unique index is sufficient with the 409 Conflict response |
| OI-14 | REQ-06 | What are the exact preset labels and durations for the date range picker? Proposed: Last 7 days, Last 30 days, Last 3 months, Last 12 months, Year to date, All time. Confirm or adjust. | Yes — Krishna to confirm or adjust |
| OI-15 | REQ-07 | Should the public search bar be embedded in the existing nav (all public pages) or only on a dedicated /search page? | Yes — Sagar to propose in Phase 3, Krishna approves |
| OI-16 | REQ-03 | Is there a cutoff time before which the intake form must be submitted (e.g., must be submitted at least 1 hour before the appointment)? Or can the patient submit it at any time before the appointment is marked Completed? | Yes — Krishna to clarify |
| OI-17 | REQ-12 | Should corporate inquiry submission trigger an in-app notification to Admin users (similar to contact_form_received)? | Yes — Krishna to clarify |
| OI-18 | REQ-11 | Should the Doctor's rating section be accessible as part of Phase 3's public doctor profile redesign? (Implies a public aggregate rating endpoint.) | Linked to OI-9 |
