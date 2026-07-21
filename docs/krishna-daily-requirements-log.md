# Krishna's Daily Requirements Log

Krishna reads this before proposing anything new — the point is to never raise a requirement that's a rerun of one already logged here, and to make sure a "new" requirement is a genuinely different, measurable improvement over anything similar already listed. Every "Krishna, start" cycle appends one dated entry in the format below. Ad-hoc requirements raised outside the daily cycle get logged too, marked "(ad hoc)".

Entries below predate Krishna's formal daily-cycle process — they're backfilled from direct user requests so Krishna starts with real history instead of a blank slate. They don't follow the full Requirement Title/Business Problem/etc. format since they weren't originally raised by Krishna, but the "don't repeat this" function is the same.

---

## 2026-07-20 (backfilled, ad hoc — user-directed, not from a "Krishna, start" cycle)

**Area: Visual design system overhaul.** Site moved from a light teal/gold "luxury" theme to a dark, cinematic, glassmorphism theme across the entire public site (full-screen sections, frosted-glass cards, deep charcoal/navy/brown palette, large editorial typography over imagery). Homepage hero rebuilt as a full-screen parallax hero. **Do not re-propose "modernize the visual design" or "add glassmorphism" — it's done.** A legitimate follow-up would be something specific and different, e.g. extending the same treatment to the authenticated portal dashboards (explicitly not yet done), or a specific section that still reads as weak.

## 2026-07-20 (backfilled, ad hoc)

**Area: Content depth / homepage density.** Departments expanded 4→10, doctors 4→10, blog articles 3→8. Root cause fixed: `GET /api/public/home` had a hardcoded `.limit(4)` capping featured departments regardless of how much seed data existed. **Do not re-propose "add more departments/doctors/content" as a generic ask** — if a specific new department or specialist is a genuine business need (e.g. a real market gap), that's a legitimate, different requirement; "the site feels sparse" in general is not, since that's already addressed.

## 2026-07-20 (backfilled, ad hoc)

**Area: Real photography.** Placeholder SVG files mislabeled `.jpg` (silently failed to render) replaced with real, visually-verified photos across hero/about/contact/departments/facility-gallery/blog/doctor sections. **Do not re-propose "add real images" — it's done**, though a specific still-weak image (subject mismatch, low quality) is a legitimate targeted fix, not a repeat.

## 2026-07-20 (backfilled, ad hoc)

**Area: Delivery infrastructure.** Standalone GitHub repo created, branch/PR/merge workflow established (Chintu + Sagar branches, Sagar sole merge gatekeeper), full agent team + five-phase-plus gate process defined (`docs/agent-collaboration-protocol.md`). Not a product requirement in the traditional sense — logged here for completeness so it doesn't get proposed again as "set up version control" or "define a dev process."

---

## Reference: what NOT to repeat, by category

- **UI/visual modernization** — done (dark cinematic + glassmorphism). Only propose visual changes that are specific to a section/page not yet covered, or a genuinely new interaction pattern, not a repeat of "make it look more premium."
- **Content volume** — done (10 departments, 10 doctors, 8 articles). Only propose specific new content tied to a real business reason (new specialty, new campaign), not "add more stuff."
- **Real imagery** — done. Only propose image work for a specific identified gap.
- **Process/infrastructure** — git workflow and agent team structure are set. Only propose changes here if there's a demonstrated process failure, not a preemptive tweak.

---

## 2026-07-20 — First formal "Krishna, start" batch (12 requirements)

**1. Doctor Availability & Slot Management**
Doctors can define their weekly availability (days, time blocks, slot duration). The appointment booking flow shows patients only genuinely open slots, not a free-text consultation_hours field. Conflict detection prevents double-booking. Doctors can block out time for leave or non-clinical work.

**2. In-App Notification Center**
A persistent notification bell/inbox for all authenticated roles. Patients receive: appointment confirmed/cancelled/reminder, lab result ready, new invoice. Doctors receive: new appointment booked for them, lab result ready for their patient. Staff receive: new contact form submission. Admin receives: account actions. In-app only — no real email/SMS (consistent with current out-of-scope). Notifications marked read/unread.

**3. Patient Pre-Visit Intake Form**
Before each scheduled appointment, the patient is prompted (in their portal) to complete a structured pre-visit questionnaire: chief complaint, symptom duration, known allergies, current medications, pain scale. The completed form is visible to the assigned doctor before the consultation starts. Doctor can see whether a form was submitted or skipped.

**4. Vitals Trend Visualization**
Staff records vitals per appointment (already specced in STF-4). This requirement adds a visual trend view — a time-series chart of a patient's blood pressure, weight, pulse, and temperature across all visits — accessible to the assigned doctor and to staff. Not just the most recent entry; historical trend plotted over visits/dates.

**5. Inter-Department Referral Management**
A doctor can create a formal referral from within a patient's record, naming the receiving department and (optionally) a specific doctor. The referral appears in the receiving doctor's portal as a pending referral with patient context (reason, referring doctor, notes). The receiving doctor can accept or decline. On acceptance, a suggested appointment is created or queued. Admin can see all referrals system-wide.

**6. Advanced Analytics & Reporting Dashboard (Admin)**
Beyond the current count metrics (ADM-8), a proper analytics dashboard with time-series charts: appointments per day/week/month, no-show rate over time, revenue collected vs. outstanding by month, top departments by patient volume, patient acquisition trend. Admin can select date ranges. Data exportable as CSV. This is a business intelligence tool, not a live operational screen.

**7. Public Symptom / Condition Search**
On the public site, visitors can search by symptom, condition, or keyword (e.g. "chest pain," "knee pain," "skin rash," "vision problems") and receive a list of relevant departments and doctors, ranked by relevance. This is distinct from browsing by department name. Helps patients who don't know which department they need land on the right specialist faster, reducing lost traffic and missed bookings.

**8. Patient Medical Record Export (PDF)**
A patient can request a complete downloadable PDF summary of their own medical history: visit notes, diagnoses, prescriptions, and lab results, organized by date. The PDF is generated on demand (within the portal), watermarked with the hospital name and patient ID, and is intended for sharing with another provider or insurer. No external email involved — download only.

**9. Appointment Waitlist System**
When a patient attempts to book a time slot that is already taken, they can join a waitlist for that doctor on that date. If the slot opens (via a cancellation), the next patient on the waitlist receives an in-app notification and has a defined time window (e.g. 2 hours) to confirm the slot before it passes to the next person on the list. If unconfirmed within the window, it cascades to the next waitlisted patient. Admin and Staff can view and manage waitlists.

**10. Discharge Summary & Follow-Up Scheduling**
When a doctor marks an appointment as Completed, they are prompted (not forced) to generate a discharge/visit summary for the patient: key findings, instructions, medications, and restrictions. The doctor can simultaneously schedule a follow-up appointment directly from this screen without requiring the patient to re-enter the booking flow. The patient sees the discharge summary in their portal under that appointment's record.

**11. Patient Satisfaction Survey & Doctor Ratings**
After an appointment is marked Completed and a cooling-off period has elapsed (24 hours), the patient receives an in-app prompt to rate their experience: 1–5 star rating for the doctor, 1–5 for overall hospital experience, and an optional free-text comment. A patient can only submit one survey per appointment. Admin sees aggregate ratings and all comments. Doctors see their own aggregate rating and anonymized comments. Individual comment text is never attributed to a specific patient in the doctor's view.

**12. Corporate Health Check Packages (B2B Revenue)**
A new section on the public site presenting bundled corporate health check packages (e.g. Basic, Comprehensive, Executive tiers), each listing included tests and screenings. Corporate clients (HR managers, procurement officers) fill out a B2B inquiry form (company name, contact, headcount, preferred package). Admin receives these inquiries in the portal and can mark them as Contacted, Proposal Sent, Closed Won, Closed Lost. This is a distinct revenue stream from individual patient care and broadens the hospital's market reach.
