# Green Valley Hospital — Delivery Plan: Batch 2 (REQ-01 through REQ-12)

**Owner**: Lavanya (Requirements Analyst & Delivery Planning Lead)
**Phase**: 5 — Task Breakdown & Delivery Plan
**Date produced**: 2026-07-20
**Cycle**: 2026-07-20 Krishna requirements batch (12 requirements)
**Companion docs**: `docs/requirements.md` §9, `docs/technical-design.md`, `db/schema.sql`, `docs/api-spec.md`

---

## 1. Executive Summary

This plan covers the full implementation task breakdown for the 12 requirements in the 2026-07-20 batch. Tasks are assigned to Chintu (primary implementer) with Sagar available for pairing on the most complex backend items. All tasks execute strictly sequentially — one at a time, never in parallel — per the batch-handling rules in `docs/agent-collaboration-protocol.md`.

Execution order follows the dependency groups defined by Sagar in `docs/technical-design.md` §4.5, with three pre-implementation housekeeping tasks that must complete before any Group A work begins. After each task Chintu implements, Sagar conducts a Phase 7 code review and Gopal conducts Phase 8 QA before the next task starts.

**Summary timeline** (Chintu implementation days only; see §3 for full milestone dates including review/QA overhead):

| Phase | Groups / Tasks | Start | End (implementation) |
|---|---|---|---|
| Pre-implementation housekeeping | TASK-001 to TASK-003 | 2026-07-20 | 2026-07-21 |
| Group A — Foundation | TASK-004 to TASK-010 | 2026-07-22 | 2026-08-05 |
| Group B — Post-foundation | TASK-011 to TASK-016 | 2026-08-06 | 2026-08-19 |
| Group C — Independent features | TASK-017 to TASK-028 | 2026-08-20 | 2026-09-14 |
| Group D — Analytics (data-stable) | TASK-029 to TASK-030 | 2026-09-15 | 2026-09-18 |
| Sagar group-level review + Gopal QA | All groups | 2026-09-19 | ~2026-10-10 |
| Final acceptance | — | 2026-10-11 | 2026-10-17 |

---

## 2. Task Breakdown

### Effort key

| Label | Definition | Working days |
|---|---|---|
| S | Small — straightforward change, 1–2 endpoints or a single simple component | 0.5 |
| M | Medium — 3–5 endpoints or a moderate UI page with state | 1.0 |
| L | Large — complex backend service or multi-section UI with async state, validation, edge cases | 2.0 |
| XL | Extra Large — very complex feature with multiple interacting backend services and UI | 3.0 |

Dates below are Chintu's estimated implementation completion dates, counted in working days from 2026-07-20. Review (Sagar) and QA (Gopal) happen between groups and add elapsed time beyond these dates (see §3).

---

### Pre-Implementation Housekeeping

These three tasks must complete before any Group A implementation begins. They are not feature tasks but are required for Chintu to have the correct contract documents and schema in place.

---

**TASK-001**
- Requirement: Cross-batch prerequisite
- Responsible: Chintu
- Title: Append Batch 2 API endpoint sections to `docs/api-spec.md`
- Description: Copy endpoint groups 11–22 verbatim from `docs/technical-design.md` §4.2 into `docs/api-spec.md` as new top-level sections. Do not rewrite or summarize — the technical design is the contract; `api-spec.md` is the published version of it. Verify section numbers do not conflict with existing sections 1–10.
- Effort: S
- Dependencies: None
- Milestone/Group: Pre-implementation
- Definition of done: `docs/api-spec.md` contains sections 11–22 matching §4.2 of `docs/technical-design.md` exactly. No existing sections modified.
- Estimated completion: 2026-07-20

---

**TASK-002**
- Requirement: Cross-batch prerequisite
- Responsible: Chintu
- Title: Update `docs/architecture.md` — ER diagram and library notes for Batch 2
- Description: Add all 16 new tables from Batch 2 DDL (`doctor_availability_schedules`, `doctor_slot_configs`, `doctor_availability_blocks`, `notifications`, `notification_schedules`, `intake_forms`, `vitals`, `referrals`, `department_symptom_tags`, `waitlist_entries`, `system_config`, `discharge_summaries`, `satisfaction_surveys`, `corporate_packages`, `corporate_inquiries`) and the `invoices.paid_at` column addition to the ER diagram section. Add a note under the backend libraries section documenting: WeasyPrint (OI-3 decision, `pip install weasyprint>=60.0`), Recharts (OI-4 decision, `npm install recharts`), and the poll-on-login notification pattern (OI-2 decision). Do not change any existing sections.
- Effort: S
- Dependencies: TASK-001
- Milestone/Group: Pre-implementation
- Definition of done: `docs/architecture.md` ER section includes all 16 new tables with FK relationships; library notes added for WeasyPrint, Recharts, poll-on-login. No existing content removed.
- Estimated completion: 2026-07-20

---

**TASK-003**
- Requirement: Cross-batch prerequisite
- Responsible: Chintu
- Title: Apply Batch 2 schema DDL and update seed data
- Description: Verify `db/schema.sql` already contains the Batch 2 DDL (Sagar appended it in Phase 4 — confirm it is present and complete including `waitlist_entries.held_slot_time TEXT` column and all indexes). If already present, no schema change needed. Then update `db/seed/seed.py` to include: (a) `INSERT OR IGNORE INTO system_config VALUES ('waitlist_confirmation_hours', '4', CURRENT_TIMESTAMP)` for REQ-09 admin config; (b) at least 2 sample `corporate_packages` rows (e.g., "Wellness Basic" tier 1 and "Executive Health" tier 2 with sample descriptions and price ranges) so the public `/corporate` page does not show an empty state on first run. Add `weasyprint>=60.0` to `requirements.txt`. Add `recharts` (latest stable ^2.12) to `src/frontend/package.json`. Verify the `notification_schedules.survey_id` FK ordering note in the schema comments — `satisfaction_surveys` must be created before `notification_schedules` in any migration script (check that the DDL order in `db/schema.sql` reflects this).
- Effort: M
- Dependencies: TASK-002
- Milestone/Group: Pre-implementation
- Definition of done: `db/schema.sql` contains all 16 new tables and `invoices.paid_at`; `db/seed/seed.py` seeds `system_config` and at least 2 `corporate_packages` rows; `requirements.txt` includes `weasyprint>=60.0`; `package.json` includes `recharts ^2.12`; local `db init` and seed run without error.
- Estimated completion: 2026-07-21

---

### Group A — Foundation (must complete before Groups B, C, D)

The schema that underpins slot availability, appointment intake integration, and the notification infrastructure must be fully functional before any downstream feature can be built safely. Chintu should flag to Akhil immediately if the slot-query algorithm or the notification fan-out design differs from what is documented in `docs/technical-design.md` §4.3 — do not improvise a different architecture.

---

**TASK-004**
- Requirement: REQ-01 (Doctor Availability & Slot Management)
- Responsible: Chintu (Sagar available for pairing on slot-query algorithm)
- Title: REQ-01 Availability backend — models, all endpoints, slot-query service
- Description: Implement the full availability backend for REQ-01: (a) SQLAlchemy models for `doctor_availability_schedules`, `doctor_slot_configs`, `doctor_availability_blocks`; (b) `get_available_slots(db, doctor_id, date_str)` as a pure function (testable in isolation) per the algorithm in `docs/technical-design.md` §4.2 endpoint 11 — this function must: load weekly schedule windows for the day-of-week, resolve slot duration from `doctor_slot_configs` (defaulting to 30 min), generate candidate slots, remove blocked slots (full-day and time-range blocks), remove already-booked slots (`status IN ('Scheduled', 'Completed')`), and remove waitlist-held slots (`status='Notified'` with `held_slot_time` matching); (c) all 19 availability endpoints: doctor-scoped (GET/POST/PUT/DELETE schedule, GET/PUT config, GET/POST/DELETE blocks) and admin-scoped (GET/POST/PUT/DELETE schedule, GET/PUT config, GET/POST/DELETE blocks for any doctor) per §4.2 endpoint group 11. Ownership checks: `403` if a doctor's schedule endpoint is called for a schedule_id belonging to a different doctor. Admin endpoints bypass ownership checks. `GET /api/doctors/{doctor_id}/available-slots?date=` must be accessible by Patient, Staff, Doctor, and Admin roles.
- Effort: XL
- Dependencies: TASK-003
- Milestone/Group: A
- Definition of done: All 19 endpoints return correct status codes per contract; `get_available_slots()` correctly excludes blocked, booked, and waitlist-held slots; unit test for the pure function covers: no schedule → empty list, full-day block → empty list, partial block → correct exclusion, already-booked slot → excluded; endpoint auth guards work for all four allowed roles on the public slots endpoint.
- Estimated completion: 2026-07-24

---

**TASK-005**
- Requirement: REQ-01 (slot validation on booking) + REQ-03 (intake form auto-create)
- Responsible: Chintu
- Title: Update `POST /api/appointments` — slot validation + intake form auto-creation
- Description: Modify the existing appointment creation endpoint (`POST /api/appointments`) to: (a) call `get_available_slots(db, doctor_id, scheduled_at.date())` before creating the appointment; if the requested `scheduled_at` time is not in the returned slot list, return `409 {"detail": "Slot no longer available. Please select another time."}`; (b) atomically insert an empty `intake_forms` row (`chief_complaint=NULL`, all optional fields NULL, `submitted_at=NULL`) linked to the new `appointment_id` inside the same transaction as the appointment creation — if intake form insertion fails, the appointment must also roll back. This is the intake form auto-creation trigger described in `docs/technical-design.md` §4.2 endpoint 13 ("Trigger" note). Cross-check: `uq_appointments_doctor_slot` unique index already provides last-line defense per OI-13 — the 409 from this index must also return the same friendly message (catch `IntegrityError` and return 409).
- Effort: M
- Dependencies: TASK-004
- Milestone/Group: A
- Definition of done: `POST /api/appointments` with a valid slot succeeds and creates both an appointment and an empty intake_forms row in one transaction; `POST` with an unavailable slot returns 409 with the specified message; `POST` with a slot that races to a duplicate triggers the unique index 409 with the same message.
- Estimated completion: 2026-07-27

---

**TASK-006**
- Requirement: REQ-06 (revenue analytics — OI-7 prerequisite)
- Responsible: Chintu
- Title: Set `paid_at` automatically on invoice status transition to 'Paid'
- Description: Update all backend endpoints that can change an invoice's `status` to 'Paid' — specifically `PATCH /api/staff/invoices/{id}` and `PATCH /api/billing/invoices/{id}` (and any other invoice-status-update handler in the codebase) — so that when `status` is set to 'Paid', `paid_at` is also set to the current UTC timestamp (server-side). `paid_at` must never be accepted from the request body. The analytics revenue endpoint (TASK-029) uses `paid_at` for the "collected" series per OI-7. Grep the codebase for all invoice status update handlers to ensure no handler is missed. Also add the index `CREATE INDEX idx_invoices_paid_at ON invoices(paid_at)` to `db/schema.sql` if not already present (Sagar included it in the DDL, but verify it is present in the file).
- Effort: S
- Dependencies: TASK-003
- Milestone/Group: A
- Definition of done: Any invoice status update that sets `status='Paid'` also sets `paid_at` to the current UTC ISO-8601 string; invoices already at 'Paid' status are not double-updated; `paid_at` is read-only from the API (not settable via request body); `idx_invoices_paid_at` index exists in schema.
- Estimated completion: 2026-07-27

---

**TASK-007**
- Requirement: REQ-02 (In-App Notification Center)
- Responsible: Chintu (Sagar available for pairing on fan-out wiring)
- Title: REQ-02 Notifications backend — infrastructure, endpoints, deferred-notification utility, fan-out wiring
- Description: Implement the full notifications backend: (a) SQLAlchemy models for `notifications` and `notification_schedules`; (b) `create_notifications(db, events: list[dict])` batch-insert helper (called at the end of every triggering transaction, never outside a transaction); (c) `check_and_fire_deferred_notifications(db, user_id)` utility — fires matured `appointment_reminder` schedules and `survey_available` schedules on each authenticated request (called from `get_current_user` dependency); (d) all 4 notification endpoints: `GET /api/notifications/unread-count` (must respond < 200ms using `idx_notifications_recipient_read`), `GET /api/notifications` (paginated, filtered to caller's user_id), `PATCH /api/notifications/{id}/read` (403 if not caller's), `POST /api/notifications/mark-all-read`; (e) wire `create_notifications()` into ALL triggering endpoints listed in `docs/technical-design.md` §4.3.1: appointment confirmed (POST /appointments), appointment cancelled, appointment NoShow, lab result finalized, invoice created, contact form submitted (fan-out to all Admin + Staff), account created, account deactivated, lab order entered (fan-out to all Lab users), referral created (fan-out to receiving dept doctors), referral accepted/declined (to patient + referring doctor), waitlist slot available (to first waiting patient), discharge summary ready (to patient), follow-up booked (to patient + doctor), poll-on-login appointment reminder, poll-on-login survey available. The fan-out for contact form and lab order queries `SELECT id FROM users WHERE role IN (...) AND is_active=1` and batch-inserts. All fan-outs inside the same transaction as the triggering action.
- Effort: L
- Dependencies: TASK-005, TASK-006
- Milestone/Group: A
- Definition of done: All 4 notification endpoints return correct shapes; unread-count endpoint query uses the index and returns in < 200ms with 1000 notification rows seeded; deferred notification fires exactly once (is_fired updated); fan-out for appointment-confirmed creates notifications for both patient and doctor; fan-out for contact form creates notifications for all active Admin + Staff users; no fan-out notification is created outside a transaction.
- Estimated completion: 2026-07-29

---

**TASK-008**
- Requirement: REQ-01 (Doctor Availability & Slot Management — Doctor UI)
- Responsible: Chintu
- Title: REQ-01 Doctor Availability UI — DoctorAvailabilityPage + AvailabilityWeekGrid + Admin override
- Description: Implement the Doctor portal availability configuration UI: (a) `pages/doctor/DoctorAvailabilityPage.tsx` at route `/doctor/availability` — weekly grid (Mon–Sun) showing existing time windows per day, "+ Add Window" action per day (opens a time-picker form), slot duration dropdown (10/15/20/30/45/60 min, PUT on change), "Block a Date" button (modal: date picker + optional time range), "Upcoming Blocks" list below the grid; (b) `components/AvailabilityWeekGrid.tsx` — reusable weekly schedule display/edit grid; (c) Doctor sidebar: add "Schedule" item with `CalendarDays` icon linking to `/doctor/availability`; (d) Admin availability override: add a "Manage Availability" action button on the doctor row in `/admin/users` (existing page) — clicking it loads the same `DoctorAvailabilityPage` UI but calls the admin-scoped endpoints (`/api/admin/doctors/{doctor_id}/availability/*`). UI states per §3.1: skeleton loading, empty state with CTA, save success inline toast, error `<PageError>` component. New route in `App.tsx`: `<Route path="/doctor/availability" element={<DoctorAvailabilityPage />} />`.
- Effort: L
- Dependencies: TASK-004
- Milestone/Group: A
- Definition of done: Doctor can view their weekly schedule, add a time window, update slot duration, and add a one-off block — all changes persist and are reflected on page reload; Admin can open the same editor for any doctor via the /admin/users doctor row action; empty state and loading skeleton render correctly; "Schedule" appears in Doctor sidebar.
- Estimated completion: 2026-07-31

---

**TASK-009**
- Requirement: REQ-01 (Patient + Staff booking flow update)
- Responsible: Chintu
- Title: REQ-01 Update patient and staff booking pages with SlotPicker component
- Description: (a) Create `components/SlotPicker.tsx` — a grid of slot time buttons; calls `GET /api/doctors/{id}/available-slots?date=` when date changes; highlights selected slot; shows "No slots available for this date" empty state with a "Join Waitlist for [date]" button (this button will be wired in TASK-012 to the waitlist flow — for now it can be a disabled placeholder with a `TODO: wire waitlist` comment and a data-testid attribute); (b) Update `PatientBookAppointmentPage` (or equivalent existing booking page) to replace any free-text time input with the `SlotPicker` — department → doctor → date picker flow per §3.1 journey, then slot grid; (c) Update the Staff booking/appointment-creation page equivalently; (d) On 409 response from `POST /appointments`: show "That slot was just booked. Please choose another time." inline message and re-fetch the slot list for the same date automatically. Past dates disabled in the date picker.
- Effort: M
- Dependencies: TASK-008
- Milestone/Group: A
- Definition of done: Patient and staff can select a doctor, pick a date, see available slots as time-button grid, select one, and book — the 409 race condition produces the correct inline message and refreshes the slot list; "Join Waitlist" placeholder button is visible when slot list is empty (disabled until TASK-012); SlotPicker renders skeleton while fetching.
- Estimated completion: 2026-08-03

---

**TASK-010**
- Requirement: REQ-02 (In-App Notification Center — frontend)
- Responsible: Chintu
- Title: REQ-02 Notifications frontend — NotificationBell, panel, full-page view, AppShell integration
- Description: (a) `components/NotificationBell.tsx` — bell icon with red badge showing unread count (hidden when 0); fetches `GET /api/notifications/unread-count` on mount and on each navigation event (use React Router location); badge shows count; clicking opens `NotificationPanel`; (b) `components/NotificationPanel.tsx` — dropdown panel (right-aligned, z-index above content), shows 20 most recent notifications newest-first; unread items highlighted (light blue background, bold title); distinct icons per event_type (`CalendarCheck` appointment, `FlaskConical` lab, `Receipt` invoice, `UserCheck` referral, `ClipboardList` survey, `AlertCircle` account, `BarChart2` waitlist); clicking a notification item calls `PATCH /api/notifications/{id}/read` then navigates to `related_entity_type`/`related_entity_id` if present; "Mark all as read" button calls `POST /api/notifications/mark-all-read`; "View All" link at bottom; empty state "You're all caught up" with `BellOff` icon; 3-row skeleton while loading; (c) `pages/shared/NotificationsPage.tsx` — full paginated list at `/notifications` (shared route, accessible from all role portals); read/unread filter toggle; (d) `AppShell.tsx` update: replace the existing placeholder `Bell` icon (VI-SHELL-4) with `<NotificationBell />`; (e) Add route `/{role}/notifications` (or a shared `/notifications` route) in `App.tsx` for all six role portals.
- Effort: L
- Dependencies: TASK-007
- Milestone/Group: A
- Definition of done: Bell icon visible in AppShell topbar for all six role portals; badge count matches unread-count API; panel opens/closes on bell click; mark-as-read works per notification and in bulk; "View All" navigates to the full notifications page; full page is paginated and filter works; no existing AppShell layout broken.
- Estimated completion: 2026-08-05

---

### Group B — Depends on Group A (REQ-09, REQ-10, REQ-11)

REQ-09 (Waitlist) requires the slot availability engine (TASK-004) and the notification infrastructure (TASK-007). REQ-10 (Discharge Summary) requires the notification infrastructure and must also create a satisfaction survey row — so REQ-11's schema must be in place (it is, from TASK-003). REQ-11 (Surveys) backend can begin once REQ-10 is done because REQ-10's discharge handler is the primary survey row creation trigger.

---

**TASK-011**
- Requirement: REQ-09 (Appointment Waitlist System — backend)
- Responsible: Chintu (Sagar available for pairing on cancellation cascade logic)
- Title: REQ-09 Waitlist backend — all endpoints, cancellation trigger, expiry check
- Description: Implement the full waitlist backend: (a) SQLAlchemy model for `waitlist_entries`; (b) all waitlist endpoints per §4.2 endpoint group 19: `POST /api/waitlist` (create entry, 409 on duplicate active entry for same patient+doctor+date), `GET /api/patients/me/waitlist` (active entries with position calculated), `DELETE /api/patients/me/waitlist/{entry_id}` (sets status='Removed'), `POST /api/waitlist/{entry_id}/confirm` (creates appointment from held slot, 400 if deadline passed, 409 if slot re-taken), `GET /api/staff/waitlist/{doctor_id}` (staff: paginated, date filter optional), `DELETE /api/staff/waitlist/{entry_id}` (staff: sets Removed with reason), `GET /api/admin/config/waitlist`, `PUT /api/admin/config/waitlist`, `GET /api/admin/waitlist/stats`; (c) `trigger_waitlist_on_cancellation(db, appointment)` — called inside `PATCH .../appointments/{id}/status` when transitioning to 'Cancelled'; sets first FIFO entry to 'Notified', sets `held_slot_time`, sets `confirmation_deadline` from `system_config.waitlist_confirmation_hours`, creates `waitlist_slot_available` notification for the patient; (d) `check_waitlist_expiry(db, user_id)` — extend `check_and_fire_deferred_notifications` (TASK-007) to also check for expired 'Notified' entries past their `confirmation_deadline`; sets them to 'Expired', re-adds patient to back of queue with new 'Waiting' entry, triggers next patient in FIFO; (e) update `get_available_slots()` (TASK-004) to exclude slots where a 'Notified' waitlist entry exists with matching `held_slot_time`, `preferred_date`, and `doctor_id` — this step may require modifying the function from TASK-004 (document this dependency clearly for Sagar's review).
- Effort: L
- Dependencies: TASK-007, TASK-010
- Milestone/Group: B
- Definition of done: Patient can join waitlist when no slots available; cancellation of an appointment triggers notification to first waiting patient and sets held_slot_time; held slot is excluded from public slot query; patient can confirm within the window and receive an appointment; expired entry re-queues the patient; staff can view and remove entries; admin can read and update the confirmation window config.
- Estimated completion: 2026-08-07

---

**TASK-012**
- Requirement: REQ-09 (Appointment Waitlist System — frontend)
- Responsible: Chintu
- Title: REQ-09 Waitlist frontend — patient waitlist page, staff page, admin config, SlotPicker join button
- Description: (a) `pages/patient/PatientWaitlistPage.tsx` at `/patient/waitlist` — lists active waitlist entries; 'Notified' entry rendered as a highlighted card with `WaitlistCountdown.tsx` component showing hours/minutes until deadline and a "Confirm Appointment" button; 'Expired' entry rendered greyed with "Moved to back of queue" label; empty state "You're not on any waitlist"; (b) `components/WaitlistCountdown.tsx` — countdown display updating in real time from `confirmation_deadline`; (c) `pages/staff/StaffWaitlistPage.tsx` at `/staff/waitlist` — doctor selector (dropdown of all active doctors), table of waitlist entries for selected doctor (patient name, join date, preferred date, status), "Remove" button per row with confirmation modal; (d) Admin waitlist config: add a "Waitlist Settings" section to `pages/admin/AdminConfigPage.tsx` at `/admin/config` (new page) — "Confirmation Window: [N] hours" editable number input with Save; admin sidebar new item "Configuration" (`Settings` icon) → `/admin/config`; (e) Wire the "Join Waitlist for [date]" button in `SlotPicker.tsx` (placeholder added in TASK-009) to `POST /api/waitlist` — shows confirmation toast "You've joined Dr. [Name]'s waitlist for [date]." and navigates to `/patient/waitlist`; (f) Patient sidebar: add "Waitlist" (`Clock` icon) → `/patient/waitlist`; Staff sidebar: add "Waitlist" (`Clock` icon) → `/staff/waitlist`; new routes in `App.tsx`.
- Effort: L
- Dependencies: TASK-011
- Milestone/Group: B
- Definition of done: Patient can join waitlist from the booking page when no slots are available; waitlist page shows 'Notified' entry with live countdown and Confirm button; confirming creates appointment and navigates to appointments list; staff can view and remove entries; admin can update the confirmation window; sidebar items visible for patient, staff, admin.
- Estimated completion: 2026-08-11

---

**TASK-013**
- Requirement: REQ-10 (Discharge Summary & Follow-Up Scheduling — backend)
- Responsible: Chintu (Sagar available for pairing on atomic transaction logic)
- Title: REQ-10 Discharge Summary backend — atomic create with follow-up, all endpoints, survey row creation
- Description: Implement the full discharge summary backend: (a) SQLAlchemy model for `discharge_summaries`; (b) `POST /api/doctor/appointments/{appointment_id}/discharge-summary` — atomic transaction per OI-8 (§4.2 endpoint 20): validate appointment is Completed + belongs to calling doctor; check no existing discharge summary; if `follow_up` block provided, call slot validation; if slot taken → 409 + rollback; if valid → INSERT follow-up appointment (status='Scheduled') first, then INSERT discharge_summaries with `follow_up_appointment_id`; create notifications (`discharge_summary_ready` for patient; if follow-up booked: `follow_up_booked` for patient + doctor); INSERT `satisfaction_surveys` row (trigger_after = completed_at + 24h, expires_at = trigger_after + 7 days, notification_sent=0); INSERT `notification_schedules` row (trigger_type='survey_available', trigger_at = trigger_after); COMMIT all; `409` if discharge summary already exists; (c) `GET /api/doctor/appointments/{appointment_id}/discharge-summary`; (d) `GET /api/patients/me/discharge-summaries` (paginated); (e) `GET /api/patients/me/appointments/{appointment_id}/discharge-summary` (403 if not patient's); (f) CRITICAL: also add `create_survey_for_appointment(db, appointment)` helper called from the existing `PATCH /api/doctor/appointments/{id}/status` endpoint whenever status transitions to 'Completed' — this is the second trigger path. Both the discharge summary POST and the status-update PATCH must call this helper to prevent a patient being denied a survey because the doctor used the quick-status route rather than the discharge panel. Add a guard: if a `satisfaction_surveys` row already exists for this appointment, do not insert a second one (idempotent).
- Effort: L
- Dependencies: TASK-007
- Milestone/Group: B
- Definition of done: Discharge summary POST succeeds with and without a follow_up block; with follow-up: follow-up appointment is created and linked atomically (both roll back on slot conflict); satisfaction_surveys row and notification_schedule row created in same transaction; quick-status-to-Completed path also creates survey row (test both paths); 409 if summary already exists for appointment; patient can retrieve their own summaries; doctor gets 403 on another doctor's appointment.
- Estimated completion: 2026-08-13

---

**TASK-014**
- Requirement: REQ-10 (Discharge Summary & Follow-Up Scheduling — frontend)
- Responsible: Chintu
- Title: REQ-10 Discharge Summary frontend — DischargePanel, patient discharge view
- Description: (a) `components/DischargePanel.tsx` — full-screen modal or slide-out triggered from the doctor's appointments list "Complete & Discharge" button (add this button to the doctor's appointment row actions, replacing or augmenting any existing "Update Status" control); fields: Key Findings (required textarea), Patient Instructions (optional, collapsible by default), Activity Restrictions (optional, collapsible), Medication Reminders (optional, collapsible); "Book Follow-Up Appointment" collapsible section: date picker (future dates only) → loads available slots from `GET /api/doctors/{id}/available-slots?date=` for the calling doctor's own id → shows SlotPicker; "Complete & Save Discharge Summary" button with spinner; success toast "Appointment marked Complete. Discharge summary saved." (with follow-up clause if booked); (b) `pages/patient/PatientDischargeSummaryPage.tsx` at `/patient/appointments/:id/discharge` — read-only view of the discharge summary: Key Findings, Instructions, Restrictions, Medication Reminders, Follow-Up Appointment date/time (if booked); accessed via "View Discharge Summary" link/button on past appointments in the patient portal; new route in `App.tsx`.
- Effort: M
- Dependencies: TASK-013
- Milestone/Group: B
- Definition of done: Doctor can open DischargePanel from appointments list, fill required field, and save — appointment transitions to Completed and summary is saved; follow-up booking within the panel works end-to-end; patient sees "View Discharge Summary" link on completed appointments; patient discharge page renders all summary fields correctly; slot conflict on follow-up booking returns the correct 409 message and does not create a partial summary.
- Estimated completion: 2026-08-14

---

**TASK-015**
- Requirement: REQ-11 (Satisfaction Survey & Doctor Ratings — backend)
- Responsible: Chintu
- Title: REQ-11 Surveys backend — patient submission endpoints, doctor ratings, admin moderation
- Description: Implement the survey submission and rating endpoints. The `satisfaction_surveys` schema and row-creation logic were already built in TASK-013 (discharge summary backend). This task adds: (a) `GET /api/patients/me/surveys` — returns all surveys for the calling patient, with computed `status` field ('pending' / 'submitted' / 'expired') derived from `submitted_at`, `trigger_after`, and `expires_at`; (b) `POST /api/patients/me/surveys/{survey_id}` — submit a survey; validate `trigger_after <= now` (400 if not yet triggered); validate `expires_at > now` (403 if expired); validate not already submitted (409); set `submitted_at`, `doctor_star_rating`, `overall_star_rating`, `comment`; (c) `GET /api/doctor/ratings` — aggregate: `AVG(doctor_star_rating)` and `COUNT(*)` where `submitted_at IS NOT NULL` and `doctor_id = calling doctor's doctor_id`; plus anonymized comment list (comment text + submitted_at only, no patient identity); (d) `GET /api/admin/surveys` (paginated, filterable by doctor_id, date range, submitted_only); (e) `GET /api/admin/surveys/{survey_id}`; (f) `PATCH /api/admin/surveys/{survey_id}/remove-comment` — sets `comment = NULL` and `is_comment_removed = 1` (idempotent). Note: `check_and_fire_deferred_notifications` in TASK-007 already handles the poll-on-login `survey_available` notification — verify it fires for `satisfaction_surveys` rows where `notification_sent=0` AND `trigger_after <= now` AND `submitted_at IS NULL` AND `expires_at > now`.
- Effort: M
- Dependencies: TASK-013
- Milestone/Group: B
- Definition of done: Patient can list surveys with correct computed status; patient can submit a survey within the valid window (400 before trigger, 403 after expiry, 409 if already submitted); doctor ratings page returns correct average and review count after a survey is submitted; admin can list all surveys and remove a comment (idempotent); poll-on-login fires `survey_available` notification for newly matured surveys.
- Estimated completion: 2026-08-17

---

**TASK-016**
- Requirement: REQ-11 (Satisfaction Survey & Doctor Ratings — frontend)
- Responsible: Chintu
- Title: REQ-11 Surveys frontend — patient surveys page, survey form, doctor ratings, admin moderation
- Description: (a) `components/StarRating.tsx` — interactive 1–5 star input component; also renders as read-only display mode for doctor ratings; (b) `components/SurveyForm.tsx` — survey submission form: two StarRating inputs (Doctor rating, Overall rating — both required), comment textarea (optional, 1000 char max with character counter); (c) `pages/patient/PatientSurveysPage.tsx` at `/patient/surveys` — lists surveys: 'pending' entries as highlighted cards with "Rate Now" CTA opening SurveyForm; 'submitted' entries as greyed cards with "Submitted" badge (no rating re-display per SURVFR-4); 'expired' entries as greyed cards with "Expired" badge; (d) `pages/doctor/DoctorRatingsPage.tsx` at `/doctor/ratings` — aggregate star display (e.g. "4.3 / 5 stars, 47 reviews"), large star visual, anonymized comment list with submitted_at; empty state if 0 reviews; Doctor sidebar: "My Ratings" (`Star` icon) → `/doctor/ratings`; (e) `pages/admin/AdminSurveysPage.tsx` at `/admin/surveys` — paginated table: patient name, doctor, appointment date, star ratings, comment text, submission date, "Remove Comment" button per row with confirmation; filters: doctor dropdown, date range, comment presence toggle; removed comment shows "[Removed by admin]" in italic muted text; Admin sidebar: "Surveys" (`Star` icon) → `/admin/surveys`; Patient sidebar: "Surveys" (`Star` icon) → `/patient/surveys`; new routes in `App.tsx`.
- Effort: L
- Dependencies: TASK-015
- Milestone/Group: B
- Definition of done: Patient can view pending surveys, submit a survey with star ratings and comment, and see it move to 'submitted' state; doctor can view their aggregate rating and anonymous comments; admin can list all surveys, filter by doctor/date, and remove a comment (which shows the removed placeholder text); sidebar items visible for patient, doctor, admin.
- Estimated completion: 2026-08-19

---

### Group C — Depends on Group A (REQ-03, REQ-04, REQ-05, REQ-07, REQ-08, REQ-12)

All Group C items depend on Group A (the schema and slot engine) being complete. They execute after Group B in the sequential plan but are not blocked by Group B technically. REQ-05 (Referrals) requires the notifications backend (TASK-007 in Group A), which is satisfied. REQ-06 (Analytics) is promoted to Group D because it needs vitals, referrals, and revenue data (paid_at) to be in a stable, final shape — those come from Group C tasks TASK-019, TASK-021, and TASK-006 respectively.

---

**TASK-017**
- Requirement: REQ-03 (Patient Pre-Visit Intake Form — backend endpoints)
- Responsible: Chintu
- Title: REQ-03 Intake Form backend — GET and PATCH endpoints
- Description: The `intake_forms` schema exists (TASK-003) and the auto-creation hook in `POST /appointments` is done (TASK-005). This task adds the two intake form endpoints: (a) `GET /api/appointments/{appointment_id}/intake` — returns the intake form for the appointment; role-check: Patient (own appointment only, 403 otherwise), Doctor (assigned to appointment per AUTHZ-2), Staff, Admin; 404 should not occur in normal flow since auto-creation ensures a row exists; (b) `PATCH /api/appointments/{appointment_id}/intake` — Patient-only; allows partial update; if `submit=true`: validates `chief_complaint` and `symptom_duration` are non-null; sets `submitted_at` = current UTC if not already set (updating an already-submitted form also updates `submitted_at`); returns 403 if `appointment.status = 'Completed'`; returns 400 if `pain_scale` provided but not in 1–10.
- Effort: M
- Dependencies: TASK-005
- Milestone/Group: C
- Definition of done: Patient can retrieve and update their own intake form; submit with missing required fields returns 400; submit on a Completed appointment returns 403; Doctor, Staff, Admin can read (not write) the form; cross-patient access returns 403.
- Estimated completion: 2026-08-20

---

**TASK-018**
- Requirement: REQ-03 (Patient Pre-Visit Intake Form — frontend)
- Responsible: Chintu
- Title: REQ-03 Intake Form frontend — patient fill/edit UI, doctor/staff read-only view
- Description: (a) `components/IntakeFormEdit.tsx` — editable intake form: Chief Complaint (required textarea), Symptom Duration (required text input), Allergies (optional textarea), Current Medications (optional textarea), Pain Scale (range input 1–10 with numeric label display and ARIA attributes per §3.3 accessibility note), Additional Notes (optional textarea); "Save Draft" button (submit=false) and "Submit" button (submit=true, validates required fields client-side); shows "Draft saved [time]" after Save Draft; shows "Submitted on [date]" read-only view with pencil icon after Submit; (b) `components/IntakeFormView.tsx` — read-only display of all intake form fields; used by Doctor and Staff views; (c) `pages/patient/PatientIntakeFormPage.tsx` at `/patient/appointments/:id/intake` — loads the intake form; shows `IntakeFormEdit` if appointment is not Completed; shows read-only `IntakeFormView` if Completed (no edit button); (d) Update patient appointment detail view to show "Pre-Visit Intake Form" card below appointment info: "Not submitted yet" state with "Fill Out Now" link to `/patient/appointments/{id}/intake`; "Submitted on [date]" state with "Edit Submission" link; (e) Add `IntakeFormView` to doctor appointment detail view (doctor can see submitted or "Patient has not yet submitted an intake form" message); add to staff patient detail view similarly; new route in `App.tsx`.
- Effort: M
- Dependencies: TASK-017
- Milestone/Group: C
- Definition of done: Patient can fill, save draft, and submit intake form; re-editing a submitted form is allowed until appointment is Completed; Completed appointment shows read-only form with no edit button; Doctor and Staff see the form read-only on the patient/appointment detail views; pain scale slider has numeric label and ARIA attributes.
- Estimated completion: 2026-08-21

---

**TASK-019**
- Requirement: REQ-04 (Vitals Trend Visualization — backend)
- Responsible: Chintu
- Title: REQ-04 Vitals backend — models and GET/POST endpoints (resolves STF-4 schema gap)
- Description: The `vitals` table schema was added in TASK-003. This task implements the backend: (a) SQLAlchemy model for `vitals`; (b) `GET /api/patients/{patient_id}/vitals` — Doctor (AUTHZ-2 check: doctor must have at least one appointment with this patient), Staff, Admin only (403 for Patient or Doctor without appointment); paginated; ordered by `recorded_at ASC`; returns all fields; (c) `POST /api/patients/{patient_id}/vitals` — Staff and Admin only (403 for Doctor or Patient); request body: `{appointment_id?, systolic_bp?, diastolic_bp?, weight_kg?, pulse_bpm?, temperature_celsius?, height_cm?}`; validation: at least one measurement field must be non-null (400 if all null); BP both-or-neither rule: if one of systolic_bp/diastolic_bp is provided, both must be (400 otherwise); range validation per VITFR-2/3: pulse_bpm 20–300, temperature_celsius 30.0–45.0, weight_kg > 0, height_cm > 0; `recorded_by_user_id` set to calling user's id server-side.
- Effort: M
- Dependencies: TASK-003
- Milestone/Group: C
- Definition of done: Staff can POST vitals with any combination of valid fields; BP both-or-neither rule enforced; range validation returns 400 with field-specific errors; Doctor with appointment with patient can GET; Doctor without appointment with patient gets 403; Patient calling POST gets 403; paginated GET returns records ordered ASC by recorded_at.
- Estimated completion: 2026-08-24

---

**TASK-020**
- Requirement: REQ-04 (Vitals Trend Visualization — frontend)
- Responsible: Chintu
- Title: REQ-04 Vitals frontend — Staff record vitals section, Doctor vitals trend charts (Recharts)
- Description: (a) Install and verify `recharts ^2.12` is in `package.json` (added in TASK-003); (b) `components/VitalsChart.tsx` — Recharts `LineChart` wrapper for a single vital metric; props: `data` array, `xKey` (date string), `yKey` (measurement), `unit` (label), `lines` array (each with `key`, `label`, `strokeDasharray` for accessibility); renders with ARIA label on the chart container; (c) Embed a "Vitals" section in `StaffPatientDetailPage` (existing page at `/staff/patients/{patientId}`): "Record Vitals" button opens an inline form with all vitals fields per §3.4; BP validation (both-or-neither) enforced client-side; success adds new row to the vitals table below; (d) Add "Vitals Trend" section to the Doctor patient records page (`/doctor/patients/{patientId}` or equivalent): if < 2 records: informational callout "Minimum 2 readings required for trend display" + individual readings table; if >= 2 records: 2×2 grid of 4 VitalsChart instances — BP chart (two lines: Systolic solid, Diastolic `strokeDasharray="4 4"`), Weight, Pulse, Temperature; X-axis: `recorded_at` date; Recharts `<Legend>` shows color + dash-pattern symbols for accessibility (VITFR-5); below charts: tabular list of all readings with date, recorder name, all values; loading skeleton in chart areas.
- Effort: L
- Dependencies: TASK-019
- Milestone/Group: C
- Definition of done: Staff can record vitals from the patient detail page; new vitals entry appears in the table without page reload; Doctor sees trend charts for patients with >= 2 readings; charts use dash-pattern distinction for BP lines (not color alone); < 2 readings shows informational callout and table; loading skeleton renders during fetch; chart colors and line styles match spec.
- Estimated completion: 2026-08-26

---

**TASK-021**
- Requirement: REQ-05 (Inter-Department Referral Management — backend)
- Responsible: Chintu
- Title: REQ-05 Referrals backend — all endpoints, notification fan-out, RBAC
- Description: Implement the full referrals backend: (a) SQLAlchemy model for `referrals`; (b) `POST /api/doctor/referrals` — Doctor only; validate AUTHZ-2 (doctor has appointment with patient); insert referral row (status='Pending'); fan-out `referral_received` notification to all active doctors in `receiving_department_id` (or just `receiving_doctor_id` if specified); (c) `GET /api/doctor/referrals/sent` — paginated, filtered by `referring_doctor_id = caller's doctor_id`, optional status filter; (d) `GET /api/doctor/referrals/received` — paginated, filtered by `receiving_department_id = caller's department_id` AND (`receiving_doctor_id IS NULL` OR `= caller's doctor_id`); ordered Urgent first then by created_at; (e) `PATCH /api/doctor/referrals/{referral_id}/accept` — 403 if caller not in receiving department (AUTHZ-13); 409 if already Accepted/Declined; sets status='Accepted', `receiving_doctor_id` to caller; sends `referral_status_changed` to patient + referring doctor; (f) `PATCH /api/doctor/referrals/{referral_id}/decline` — 403 AUTHZ-13 check; requires `note` in body (400 if missing); sets status='Declined' (terminal per OI-5 assumption); sends `referral_status_changed` to patient + referring doctor; (g) `PATCH /api/doctor/referrals/{referral_id}/complete` — 403 if caller is not `receiving_doctor_id`; sets status='Completed'; (h) `GET /api/patients/me/referrals` — paginated, patient's own referrals only; exposes: referral_id, referring_doctor_name, receiving_department_name, receiving_doctor_name (if set), urgency, status, created_at, receiving_doctor_note; NO `reason` field (OI-6 assumption); (i) `GET /api/admin/referrals` — paginated, filterable by status/department_id/date range; NO `reason` field (OI-6 assumption).
- Effort: L
- Dependencies: TASK-007
- Milestone/Group: C
- Definition of done: Doctor can create referral and receiving dept doctors receive `referral_received` notification; accept/decline work with correct 403/409 guards; declined referral has terminal 'Declined' status; `referral_status_changed` notifications sent to patient and referring doctor on accept/decline; patient sees their referrals without the clinical `reason` field; admin sees all referrals without `reason` field; urgency sort on received list works.
- Estimated completion: 2026-08-28

---

**TASK-022**
- Requirement: REQ-05 (Inter-Department Referral Management — frontend)
- Responsible: Chintu
- Title: REQ-05 Referrals frontend — doctor referrals page, patient referrals page, create modal
- Description: (a) `pages/doctor/DoctorReferralsPage.tsx` at `/doctor/referrals` — two tabs: "Received" (referrals for this doctor's department, Urgent badge pinned to top) and "Sent"; each referral card: patient info, referring/receiving doctor and dept, urgency badge (orange/amber for Urgent), status badge using existing `<StatusBadge>` component (add variants: Pending, Accepted, Declined, AppointmentBooked, Completed); "Accept" button (Received, Pending) → modal with optional acceptance note; "Decline" button (Received, Pending) → modal with required decline reason; "Mark Complete" button (Received, Accepted); empty state per tab; (b) Add "Create Referral" button to Doctor patient records page (the same page where TASK-020 adds Vitals) → modal: Receiving Department dropdown (loads all active departments), Receiving Doctor dropdown within selected dept (optional, loads on dept change), Clinical Reason required textarea, Urgency radio (Routine / Urgent); submit calls `POST /api/doctor/referrals`; success shows "Referral sent" toast and adds entry to Sent tab; (c) `pages/patient/PatientReferralsPage.tsx` at `/patient/referrals` — read-only list of patient's own referrals: department, doctor name (if assigned), urgency badge, status badge, timeline; empty state; (d) Patient sidebar: "Referrals" (`ArrowRightLeft` icon) → `/patient/referrals`; Doctor sidebar: "Referrals" (`ArrowRightLeft` icon) → `/doctor/referrals`; new routes in `App.tsx`.
- Effort: L
- Dependencies: TASK-021
- Milestone/Group: C
- Definition of done: Doctor can create a referral from the patient records page; receiving doctor sees it in Received tab with correct urgency ordering; accept/decline modals work and update status; patient sees their referrals read-only without clinical reason; sidebar items appear for doctor and patient; urgent referrals shown with amber badge and sorted first.
- Estimated completion: 2026-09-01

---

**TASK-023**
- Requirement: REQ-07 (Public Symptom / Condition Search — backend)
- Responsible: Chintu
- Title: REQ-07 Symptom Search backend — search endpoint and admin tag management endpoints
- Description: Implement the search and tag management backend: (a) SQLAlchemy model for `department_symptom_tags`; (b) `GET /api/public/search?q=` — public (no auth required); 400 if `len(q) < 2`; truncate `q` to 200 chars server-side; query departments via UNION SQL pattern (§4.2 endpoint 17): name match (rank 1), description match (rank 2), symptom tag match (rank 3); deduplicate departments across ranks; query doctors by specialty or bio match; return `{"departments": [...], "doctors": [...], "query": "...", "total": N}`; active departments only; active doctor accounts only; `match_type` field per result; (c) `GET /api/admin/departments/{department_id}/tags` — Admin only; (d) `POST /api/admin/departments/{department_id}/tags` — Admin only; 409 if tag_text already exists for this dept (case-insensitive check at app layer since SQLite has no native case-insensitive unique constraint); 400 if dept already has 50 tags; max 100 chars per tag; (e) `PUT /api/admin/departments/{department_id}/tags/{tag_id}` — 409 on case-insensitive conflict; (f) `DELETE /api/admin/departments/{department_id}/tags/{tag_id}` — 204.
- Effort: M
- Dependencies: TASK-003
- Milestone/Group: C
- Definition of done: Public search returns departments by name/description/tag and doctors by specialty/bio; case-insensitive LIKE matching works; deduplication within department results works; 50-tag limit enforced; case-insensitive duplicate tag detection enforced; search returns 400 for query < 2 chars; search returns empty results (not error) when no matches.
- Estimated completion: 2026-09-02

---

**TASK-024**
- Requirement: REQ-07 (Public Symptom / Condition Search — frontend)
- Responsible: Chintu
- Title: REQ-07 Symptom Search frontend — public search bar, /search page, admin tags management
- Description: (a) `pages/public/SearchPage.tsx` at `/search` — reads query from `?q=` URL param; fetches `GET /api/public/search?q=`; renders two sections: "Departments" (cards: icon, name, description snippet, "View Department" link) and "Doctors" (cards: photo, name, specialty, "View Profile" link); total count badge at top ("N results for 'query'"); no-results empty state with suggestion to browse departments or contact; loading skeleton cards; (b) Update public nav header (`PublicLayout.tsx` or the shared nav component): embed a compact search input with `Search` icon (placeholder: "Search symptoms, conditions, doctors..."); desktop: always visible; mobile (< 768px): `Search` icon button that expands a full-width input overlay on click; pressing Enter or clicking search icon navigates to `/search?q={query}`; do not navigate if query < 2 chars; (c) Admin symptom tags: update existing `/admin/departments` page to add a "Symptom Tags" button per department row (shows count badge of current tags); clicking expands an inline panel (not a new page): existing tags as removable chips (`X` per tag), type-ahead text input + "Add" button; 50-tag limit message when reached; (d) New public route `/search` under `PublicLayout` in `App.tsx`; new public nav item may need adjusting (search bar replaces a link slot — check that nav still fits on mobile).
- Effort: L
- Dependencies: TASK-023
- Milestone/Group: C
- Definition of done: Visitor can type in the nav search bar and land on `/search?q=...` with results; department results ordered by name > description > tag match; doctor results show profile photo and specialty; no results renders friendly empty state; admin can add/remove symptom tags for each department from the departments admin page; 50-tag limit prevents addition.
- Estimated completion: 2026-09-04

---

**TASK-025**
- Requirement: REQ-08 (Patient Medical Record Export — PDF backend)
- Responsible: Chintu (Sagar available for pairing on WeasyPrint template design)
- Title: REQ-08 PDF Export backend — WeasyPrint service, HTML template, streaming endpoint
- Description: (a) Verify `weasyprint>=60.0` is in `requirements.txt` (added in TASK-003); confirm WeasyPrint is importable in the FastAPI app; (b) `src/backend/app/services/pdf_export.py` — contains: `get_appointments_for_pdf(db, patient_id, start_date, end_date)` (fetches appointments with all associations: visit notes, prescriptions, lab results, vitals, intake forms, discharge summaries, sorted by `scheduled_at ASC`); `render_pdf_template(patient, appointments, date_range)` (builds an HTML string using Jinja2 or `string.Template`; CSS must be print-safe: white background, dark grey text, no `backdrop-filter`, no dark backgrounds); (c) HTML template structure per §3.8: cover page (hospital name, "Medical Record" subtitle, patient name/DOB/ID, export date, date range), diagonal watermark every page (low opacity, 45° rotation via `position: fixed` div; WeasyPrint honors fixed positioning), per-appointment sections (date, doctor name, department, visit notes, diagnosis, prescriptions table, lab results, vitals if recorded, intake form chief complaint if submitted, discharge summary if present), clean page breaks between appointments; (d) `GET /api/patients/me/export-pdf` — Patient only (AUTHZ-11: 403 for any other role); optional query params `start_date` and `end_date` (YYYY-MM-DD); 400 if date params invalid; calls `get_appointments_for_pdf()` then `render_pdf_template()` then `HTML(string=html_content).write_pdf()`; returns `StreamingResponse` with `Content-Type: application/pdf`, `Content-Disposition: attachment; filename="GVH_MedicalRecord_{patient_id}_{YYYYMMDD}.pdf"`.
- Effort: L
- Dependencies: TASK-003
- Milestone/Group: C
- Definition of done: Patient calling the endpoint receives a downloadable PDF with correct filename; PDF renders cover page, watermark on every page, and per-appointment sections with all associated data; date range filter limits which appointments appear; non-Patient roles get 403; invalid date params get 400; empty date range returns a PDF with "No visits for the selected period" message (not an error); WeasyPrint import does not break application startup.
- Estimated completion: 2026-09-08

---

**TASK-026**
- Requirement: REQ-08 (Patient Medical Record Export — frontend)
- Responsible: Chintu
- Title: REQ-08 PDF Export frontend — export button and date range modal in PatientRecordsPage
- Description: Update the existing `PatientRecordsPage` (at `/patient/records`): (a) Add an "Export PDF" secondary button with `Download` icon (Lucide) in the page header; (b) Clicking opens a small modal: optional start date and end date pickers; two actions: "Export All Records" (no date filter) or "Export Selected Range" (enabled only if both dates provided); (c) Clicking either action calls `GET /api/patients/me/export-pdf` (with or without date params); button shows spinner "Generating..."; browser handles the file download natively (the endpoint streams PDF bytes with a download Content-Disposition header — no intermediate page navigation needed); modal closes after download starts; (d) Error handling: toast "PDF generation failed. Please try again." on network error or non-200 response; add `exportPDF(startDate?, endDate?)` function to `src/frontend/src/api/patient.ts`.
- Effort: S
- Dependencies: TASK-025
- Milestone/Group: C
- Definition of done: "Export PDF" button visible on the patient records page; modal opens and allows optional date range selection; clicking "Export All Records" triggers browser download of a PDF; clicking "Export Selected Range" with dates triggers date-filtered PDF download; spinner shows during generation; error toast shows on failure.
- Estimated completion: 2026-09-09

---

**TASK-027**
- Requirement: REQ-12 (Corporate Health Check Packages — backend)
- Responsible: Chintu
- Title: REQ-12 Corporate Packages backend — public and admin endpoints
- Description: Implement the full corporate backend: (a) SQLAlchemy models for `corporate_packages` and `corporate_inquiries`; (b) `GET /api/public/corporate/packages` — public; active packages only, ordered by `tier_order ASC`; returns package fields excluding `is_active`; (c) `POST /api/public/corporate/inquiries` — public; validate required fields (company_name, contact_name, email); validate email format (422 on invalid); 400 if headcount < 1 when provided; insert inquiry with status='New'; returns `{"inquiry_id": N, "message": "Thank you! We'll be in touch shortly."}`; no notification per OI-17 assumption; (d) `GET /api/admin/corporate/packages` — Admin only; all packages including inactive; (e) `POST /api/admin/corporate/packages` — Admin only; (f) `PUT /api/admin/corporate/packages/{package_id}` — Admin only; (g) `DELETE /api/admin/corporate/packages/{package_id}` — Admin only; soft delete: sets `is_active=0`, returns `{"package_id": N, "is_active": false}`; (h) `GET /api/admin/corporate/inquiries` — Admin only; paginated, filterable by status; response includes `pipeline_total_cents = SUM(deal_value_cents) WHERE status='ClosedWon'`; (i) `GET /api/admin/corporate/inquiries/{inquiry_id}` — Admin only; (j) `PATCH /api/admin/corporate/inquiries/{inquiry_id}` — Admin only; updates status, notes, deal_value_cents; 400 if deal_value_cents < 0.
- Effort: M
- Dependencies: TASK-003
- Milestone/Group: C
- Definition of done: Public can fetch active packages (seed data from TASK-003 returns 2 packages); public can submit an inquiry and receive the thank-you message; admin can create/update/soft-delete packages; admin can view and update inquiry pipeline with correct pipeline_total_cents calculation; deactivated packages are excluded from the public endpoint.
- Estimated completion: 2026-09-10

---

**TASK-028**
- Requirement: REQ-12 (Corporate Health Check Packages — frontend)
- Responsible: Chintu
- Title: REQ-12 Corporate Packages frontend — public page, admin management, public nav
- Description: (a) `pages/public/CorporatePage.tsx` at `/corporate` — page hero "Corporate Health Solutions for Your Team"; fetches `GET /api/public/corporate/packages`; renders package cards (2–4 per row): tier badge, package name, description, included services bulleted list, price range display, "Get a Quote" CTA scrolling to inquiry form below; inquiry form: Company Name, Contact Person, Email (required), Phone (optional), Employee Headcount (number input), Preferred Package dropdown (populated from packages), Preferred Schedule text; "Submit Inquiry" button; on success: form replaced by "Thank you! We'll be in touch shortly." message (same UX pattern as the existing contact form); empty packages fallback: "We're preparing our corporate packages. Please contact us directly."; (b) `pages/admin/AdminCorporatePage.tsx` at `/admin/corporate` — two tabs: "Packages" (table with edit/deactivate actions; "New Package" button → form modal for all fields including `included_services_json` as a multi-line textarea for comma-separated services); "Inquiries" (pipeline table: status column color-coded, filter by status dropdown, pipeline value displayed at top; clicking a row expands detail: all fields, status dropdown, notes textarea, deal value input in dollars displayed as cents internally, "Save Changes"); (c) Public nav (`PublicLayout.tsx`): add "For Organizations" nav item linking to `/corporate` per OI-10 assumption; (d) Admin sidebar: add "Corporate" (`Building2` icon) → `/admin/corporate`; (e) New routes in `App.tsx`: `/corporate` under PublicLayout, `/admin/corporate` under Admin portal.
- Effort: L
- Dependencies: TASK-027
- Milestone/Group: C
- Definition of done: Visitor can navigate to `/corporate` via public nav, see package cards from the database, submit an inquiry, and see the success message; empty packages state renders fallback; admin can create a new package and see it appear on the public page; admin can manage the inquiry pipeline with status updates and deal value tracking; pipeline total shows correct ClosedWon sum; "For Organizations" appears in public nav on desktop and mobile.
- Estimated completion: 2026-09-14

---

### Group D — Depends on Group C (REQ-06 Analytics)

REQ-06 is placed last because the analytics dashboard is only meaningful once the underlying data tables it queries are fully implemented and correct: vitals data flows from REQ-04 (TASK-019), referral counts from REQ-05 (TASK-021), and accurate revenue 'collected' figures depend on `paid_at` being set correctly by TASK-006. Implementing analytics before those features are stable risks building charts against incomplete or wrongly-shaped data.

---

**TASK-029**
- Requirement: REQ-06 (Analytics Dashboard — backend)
- Responsible: Chintu
- Title: REQ-06 Analytics backend — four aggregate query endpoints with CSV export
- Description: Implement the analytics backend using raw SQL per §4.3.4 (no ORM query builder): (a) `GET /api/admin/analytics/appointments?start=&end=&format?=` — Admin only; runs the appointment volume SQL aggregate query from §4.3.4; returns items array with month, total, completed, cancelled, noshow, scheduled, noshow_rate; optional `?format=csv` returns CSV with matching header row; 400 if end < start; defaults: start = today − 365d, end = today if either missing; (b) `GET /api/admin/analytics/revenue?start=&end=&format?=` — Admin only; two-series query: invoiced (uses `invoices.created_at`) and collected (uses `invoices.paid_at` where non-null, per OI-7); CSV export; (c) `GET /api/admin/analytics/departments?start=&end=&format?=` — Admin only; appointment count per department sorted descending; CSV; (d) `GET /api/admin/analytics/patient-acquisition?start=&end=&format?=` — Admin only; new patients per month grouped by `users.created_at` for `role='Patient'`; CSV; CSV format for all: `Content-Type: text/csv`, `Content-Disposition: attachment; filename="gvh_analytics_{metric}_{start}_{end}.csv"`, header row matching JSON field names.
- Effort: L
- Dependencies: TASK-019 (vitals ensures patient data is complete), TASK-021 (referrals stable), TASK-006 (paid_at reliable)
- Milestone/Group: D
- Definition of done: All four endpoints return correct JSON shapes; noshow_rate is a percentage rounded to 2 decimal places; revenue endpoint correctly splits invoiced vs collected using paid_at (not created_at for collected); department rankings are sorted descending by count; patient acquisition groups by users.created_at month for Patient role only; CSV export produces downloadable file with correct filename and header; 400 returned when end < start; default date range applies when params absent.
- Estimated completion: 2026-09-16

---

**TASK-030**
- Requirement: REQ-06 (Analytics Dashboard — frontend)
- Responsible: Chintu
- Title: REQ-06 Analytics frontend — AdminAnalyticsPage with four Recharts chart sections and CSV export
- Description: (a) `pages/admin/AdminAnalyticsPage.tsx` at `/admin/analytics` — date range picker at top (start date + end date inputs); preset buttons below: "Last 7 days", "Last 30 days", "Last 3 months", "Last 12 months", "Year to date", "All time" per OI-14 assumption; changing range re-fetches all sections; (b) Four chart sections that load independently (parallel fetches, each has its own loading/error state): Appointment Volume (Recharts `BarChart`, grouped bars by status: Completed green, Cancelled amber, NoShow red, Scheduled blue), No-Show Rate (Recharts `LineChart`, single line as percentage per month), Revenue (Recharts `LineChart`, two series: Invoiced blue, Collected green), Department Rankings (Recharts `BarChart` horizontal, departments on Y-axis), Patient Acquisition (Recharts `AreaChart`, new patients per month); (c) Each section has an "Export CSV" button — calls the same endpoint with `?format=csv` and triggers browser download; "Downloading..." spinner on the button during export; (d) Loading state: grey animated skeleton rectangles in each chart area; empty range state: "No data for the selected period" inside each chart area; error state: `<PageError>` per section (one failing does not break others); (e) Admin sidebar: add "Analytics" (`BarChart2` icon) → `/admin/analytics`; new route in `App.tsx`.
- Effort: L
- Dependencies: TASK-029
- Milestone/Group: D
- Definition of done: Admin can navigate to `/admin/analytics`, select a date range or preset, and see all four chart sections populated from the API; each section loads independently and shows its own skeleton/error; all five preset buttons apply the correct date range; CSV export for each section triggers a browser download; sidebar item "Analytics" appears in admin portal.
- Estimated completion: 2026-09-18

---

## 3. Milestone Plan

All dates assume Chintu working 5 days/week, one task at a time. Date ranges below are estimated implementation completion dates. Sagar's Phase 7 code review and Gopal's Phase 8 QA happen **between groups** (not between every individual task) to reduce overhead — Sagar reviews the group's branch/PR, Gopal tests against the group's acceptance criteria, then the group is merged before the next group begins implementation. Total elapsed calendar time is therefore longer than pure implementation days.

### Milestone 0 — Pre-Implementation Housekeeping

| | Date |
|---|---|
| Start | 2026-07-20 |
| TASK-001 complete | 2026-07-20 |
| TASK-002 complete | 2026-07-20 |
| TASK-003 complete | 2026-07-21 |
| Milestone 0 complete | **2026-07-21** |

### Milestone 1 — Group A (Foundation)

Group A delivers the availability engine, the updated booking flow, and the full notifications infrastructure. Nothing else can begin until this milestone passes Sagar review and Gopal QA.

| | Date |
|---|---|
| Chintu starts Group A | 2026-07-22 |
| TASK-004 (Availability backend) | 2026-07-24 |
| TASK-005 (Appointment update) | 2026-07-27 |
| TASK-006 (paid_at invoice) | 2026-07-27 |
| TASK-007 (Notifications backend) | 2026-07-29 |
| TASK-008 (Doctor Availability UI) | 2026-07-31 |
| TASK-009 (Booking pages SlotPicker) | 2026-08-03 |
| TASK-010 (Notifications frontend) | 2026-08-05 |
| **Chintu implementation complete — Group A** | **2026-08-05** |
| Sagar Phase 7 review (target) | 2026-08-07 |
| Gopal Phase 8 QA (target) | 2026-08-12 |
| **Group A milestone complete / merge to main** | **2026-08-12** |

### Milestone 2 — Group B (Post-Foundation: Waitlist, Discharge, Surveys)

| | Date |
|---|---|
| Chintu starts Group B | 2026-08-06 (implementation; review/QA of Group A runs concurrently with Sagar/Gopal) |
| TASK-011 (Waitlist backend) | 2026-08-07 |
| TASK-012 (Waitlist frontend) | 2026-08-11 |
| TASK-013 (Discharge Summary backend) | 2026-08-13 |
| TASK-014 (Discharge Summary frontend) | 2026-08-14 |
| TASK-015 (Surveys backend) | 2026-08-17 |
| TASK-016 (Surveys frontend) | 2026-08-19 |
| **Chintu implementation complete — Group B** | **2026-08-19** |
| Sagar Phase 7 review (target) | 2026-08-21 |
| Gopal Phase 8 QA (target) | 2026-08-26 |
| **Group B milestone complete / merge to main** | **2026-08-26** |

Note on overlap: Chintu's Group B implementation work (TASK-011 onward) begins 2026-08-06, while Sagar's review of Group A runs from 2026-08-07. This is intentional — Chintu does not wait for Sagar's review to complete before starting Group B implementation. Sagar reviews Group A while Chintu works on Group B. The merge to main for Group A (2026-08-12) must precede the merge for Group B.

### Milestone 3 — Group C (Independent Features)

| | Date |
|---|---|
| Chintu starts Group C | 2026-08-20 |
| TASK-017 (Intake Form backend) | 2026-08-20 |
| TASK-018 (Intake Form frontend) | 2026-08-21 |
| TASK-019 (Vitals backend) | 2026-08-24 |
| TASK-020 (Vitals frontend) | 2026-08-26 |
| TASK-021 (Referrals backend) | 2026-08-28 |
| TASK-022 (Referrals frontend) | 2026-09-01 |
| TASK-023 (Symptom Search backend) | 2026-09-02 |
| TASK-024 (Symptom Search frontend) | 2026-09-04 |
| TASK-025 (PDF Export backend) | 2026-09-08 |
| TASK-026 (PDF Export frontend) | 2026-09-09 |
| TASK-027 (Corporate backend) | 2026-09-10 |
| TASK-028 (Corporate frontend) | 2026-09-14 |
| **Chintu implementation complete — Group C** | **2026-09-14** |
| Sagar Phase 7 review (target) | 2026-09-17 |
| Gopal Phase 8 QA (target) | 2026-09-24 |
| **Group C milestone complete / merge to main** | **2026-09-24** |

### Milestone 4 — Group D (Analytics)

| | Date |
|---|---|
| Chintu starts Group D | 2026-09-15 (implementation; Sagar/Gopal reviewing Group C concurrently) |
| TASK-029 (Analytics backend) | 2026-09-16 |
| TASK-030 (Analytics frontend) | 2026-09-18 |
| **Chintu implementation complete — Group D** | **2026-09-18** |
| Sagar Phase 7 review (target) | 2026-09-22 |
| Gopal Phase 8 QA (target) | 2026-09-29 |
| **Group D milestone complete / merge to main** | **2026-09-29** |

### Final Acceptance Milestone

| | Date |
|---|---|
| All groups merged to main | 2026-09-29 |
| Indra deployment / launch config review (if any) | 2026-09-30 to 2026-10-02 |
| Final end-to-end acceptance testing (cross-feature regression) | 2026-10-05 to 2026-10-10 |
| **Target final acceptance (Krishna sign-off)** | **2026-10-14** |
| Buffer for fixes found in acceptance | through 2026-10-17 |

---

## 4. Risks and Assumptions

### 4.1 Thirteen Documented Assumptions (Sagar §1.1) — Risk Register

Each assumption below was made by Sagar to unblock design. If Krishna overrides any assumption, the relevant backend endpoint(s) and/or frontend page(s) must be re-worked before that task's implementation begins. Krishna confirmation must happen before Chintu starts the affected task; Lavanya will flag to Akhil if a Krishna response is still pending when a task is about to start.

| # | OI | Assumption in Design | Affected Tasks | Risk if Overridden | Override Lead-Time Needed |
|---|---|---|---|---|---|
| 1 | OI-1 | Both Admin and Doctor can configure availability; Doctor manages own; Admin can override any | TASK-004, TASK-008 | Remove doctor write endpoints; add "request change" workflow. Medium rework | Before TASK-004 starts |
| 2 | OI-5 | Declined referral status is terminal ('Declined', not reset to 'Pending') | TASK-021, TASK-022 | Add a status-reset path from Declined → Pending with notification; minor backend change | Before TASK-021 |
| 3 | OI-6 | Admin does NOT see the clinical `reason` field on referrals | TASK-021 | Remove field exclusion from admin serializer; trivial change | Before TASK-021 |
| 4 | OI-7 | Revenue 'collected' series uses `invoices.paid_at`; Admin cannot approximate via `created_at WHERE status='Paid'` | TASK-006, TASK-029 | Drop `paid_at`; use `created_at WHERE status='Paid'` approximation. Minor schema change | Before TASK-006 |
| 5 | OI-9 | Doctor aggregate star rating is NOT publicly visible | TASK-015, public doctor profile | Add average_rating and total_reviews to public doctor endpoint; minor addition | Before TASK-015 |
| 6 | OI-10 | Corporate Packages appear as "For Organizations" top-level public nav item | TASK-028 | Move to About sub-page or footer only; minor frontend routing change | Before TASK-028 |
| 7 | OI-11 | `contact_form_received` notification fans out to all active Admin + Staff users | TASK-007 | Restrict to Admin role only; one-line query change in fan-out | Before TASK-007 |
| 8 | OI-12 | Waitlist is per-doctor-per-date; `preferred_date` is NOT NULL; uniqueness constraint on (patient_id, doctor_id, preferred_date) | TASK-011, TASK-012 | Per-doctor globally: make `preferred_date` nullable; change uniqueness constraint; update trigger logic. Moderate rework | Before TASK-011 |
| 9 | OI-14 | Analytics date preset labels: "Last 7 days", "Last 30 days", "Last 3 months", "Last 12 months", "Year to date", "All time" | TASK-030 | Frontend label change only; trivial | Before TASK-030 |
| 10 | OI-15 | Public search bar embedded in nav header (compact on desktop; icon-expands on mobile) | TASK-024 | Remove nav bar; add search section to homepage and link to /search only; moderate frontend change | Before TASK-024 |
| 11 | OI-16 | No cutoff time for intake form submission; editable until appointment is Completed | TASK-017, TASK-018 | Add cutoff check in PATCH endpoint; minor backend addition, no schema change | Before TASK-017 |
| 12 | OI-17 | Corporate inquiry submission does NOT create an in-app notification | TASK-027 | Add fan-out to all active Admin users in POST handler; minor backend addition | Before TASK-027 |
| 13 | OI-18 | Doctor ratings NOT added to public doctor profile (linked to OI-9) | TASK-015 | Same as OI-9 override; add aggregate fields to public doctor endpoint | Before TASK-015 |

### 4.2 Additional Delivery Risks

**R-1: WeasyPrint system dependency**
WeasyPrint requires system fonts and libpango/libcairo on the host machine. On Windows (the current dev environment per `docs/project-status.md`), these dependencies may require GTK+ runtime installation. If WeasyPrint fails to install or run in the current dev environment, Chintu must flag to Akhil immediately — this is a potential TASK-025 blocker. Mitigation: Chintu should attempt `pip install weasyprint` and a trivial `HTML(string="<p>test</p>").write_pdf()` call as the very first step of TASK-025 before writing any application code.

**R-2: Recharts accessibility validation**
The VITFR-5 requirement (accessible charts — not color-only distinction) requires explicit `strokeDasharray` patterns and ARIA labels on all Recharts instances. Gopal's QA for TASK-020 and TASK-030 must include a basic accessibility check (keyboard navigability, presence of ARIA labels, non-color legend symbols) — this is easy to miss without explicit test cases.

**R-3: Notification fan-out transaction scope**
TASK-007 requires all notification fan-outs to happen inside the same transaction as the triggering action. If any fan-out query (e.g., "all active Admin + Staff users") is slow or returns unexpectedly many results, it may cause perceptible latency on the triggering endpoint. Sagar flagged this in OI-11. Chintu must add a brief performance note in the PR if the contact-form fan-out targets more than 50 users in the test dataset.

**R-4: Sequential execution throughput**
The strictly sequential task execution model means Group C cannot start until Group B is fully implemented by Chintu. Group B contains two relatively independent feature areas (Waitlist and Discharge/Survey). If a Group B task is blocked (e.g., waitlist cascade logic requires a design fix), it delays the start of all Group C work. Mitigation: Sagar should be on standby for pairing on TASK-011 and TASK-013 specifically.

**R-5: `paid_at` data gap for historical invoices**
TASK-006 sets `paid_at` going forward on status transitions. Existing invoices in the database with `status='Paid'` will have `paid_at = NULL`. The analytics revenue 'collected' chart will show gaps for historical data. This is acceptable per OI-7 (accurate going forward), but Gopal's QA must not treat NULL `paid_at` on historical invoices as a bug — it is expected behavior. A seed-data note should clarify this for the QA dataset.

**R-6: Krishna assumption confirmations outstanding**
As of 2026-07-20, all 13 assumptions (OI-1, OI-5 through OI-18) are documented but not yet confirmed by Krishna. The plan above has flagged "before [TASK-XXX] starts" deadlines per assumption. If Krishna has not confirmed by those deadlines, Akhil must pause the affected task and escalate before Chintu begins implementation — building against an unconfirmed assumption that Krishna overrides costs more time than the pause.

---

## 5. Agent Responsibility Summary

| Agent | Role in This Plan |
|---|---|
| Chintu | Implements all 30 tasks sequentially on `feature/chintu-<slug>` branches |
| Sagar | Phase 7 code review per group (reviews PR diff against `docs/technical-design.md`, `db/schema.sql`, `docs/api-spec.md`); available for pairing on TASK-004, TASK-007, TASK-011, TASK-013, TASK-025 |
| Gopal | Phase 8 QA per group against acceptance criteria in `docs/requirements.md` §9 |
| Indra | Deployment/launch config review after all groups merge to `main` |
| Sunny | Tracks daily progress against the milestones in §3; runs standups; updates `docs/scrum-tracker.xlsx` |
| Lavanya | Sets milestones (this document); does not run standups (Sunny's ceremony) |
| Akhil | Orchestrates sequential task invocations; enforces phase gate; pauses and escalates blocked tasks |
| Krishna | Reviews and confirms the 13 outstanding assumptions (§4.1) before their respective task deadlines; final acceptance sign-off by 2026-10-14 |

---

## 6. Definition of Done — Batch Level

The entire 12-requirement batch is considered done when all of the following are true:

1. All 30 tasks (TASK-001 through TASK-030) have been implemented by Chintu, reviewed by Sagar (Phase 7), and tested by Gopal (Phase 8).
2. All four group branches have been merged to `main` by Sagar.
3. Indra has completed any deployment/launch config review.
4. `db/seed/seed.py` runs cleanly against the final schema with no errors.
5. The public site, all six role portals, and all new pages/routes are reachable without 404 or 500 errors in a clean local run.
6. No P0 or P1 bugs are open in Gopal's QA report.
7. All 13 outstanding Krishna-directed assumptions (§4.1) have been either confirmed or resolved via an updated design before their respective task implementations.
8. Krishna has provided final acceptance sign-off.
