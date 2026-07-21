import { apiClient } from './client';
import type { Paginated } from '../types';

export interface Referral {
  referral_id: number;
  referring_doctor_id: number;
  referring_doctor_name: string | null;
  receiving_department_id: number;
  receiving_department_name: string | null;
  receiving_doctor_id: number | null;
  receiving_doctor_name: string | null;
  patient_id: number;
  patient_name: string | null;
  urgency: 'Routine' | 'Urgent';
  status: string;
  reason?: string;
  receiving_doctor_note: string | null;
  referred_appointment_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface ReferralCreate {
  patient_id: number;
  to_department_id: number;
  to_doctor_id?: number;
  reason: string;
  urgency: 'Routine' | 'Urgent';
}

export const createReferral = (payload: ReferralCreate) =>
  apiClient.post<Referral>('/doctor/referrals', payload).then((r) => r.data);

export const getSentReferrals = (params?: { status?: string; page?: number; page_size?: number }) =>
  apiClient.get<Paginated<Referral>>('/doctor/referrals/sent', { params }).then((r) => r.data);

export const getReceivedReferrals = (params?: { page?: number; page_size?: number }) =>
  apiClient.get<Paginated<Referral>>('/doctor/referrals/received', { params }).then((r) => r.data);

export const acceptReferral = (referralId: number, note?: string) =>
  apiClient
    .patch<Referral>(`/doctor/referrals/${referralId}/accept`, { note })
    .then((r) => r.data);

export const declineReferral = (referralId: number, note: string) =>
  apiClient
    .patch<Referral>(`/doctor/referrals/${referralId}/decline`, { note })
    .then((r) => r.data);

export const completeReferral = (referralId: number) =>
  apiClient.patch<Referral>(`/doctor/referrals/${referralId}/complete`).then((r) => r.data);

export const getMyReferrals = (params?: { page?: number; page_size?: number }) =>
  apiClient.get<Paginated<Referral>>('/patients/me/referrals', { params }).then((r) => r.data);

export const adminListReferrals = (params?: { status?: string; department_id?: number; page?: number; page_size?: number }) =>
  apiClient.get<Paginated<Referral>>('/admin/referrals', { params }).then((r) => r.data);
