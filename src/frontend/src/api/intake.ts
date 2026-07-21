import { apiClient } from './client';

export interface IntakeForm {
  submitted: boolean;
  intake_form_id?: number;
  appointment_id?: number;
  chief_complaint?: string | null;
  symptom_duration?: string | null;
  allergies?: string | null;
  current_medications?: string | null;
  pain_scale?: number | null;
  additional_notes?: string | null;
  submitted_at?: string | null;
  created_at?: string | null;
}

export interface IntakePatch {
  chief_complaint?: string;
  symptom_duration?: string;
  allergies?: string;
  current_medications?: string;
  pain_scale?: number;
  additional_notes?: string;
  submit?: boolean;
}

export const getIntakeForm = (appointmentId: number) =>
  apiClient.get<IntakeForm>(`/appointments/${appointmentId}/intake`).then((r) => r.data);

export const patchIntakeForm = (appointmentId: number, payload: IntakePatch) =>
  apiClient.patch<IntakeForm>(`/appointments/${appointmentId}/intake`, payload).then((r) => r.data);
