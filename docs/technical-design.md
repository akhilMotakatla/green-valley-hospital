# Green Valley Hospital — Technical Design

Owner: Solution Architect (Sagar)
Consumers: Lavanya (Phase 5 task breakdown), Chintu (Phase 6 implementation), Gopal (Phase 8 QA)
Companion docs: `docs/requirements.md` (especially §9), `db/schema.sql`, `docs/api-spec.md`, `docs/architecture.md`

---

## Section 1 — Batch 2 Design (2026-07-20): REQ-01 through REQ-12

### 1.0 Architectural Decisions (Open Items Resolved by Sagar)

These are final. Chintu builds against them; do not re-open without a new Krishna cycle.

---

**OI-2 (Notification scheduler) — Decision: Poll-on-login, no background scheduler added.**

Rationale: Adding APScheduler or a Celery worker introduces a new process to manage, a Redis/broker dependency, and deployment complexity inconsistent with the current single-process, local-dev-only SQLite/FastAPI stack. For this build's scale (clinic, not hospital network), delayed notifications appearing on the user's next authenticated request is acceptable latency. The poll happens at a single shared utility function called by a FastAPI middleware or dependency on every authenticated request. Implementation pattern:

```
def check_and_fire_deferred_notifications(db: Session, user_id: int):
    now = datetime.utcnow().isoformat()
    # Fire appointment reminders
    pending_reminders = db.execute(
        "SELECT ns.* FROM notification_schedules ns
         JOIN appointments a ON ns.appointment_id = a.appointment_id
         WHERE a.patient_id = (SELECT patient_id FROM patients WHERE user_id = ?)
           AND ns.trigger_type = 'appointment_reminder'
           AND ns.trigger_at <= ?
           AND ns.is_fired = 0",
        (user_id, now)
    ).fetchall()
    for r in pending_reminders:
        create_notification(db, recipient_user_id=user_id, event_type='appointment_reminder', ...)
        db.execute("UPDATE notification_schedules SET is_fired = 1 WHERE schedule_id = ?", (r.schedule_id,))
    # Fire survey availability
    pending_surveys = db.execute(
        "SELECT * FROM satisfaction_surveys
         WHERE patient_id = (SELECT patient_id FROM patients WHERE user_id = ?)
           AND submitted_at IS NULL
           AND trigger_after <= ?
           AND expires_at > ?
           AND notification_sent = 0",
        (user_id, now, now)
    ).fetchall()
    for s in pending_surveys:
        create_notification(db, recipient_user_id=user_id, event_type='survey_available', ...)
        db.execute("UPDATE satisfaction_surveys SET notification_sent = 1 WHERE survey_id = ?", (s.survey_id,))
    db.commit()
```

This function is called from a shared FastAPI dependency (`get_current_user`) so it fires on every authenticated endpoint call with minimal overhead (indexed queries, early-exit when none pending).

**Known limitation**: If a patient never logs in, the notification is never fired. Appointment reminders fire at or after the 24h mark — never exactly at it. This is acceptable for this build.

---

**OI-3 (PDF library) — Decision: WeasyPrint.**

Rationale: WeasyPrint takes an HTML string (rendered via Python's `string.Template` or Jinja2) and converts it to PDF. This means the PDF layout is specified in HTML/CSS — far easier to maintain, review, and redesign than programmatic ReportLab coordinate math. It produces well-structured PDFs including proper page breaks, headers, footers, and watermarks via CSS `@page` and `::before`/`::after` rules. ReportLab would require low-level coordinate placement for the watermark which is error-prone. WeasyPrint is pip-installable (`pip install weasyprint`). It requires system fonts but does not require a headless browser.

`requirements.txt` must add: `weasyprint>=60.0`.

WeasyPrint's `@page` rule handles the watermark:
```css
@page {
    @bottom-center {
        content: "Green Valley Hospital | {patient_name} | ID:{patient_id}";
        font-size: 9pt;
        color: rgba(0,0,0,0.15);
        transform: rotate(-45deg);
    }
}
```

Actual diagonal watermark across page body: implemented using a `<div class="watermark">` with `position: fixed; top: 50%; left: 50%; transform: rotate(-45deg); opacity: 0.12;` — WeasyPrint honors fixed positioning.

---

**OI-4 (Chart library) — Decision: Recharts.**

Rationale: Recharts is built natively for React (not a wrapper over Chart.js Canvas API), is well-maintained, supports React 19, is fully TypeScript-typed, and produces accessible SVG output (fulfills VITFR-5's accessibility requirement via distinct line styles, not just color). Nivo is also React-native but heavier (d3 dependency graph). react-chartjs-2 wraps Canvas-based Chart.js which makes accessibility harder. Recharts uses `strokeDasharray` to distinguish series (e.g., systolic = solid, diastolic = dashed).

`package.json` must add: `recharts` (latest stable, currently ^2.12).

---

**OI-8 (Discharge summary + follow-up atomicity) — Decision: Atomic (single transaction).**

The discharge summary creation endpoint accepts an optional `follow_up` block. If provided, the backend creates the follow-up appointment first (validating slot availability via the same logic as `POST /appointments`), then creates the discharge summary linked to the new `follow_up_appointment_id`, all inside one SQLAlchemy transaction. If slot validation fails (slot taken), the entire transaction rolls back — the discharge summary is NOT created. The doctor must rebook a different slot and retry.

This is cleaner than two-step (DSFR-3) because it avoids a state where a summary exists referencing a not-yet-created appointment. The frontend discharge summary form includes the follow-up date/time picker inline and submits everything in one request.

---

**OI-13 (Session lock during availability edit) — Decision: No session lock; unique index is sufficient.**

The existing `uq_appointments_doctor_slot` unique index provides last-line defense. If a patient is on the slot-selection screen when a doctor updates their availability and removes that slot, the patient's subsequent `POST /appointments` call will either succeed (slot still valid) or get a 409 Conflict (slot gone or taken). The 409 response includes a `{"detail": "Slot no longer available. Please select another time."}` message, and the frontend re-fetches available slots. This is the same race-condition behavior as AC-AVL-4 — no special locking needed.

---

### 1.1 Documented Assumptions (Items Flagged for Krishna — Decisions Made Pending Confirmation)

These are my reasonable assumptions to unblock design. Each must be confirmed with Krishna before Chintu implements the affected feature. If Krishna overrides an assumption, the relevant section of this document and `db/schema.sql`/`docs/api-spec.md` must be updated before implementation begins.

| OI | Assumption Made | Impact if Krishna Overrides |
|---|---|---|
| OI-1 | Both Admin and Doctor can configure the doctor's availability (schedule, slot config, blocks). Doctor manages their own; Admin can view and override any doctor's. | If Admin-only: remove doctor-scoped availability write endpoints; add a "request change" workflow instead. |
| OI-5 | When a receiving doctor declines a referral, the referral status transitions to `Declined` and stays there (terminal). The referring doctor can create a new referral if needed. **This overrides REFFR-4** which says "returns to Pending". Rationale: a permanent Declined state is auditable and avoids zombie referrals cycling indefinitely. | If returns-to-Pending: change the Declined transition to reset status='Pending' and notify remaining dept doctors; no schema change needed (status CHECK already allows both paths). |
| OI-6 | Admin sees referral operational fields only (department, doctor names, urgency, status, dates). Admin does NOT see the clinical `reason` field — consistent with ADM-10. | If Admin sees reason: remove the field exclusion from the admin referrals serializer. |
| OI-7 | A `paid_at TEXT` column is added to `invoices` table. It is set (server-side, to current UTC timestamp) when invoice status changes to 'Paid'. The revenue analytics "collected" series uses `paid_at` month grouping, not `created_at WHERE status='Paid'`. | If approximation is acceptable: drop the `paid_at` column and use `created_at WHERE status='Paid'` for the revenue chart — simpler but less accurate. |
| OI-9 | Doctor aggregate star rating (average + count) is NOT publicly visible on the unauthenticated public doctor profile. It is visible only within the authenticated doctor portal (`/doctor/ratings`) and admin portal. The public `/api/public/doctors/{id}` endpoint does NOT include rating fields. | If public: add `average_rating` and `total_reviews` fields to the public doctor profile response; add a public-safe aggregate endpoint. No schema change needed. |
| OI-10 | Corporate Health Packages appear as a new top-level public nav item ("For Organizations") linking to `/corporate`. This gives it high visibility for B2B conversion without cluttering the main patient-facing nav. The `/corporate` route is added under `PublicLayout`. | If sub-page of About or footer-only: move route location and remove nav item. |
| OI-11 | `contact_form_received` notification goes to all active Admin and Staff users (as specified in NOTIFFR event table). No designation/role sub-filtering in this build. Noted concern: this can fan-out to many users at once if Staff headcount is large — acceptable for current scale. | If Admin-only: restrict recipient query to `role='Admin'` only. |
| OI-12 | Waitlist is **per-doctor-per-date** (patient specifies a preferred date when joining; a slot notification is only sent when a cancellation on that specific date opens up). **This deviates from WLFR-1** which says per-doctor globally. The `preferred_date` column in `waitlist_entries` is made NOT NULL (not nullable as in §9.15). Uniqueness constraint: one active ('Waiting' or 'Notified') entry per (patient_id, doctor_id, preferred_date). | If per-doctor globally: make `preferred_date` nullable, change uniqueness constraint to (patient_id, doctor_id), and update cancellation trigger to notify regardless of date. |
| OI-14 | Analytics date range presets: "Last 7 days", "Last 30 days", "Last 3 months", "Last 12 months", "Year to date", "All time" (as proposed in requirements). No changes to these labels. | If different labels/durations: only frontend change needed. |
| OI-15 | Public search bar is embedded in the public site navigation header (compact input visible on all public pages, all viewports ≥ 768px; on mobile, a search icon button reveals the input). Submitting navigates to `/search?q={query}` results page. | If dedicated page only: remove nav bar search; add a prominent search section on the home page and a link to /search. |
| OI-16 | No cutoff time for intake form submission. Patient can submit/re-edit the intake form at any time before the appointment is marked Completed. Once Completed, form becomes permanently read-only (INTAKEFR-4). | If cutoff required: add a check in the PATCH endpoint: `if appointment.scheduled_at - now < cutoff_minutes: return 403`. Schema unchanged. |
| OI-17 | Corporate inquiry submission (`POST /public/corporate/inquiries`) does NOT create an in-app notification. Admin sees all inquiries via their pipeline view. Rationale: inquiry volume may be high and notifications would be noisy; pipeline view is the right tool for this. | If notification wanted: add a fan-out notification (event_type='corporate_inquiry_received') to all active Admin users in the POST handler. |
| OI-18 | Linked to OI-9. Doctor ratings section is NOT added to the public doctor profile in this build. This is deferred until OI-9 is confirmed. |  |

---

## Phase 3 — Product & UX Design

### 3.1 REQ-01 — Doctor Availability & Slot Management

**Portal/pages affected**: Doctor portal (own availability config), Admin portal (manage any doctor's availability), Patient portal (slot selection during booking), Staff portal (slot selection during front-desk booking).

**User Journey — Doctor configuring own availability (happy path)**:
1. Doctor navigates to `/doctor/availability` (new page, "Schedule" in sidebar).
2. Page loads a weekly grid (Mon–Sun) showing any existing time windows per day.
3. Doctor clicks "+ Add Window" on a day, enters start time and end time (time pickers, HH:MM), saves.
4. Doctor sets slot duration using a dropdown (10/15/20/30/45/60 min, default 30). Change saved immediately via PUT.
5. Doctor sees a preview: "Your 30-minute slots on Mondays: 09:00, 09:30, 10:00..."
6. Doctor clicks "Block a Date" to open a modal: date picker, optional time range. If no time range, full-day block. Saves block.
7. Block appears in a "Upcoming Blocks" list below the weekly grid.

**User Journey — Admin managing a doctor's availability**:
1. Admin navigates to `/admin/users`, finds the doctor, clicks "Manage Availability" (new action button on doctor user row).
2. Same availability editor UI loads, pre-populated with that doctor's current schedule. Admin can edit all fields.
3. Admin saves — endpoint is the admin-scoped availability endpoints.

**User Journey — Patient booking with slot selection (replaces current BookAppointmentPage flow)**:
1. Patient is on `/patient/book`. Selects department → doctor → date (date picker).
2. System calls `GET /api/doctors/{id}/available-slots?date=YYYY-MM-DD`. Displays available slots as a time-button grid.
3. Patient clicks a slot time button (e.g., "10:30 AM"). Button highlights.
4. Patient confirms booking. `POST /api/appointments` called with `doctor_id`, `scheduled_at` = selected slot.
5. On success: appointment created, redirected to `/patient` (appointments list) with a success toast.
6. If no slots available for selected date: "No slots available for this date" message + a "Join Waitlist" button (REQ-09 entry point).
7. If 409 on booking submit: "That slot was just booked by another patient. Please choose another time." Slot list auto-refreshes.

**User Journey — Error paths**:
- Date picker for booking: selecting past dates is disabled (grey, non-clickable).
- Slot time list is empty for selected date: "No availability for this date" message, suggest trying adjacent dates.
- Network error loading slots: `<PageError>` component with "Try again" button.

**Navigation changes**:
- Doctor sidebar: new item "Schedule" (`CalendarDays` icon) → `/doctor/availability`.
- Admin sidebar: no new item (access via Users page doctor row action button).

**UI states**:
- Loading: skeleton for the weekly grid.
- Empty (no schedule configured): illustrated empty state "No availability configured yet. Add your first time window to start accepting appointments." with a CTA button.
- Error: `<PageError>` component.
- Success save: inline toast "Schedule updated".

---

### 3.2 REQ-02 — In-App Notification Center

**Portal/pages affected**: All six role portals (bell icon in `AppShell` topbar), plus a new full-page notifications list per role.

**User Journey — Viewing notifications (happy path)**:
1. User logs in. `AppShell` topbar calls `GET /api/notifications/unread-count` on mount.
2. Bell icon shows a red badge with count (hidden if count = 0). Badge uses the existing `BillingNotificationsPage` pattern from the billing role as reference.
3. User clicks bell. A dropdown panel slides in (right-aligned, z-index above content, below modal). Shows 20 most recent notifications, newest first.
4. Unread notifications have a light blue/primary background highlight and bold title.
5. User clicks a notification item. If `related_entity_type` is set, navigates to the relevant page (e.g., appointment detail, invoice page). `PATCH /api/notifications/{id}/read` called.
6. User clicks "Mark all as read" button at top of panel. `POST /api/notifications/mark-all-read` called. Badge disappears, all items lose highlight.
7. User clicks "View All" link at bottom of panel → navigates to `/notifications` (new route, inside current role's `AppShell`).

**Full notifications page (`/notifications`)**:
- Paginated list (page_size=20). Calls `GET /api/notifications?page=&page_size=`.
- Filter by read/unread toggle.
- Each row: event icon, title, body, timestamp, read status badge.

**User Journey — Poll-on-login deferred notification**:
1. Patient logs in 25h after appointment was completed. Backend middleware fires `check_and_fire_deferred_notifications`.
2. A new notification appears in the bell dropdown with event_type='survey_available'. Patient sees it on next bell click without needing a page refresh.

**Navigation changes** (all role sidebars):
- No new sidebar item — notifications are accessed via the topbar bell.
- Add new route `/{role}/notifications` (or shared `/notifications` with role guard) in `App.tsx`.
- The existing `VI-SHELL-4` `Bell` placeholder in `AppShell` topbar must be wired up (was placeholder only).

**UI states**:
- Bell badge: shows count badge only when unread_count > 0.
- Empty panel: "You're all caught up. No notifications." centered text with `BellOff` icon.
- Loading panel: 3-row skeleton.
- New notification types have distinct icons: `CalendarCheck` (appointment), `FlaskConical` (lab), `Receipt` (invoice), `UserCheck` (referral), `ClipboardList` (survey), `AlertCircle` (account), `BarChart2` (waitlist).

---

### 3.3 REQ-03 — Patient Pre-Visit Intake Form

**Portal/pages affected**: Patient portal (fill/edit), Doctor portal (read-only view in appointment detail), Staff portal (read-only view).

**User Journey — Patient filling intake form (happy path)**:
1. Patient views appointment detail (from appointments list, clicking a row or "View Details" button on a Scheduled appointment).
2. A "Pre-Visit Intake Form" card is visible below appointment info. If not yet submitted: "Not submitted yet" state with a "Fill Out Now" button.
3. Patient clicks "Fill Out Now". Form expands in-place (or navigates to `/patient/appointments/{id}/intake`).
4. Patient fills in fields: Chief Complaint (required), Symptom Duration (required), Allergies, Current Medications, Pain Scale (1–10 slider), Additional Notes.
5. Patient can "Save Draft" (all fields optional) or "Submit" (required fields validated client-side and server-side).
6. On submit success: form collapses showing "Submitted on [date]" status card with a pencil icon to re-edit.
7. Patient can re-edit and resubmit (updated `submitted_at`) until appointment is Completed.

**User Journey — After appointment Completed**:
1. Patient views past appointment. Intake form section shows "Submitted" status with all field values (read-only view).
2. No edit button visible. Any attempt to modify (direct API call) returns 403.

**User Journey — Doctor viewing intake**:
1. Doctor clicks on a patient's appointment row → appointment detail view (within DoctorPatientRecordsPage or new `/doctor/appointments/{id}` route).
2. "Patient Intake Form" section shows. If submitted: all fields displayed read-only. If not submitted: "Patient has not yet submitted an intake form" informational message.

**Navigation changes**:
- No new nav items. Intake form is embedded within existing appointment detail views.
- New routes: `/patient/appointments/:id/intake` (patient write), `/doctor/appointments/:id` (doctor detail view — may already exist or be inline in records page).

**UI states**:
- Not submitted (patient view): CTA to fill out form.
- Draft saved (patient): "Draft saved [time]" subtle indicator with "Continue Editing" + "Submit" buttons.
- Submitted (patient): Read-only view with "Edit Submission" button.
- Completed (patient): Read-only, no edit button.
- Doctor / Staff view: always read-only. "Not submitted" message.
- Loading: skeleton fields.

**Accessibility**: Pain scale uses a `<input type="range" min="1" max="10">` with explicit numeric label display and ARIA attributes.

---

### 3.4 REQ-04 — Vitals Trend Visualization

**Portal/pages affected**: Staff portal (record vitals on patient detail), Doctor portal (view vitals trend on patient records page).

**User Journey — Staff recording vitals (happy path)**:
1. Staff on `/staff/patients/{patientId}` (patient detail page). New "Vitals" tab or section on the page.
2. "Record Vitals" button opens a form: BP Systolic, BP Diastolic, Weight (kg), Pulse (bpm), Temperature (°C), Height (cm, optional). Optional appointment link (dropdown of the patient's Scheduled appointments today).
3. Staff clicks "Save Vitals". Validation: BP both-or-neither rule, ranges checked.
4. Success: new vitals row appears in a table below the form.

**User Journey — Doctor viewing vitals trend**:
1. Doctor on `/doctor/patients/{patientId}` (patient records page). New "Vitals Trend" section added below existing records.
2. If fewer than 2 records: informational callout "Not enough vitals data to display trend (minimum 2 readings required)." Table of individual readings shown.
3. If 2+ records: four Recharts `LineChart` components displayed in a 2×2 grid:
   - BP chart: two lines — Systolic (solid) and Diastolic (dashed), both in blue tones.
   - Weight chart: single line.
   - Pulse chart: single line.
   - Temperature chart: single line.
   - X-axis: appointment date or `recorded_at` date. Y-axis: measurement value with unit label.
4. Below charts: tabular list of all individual readings with date, recorder name, and all values.

**Navigation changes**: No new nav items. Vitals section is embedded within existing patient detail/records pages.

**UI states**:
- Empty (< 2 readings): informational message + table (may still show 1 reading in table).
- Loading charts: skeleton loaders in the chart areas.
- Error loading vitals: `<PageError>` component.
- Validation error on save: inline field errors below each input.

**Accessibility**: All chart colors supplemented with line-dash patterns (VITFR-5). Charts have ARIA labels. Recharts `<Legend>` shows both color and dash-pattern symbols.

---

### 3.5 REQ-05 — Inter-Department Referral Management

**Portal/pages affected**: Doctor portal (send and receive referrals), Patient portal (view own referral status).

**User Journey — Doctor creating a referral (happy path)**:
1. Doctor on `/doctor/patients/{patientId}` (patient records page). New "Referrals" section with "Create Referral" button.
2. Modal opens: Receiving Department (dropdown), Receiving Doctor within dept (optional dropdown, loads on dept selection), Clinical Reason (required textarea), Urgency (Routine / Urgent radio).
3. Doctor submits. On success: referral appears in "Sent Referrals" list with status "Pending" and a `referral_received` notification is sent to receiving dept doctors (REQ-02).
4. Doctor can see status changes in "Sent Referrals" list as receiving doctor accepts/declines.

**User Journey — Doctor receiving and accepting a referral**:
1. Doctor on `/doctor/referrals` (new page, "Referrals" in sidebar). Two tabs: "Received" and "Sent".
2. "Received" tab shows referrals for their department (Urgent first), with patient info, referring doctor, reason, urgency badge.
3. Doctor clicks "Accept". Modal: optional acceptance note. Confirms. Referral status → Accepted. Notification sent to patient and referring doctor.
4. Doctor is now in the referral, can click "Book Appointment" within the referral card → opens the appointment booking form pre-populated with patient and reason. On booking: referral status → AppointmentBooked.
5. After consultation: doctor clicks "Mark Complete" → referral status → Completed.

**User Journey — Referral declined**:
1. Doctor clicks "Decline". Modal: required decline reason. Confirms.
2. Referral status → Declined. Notification sent to patient and referring doctor.
3. Referring doctor sees status "Declined" in their "Sent" tab. They can create a new referral for the same patient if needed.

**Patient journey — viewing referrals**:
1. Patient on `/patient/referrals` (new page, "Referrals" in patient sidebar).
2. List of all referrals: department, doctor name (if assigned), urgency, current status, and timeline.
3. Read-only. No patient action available.

**Navigation changes**:
- Doctor sidebar: new item "Referrals" (`ArrowRightLeft` icon) → `/doctor/referrals`.
- Patient sidebar: new item "Referrals" (`ArrowRightLeft` icon) → `/patient/referrals`.

**UI states**:
- Empty (no referrals sent/received): illustrated empty state per tab.
- Urgent referrals: orange/amber urgency badge, pinned to top of received list.
- Status badges: use existing `<StatusBadge>` component, add Pending/Accepted/Declined/AppointmentBooked/Completed variants.

---

### 3.6 REQ-06 — Analytics Dashboard (Admin)

**Portal/page affected**: Admin portal, new page `/admin/analytics`.

**User Journey — Admin viewing analytics (happy path)**:
1. Admin navigates to `/admin/analytics` ("Analytics" in admin sidebar, `BarChart2` icon).
2. Page loads with a date range picker at the top. Default range: Last 30 days. Presets shown as buttons below the range inputs.
3. Four chart sections load independently (lazy/parallel fetch):
   - **Appointment Volume**: Recharts `BarChart` (grouped bars — Completed green, Cancelled amber, NoShow red, Scheduled blue). X-axis: month. Data from `GET /admin/analytics/appointments`.
   - **No-Show Rate**: Recharts `LineChart`. Single line: % NoShow per month. Data included in appointments response.
   - **Revenue**: Recharts `LineChart`, two series — Invoiced (blue) and Collected (green). Data from `GET /admin/analytics/revenue`.
   - **Department Rankings**: Recharts `BarChart` (horizontal). Departments on Y-axis, appointment count on X-axis. Data from `GET /admin/analytics/departments`.
   - **Patient Acquisition**: Recharts `AreaChart`. New patients per month. Data from `GET /admin/analytics/patient-acquisition`.
4. Each section has a "Export CSV" button. Clicking calls the same endpoint with `?format=csv` and triggers browser download.
5. Changing the date range re-fetches all four sections.

**Navigation changes**:
- Admin sidebar: new item "Analytics" (`BarChart2` icon) → `/admin/analytics`.

**UI states**:
- Loading: skeleton charts (grey animated rectangles in chart area).
- Empty range (no data): "No data for the selected period" message inside each chart area.
- Error: `<PageError>` per section (sections are independent — one failing doesn't break others).
- Export in progress: "Downloading..." spinner on the export button.

---

### 3.7 REQ-07 — Public Symptom / Condition Search

**Portal/page affected**: Public site (search bar in nav + new `/search` results page), Admin portal (symptom tag management).

**User Journey — Visitor searching (happy path)**:
1. Visitor sees a search bar in the public nav header (compact input with `Search` icon, placeholder "Search symptoms, conditions, doctors...").
2. Visitor types "chest pain" and presses Enter or clicks the search icon.
3. Browser navigates to `/search?q=chest+pain`.
4. Results page loads: two sections — "Departments" (cards with icon, name, description snippet, "View Department" link) and "Doctors" (cards with photo, name, specialty, "View Profile" link). Departments appear first.
5. No results: "No results found for 'chest pain'" with a suggestion to browse departments or contact the hospital.

**User Journey — Admin managing symptom tags**:
1. Admin on `/admin/departments`. Each department row has a "Symptom Tags" button (count badge showing current tag count).
2. Clicking opens a slide-out panel or navigates to `/admin/departments/{id}/tags` (inline expansion preferred).
3. Admin sees existing tags as removable chips (`X` button per tag). Type-ahead input to add new tag. "Add" button.
4. Max 50 tags per department — when reached, input is disabled and a message appears.

**Navigation changes**:
- Public nav: search bar embedded (OI-15 decision). Desktop: always visible as compact input. Mobile: search icon `Search` button expands a full-width input overlay.
- New public route `/search` under `PublicLayout`.
- Admin: symptom tag management added to `/admin/departments` page (no new top-level nav item).

**UI states**:
- Search bar empty (< 2 chars): no results fetch, show minimal placeholder.
- Loading results: skeleton cards.
- No results: friendly empty state message.
- Total count badge: shown at top of results page ("5 results for 'chest pain'").

---

### 3.8 REQ-08 — Patient Medical Record Export (PDF)

**Portal/page affected**: Patient portal, records page (`/patient/records`).

**User Journey — Patient exporting PDF (happy path)**:
1. Patient on `/patient/records`. New "Export PDF" button in the page header (secondary button, `Download` icon from Lucide).
2. Clicking opens a small modal: optional date range (start/end date pickers). "Export All Records" (no date filter) or "Export Selected Range" (date filter applied).
3. Patient clicks "Generate PDF". Button shows spinner.
4. Browser downloads a PDF file named `GVH_MedicalRecord_{patient_id}_{YYYYMMDD}.pdf` immediately. No page navigation.
5. Modal closes after download starts.

**User Journey — Error paths**:
- Backend timeout (> 30s): "PDF generation timed out. Please try a smaller date range."
- No records in selected range: PDF still generates, showing "No visits for the selected period" in the relevant section.

**Navigation changes**: No new pages or nav items. Feature is embedded in the existing patient records page.

**PDF structure (visual design)**:
- Cover page: hospital name (large), "Medical Record" subtitle, patient name/DOB/ID, export date, date range.
- Diagonal watermark on every page (low opacity, 45°).
- Per-appointment sections: date, doctor name, department, visit notes, diagnosis, prescriptions table, lab results, vitals (if recorded).
- Clean, print-optimized: no dark backgrounds, no glassmorphism — white background, black/dark grey text.

**UI states**:
- Generating: button spinner.
- Success: file download begins (browser handles it natively).
- Error: toast message with retry option.

---

### 3.9 REQ-09 — Appointment Waitlist System

**Portal/pages affected**: Patient portal (join waitlist from booking flow, view waitlist), Staff portal (manage waitlist), Admin portal (config + stats).

**User Journey — Patient joining waitlist (happy path)**:
1. Patient on `/patient/book`. Selects doctor and date. Slot list returns empty ("No slots available on this date").
2. "Join Waitlist for [date]" button appears below the empty slot list.
3. Patient clicks. A brief confirmation: "You've joined Dr. [Name]'s waitlist for [date]. We'll notify you when a slot opens."
4. New waitlist entry created. Patient can see it in `/patient/waitlist` (new page).

**User Journey — Patient receives slot notification and confirms**:
1. Patient gets a `waitlist_slot_available` notification in the bell dropdown. Notification body: "A slot opened up with Dr. [Name] for [date]. Confirm by [deadline time]."
2. Patient clicks notification → navigates to `/patient/waitlist`.
3. Waitlist entry shows "Slot Available — Confirm by [time]" with a countdown and a "Confirm Appointment" button.
4. Patient clicks "Confirm Appointment". `POST /api/waitlist/{entry_id}/confirm`. New appointment created.
5. Confirmation: "Appointment booked! View in your appointments."

**User Journey — Confirmation window expires**:
1. Patient logs in after deadline. On poll-on-login, backend detects expired entry, sets it to 'Expired', creates a new 'Waiting' entry at back of queue.
2. Patient sees on `/patient/waitlist`: old entry shows "Expired — Moved to back of queue". New entry shows "Waiting (Position: [N])".

**Staff journey — managing waitlist**:
1. Staff on `/staff/waitlist` (new page or section within StaffDirectoryPage). Doctor selector → shows that doctor's waitlist.
2. Table: patient name, join date, preferred date, position, status.
3. "Remove" button per row → confirmation modal → removes entry with recorded reason.

**Admin config**:
1. Admin at `/admin/config` (new page) or inline in `/admin` dashboard. "Waitlist Settings" section.
2. "Confirmation Window: [4] hours" (editable number input). Save button.

**Navigation changes**:
- Patient sidebar: new item "Waitlist" (`Clock` icon) → `/patient/waitlist`.
- Staff sidebar: new item "Waitlist" (`Clock` icon) → `/staff/waitlist`.
- Admin sidebar: new item "Configuration" (`Settings` icon) → `/admin/config` (or merge into existing dashboard settings section).

**UI states**:
- Empty waitlist (patient): "You're not on any waitlist." with optional CTA.
- Notified entry: highlighted card with countdown timer and confirm button.
- Expired entry: greyed card with "Moved to back of queue" label.
- Staff empty list for doctor: "No patients currently on waitlist for this doctor."

---

### 3.10 REQ-10 — Discharge Summary & Follow-Up Scheduling

**Portal/pages affected**: Doctor portal (create discharge summary when completing appointment), Patient portal (view discharge summaries).

**User Journey — Doctor creating discharge summary (happy path)**:
1. Doctor on their appointments page. Clicks "Complete & Discharge" button on a Scheduled appointment (replaces or augments the current "Update Status" flow).
2. A full-screen modal or slide-out panel appears: "Discharge Summary".
3. Required field: Key Findings (textarea). Optional fields: Patient Instructions, Activity Restrictions, Medication Reminders (all textareas).
4. "Book Follow-Up Appointment" section (collapsible, default collapsed). Doctor expands it, picks a date (date picker), system loads available slots for that date from the doctor's own schedule. Doctor selects a slot.
5. Doctor clicks "Complete & Save Discharge Summary". Button shows spinner.
6. Backend: marks appointment Completed, creates discharge summary, optionally creates follow-up appointment — all atomic.
7. Success: "Appointment marked Complete. Discharge summary saved. Follow-up appointment booked." Toast message.
8. Doctor can skip the discharge summary entirely by using the existing "Update Status → Completed" action (if one exists) without opening the discharge panel.

**User Journey — Patient viewing discharge summary**:
1. Patient on `/patient` (appointments). Past appointment shows a "View Discharge Summary" button (or link) in the appointment row.
2. Navigates to `/patient/appointments/{id}/discharge` (or inline expansion).
3. Full discharge summary displayed: Key Findings, Instructions, Restrictions, Medication Reminders, Follow-Up Appointment (if booked, with date/time).
4. Follow-up appointment also appears in the patient's upcoming appointments list.

**Navigation changes**:
- Patient sidebar: no new item. Discharge summaries are accessible from the appointments list.
- Doctor portal: no new sidebar item. Discharge panel is triggered from the appointments list actions.

**UI states**:
- Discharge panel: all optional fields collapsed by default, expand on click.
- Follow-up date picker: only future dates, only dates where the doctor has slots available.
- Follow-up slot list: same empty state as booking ("No slots on this date").
- Patient view: read-only card with clear section headers.

---

### 3.11 REQ-11 — Patient Satisfaction Survey & Doctor Ratings

**Portal/pages affected**: Patient portal (submit survey), Doctor portal (view aggregate ratings).

**User Journey — Patient submitting survey (happy path)**:
1. Patient receives `survey_available` notification 24h after appointment completion.
2. Notification navigates to `/patient/surveys` (new page or inline on appointment detail).
3. Page shows: pending surveys (triggered but not yet expired and not yet submitted). Each survey: doctor name, appointment date.
4. Patient clicks "Rate Experience". Survey form: Doctor star rating (1–5 interactive stars), Overall Experience star rating (1–5), Comment (optional, max 1000 chars, char counter).
5. Patient submits. `submitted_at` set. Survey moves to "Submitted" section (status only shown — no rating values re-displayed per SURVFR-4).
6. Expired surveys shown in a "Expired" section — greyed out, "Submission period ended" label.

**User Journey — Doctor viewing ratings**:
1. Doctor navigates to `/doctor/ratings` (new page, "My Ratings" in sidebar, `Star` icon).
2. Page shows: aggregate score (large star display, e.g., "4.3 / 5 stars, 47 reviews"), total review count.
3. Anonymized comment list below: comment text + submission date. No patient name shown.
4. If 0 reviews: "No ratings yet. Ratings appear after patients complete their post-visit survey."

**User Journey — Admin moderating surveys**:
1. Admin on `/admin/surveys` (new page, "Surveys" in sidebar).
2. Full table: patient name, doctor, appointment date, doctor rating, overall rating, comment text, submission date.
3. Filterable by doctor, date range, comment presence.
4. "Remove Comment" button per row → confirmation → comment set to null, `is_comment_removed = true`. Star ratings remain.

**Navigation changes**:
- Patient sidebar: new item "Surveys" (`Star` icon) → `/patient/surveys`.
- Doctor sidebar: new item "My Ratings" (`Star` icon) → `/doctor/ratings`.
- Admin sidebar: new item "Surveys" (`Star` icon) → `/admin/surveys`.

**UI states**:
- Pending survey: highlighted card with "Rate Now" CTA button.
- Submitted survey: greyed card with "Submitted" badge.
- Expired survey: greyed card with "Expired" badge.
- Doctor ratings page (0 reviews): empty state.
- Admin comment removed: cell shows "[Removed by admin]" in italic muted text.

---

### 3.12 REQ-12 — Corporate Health Check Packages (B2B)

**Portal/pages affected**: Public site (new `/corporate` page), Admin portal (new corporate management pages).

**User Journey — Visitor viewing packages and submitting inquiry (happy path)**:
1. Visitor sees "For Organizations" link in the public site nav → navigates to `/corporate`.
2. Page shows: page hero ("Corporate Health Solutions for Your Team"), package cards (2–4 tiers).
3. Each package card: tier badge/order, package name (e.g., "Wellness Basic"), description, included services as a bulleted list, price range display (e.g., "$500–$800 per employee"), "Get a Quote" CTA button.
4. Below packages: inquiry form. Fields: Company Name, Contact Person, Email, Phone (optional), Employee Headcount, Preferred Package (dropdown), Preferred Schedule (text).
5. Visitor submits. `POST /api/public/corporate/inquiries`. Success: "Thank you! We'll be in touch shortly." — form replaced by success message.

**User Journey — Admin managing packages and pipeline**:
1. Admin navigates to `/admin/corporate` (new page, "Corporate" in admin sidebar, `Building2` icon).
2. Two tabs: "Packages" and "Inquiries".
3. Packages tab: table of packages with edit/deactivate actions. "New Package" button → form modal.
4. Inquiries tab: pipeline view with status column. Filter by status dropdown. Total revenue pipeline shown at top ("Pipeline Value: $245,000").
5. Admin clicks an inquiry row → detail view (or inline expansion): all fields, status dropdown, notes textarea, deal value input. "Save Changes" button.

**Navigation changes**:
- Public nav: new item "For Organizations" → `/corporate`.
- Admin sidebar: new item "Corporate" (`Building2` icon) → `/admin/corporate`.

**UI states**:
- Empty packages (public): "We're preparing our corporate packages. Please contact us directly." fallback.
- Deactivated package: hidden from public page, grayed in admin table.
- Inquiry form: success state replaces form (same pattern as contact form).
- Admin pipeline: color-coded status chips. Pipeline value prominently displayed.

---

## Phase 4 — Technical Design

### 4.1 Schema Changes (additions to `db/schema.sql`)

All additions are in `db/schema.sql`. The DDL below is the authoritative source. Chintu copies it verbatim into the schema file.

#### 4.1.1 Modify `invoices` table — add `paid_at` column (OI-7)

```sql
-- Add paid_at column to invoices for accurate revenue reporting (OI-7).
-- Set server-side when status changes to 'Paid'.
ALTER TABLE invoices ADD COLUMN paid_at TEXT;
CREATE INDEX idx_invoices_paid_at ON invoices(paid_at);
```

Note: SQLite's `ALTER TABLE` only supports `ADD COLUMN`. For a fresh schema, this column is defined inline in the `CREATE TABLE` statement.

#### 4.1.2 New tables — full DDL

```sql
-- ============================================================
-- BATCH 2 (2026-07-20): REQ-01 through REQ-12
-- ============================================================

-- REQ-01: Doctor availability schedule
-- One row per day-of-week time window per doctor.
-- day_of_week: 0=Monday, 6=Sunday.
CREATE TABLE doctor_availability_schedules (
    schedule_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id       INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    day_of_week     INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time      TEXT NOT NULL,   -- HH:MM format
    end_time        TEXT NOT NULL,   -- HH:MM format
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (doctor_id, day_of_week, start_time)
);

CREATE INDEX idx_avail_schedules_doctor ON doctor_availability_schedules(doctor_id);

-- REQ-01: Doctor slot duration config (one row per doctor)
CREATE TABLE doctor_slot_configs (
    config_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id               INTEGER NOT NULL UNIQUE REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    slot_duration_minutes   INTEGER NOT NULL DEFAULT 30
                                CHECK (slot_duration_minutes IN (10, 15, 20, 30, 45, 60)),
    updated_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- REQ-01: One-off availability blocks (override weekly schedule for a date)
-- Constraint: if start_time is non-null then end_time must be non-null and vice versa.
-- Full-day block: both start_time and end_time are NULL.
CREATE TABLE doctor_availability_blocks (
    block_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id   INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    block_date  TEXT NOT NULL,   -- YYYY-MM-DD
    start_time  TEXT,            -- HH:MM or NULL (NULL = full-day block)
    end_time    TEXT,            -- HH:MM or NULL (must match start_time nullability)
    reason      TEXT,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_avail_blocks_doctor ON doctor_availability_blocks(doctor_id);
CREATE INDEX idx_avail_blocks_date ON doctor_availability_blocks(block_date);

-- REQ-02: In-app notifications
CREATE TABLE notifications (
    notification_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type          TEXT NOT NULL,
    title               TEXT NOT NULL CHECK (LENGTH(title) <= 120),
    body                TEXT NOT NULL CHECK (LENGTH(body) <= 500),
    related_entity_type TEXT,    -- e.g. 'appointment', 'invoice', 'lab_result', 'referral', 'survey'
    related_entity_id   INTEGER,
    is_read             INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0, 1)),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Critical: (recipient_user_id, is_read) index for O(1) unread count queries (NOTIFNFR-1)
CREATE INDEX idx_notifications_recipient_read ON notifications(recipient_user_id, is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- REQ-02: Deferred notification triggers (poll-on-login pattern, OI-2)
-- survey_id FK references satisfaction_surveys below (defined later in this file).
CREATE TABLE notification_schedules (
    schedule_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id  INTEGER REFERENCES appointments(appointment_id) ON DELETE CASCADE,
    survey_id       INTEGER,  -- FK to satisfaction_surveys added via CHECK after that table exists
    trigger_type    TEXT NOT NULL
                        CHECK (trigger_type IN ('appointment_reminder', 'survey_available')),
    trigger_at      TEXT NOT NULL,  -- ISO 8601 timestamp
    is_fired        INTEGER NOT NULL DEFAULT 0 CHECK (is_fired IN (0, 1)),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notif_schedules_trigger_at ON notification_schedules(trigger_at, is_fired);

-- REQ-03: Patient pre-visit intake forms (1:1 with appointment)
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
    submitted_at        TEXT,   -- NULL = draft; set on first full submission
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_intake_forms_appointment ON intake_forms(appointment_id);
CREATE INDEX idx_intake_forms_patient ON intake_forms(patient_id);

-- REQ-04: Patient vitals (resolves STF-4 schema gap, Section 9.14)
-- appointment_id is nullable: vitals can be taken without a specific appointment.
CREATE TABLE vitals (
    vital_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id              INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    appointment_id          INTEGER REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    recorded_by_user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    systolic_bp             INTEGER,   -- mmHg; must be paired with diastolic_bp
    diastolic_bp            INTEGER,   -- mmHg; must be paired with systolic_bp
    weight_kg               REAL,      -- must be > 0 if provided
    pulse_bpm               INTEGER,   -- 20–300 if provided
    temperature_celsius     REAL,      -- 30.0–45.0 if provided
    height_cm               REAL,      -- must be > 0 if provided
    recorded_at             TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vitals_patient ON vitals(patient_id);
CREATE INDEX idx_vitals_appointment ON vitals(appointment_id);
CREATE INDEX idx_vitals_recorded_at ON vitals(recorded_at);

-- REQ-05: Inter-department referrals
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

CREATE INDEX idx_referrals_patient ON referrals(patient_id);
CREATE INDEX idx_referrals_referring_doctor ON referrals(referring_doctor_id);
CREATE INDEX idx_referrals_receiving_dept ON referrals(receiving_department_id);
CREATE INDEX idx_referrals_status ON referrals(status);
-- Urgency+status index for FIFO queue queries (Urgent first, then created_at)
CREATE INDEX idx_referrals_dept_status_urgency ON referrals(receiving_department_id, status, urgency, created_at);

-- REQ-07: Department symptom tags for public search
-- Case-insensitive uniqueness of tag_text per department is enforced at the application layer.
CREATE TABLE department_symptom_tags (
    tag_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id   INTEGER NOT NULL REFERENCES departments(department_id) ON DELETE CASCADE,
    tag_text        TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_symptom_tags_department ON department_symptom_tags(department_id);
-- FTS-style search support: index on tag_text for LIKE queries
CREATE INDEX idx_symptom_tags_text ON department_symptom_tags(tag_text);

-- REQ-09: Appointment waitlist
-- Per OI-12 assumption: per-doctor-per-date. preferred_date is NOT NULL.
-- Uniqueness: one active (Waiting or Notified) entry per (patient_id, doctor_id, preferred_date).
CREATE TABLE waitlist_entries (
    entry_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id              INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id               INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    preferred_date          TEXT NOT NULL,  -- YYYY-MM-DD; NOT NULL per OI-12 assumption
    status                  TEXT NOT NULL DEFAULT 'Waiting'
                                CHECK (status IN ('Waiting', 'Notified', 'Confirmed', 'Expired', 'Removed')),
    notified_at             TEXT,
    confirmation_deadline   TEXT,
    removed_reason          TEXT,           -- set when staff removes entry with recorded reason
    created_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- FIFO queue index: doctor, date, active statuses, ordered by join time
CREATE INDEX idx_waitlist_doctor_date_status ON waitlist_entries(doctor_id, preferred_date, status, created_at);
CREATE INDEX idx_waitlist_patient ON waitlist_entries(patient_id);

-- REQ-09: System configuration (key-value store)
-- Initial data: ('waitlist_confirmation_hours', '4')
CREATE TABLE system_config (
    config_key      TEXT PRIMARY KEY,
    config_value    TEXT NOT NULL,
    updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- REQ-10: Discharge summaries (1:1 with appointment; appointment must be Completed)
CREATE TABLE discharge_summaries (
    summary_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id              INTEGER NOT NULL UNIQUE REFERENCES appointments(appointment_id) ON DELETE RESTRICT,
    patient_id                  INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id                   INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    key_findings                TEXT NOT NULL,
    patient_instructions        TEXT,
    activity_restrictions       TEXT,
    medication_reminders        TEXT,
    follow_up_appointment_id    INTEGER REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    created_at                  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_discharge_summaries_patient ON discharge_summaries(patient_id);
CREATE INDEX idx_discharge_summaries_doctor ON discharge_summaries(doctor_id);

-- REQ-11: Patient satisfaction surveys (1:1 with appointment; only for Completed appointments)
CREATE TABLE satisfaction_surveys (
    survey_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id          INTEGER NOT NULL UNIQUE REFERENCES appointments(appointment_id) ON DELETE RESTRICT,
    patient_id              INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id               INTEGER NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    trigger_after           TEXT NOT NULL,   -- ISO 8601: appointment completed_at + 24h
    expires_at              TEXT NOT NULL,   -- ISO 8601: trigger_after + 7 days
    notification_sent       INTEGER NOT NULL DEFAULT 0 CHECK (notification_sent IN (0, 1)),
    submitted_at            TEXT,            -- NULL = pending; set on patient submission
    doctor_star_rating      INTEGER CHECK (doctor_star_rating BETWEEN 1 AND 5),
    overall_star_rating     INTEGER CHECK (overall_star_rating BETWEEN 1 AND 5),
    comment                 TEXT CHECK (comment IS NULL OR LENGTH(comment) <= 1000),
    is_comment_removed      INTEGER NOT NULL DEFAULT 0 CHECK (is_comment_removed IN (0, 1))
);

CREATE INDEX idx_surveys_patient ON satisfaction_surveys(patient_id);
CREATE INDEX idx_surveys_doctor ON satisfaction_surveys(doctor_id);
-- Poll-on-login query index: find unnotified, pending, matured surveys for a patient
CREATE INDEX idx_surveys_poll ON satisfaction_surveys(patient_id, notification_sent, submitted_at);

-- REQ-12: Corporate health packages
CREATE TABLE corporate_packages (
    package_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    TEXT NOT NULL,
    tier_order              INTEGER NOT NULL,
    description             TEXT NOT NULL,
    included_services_json  TEXT NOT NULL,   -- JSON array of service strings
    price_range_display     TEXT NOT NULL,   -- e.g. "$500–$800 per employee" (marketing copy)
    is_active               INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_corporate_packages_active ON corporate_packages(is_active, tier_order);

-- REQ-12: Corporate inquiry pipeline
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

CREATE INDEX idx_corporate_inquiries_status ON corporate_inquiries(status);
CREATE INDEX idx_corporate_inquiries_created_at ON corporate_inquiries(created_at);
```

#### 4.1.3 Schema change summary for cross-agent notification

Gopal: 16 new tables + 1 column addition (`invoices.paid_at`) require test coverage.
Indra: seed data needed for `system_config` (`INSERT INTO system_config VALUES ('waitlist_confirmation_hours', '4', CURRENT_TIMESTAMP)`). Seed data for `corporate_packages` (at least 2 sample packages) is needed for the public site to not show an empty page.
Chintu: `notification_schedules.survey_id` is a nullable FK to `satisfaction_surveys.survey_id`. Since SQLite allows forward-declared FKs in the DDL only if the referenced table exists, ensure `satisfaction_surveys` is created before `notification_schedules` in the migration script (or add the FK constraint via a trigger/app-layer check as SQLite does not enforce FK existence at DDL time).

---

### 4.2 API Endpoints — New Endpoints (Batch 2)

All endpoints follow existing conventions: `/api` base path, snake_case JSON, ISO-8601 timestamps, `Authorization: Bearer <jwt>` for protected routes, standard error shape `{"detail": "..."}`.

**Merge point**: These endpoints must be merged into `docs/api-spec.md` as new sections (11 through 22) before Chintu begins implementation. This document is the design source; `api-spec.md` is the published contract.

---

#### 11. Availability (REQ-01)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/doctors/{doctor_id}/available-slots` | Patient / Staff / Doctor / Admin | query: `date=YYYY-MM-DD` (required) | `200` `{"doctor_id": N, "date": "YYYY-MM-DD", "slot_duration_minutes": 30, "slots": ["09:00", "09:30", ...]}` — empty slots array if no availability. `400` if date missing or invalid format. |
| GET | `/api/doctor/availability/schedule` | Doctor | — | `200` `{"items": [{schedule_id, day_of_week, start_time, end_time, is_active}]}` |
| POST | `/api/doctor/availability/schedule` | Doctor | `{day_of_week: 0-6, start_time: "HH:MM", end_time: "HH:MM"}` | `201` `{schedule_id, doctor_id, day_of_week, start_time, end_time, is_active}`. `400` if start >= end or invalid values. `409` if window overlaps an existing window for same day. |
| PUT | `/api/doctor/availability/schedule/{schedule_id}` | Doctor | `{start_time?, end_time?, is_active?}` | `200` updated schedule row. `403` if schedule_id doesn't belong to calling doctor. |
| DELETE | `/api/doctor/availability/schedule/{schedule_id}` | Doctor | — | `204`. `403` ownership check. |
| GET | `/api/doctor/availability/config` | Doctor | — | `200` `{config_id, doctor_id, slot_duration_minutes, updated_at}` — returns default if no config row exists yet. |
| PUT | `/api/doctor/availability/config` | Doctor | `{slot_duration_minutes: 10\|15\|20\|30\|45\|60}` | `200` `{config_id, doctor_id, slot_duration_minutes, updated_at}`. `400` if value not in allowed set. |
| GET | `/api/doctor/availability/blocks` | Doctor | query: `?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD` (optional) | `200` `{"items": [{block_id, block_date, start_time, end_time, reason, created_at}]}` |
| POST | `/api/doctor/availability/blocks` | Doctor | `{block_date: "YYYY-MM-DD", start_time?: "HH:MM", end_time?: "HH:MM", reason?: "..."}` | `201` block row. `400` if only one of start_time/end_time provided. |
| DELETE | `/api/doctor/availability/blocks/{block_id}` | Doctor | — | `204`. `403` ownership check. |
| GET | `/api/admin/doctors/{doctor_id}/availability/schedule` | Admin | — | `200` same shape as doctor's own GET |
| POST | `/api/admin/doctors/{doctor_id}/availability/schedule` | Admin | same as doctor's POST | `201` schedule row |
| PUT | `/api/admin/doctors/{doctor_id}/availability/schedule/{schedule_id}` | Admin | same as doctor's PUT | `200` updated |
| DELETE | `/api/admin/doctors/{doctor_id}/availability/schedule/{schedule_id}` | Admin | — | `204` |
| GET | `/api/admin/doctors/{doctor_id}/availability/config` | Admin | — | `200` config row |
| PUT | `/api/admin/doctors/{doctor_id}/availability/config` | Admin | same as doctor's PUT | `200` updated |
| GET | `/api/admin/doctors/{doctor_id}/availability/blocks` | Admin | query: `from_date?`, `to_date?` | `200` blocks list |
| POST | `/api/admin/doctors/{doctor_id}/availability/blocks` | Admin | same as doctor's POST | `201` block row |
| DELETE | `/api/admin/doctors/{doctor_id}/availability/blocks/{block_id}` | Admin | — | `204` |

**Slot-query algorithm (backend service, must be implemented as a pure function for testability)**:

```python
def get_available_slots(db, doctor_id, date_str):
    # 1. Get doctor's weekly schedule for this day of week
    dow = datetime.strptime(date_str, "%Y-%m-%d").weekday()  # 0=Mon
    windows = db.query("SELECT start_time, end_time FROM doctor_availability_schedules
                        WHERE doctor_id=? AND day_of_week=? AND is_active=1", doctor_id, dow)
    if not windows:
        return []

    # 2. Get slot duration
    config = db.query("SELECT slot_duration_minutes FROM doctor_slot_configs WHERE doctor_id=?", doctor_id)
    slot_minutes = config.slot_duration_minutes if config else 30

    # 3. Generate all candidate slots from windows
    candidates = []
    for w in windows:
        t = datetime.strptime(f"{date_str}T{w.start_time}", "%Y-%m-%dT%H:%M")
        end = datetime.strptime(f"{date_str}T{w.end_time}", "%Y-%m-%dT%H:%M")
        while t + timedelta(minutes=slot_minutes) <= end:
            candidates.append(t.strftime("%H:%M"))
            t += timedelta(minutes=slot_minutes)

    # 4. Remove slots blocked by one-off blocks
    blocks = db.query("SELECT start_time, end_time FROM doctor_availability_blocks
                       WHERE doctor_id=? AND block_date=?", doctor_id, date_str)
    for block in blocks:
        if block.start_time is None:  # full-day block
            return []
        blocked_start = datetime.strptime(block.start_time, "%H:%M")
        blocked_end = datetime.strptime(block.end_time, "%H:%M")
        candidates = [s for s in candidates if not (
            datetime.strptime(s, "%H:%M") >= blocked_start and
            datetime.strptime(s, "%H:%M") < blocked_end
        )]

    # 5. Remove already-booked slots
    booked = db.query("SELECT strftime('%H:%M', scheduled_at) as t FROM appointments
                       WHERE doctor_id=? AND date(scheduled_at)=?
                         AND status IN ('Scheduled', 'Completed')", doctor_id, date_str)
    booked_times = {r.t for r in booked}
    candidates = [s for s in candidates if s not in booked_times]

    # 6. Also exclude waitlist-held slots (status='Notified' for this doctor+date)
    held = db.query("SELECT ... FROM waitlist_entries
                     WHERE doctor_id=? AND preferred_date=? AND status='Notified'", doctor_id, date_str)
    # Held slot time: derive from the appointment that was cancelled
    # (Implementation note: held slot times need to be tracked — see waitlist design below)

    return sorted(candidates)
```

Note: Waitlist slot holding (WLFR-4) requires tracking which specific slot time is held. The `waitlist_entries` table should add a `held_slot_time TEXT` column (nullable, set to `HH:MM` when a cancellation triggers a waitlist notification). Chintu must add this column.

---

#### 12. Notifications (REQ-02)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/notifications/unread-count` | Any authenticated | — | `200` `{"unread_count": N}` — NOTIFNFR-1: must respond < 200ms. Uses `idx_notifications_recipient_read`. |
| GET | `/api/notifications` | Any authenticated | query: `page`, `page_size` | `200` `{"items": [{notification_id, event_type, title, body, related_entity_type, related_entity_id, is_read, created_at}], total, page, page_size, total_pages}` — filtered to `recipient_user_id = current_user.id` |
| PATCH | `/api/notifications/{notification_id}/read` | Any authenticated | — | `200` `{notification_id, is_read: true}`. `403` if notification doesn't belong to caller. `404` if not found. |
| POST | `/api/notifications/mark-all-read` | Any authenticated | — | `200` `{"marked_read": N}` where N = count of rows updated. |

**Notification creation helper** (used in all triggering endpoints):

```python
def create_notifications(db, events: list[dict]):
    """
    events: [{"recipient_user_id": int, "event_type": str, "title": str,
               "body": str, "related_entity_type": str|None, "related_entity_id": int|None}]
    Batch-inserts all notification rows at end of triggering transaction.
    """
    db.execute_many("INSERT INTO notifications (...) VALUES (...)", events)
```

All triggering endpoints (appointment booking, lab result finalization, invoice creation, etc.) call `create_notifications()` as the last step before `db.commit()`.

---

#### 13. Intake Forms (REQ-03)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/appointments/{appointment_id}/intake` | Patient (own) / Doctor (assigned) / Staff / Admin | — | `200` intake form row (all fields). `403` if patient calling for another patient's appointment. `404` if no intake form yet (Note: intake forms are created automatically on appointment creation — so 404 should not occur in normal flow). |
| PATCH | `/api/appointments/{appointment_id}/intake` | Patient (own) only | `{chief_complaint?, symptom_duration?, allergies?, current_medications?, pain_scale?, additional_notes?, submit?: bool}` | `200` updated intake form. `403` if appointment.status = 'Completed'. `400` if `submit=true` and required fields (chief_complaint, symptom_duration) are missing. `400` if pain_scale not in 1–10. |

**Trigger**: When `POST /api/appointments` creates a new appointment, also insert an empty `intake_forms` row (`chief_complaint=NULL, ..., submitted_at=NULL`). This is atomic with the appointment creation.

---

#### 14. Vitals (REQ-04)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/patients/{patient_id}/vitals` | Doctor (AUTHZ-2) / Staff / Admin | query: `page`, `page_size` | `200` `{"items": [{vital_id, patient_id, appointment_id, recorded_by_user_id, systolic_bp, diastolic_bp, weight_kg, pulse_bpm, temperature_celsius, height_cm, recorded_at}], total, page, page_size, total_pages}` ordered by `recorded_at ASC`. |
| POST | `/api/patients/{patient_id}/vitals` | Staff / Admin | `{appointment_id?: int, systolic_bp?: int, diastolic_bp?: int, weight_kg?: float, pulse_bpm?: int, temperature_celsius?: float, height_cm?: float}` | `201` vital row. Validation: at least one field non-null; BP both-or-neither; ranges per VITFR-2/3. `403` if Doctor or Patient calls this. `400` on validation failure. |

---

#### 15. Referrals (REQ-05)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| POST | `/api/doctor/referrals` | Doctor | `{patient_id, receiving_department_id, receiving_doctor_id?, reason, urgency: "Routine"\|"Urgent"}` | `201` referral row + `{"referral_id": N, "status": "Pending", ...}`. `403` if doctor has no appointment with patient (AUTHZ-2). After creation, fan-out `referral_received` notifications to all active doctors in `receiving_department_id` (or just `receiving_doctor_id` if specified). |
| GET | `/api/doctor/referrals/sent` | Doctor | query: `status?`, `page`, `page_size` | `200` paginated list of referrals where `referring_doctor_id = calling_doctor.id` |
| GET | `/api/doctor/referrals/received` | Doctor | query: `status?`, `page`, `page_size` | `200` paginated list: referrals where `receiving_department_id = calling_doctor.department_id` AND (`receiving_doctor_id IS NULL` OR `receiving_doctor_id = calling_doctor.doctor_id`). Ordered: Urgent first, then by created_at. |
| PATCH | `/api/doctor/referrals/{referral_id}/accept` | Doctor | `{note?: "..."}` | `200` updated referral (status='Accepted', receiving_doctor_id set to calling doctor). `403` if calling doctor not in receiving department (AUTHZ-13). `409` if referral already Accepted/Declined. Sets `receiving_doctor_id` and `status` atomically. Sends `referral_status_changed` notifications to patient and referring doctor. |
| PATCH | `/api/doctor/referrals/{referral_id}/decline` | Doctor | `{note: "..." (required)}` | `200` updated referral (status='Declined'). `403` if not in receiving department. `400` if note missing. Sends `referral_status_changed` notifications to patient and referring doctor. |
| PATCH | `/api/doctor/referrals/{referral_id}/complete` | Doctor | — | `200` updated referral (status='Completed'). `403` if calling doctor is not `receiving_doctor_id` on this referral. |
| GET | `/api/patients/me/referrals` | Patient | query: `page`, `page_size` | `200` paginated list of referrals where `patient_id = caller's patient_id`. Fields exposed: referral_id, referring_doctor_name, receiving_department_name, receiving_doctor_name (if set), urgency, status, created_at, receiving_doctor_note. No `reason` field (per OI-6 assumption — clinical field). |
| GET | `/api/admin/referrals` | Admin | query: `status?`, `department_id?`, `start_date?`, `end_date?`, `page`, `page_size` | `200` paginated referrals. Fields: referral_id, referring_doctor_name, receiving_department_name, receiving_doctor_name, urgency, status, created_at, updated_at. No `reason` field (OI-6). |

---

#### 16. Analytics (REQ-06)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/admin/analytics/appointments` | Admin | query: `start=YYYY-MM-DD`, `end=YYYY-MM-DD`, `format?=csv` | `200 application/json` `{"items": [{"month": "2026-01", "total": 42, "completed": 30, "cancelled": 8, "noshow": 4, "scheduled": 0, "noshow_rate": 9.52}], "start": "...", "end": "..."}` OR `200 text/csv` with same data as CSV. `400` if end < start. |
| GET | `/api/admin/analytics/revenue` | Admin | query: `start`, `end`, `format?=csv` | `200` `{"items": [{"month": "2026-01", "invoiced_cents": 500000, "collected_cents": 320000}]}`. Uses `invoices.created_at` for invoiced; `invoices.paid_at` for collected (per OI-7). |
| GET | `/api/admin/analytics/departments` | Admin | query: `start`, `end`, `format?=csv` | `200` `{"items": [{"department_id": 1, "department_name": "Cardiology", "appointment_count": 95}]}` sorted by count descending. |
| GET | `/api/admin/analytics/patient-acquisition` | Admin | query: `start`, `end`, `format?=csv` | `200` `{"items": [{"month": "2026-01", "new_patients": 12}]}` grouped by `users.created_at` month for users with role='Patient'. |

**Default date range**: if `start` or `end` missing, default to `start = today - 365 days`, `end = today`.

**CSV format**: when `?format=csv`, set `Content-Type: text/csv`, `Content-Disposition: attachment; filename="gvh_analytics_{metric}_{start}_{end}.csv"`. Body: CSV with header row matching the JSON field names.

---

#### 17. Public Search (REQ-07)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/public/search` | Public | query: `q=...` (2–200 chars) | `200` `{"departments": [{department_id, name, description_snippet, match_type: "name"\|"description"\|"tag"}], "doctors": [{doctor_id, full_name, specialty, department_name, profile_photo_path, match_type: "specialty"\|"bio"}], "query": "...", "total": N}`. `400` if `len(q) < 2`. Truncate `q` to 200 chars server-side. Only active departments and active doctor accounts. |
| GET | `/api/admin/departments/{department_id}/tags` | Admin | — | `200` `{"items": [{tag_id, tag_text, created_at}]}` |
| POST | `/api/admin/departments/{department_id}/tags` | Admin | `{tag_text: "..."}` (max 100 chars) | `201` `{tag_id, department_id, tag_text, created_at}`. `409` if tag_text already exists for this department (case-insensitive check). `400` if department already has 50 tags. |
| PUT | `/api/admin/departments/{department_id}/tags/{tag_id}` | Admin | `{tag_text: "..."}` | `200` updated tag. `409` if new tag_text conflicts. |
| DELETE | `/api/admin/departments/{department_id}/tags/{tag_id}` | Admin | — | `204` |

**Search SQL pattern** (case-insensitive LIKE, SQLite):
```sql
-- Departments matching on name (rank=1), description (rank=2), or tags (rank=3)
SELECT d.*, 1 as rank FROM departments d
  WHERE d.is_active=1 AND LOWER(d.name) LIKE '%' || LOWER(?) || '%'
UNION ALL
SELECT d.*, 2 FROM departments d
  WHERE d.is_active=1 AND LOWER(d.description) LIKE '%' || LOWER(?) || '%'
    AND d.department_id NOT IN (... name matches ...)
UNION ALL
SELECT d.*, 3 FROM departments d
  JOIN department_symptom_tags t ON t.department_id = d.department_id
  WHERE d.is_active=1 AND LOWER(t.tag_text) LIKE '%' || LOWER(?) || '%'
    AND d.department_id NOT IN (... name or desc matches ...)
ORDER BY rank ASC
```

---

#### 18. PDF Export (REQ-08)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/patients/me/export-pdf` | Patient only | query: `start_date?=YYYY-MM-DD`, `end_date?=YYYY-MM-DD` | `200 application/pdf` with `Content-Disposition: attachment; filename="GVH_MedicalRecord_{patient_id}_{YYYYMMDD}.pdf"`. Body: PDF bytes streamed directly. `403` if any non-Patient role calls this (AUTHZ-11). `400` if date params invalid. |

**WeasyPrint implementation sketch**:
```python
from weasyprint import HTML
from fastapi.responses import StreamingResponse
import io

@router.get("/patients/me/export-pdf")
def export_patient_pdf(start_date: str = None, end_date: str = None,
                       current_user=Depends(require_role("Patient")), db=Depends(get_db)):
    # Gather data
    patient = get_patient_for_user(db, current_user.id)
    appointments = get_appointments_for_pdf(db, patient.patient_id, start_date, end_date)
    # ... gather prescriptions, lab results, vitals, intake forms, discharge summaries

    # Render HTML template
    html_content = render_pdf_template(patient, appointments, ...)

    # Generate PDF bytes
    pdf_bytes = HTML(string=html_content).write_pdf()

    filename = f"GVH_MedicalRecord_{patient.patient_id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

New file: `src/backend/app/services/pdf_export.py` — contains `render_pdf_template()` and `get_appointments_for_pdf()`. Template: `src/backend/app/templates/medical_record.html` (Jinja2-style string template, no external file serving).

---

#### 19. Waitlist (REQ-09)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| POST | `/api/waitlist` | Patient | `{doctor_id, preferred_date: "YYYY-MM-DD"}` | `201` `{entry_id, patient_id, doctor_id, preferred_date, status: "Waiting", created_at, position: N}`. `409` if patient already has active ('Waiting' or 'Notified') entry for same (doctor_id, preferred_date). |
| GET | `/api/patients/me/waitlist` | Patient | — | `200` `{"items": [{entry_id, doctor_id, doctor_name, department_name, preferred_date, status, position, notified_at, confirmation_deadline, created_at}]}` active entries only (Waiting or Notified). |
| DELETE | `/api/patients/me/waitlist/{entry_id}` | Patient | — | `204`. Sets `status='Removed'`. `403` if entry doesn't belong to caller. `400` if status is already Confirmed/Expired/Removed. |
| POST | `/api/waitlist/{entry_id}/confirm` | Patient | — | `201` `{appointment_id: N}` (new appointment created). `403` if entry doesn't belong to caller. `400` if status != 'Notified'. `400` if confirmation_deadline has passed. `409` if slot was taken between notification and confirm. |
| GET | `/api/staff/waitlist/{doctor_id}` | Staff | query: `date?`, `page`, `page_size` | `200` paginated list of all active waitlist entries for the doctor (optional: filter by date). Fields include patient_name, join date, preferred date, status. |
| DELETE | `/api/staff/waitlist/{entry_id}` | Staff | body: `{reason: "..."}` | `204`. Sets `status='Removed'`, `removed_reason=reason`. |
| GET | `/api/admin/config/waitlist` | Admin | — | `200` `{"confirmation_hours": 4}` |
| PUT | `/api/admin/config/waitlist` | Admin | `{confirmation_hours: N}` (1–72) | `200` `{"confirmation_hours": N}`. `400` if out of range. |
| GET | `/api/admin/waitlist/stats` | Admin | query: `start=YYYY-MM-DD`, `end=YYYY-MM-DD` | `200` `{"global_avg_minutes": N, "by_doctor": [{doctor_id, doctor_name, avg_minutes, total_confirmations}]}` |

**Waitlist cancellation trigger logic** (called inside `PATCH /api/appointments/{id}/status` when status → 'Cancelled'):
```python
def trigger_waitlist_on_cancellation(db, appointment):
    if appointment.status != 'Cancelled':
        return
    # Find first FIFO waiting entry for this doctor + date
    entry = db.query(
        "SELECT * FROM waitlist_entries
         WHERE doctor_id=? AND preferred_date=date(?) AND status='Waiting'
         ORDER BY created_at ASC LIMIT 1",
        appointment.doctor_id, appointment.scheduled_at
    ).first()
    if not entry:
        return
    # Get confirmation window
    config = db.query("SELECT config_value FROM system_config WHERE config_key='waitlist_confirmation_hours'").first()
    hours = int(config.config_value) if config else 4
    now = datetime.utcnow()
    deadline = now + timedelta(hours=hours)
    # Update entry and create notification
    db.execute("UPDATE waitlist_entries SET status='Notified', notified_at=?, confirmation_deadline=?,
                held_slot_time=strftime('%H:%M',?) WHERE entry_id=?",
               now.isoformat(), deadline.isoformat(),
               appointment.scheduled_at, entry.entry_id)
    create_notifications(db, [{
        "recipient_user_id": get_user_id_for_patient(db, entry.patient_id),
        "event_type": "waitlist_slot_available",
        "title": "A slot is available!",
        "body": f"A slot opened with Dr. {get_doctor_name(db, appointment.doctor_id)} "
                f"on {entry.preferred_date}. Confirm by {deadline.strftime('%H:%M UTC')}.",
        "related_entity_type": "waitlist_entry",
        "related_entity_id": entry.entry_id
    }])
```

**Expiry check** (poll-on-login for the waitlisted patient):
```python
def check_waitlist_expiry(db, user_id):
    now = datetime.utcnow().isoformat()
    patient = db.query("SELECT patient_id FROM patients WHERE user_id=?", user_id).first()
    if not patient:
        return
    expired = db.query(
        "SELECT * FROM waitlist_entries WHERE patient_id=? AND status='Notified' AND confirmation_deadline < ?",
        patient.patient_id, now
    ).fetchall()
    for entry in expired:
        db.execute("UPDATE waitlist_entries SET status='Expired' WHERE entry_id=?", entry.entry_id)
        # Re-add to back of queue as new Waiting entry
        db.execute("INSERT INTO waitlist_entries (patient_id, doctor_id, preferred_date, status, created_at)
                    VALUES (?,?,?,'Waiting',?)", patient.patient_id, entry.doctor_id, entry.preferred_date, now)
        # Notify next patient in queue
        trigger_next_waitlist(db, entry.doctor_id, entry.preferred_date)
```

---

#### 20. Discharge Summaries (REQ-10)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| POST | `/api/doctor/appointments/{appointment_id}/discharge-summary` | Doctor | `{key_findings: "..." (required), patient_instructions?: "...", activity_restrictions?: "...", medication_reminders?: "...", follow_up?: {scheduled_at: "ISO-8601"}}` | `201` `{summary_id, appointment_id, key_findings, ..., follow_up_appointment_id: N\|null}`. `400` if appointment.status != 'Completed'. `403` if doctor not assigned to appointment. `409` if discharge summary already exists for this appointment. If `follow_up` block provided: slot validation runs first; if slot taken, returns `409 {"detail": "Follow-up slot no longer available."}` and no summary is created. All inside one transaction. |
| GET | `/api/doctor/appointments/{appointment_id}/discharge-summary` | Doctor (assigned) | — | `200` summary or `404` if none created yet. |
| GET | `/api/patients/me/discharge-summaries` | Patient | query: `page`, `page_size` | `200` paginated list of patient's own discharge summaries with appointment info. |
| GET | `/api/patients/me/appointments/{appointment_id}/discharge-summary` | Patient | — | `200` summary. `403` if appointment not patient's own. `404` if no summary. |

**Atomicity (OI-8)**: The `POST` handler runs this flow:
1. BEGIN TRANSACTION
2. Validate appointment is Completed and belongs to calling doctor.
3. Check no existing discharge summary for this appointment.
4. If `follow_up` provided: call slot validation (same logic as `POST /appointments`). If slot taken → ROLLBACK → 409.
5. If follow-up valid: INSERT appointment row (follow-up, status='Scheduled').
6. INSERT discharge_summaries row with `follow_up_appointment_id` pointing to new appointment.
7. CREATE notifications: `discharge_summary_ready` for patient. If follow-up created: also `follow_up_booked` for patient and doctor.
8. INSERT satisfaction_surveys row (trigger_after = now + 24h, expires_at = trigger_after + 7 days).
9. INSERT notification_schedules row (trigger_type='survey_available', trigger_at = trigger_after).
10. COMMIT

Note: Steps 8–9 run whenever an appointment is marked Completed (even without a discharge summary). The discharge summary creation POST is the only trigger point if the doctor goes through the discharge panel. If the doctor just updates status to 'Completed' via `PATCH /api/doctor/appointments/{id}/status`, the survey row must also be created there.

---

#### 21. Satisfaction Surveys (REQ-11)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/patients/me/surveys` | Patient | — | `200` `{"items": [{survey_id, appointment_id, appointment_date, doctor_name, trigger_after, expires_at, submitted_at, status: "pending"\|"submitted"\|"expired"}]}`. Status: `submitted` if submitted_at non-null; `expired` if expires_at < now and submitted_at null; `pending` otherwise. |
| POST | `/api/patients/me/surveys/{survey_id}` | Patient | `{doctor_star_rating: 1-5, overall_star_rating: 1-5, comment?: "..." (max 1000)}` | `201` `{"survey_id": N, "submitted_at": "..."}`. `403` if survey doesn't belong to caller. `400` if survey not triggered yet (trigger_after > now). `403` if survey expired (expires_at < now). `409` if already submitted. |
| GET | `/api/doctor/ratings` | Doctor | — | `200` `{"average_doctor_rating": 4.3, "total_reviews": 47, "comments": [{comment, submitted_at}]}`. Comments ordered by submitted_at DESC. No patient identity. |
| GET | `/api/admin/surveys` | Admin | query: `doctor_id?`, `start_date?`, `end_date?`, `submitted_only?`, `page`, `page_size` | `200` paginated. Each item: survey_id, appointment_id, patient_id, patient_name, doctor_id, doctor_name, doctor_star_rating, overall_star_rating, comment, is_comment_removed, submitted_at. |
| GET | `/api/admin/surveys/{survey_id}` | Admin | — | `200` single survey record. |
| PATCH | `/api/admin/surveys/{survey_id}/remove-comment` | Admin | — | `200` `{"survey_id": N, "is_comment_removed": true, "comment": null}`. Idempotent. |

---

#### 22. Corporate Packages & Inquiries (REQ-12)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/public/corporate/packages` | Public | — | `200` `{"items": [{package_id, name, tier_order, description, included_services_json, price_range_display}]}` active packages only, ordered by tier_order ASC. |
| POST | `/api/public/corporate/inquiries` | Public | `{company_name, contact_name, email, phone?, headcount?, package_id?, preferred_schedule?}` | `201` `{"inquiry_id": N, "message": "Thank you! We'll be in touch shortly."}`. `400` if headcount < 1 (when provided). `422` if required fields missing or email format invalid. |
| GET | `/api/admin/corporate/packages` | Admin | — | `200` all packages including inactive. Fields include is_active. |
| POST | `/api/admin/corporate/packages` | Admin | `{name, tier_order, description, included_services_json, price_range_display, is_active?}` | `201` new package row. |
| PUT | `/api/admin/corporate/packages/{package_id}` | Admin | any subset of package fields | `200` updated package. |
| DELETE | `/api/admin/corporate/packages/{package_id}` | Admin | — | `200` `{"package_id": N, "is_active": false}` (soft delete: sets `is_active=0`). |
| GET | `/api/admin/corporate/inquiries` | Admin | query: `status?`, `page`, `page_size` | `200` `{"items": [...], "total": N, "page": P, "page_size": PS, "total_pages": TP, "pipeline_total_cents": M}` where `pipeline_total_cents = SUM(deal_value_cents) WHERE status='ClosedWon'`. |
| GET | `/api/admin/corporate/inquiries/{inquiry_id}` | Admin | — | `200` full inquiry including notes, deal_value_cents. |
| PATCH | `/api/admin/corporate/inquiries/{inquiry_id}` | Admin | `{status?, notes?, deal_value_cents?}` | `200` updated inquiry. `400` if deal_value_cents < 0. |

---

### 4.3 Backend Service Logic — Complex Flows

#### 4.3.1 Notification Fan-out (REQ-02)

Triggering actions and their recipients (all fan-out happens inside the same request transaction as the triggering action):

| Trigger | Where to hook | Recipients | event_type |
|---|---|---|---|
| `POST /api/appointments` | End of appointment creation handler | Patient, Doctor | `appointment_confirmed` |
| Appointment status → 'Cancelled' | `PATCH /...appointments/{id}/status` | Patient, Doctor | `appointment_cancelled` |
| Appointment status → 'NoShow' | Same | Patient only | `appointment_noshow` |
| Lab result `is_finalized = 1` | `POST /api/lab/orders/{id}/results` or PATCH finalize | Ordering Doctor, Patient | `lab_result_ready` |
| `POST /api/staff/invoices` or `POST /api/admin/invoices` | Invoice creation | Patient | `invoice_created` |
| `POST /api/public/contact-messages` | Contact form submission | All active Admin + Staff users | `contact_form_received` |
| `POST /api/admin/users` | Admin creates account | Newly created user | `account_created` |
| `PATCH /api/admin/users/{id}/status` (deactivate) | Deactivation | Deactivated user | `account_deactivated` |
| `POST /api/lab/orders` creation | Lab order entered queue | All active Lab users | `lab_order_assigned` |
| `POST /api/doctor/referrals` | Referral created | All active doctors in receiving dept (or receiving_doctor_id if specified) | `referral_received` |
| `PATCH /api/doctor/referrals/{id}/accept` | Accepted | Patient, Referring Doctor | `referral_status_changed` |
| `PATCH /api/doctor/referrals/{id}/decline` | Declined | Patient, Referring Doctor | `referral_status_changed` |
| Cancellation triggers waitlist | Inside cancellation handler | First waitlisted patient | `waitlist_slot_available` |
| `POST /api/doctor/appointments/{id}/discharge-summary` | Summary created | Patient | `discharge_summary_ready` |
| Follow-up appointment created inside discharge summary POST | Same | Patient, Doctor | `follow_up_booked` |
| Poll-on-login: appointment_reminder schedule matures | `check_and_fire_deferred_notifications` | Patient, Doctor | `appointment_reminder` |
| Poll-on-login: survey trigger_after matures | Same | Patient | `survey_available` |

**Fan-out cap concern (OI-11)**: `contact_form_received` and `lab_order_assigned` can fan out to N users. For `contact_form_received`, query `SELECT id FROM users WHERE role IN ('Admin','Staff') AND is_active=1` and batch-insert. For typical hospital scale (< 50 admin/staff), this is a single bulk INSERT — acceptable.

#### 4.3.2 FIFO Waitlist Cascade (REQ-09)

When a slot is freed (appointment cancelled):
1. Lock the waitlist FIFO query using `SELECT ... ORDER BY created_at ASC LIMIT 1` — SQLite's serialized writes make this safe without explicit row-level locks.
2. Set `held_slot_time = HH:MM extracted from cancelled appointment.scheduled_at`.
3. The freed slot is NOT returned by `GET /doctors/{id}/available-slots` while `status='Notified'` exists for that (doctor_id, date, held_slot_time). The slot query must exclude held slots.
4. When confirmation window expires (poll-on-login): next patient is promoted — re-run the cascade.

#### 4.3.3 Server-side PDF (REQ-08)

Sequence:
1. Authenticate patient.
2. Query: all appointments in date range (with visit notes, prescriptions, lab results, vitals, intake forms, discharge summaries).
3. Sort by `scheduled_at` ASC.
4. Render to HTML string via `string.Template` or Jinja2. Keep CSS minimal (print-safe: no `backdrop-filter`, no dark backgrounds).
5. `HTML(string=html).write_pdf()` — returns bytes.
6. Stream as `StreamingResponse`.

Performance: for 100 appointments with all associations, WeasyPrint generation should be well within 10s. If performance is a concern in practice, pagination of the data gather step (not the PDF output) can be added.

#### 4.3.4 Analytics Aggregation (REQ-06)

Each analytics endpoint runs one or two SQL aggregate queries. No ORM query builder — use raw SQL for clarity and performance.

```sql
-- Appointment volume by month
SELECT
    strftime('%Y-%m', scheduled_at) AS month,
    COUNT(*) AS total,
    SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END) AS cancelled,
    SUM(CASE WHEN status='NoShow' THEN 1 ELSE 0 END) AS noshow,
    SUM(CASE WHEN status='Scheduled' THEN 1 ELSE 0 END) AS scheduled,
    ROUND(
        100.0 * SUM(CASE WHEN status='NoShow' THEN 1 ELSE 0 END) /
        NULLIF(COUNT(*) - SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END), 0),
        2
    ) AS noshow_rate
FROM appointments
WHERE date(scheduled_at) BETWEEN ? AND ?
GROUP BY month
ORDER BY month ASC;
```

```sql
-- Revenue by month (OI-7: uses paid_at for collected series)
SELECT
    strftime('%Y-%m', created_at) AS month,
    SUM(total_amount_cents) AS invoiced_cents,
    SUM(CASE WHEN status='Paid' THEN total_amount_cents ELSE 0 END) AS collected_approx_cents
FROM invoices
WHERE date(created_at) BETWEEN ? AND ?
GROUP BY month
ORDER BY month ASC;
-- NOTE: collected_approx_cents uses created_at grouping as fallback only if paid_at is NULL
-- Accurate collected query:
SELECT
    strftime('%Y-%m', paid_at) AS month,
    SUM(total_amount_cents) AS collected_cents
FROM invoices
WHERE status='Paid' AND paid_at IS NOT NULL AND date(paid_at) BETWEEN ? AND ?
GROUP BY month ORDER BY month ASC;
```

---

### 4.4 Frontend Component Structure (New Components)

All new page components follow the existing naming convention (PascalCase, location: `src/frontend/src/pages/{role}/`). New shared components go in `src/frontend/src/components/`.

#### New pages

| Component file | Route | Role |
|---|---|---|
| `pages/doctor/DoctorAvailabilityPage.tsx` | `/doctor/availability` | Doctor |
| `pages/doctor/DoctorReferralsPage.tsx` | `/doctor/referrals` | Doctor |
| `pages/doctor/DoctorRatingsPage.tsx` | `/doctor/ratings` | Doctor |
| `pages/patient/PatientIntakeFormPage.tsx` | `/patient/appointments/:id/intake` | Patient |
| `pages/patient/PatientDischargeSummaryPage.tsx` | `/patient/appointments/:id/discharge` | Patient |
| `pages/patient/PatientWaitlistPage.tsx` | `/patient/waitlist` | Patient |
| `pages/patient/PatientSurveysPage.tsx` | `/patient/surveys` | Patient |
| `pages/patient/PatientReferralsPage.tsx` | `/patient/referrals` | Patient |
| `pages/staff/StaffVitalsPage.tsx` | Embedded in `StaffPatientDetailPage` as a section (no new route) | Staff |
| `pages/staff/StaffWaitlistPage.tsx` | `/staff/waitlist` | Staff |
| `pages/admin/AdminAnalyticsPage.tsx` | `/admin/analytics` | Admin |
| `pages/admin/AdminSurveysPage.tsx` | `/admin/surveys` | Admin |
| `pages/admin/AdminCorporatePage.tsx` | `/admin/corporate` | Admin |
| `pages/admin/AdminConfigPage.tsx` | `/admin/config` | Admin |
| `pages/public/CorporatePage.tsx` | `/corporate` | Public |
| `pages/public/SearchPage.tsx` | `/search` | Public |
| `pages/shared/NotificationsPage.tsx` | `/{role}/notifications` (or shared `/notifications` with redirect logic) | All authenticated |

#### New shared components

| Component file | Purpose |
|---|---|
| `components/NotificationBell.tsx` | Bell icon with unread badge; dropdown panel; integrates with `/api/notifications/unread-count` and `/api/notifications`. Replaces the placeholder `Bell` icon in `AppShell`. |
| `components/NotificationPanel.tsx` | The dropdown notification list rendered by `NotificationBell`. |
| `components/AvailabilityWeekGrid.tsx` | Weekly Mon–Sun grid for doctor schedule config. |
| `components/SlotPicker.tsx` | Grid of slot time buttons for patient/staff booking. Calls `/api/doctors/{id}/available-slots?date=...`. |
| `components/StarRating.tsx` | Interactive 1–5 star input (patient survey, doctor ratings read-only display). |
| `components/VitalsChart.tsx` | Recharts `LineChart` wrapper for a single vital metric. Used 4x in the vitals trend section. |
| `components/DischargePanel.tsx` | The discharge summary creation panel (shown after appointment Completed action). |
| `components/WaitlistCountdown.tsx` | Countdown display for `Notified` waitlist entry (hours/minutes until confirmation deadline). |
| `components/IntakeFormView.tsx` | Read-only intake form display for Doctor/Staff views. |
| `components/IntakeFormEdit.tsx` | Editable intake form for patient submission. |
| `components/SurveyForm.tsx` | Survey submission form (star pickers + comment textarea). |

#### API client additions

New functions to add to `src/frontend/src/api/`:
- `api/notifications.ts` — `getUnreadCount()`, `getNotifications()`, `markAsRead()`, `markAllRead()`
- `api/availability.ts` — `getAvailableSlots()`, `getSchedule()`, `createScheduleWindow()`, ...
- `api/vitals.ts` — `getVitals()`, `recordVitals()`
- `api/referrals.ts` — `createReferral()`, `getSentReferrals()`, `getReceivedReferrals()`, `acceptReferral()`, `declineReferral()`
- `api/waitlist.ts` — `joinWaitlist()`, `getMyWaitlist()`, `confirmWaitlistSlot()`, `leaveWaitlist()`
- `api/surveys.ts` — `getMySurveys()`, `submitSurvey()`, `getDoctorRatings()`
- `api/analytics.ts` — `getAppointmentAnalytics()`, `getRevenueAnalytics()`, `getDepartmentAnalytics()`, `getAcquisitionAnalytics()`
- `api/corporate.ts` — `getCorporatePackages()`, `submitCorporateInquiry()`, `getAdminPackages()`, ...
- Add to `api/patient.ts`: `exportPDF()`, `getIntakeForm()`, `submitIntakeForm()`, `getDischargesSummaries()`
- Add to `api/doctor.ts`: `createDischargesummary()`, `getDoctorRatings()`
- Add to `api/public.ts`: `searchPublic()`, `getCorporatePackages()`

#### Route additions to `App.tsx`

New routes to add in the appropriate role blocks:
```tsx
// Admin
<Route path="/admin/analytics" element={<AdminAnalyticsPage />} />
<Route path="/admin/surveys" element={<AdminSurveysPage />} />
<Route path="/admin/corporate" element={<AdminCorporatePage />} />
<Route path="/admin/config" element={<AdminConfigPage />} />

// Doctor
<Route path="/doctor/availability" element={<DoctorAvailabilityPage />} />
<Route path="/doctor/referrals" element={<DoctorReferralsPage />} />
<Route path="/doctor/ratings" element={<DoctorRatingsPage />} />

// Patient
<Route path="/patient/appointments/:id/intake" element={<PatientIntakeFormPage />} />
<Route path="/patient/appointments/:id/discharge" element={<PatientDischargeSummaryPage />} />
<Route path="/patient/waitlist" element={<PatientWaitlistPage />} />
<Route path="/patient/surveys" element={<PatientSurveysPage />} />
<Route path="/patient/referrals" element={<PatientReferralsPage />} />
<Route path="/patient/notifications" element={<NotificationsPage />} />

// Staff
<Route path="/staff/waitlist" element={<StaffWaitlistPage />} />

// Public
<Route path="/corporate" element={<CorporatePage />} />
<Route path="/search" element={<SearchPage />} />
```

#### AppShell topbar update

`AppShell.tsx` must import and render `<NotificationBell />` in the topbar (replacing the existing placeholder `Bell` icon from VI-SHELL-4). `NotificationBell` is self-contained: it fetches unread count on mount and on each navigation event.

---

### 4.5 Dependency Sequencing for Phase 5 Task Breakdown

Lavanya must sequence the implementation tasks in this order (Phase 6 is strictly sequential):

**Group A — Must be done first (foundations):**
1. `db/schema.sql` additions (all 16 new tables + `invoices.paid_at`) — schema migration, no UI
2. `vitals` table + `GET/POST /api/patients/{patient_id}/vitals` (resolves pre-existing STF-4 gap; needed by REQ-04)
3. REQ-01 full backend: `doctor_availability_schedules`, `doctor_slot_configs`, `doctor_availability_blocks` tables + all availability endpoints + `get_available_slots()` service function
4. Update `POST /api/appointments` to validate slot availability (call `get_available_slots()`) + create intake_form row

**Group B — Requires Group A:**
5. REQ-02 notification infrastructure: `notifications` table, `notification_schedules` table, `create_notifications()` helper, `/api/notifications/*` endpoints, `check_and_fire_deferred_notifications()` utility, wire into all triggering endpoints listed in §4.3.1
6. Frontend `NotificationBell` component + `AppShell` integration (requires REQ-02 backend complete)

**Group C — Requires Group A (and optionally Group B for notifications):**
7. REQ-03 intake forms: endpoint + patient UI (intake form fill) + doctor/staff read-only view
8. REQ-04 vitals UI: Staff recording form + Doctor vitals trend charts (Recharts, `VitalsChart` component)
9. REQ-05 referrals: backend + doctor UI + patient read-only view (requires REQ-02 for notifications)
10. REQ-06 analytics dashboard: backend queries + frontend charts (Recharts)
11. REQ-07 public search: backend search endpoint + symptom tags admin UI + public search bar + `/search` page
12. REQ-08 PDF export: WeasyPrint backend + patient export button + date range filter modal

**Group D — Requires Group A + Group B:**
13. REQ-09 waitlist: backend (cancellation trigger, confirm endpoint) + patient waitlist UI + staff waitlist management + admin config
14. REQ-10 discharge summaries: backend (atomic create) + doctor discharge panel + patient discharge view + survey row creation (requires REQ-11 schema)
15. REQ-11 surveys: backend (poll-on-login trigger) + patient survey UI + doctor ratings page + admin moderation

**Group E — Independent:**
16. REQ-12 corporate packages: public packages page + inquiry form + admin pipeline management (no dependency on Groups A/B/C/D)

---

### 4.6 Cross-Requirement Consistency Checks

Before Chintu begins implementation, verify:

1. **Field naming consistency** (all uses of the same entity): `patient_id` (always integer FK, never `patientId` or `pid`), `doctor_id`, `appointment_id`, `survey_id`, `entry_id`, `package_id`, `inquiry_id` — all snake_case in JSON responses.

2. **AUTHZ-2 enforcement** (Doctor can only access patients they have appointment with): Required on all new doctor-facing endpoints touching patient data: vitals GET, referral creation, intake form read, discharge summary create.

3. **Intake form auto-creation**: Must be created atomically with appointment in `POST /appointments`. If intake form creation fails, the appointment must not be created either (one transaction).

4. **Survey auto-creation**: Must be created whenever an appointment transitions to 'Completed' — whether via `PATCH /api/doctor/appointments/{id}/status` (existing endpoint) or via the discharge summary POST handler. Both code paths must trigger survey creation. Add a helper `create_survey_for_appointment(db, appointment)` called from both.

5. **Slots excluded from public query when waitlist-held**: The `get_available_slots()` function must exclude slots where a `waitlist_entries` row exists with `status='Notified'` AND `held_slot_time = slot_time` AND `preferred_date = query_date` AND `doctor_id = query_doctor_id`.

6. **`paid_at` set automatically**: Whenever `PATCH /api/staff/invoices/{id}` or `PATCH /api/billing/invoices/{id}` changes `status` to 'Paid', the backend must also set `paid_at = current UTC timestamp`. No endpoint accepts `paid_at` in the request body.

---

## Communications Log

This design was produced as Sagar's Phase 3+4 output for the 2026-07-20 Krishna cycle (12-requirement batch). Lavanya should read this document fully before beginning Phase 5 task breakdown. The dependency sequencing in §4.5 is the recommended task ordering for Lavanya's milestone plan.

Files written in this phase:
- `docs/technical-design.md` (this file — created)
- `db/schema.sql` (Batch 2 DDL appended — see §4.1.2)
- `docs/project-status.md` (changelog entry added)

Files that need updating by Chintu before implementation begins:
- `docs/api-spec.md` — append new endpoint sections 11–22 from §4.2 above
- `docs/architecture.md` — update ER diagram with 16 new tables and `invoices.paid_at` column; add note on WeasyPrint (OI-3), Recharts (OI-4), poll-on-login notification pattern (OI-2)
- `requirements.txt` — add `weasyprint>=60.0`
- `package.json` — add `recharts` (latest stable)
- `waitlist_entries` table: add `held_slot_time TEXT` column (nullable; noted in §4.2 endpoint 19)
