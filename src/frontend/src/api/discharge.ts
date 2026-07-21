/**
 * REQ-10 — Discharge Summary & Follow-Up Scheduling API calls.
 */
import { apiClient } from './client';

export interface DischargeSummary {
  summary_id: number;
  appointment_id: number;
  patient_id: number;
  doctor_id: number;
  key_findings: string;
  patient_instructions: string | null;
  activity_restrictions: string | null;
  medication_reminders: string | null;
  follow_up_appointment_id: number | null;
  created_at: string;
  // enriched fields from patient endpoints
  appointment_scheduled_at?: string | null;
  doctor_name?: string | null;
}

export interface CreateDischargeSummaryPayload {
  key_findings: string;
  patient_instructions?: string | null;
  activity_restrictions?: string | null;
  medication_reminders?: string | null;
  follow_up?: { scheduled_at: string } | null;
}

// Doctor
export const createDischargeSummary = (
  appointmentId: number,
  payload: CreateDischargeSummaryPayload,
) =>
  apiClient
    .post<DischargeSummary>(
      `/doctor/appointments/${appointmentId}/discharge-summary`,
      payload,
    )
    .then((r) => r.data);

export const getDischargeSummaryDoctor = (appointmentId: number) =>
  apiClient
    .get<DischargeSummary>(`/doctor/appointments/${appointmentId}/discharge-summary`)
    .then((r) => r.data);

// Patient
export const getMyDischargeSummaries = (params?: { page?: number; page_size?: number }) =>
  apiClient
    .get<{
      items: DischargeSummary[];
      total: number;
      page: number;
      page_size: number;
      total_pages: number;
    }>('/patients/me/discharge-summaries', { params })
    .then((r) => r.data);

export const getMyDischargeSummaryForAppointment = (appointmentId: number) =>
  apiClient
    .get<DischargeSummary>(
      `/patients/me/appointments/${appointmentId}/discharge-summary`,
    )
    .then((r) => r.data);
