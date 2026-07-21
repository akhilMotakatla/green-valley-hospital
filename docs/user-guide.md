# Green Valley Hospital — User Guide

This guide covers every role in the system and what each user can do. All features are accessed through the web app at `http://localhost:5173` (development) unless otherwise noted.

---

## Public Site (No Login Required)

Any visitor can access the public site without an account.

### Home Page
- View hospital highlights, featured departments, specialist doctors, and patient testimonials.
- Use the **Book Appointment** button (top-right) to go to patient registration.
- Use **Explore Departments** to browse all specialties.

### Departments
- Browse all active departments with descriptions and icons.
- Use the **search bar** to filter departments by name or description (client-side, instant).
- Click a department card to see the list of doctors in that specialty.

### Doctor Profile
- Each doctor card links to a full profile: photo, bio, qualifications, specialty, and consultation hours.
- A **Book Appointment** CTA at the bottom of the profile links to signup/login.

### About
- Static hospital background: mission, vision, values, history timeline, facility gallery, and accreditations.

### Blog
- Browse published health articles. Draft articles are never visible on the public site.
- Click an article to read the full content with estimated read time.

### Contact
- View hospital address, phone, emergency number (+1 555 000-9999), and email.
- Submit a contact form (name, email, subject, message). Required fields are validated client-side and server-side. A success confirmation is shown in-app; no email is sent.

### Login / Sign Up
- **Sign up** creates a **Patient** account only. Enter name, email, password, phone, and date of birth.
- **Login** with email and password. Incorrect credentials return a generic error (email existence is not revealed). Deactivated accounts receive a specific inactive message.

---

## Patient Portal

After logging in as a Patient, the sidebar shows: Appointments, Medical Records, Invoices, Profile.

### Appointments
- **Book an appointment**: browse doctors by department, select a doctor, pick a date and available time slot, enter a reason. Double-booked slots are rejected (409 Conflict).
- **View your appointments**: see all upcoming and past appointments with status (Scheduled / Completed / Cancelled / NoShow).
- **Cancel an appointment**: available only if the appointment is more than 1 hour away. Within 1 hour, cancellation is blocked.

### Medical Records
- View visit notes and diagnoses written by doctors after completed appointments.
- View prescriptions (medicines, dosage, instructions, duration) issued to you.
- View lab / X-ray / scan results once the Lab role has uploaded them.
- All records are read-only to patients.

### Invoices
- View billing records for your appointments (line items, total, payment status: Pending / Paid / Waived).
- Invoices are read-only; payment is handled offline.

### Profile
- Edit your contact info, emergency contact name/phone, and date of birth.
- You cannot change your own role or account activation status.

---

## Doctor Portal

After logging in as a Doctor, the sidebar shows: Appointments, Patient Records, Profile.

### Appointments
- View all appointments assigned to you (upcoming and past).
- Update appointment status: **Scheduled → Completed / No-show / Cancelled**.
- Add visit notes and a diagnosis when marking an appointment Completed.
- Create a **prescription** tied to the appointment (medicine name, dosage, frequency, duration, instructions).
- Create a **lab / X-ray / scan order** for the patient, specifying test type and notes.

### Patient Records
- Access medical records only for patients who have (or have had) an appointment with you.
- View visit notes, prescriptions, and lab results for those patients.
- View lab results once the Lab role has uploaded them.

### Profile
- Edit your public-facing bio, qualifications, and consultation hours.
- Update your profile photo path (place the image file in `public/images/doctors/` and enter the relative path).

---

## Staff Portal

After logging in as a Staff member (Nurse / Receptionist), the sidebar shows: Appointments, Patients, Contact Messages, Staff Directory.

### Appointments
- Book, view, and edit appointments for **any patient** (front-desk and phone bookings).
- Walk-in bookings: register a new patient account on behalf of the patient using the **Register Patient** flow.

### Patients
- Search and view patient demographic information (name, DOB, contact details, emergency contact).
- Record patient vitals before a doctor consultation: height, weight, blood pressure, temperature, pulse.
- View (but not edit) prescriptions and lab results to assist with coordination.

### Contact Messages
- View all submitted contact form messages.
- Mark messages as Reviewed or Resolved.

### Staff Directory
- View the full list of active doctors with department, specialty, and consultation hours — to assist with booking queries.

---

## Admin Portal

After logging in as Admin, the sidebar shows: Dashboard, Appointments, Users, Departments, Invoices, Blog, Contact Messages, Audit Log.

### Dashboard
- Summary metrics: total patients, doctors, appointments today, pending lab orders.
- Quick-action buttons: Add User, New Department, View Appointments, View Messages.

### Users
- Create new accounts for any role (Doctor, Staff, Lab, Admin). Patients self-register.
- Edit user details and assign/change departments.
- Deactivate accounts (deactivated users cannot log in). Reactivate as needed.

### Departments
- Create, edit, and deactivate department / specialty records.
- Deactivating a department does not delete it — existing doctor assignments are preserved.

### Appointments
- View all appointments across the hospital.
- Filter by department, doctor, date, and status.

### Invoices
- View all billing records across all patients.
- Create and edit invoices (line items, total amount, payment status).

### Blog
- Create, edit, publish, unpublish, and delete health articles.
- Draft articles are invisible to the public; Published articles appear immediately.
- Set a cover image path and article slug.

### Contact Messages
- View all contact form submissions.
- Mark messages as Reviewed or Resolved.

### Audit Log
- View a chronological record of account creation/deactivation and role-change events.
- Each entry shows: who performed the action, what action, which target user, and when.

---

## Lab Portal

After logging in as a Lab user, the sidebar shows: Lab Orders.

### Lab Orders
- View the queue of all pending lab / X-ray / scan orders.
- Filter by test type (Lab / X-ray / Scan) and status (Pending / InProgress / Completed).
- Update order status: **Pending → In Progress → Completed**.
- Enter result data (text/values) and optionally attach a file (stored in `uploads/`).
- Once an order is marked Completed, editing it creates a new **versioned result entry** — the original is preserved. Both versions remain retrievable.

---

## Access Control Summary

| Feature | Admin | Doctor | Patient | Staff | Lab |
|---|:---:|:---:|:---:|:---:|:---:|
| Manage user accounts | ✅ | ❌ | Self only | Create Patient | ❌ |
| Manage departments | ✅ | Read | Read | Read | Read |
| View all appointments | ✅ | Own only | Own only | ✅ (create/edit) | ❌ |
| Write visit notes / diagnoses | ❌ | Own patients | ❌ | ❌ | ❌ |
| Write prescriptions | ❌ | Own patients | ❌ | ❌ | ❌ |
| Create lab orders | ❌ | Own patients | ❌ | ❌ | ❌ |
| Upload lab results | ❌ | ❌ | ❌ | ❌ | ✅ |
| View lab results | Read (all) | Own patients | Own only | Read | Create/edit |
| Manage invoices | ✅ | ❌ | Read own | Create/edit | ❌ |
| Manage blog | ✅ | ❌ | Read published | ❌ | ❌ |
| View contact messages | ✅ | ❌ | Submit only | Read/resolve | ❌ |
| Record patient vitals | ❌ | ❌ | ❌ | ✅ | ❌ |
| View audit log | ✅ | ❌ | ❌ | ❌ | ❌ |
