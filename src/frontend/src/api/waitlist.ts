/**
 * REQ-09 — Appointment Waitlist API calls.
 */
import { apiClient } from './client';

export interface WaitlistEntry {
  entry_id: number;
  patient_id: number;
  doctor_id: number;
  doctor_name: string;
  department_name: string;
  preferred_date: string;
  status: 'Waiting' | 'Notified' | 'Confirmed' | 'Expired' | 'Removed';
  position: number | null;
  notified_at: string | null;
  confirmation_deadline: string | null;
  held_slot_time: string | null;
  created_at: string;
}

export interface StaffWaitlistEntry {
  entry_id: number;
  patient_id: number;
  patient_name: string;
  doctor_id: number;
  preferred_date: string;
  status: string;
  position: number | null;
  notified_at: string | null;
  confirmation_deadline: string | null;
  created_at: string;
}

export interface WaitlistConfig {
  confirmation_hours: number;
}

// Patient
export const joinWaitlist = (payload: { doctor_id: number; preferred_date: string }) =>
  apiClient.post<WaitlistEntry>('/waitlist', payload).then((r) => r.data);

export const getMyWaitlist = () =>
  apiClient.get<{ items: WaitlistEntry[] }>('/patients/me/waitlist').then((r) => r.data.items);

export const leaveWaitlist = (entryId: number) =>
  apiClient.delete(`/patients/me/waitlist/${entryId}`);

export const confirmWaitlistSlot = (entryId: number) =>
  apiClient
    .post<{ appointment_id: number }>(`/waitlist/${entryId}/confirm`)
    .then((r) => r.data);

// Staff
export const staffGetWaitlist = (
  doctorId: number,
  params?: { date?: string; page?: number; page_size?: number },
) =>
  apiClient
    .get<{ items: StaffWaitlistEntry[]; total: number; page: number; page_size: number; total_pages: number }>(
      `/staff/waitlist/${doctorId}`,
      { params },
    )
    .then((r) => r.data);

export const staffRemoveWaitlistEntry = (entryId: number, reason?: string) =>
  apiClient.delete(`/staff/waitlist/${entryId}`, { data: { reason } });

// Admin
export const getWaitlistConfig = () =>
  apiClient.get<WaitlistConfig>('/admin/config/waitlist').then((r) => r.data);

export const updateWaitlistConfig = (confirmationHours: number) =>
  apiClient
    .put<WaitlistConfig>('/admin/config/waitlist', { confirmation_hours: confirmationHours })
    .then((r) => r.data);
