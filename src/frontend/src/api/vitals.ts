import { apiClient } from './client';
import type { Paginated } from '../types';

export interface VitalsRecord {
  vital_id: number;
  patient_id: number;
  appointment_id: number | null;
  recorded_by_user_id: number;
  systolic_bp: number | null;
  diastolic_bp: number | null;
  weight_kg: number | null;
  pulse_bpm: number | null;
  temperature_celsius: number | null;
  height_cm: number | null;
  recorded_at: string;
}

export interface VitalsPost {
  appointment_id?: number;
  systolic_bp?: number;
  diastolic_bp?: number;
  weight_kg?: number;
  pulse_bpm?: number;
  temperature_celsius?: number;
  height_cm?: number;
}

export const postVitals = (patientId: number, payload: VitalsPost) =>
  apiClient.post<VitalsRecord>(`/patients/${patientId}/vitals`, payload).then((r) => r.data);

export const getPatientVitals = (patientId: number, page = 1, pageSize = 100) =>
  apiClient
    .get<Paginated<VitalsRecord>>(`/patients/${patientId}/vitals`, {
      params: { page, page_size: pageSize },
    })
    .then((r) => r.data);

export const getAppointmentVitals = (appointmentId: number) =>
  apiClient
    .get<{ items: VitalsRecord[] }>(`/appointments/${appointmentId}/vitals`)
    .then((r) => r.data);
