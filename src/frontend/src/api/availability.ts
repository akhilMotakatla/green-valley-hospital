/**
 * REQ-01 — Doctor Availability & Slot Management API calls.
 * Doctor-scoped: /doctor/availability/*
 * Admin-scoped:  /admin/doctors/{doctorId}/availability/*
 */
import { apiClient } from './client';

export interface AvailabilitySchedule {
  schedule_id: number;
  doctor_id: number;
  /** 0 = Monday … 6 = Sunday */
  day_of_week: number;
  start_time: string;  // HH:MM
  end_time: string;    // HH:MM
  is_active: boolean;
  created_at: string;
}

export interface SlotConfig {
  config_id: number | null;
  doctor_id: number;
  slot_duration_minutes: number;
  updated_at: string | null;
}

export interface AvailabilityBlock {
  block_id: number;
  doctor_id: number;
  block_date: string;        // YYYY-MM-DD
  start_time: string | null; // null = full-day block
  end_time: string | null;
  reason: string | null;
  created_at: string;
}

export interface AvailableSlots {
  doctor_id: number;
  date: string;
  slot_duration_minutes: number;
  slots: string[]; // HH:MM strings
}

// ---------------------------------------------------------------------------
// Doctor-scoped
// ---------------------------------------------------------------------------

export const getMySchedule = () =>
  apiClient
    .get<{ items: AvailabilitySchedule[] }>('/doctor/availability/schedule')
    .then((r) => r.data.items);

export const createScheduleWindow = (payload: {
  day_of_week: number;
  start_time: string;
  end_time: string;
}) =>
  apiClient
    .post<AvailabilitySchedule>('/doctor/availability/schedule', payload)
    .then((r) => r.data);

export const updateScheduleWindow = (
  scheduleId: number,
  payload: { start_time?: string; end_time?: string; is_active?: boolean },
) =>
  apiClient
    .put<AvailabilitySchedule>(`/doctor/availability/schedule/${scheduleId}`, payload)
    .then((r) => r.data);

export const deleteScheduleWindow = (scheduleId: number) =>
  apiClient.delete(`/doctor/availability/schedule/${scheduleId}`);

export const getMySlotConfig = () =>
  apiClient.get<SlotConfig>('/doctor/availability/config').then((r) => r.data);

export const updateMySlotConfig = (slotDurationMinutes: number) =>
  apiClient
    .put<SlotConfig>('/doctor/availability/config', {
      slot_duration_minutes: slotDurationMinutes,
    })
    .then((r) => r.data);

export const getMyBlocks = (fromDate?: string, toDate?: string) =>
  apiClient
    .get<{ items: AvailabilityBlock[] }>('/doctor/availability/blocks', {
      params: { from_date: fromDate, to_date: toDate },
    })
    .then((r) => r.data.items);

export const createBlock = (payload: {
  block_date: string;
  start_time?: string | null;
  end_time?: string | null;
  reason?: string | null;
}) =>
  apiClient.post<AvailabilityBlock>('/doctor/availability/blocks', payload).then((r) => r.data);

export const deleteBlock = (blockId: number) =>
  apiClient.delete(`/doctor/availability/blocks/${blockId}`);

// ---------------------------------------------------------------------------
// Shared: get available slots (Patient / Staff / Doctor / Admin)
// ---------------------------------------------------------------------------

export const getAvailableSlots = (doctorId: number, date: string) =>
  apiClient
    .get<AvailableSlots>(`/doctors/${doctorId}/available-slots`, { params: { date } })
    .then((r) => r.data);

// ---------------------------------------------------------------------------
// Admin-scoped
// ---------------------------------------------------------------------------

export const adminGetSchedule = (doctorId: number) =>
  apiClient
    .get<{ items: AvailabilitySchedule[] }>(
      `/admin/doctors/${doctorId}/availability/schedule`,
    )
    .then((r) => r.data.items);

export const adminCreateScheduleWindow = (
  doctorId: number,
  payload: { day_of_week: number; start_time: string; end_time: string },
) =>
  apiClient
    .post<AvailabilitySchedule>(
      `/admin/doctors/${doctorId}/availability/schedule`,
      payload,
    )
    .then((r) => r.data);

export const adminUpdateScheduleWindow = (
  doctorId: number,
  scheduleId: number,
  payload: { start_time?: string; end_time?: string; is_active?: boolean },
) =>
  apiClient
    .put<AvailabilitySchedule>(
      `/admin/doctors/${doctorId}/availability/schedule/${scheduleId}`,
      payload,
    )
    .then((r) => r.data);

export const adminDeleteScheduleWindow = (doctorId: number, scheduleId: number) =>
  apiClient.delete(
    `/admin/doctors/${doctorId}/availability/schedule/${scheduleId}`,
  );

export const adminGetSlotConfig = (doctorId: number) =>
  apiClient
    .get<SlotConfig>(`/admin/doctors/${doctorId}/availability/config`)
    .then((r) => r.data);

export const adminUpdateSlotConfig = (doctorId: number, slotDurationMinutes: number) =>
  apiClient
    .put<SlotConfig>(`/admin/doctors/${doctorId}/availability/config`, {
      slot_duration_minutes: slotDurationMinutes,
    })
    .then((r) => r.data);

export const adminGetBlocks = (doctorId: number, fromDate?: string, toDate?: string) =>
  apiClient
    .get<{ items: AvailabilityBlock[] }>(
      `/admin/doctors/${doctorId}/availability/blocks`,
      { params: { from_date: fromDate, to_date: toDate } },
    )
    .then((r) => r.data.items);

export const adminCreateBlock = (
  doctorId: number,
  payload: {
    block_date: string;
    start_time?: string | null;
    end_time?: string | null;
    reason?: string | null;
  },
) =>
  apiClient
    .post<AvailabilityBlock>(
      `/admin/doctors/${doctorId}/availability/blocks`,
      payload,
    )
    .then((r) => r.data);

export const adminDeleteBlock = (doctorId: number, blockId: number) =>
  apiClient.delete(`/admin/doctors/${doctorId}/availability/blocks/${blockId}`);
