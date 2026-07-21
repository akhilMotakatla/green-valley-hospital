// Shared types matching docs/api-spec.md wire format (snake_case, pass-through).

export type Role = 'Admin' | 'Doctor' | 'Patient' | 'Staff' | 'Lab' | 'BillingSpecialist';

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface User {
  id: number;
  email: string;
  role: Role;
  full_name: string;
  phone: string | null;
  is_active: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  role: Role;
  user_id: number;
}

export interface JwtClaims {
  sub: string | number;
  role: Role;
  email: string;
  full_name: string;
  iat: number;
  exp: number;
}

// ---------- Public ----------
export interface Department {
  department_id: number;
  name: string;
  description: string | null;
  is_active?: boolean;
}

export interface PublicDoctorListing {
  doctor_id: number;
  full_name: string;
  specialty: string;
  qualifications: string | null;
  years_experience: number;
  profile_photo_path: string | null;
}

export interface PublicDoctorProfile {
  doctor_id: number;
  full_name: string;
  specialty: string;
  department: { department_id: number; name: string };
  qualifications: string | null;
  bio: string | null;
  years_experience: number;
  consultation_hours: string | null;
  profile_photo_path: string | null;
}

export interface ContactInfo {
  address: string;
  general_phone: string;
  emergency_phone: string;
}

export interface BlogListItem {
  article_id: number;
  title: string;
  slug: string;
  summary: string;
  author_name: string;
  cover_image_path: string | null;
  published_at: string | null;
}

export interface BlogArticleDetail {
  article_id: number;
  title: string;
  slug: string;
  body: string;
  author_name: string;
  cover_image_path: string | null;
  published_at: string | null;
}

export interface HomeFeaturedDoctor {
  doctor_id: number;
  full_name: string;
  specialty: string;
  profile_photo_path: string | null;
}

export interface HomeFeaturedDepartment {
  department_id: number;
  name: string;
  description: string | null;
  first_doctor: HomeFeaturedDoctor | null;
}

export interface HomeRecentArticle {
  article_id: number;
  title: string;
  slug: string;
  summary: string;
  author_name: string;
  published_at: string | null;
  cover_image_path: string | null;
}

export interface HomeContent {
  tagline: string;
  highlights: string[];
  featured_departments: HomeFeaturedDepartment[];
  recent_articles: HomeRecentArticle[];
}

export interface AboutContent {
  mission: string;
  history: string;
  facilities: string;
  accreditations: string;
}

// ---------- Appointments / clinical ----------
export type AppointmentStatus = 'Scheduled' | 'Completed' | 'Cancelled' | 'NoShow';

export interface AppointmentBase {
  appointment_id: number;
  scheduled_at: string;
  status: AppointmentStatus;
  reason: string | null;
}

export interface PatientAppointment extends AppointmentBase {
  doctor_id: number;
  doctor_name: string;
}

export interface DoctorAppointment extends AppointmentBase {
  patient_id: number;
  patient_name: string;
}

export interface AdminAppointment extends AppointmentBase {
  patient_id: number;
  patient_name: string;
  doctor_id: number;
  doctor_name: string;
  department_name: string;
}

export interface VisitNote {
  record_id: number;
  appointment_id: number;
  patient_id: number;
  doctor_id: number;
  diagnosis: string | null;
  notes: string;
  created_at: string;
}

export interface Medicine {
  name: string;
  dosage: string;
  frequency: string;
  duration: string;
}

export interface Prescription {
  prescription_id: number;
  appointment_id: number;
  patient_id: number;
  doctor_id: number;
  medicines: Medicine[];
  instructions: string | null;
  created_at: string;
}

export interface LabResult {
  result_id: number;
  result_data: string;
  file_attachment_path: string | null;
  version: number;
  is_finalized: boolean;
  finalized_at: string | null;
}

export interface LabOrder {
  order_id: number;
  patient_id?: number;
  doctor_id?: number;
  patient_name?: string;
  patient_dob?: string;
  ordering_doctor_name?: string;
  test_type: 'Lab' | 'XRay' | 'Scan';
  test_subtype: string | null;
  status: 'Pending' | 'InProgress' | 'Completed';
  notes: string | null;
  created_at: string;
}

export interface PatientRecordsBundle {
  visit_notes: VisitNote[];
  prescriptions: Prescription[];
  lab_results: unknown[];
}

export interface Invoice {
  invoice_id: number;
  patient_id?: number;
  patient_name?: string;
  appointment_id: number | null;
  total_amount_cents: number;
  status: 'Pending' | 'Paid' | 'Waived';
  created_at: string;
}

export interface ContactMessage {
  message_id: number;
  name: string;
  email: string;
  phone: string | null;
  subject: string;
  message: string;
  status: 'New' | 'Reviewed' | 'Resolved';
  created_at: string;
}

export interface AuditLogEntry {
  log_id: number;
  actor_user_id: number;
  actor_name: string;
  action: string;
  target_user_id: number | null;
  target_name: string | null;
  details: string | null;
  created_at: string;
}

export interface DashboardSummary {
  patient_count: number;
  doctor_count: number;
  appointments_today: number;
  pending_lab_orders: number;
}

export interface StaffPatientListItem {
  patient_id: number;
  full_name: string;
  email: string;
  phone: string | null;
}

export interface StaffPatientDetail {
  patient_id: number;
  full_name: string;
  email: string;
  phone: string | null;
  date_of_birth: string;
  upcoming_appointments: AppointmentBase[];
}

export interface DirectoryDoctor {
  doctor_id: number;
  full_name: string;
  specialty: string;
  department_name: string;
  consultation_hours: string | null;
  profile_photo_path: string | null;
}

// ---------- Billing Specialist ----------

export interface BillingDashboard {
  outstanding_invoices: number;
  awaiting_claims: number;
  collected_this_month_cents: number;
  total_patients_billed: number;
}

export interface LineItem {
  description: string;
  amount_cents: number;
}

export interface BillingInvoice {
  invoice_id: number;
  patient_id: number;
  patient_name: string;
  appointment_id: number | null;
  appointment_date: string | null;
  doctor_name: string | null;
  department_name: string | null;
  line_items: LineItem[];
  total_amount_cents: number;
  status: 'Pending' | 'Paid' | 'Waived';
  has_insurance_claim: number;
  created_by_user_id?: number;
  created_at: string;
}

export interface BillingInvoiceListItem {
  invoice_id: number;
  patient_id: number;
  patient_name: string;
  appointment_id: number | null;
  appointment_date: string | null;
  total_amount_cents: number;
  status: 'Pending' | 'Paid' | 'Waived';
  has_insurance_claim: number;
  created_at: string;
}

export interface BillingPatient {
  patient_id: number;
  full_name: string;
  date_of_birth: string;
  phone: string | null;
  email: string;
}

export interface BillingAppointment {
  appointment_id: number;
  patient_id: number;
  patient_name: string;
  scheduled_at: string;
  status: 'Scheduled' | 'Completed' | 'Cancelled' | 'NoShow';
  doctor_name: string;
  department_name: string;
}

export interface BillingNotification {
  notification_id: number;
  recipient_user_id: number;
  recipient_name: string;
  subject: string;
  body_html?: string;
  sent_at: string;
  trigger_event: string;
  related_invoice_id: number | null;
  status: string;
}
