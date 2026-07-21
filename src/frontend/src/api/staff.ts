import { apiClient } from './client';
import type {
  ContactMessage,
  DirectoryDoctor,
  Paginated,
  StaffPatientDetail,
  StaffPatientListItem,
} from '../types';

export interface RegisterPatientPayload {
  full_name: string;
  email: string;
  phone: string;
  date_of_birth: string;
  gender?: string;
  address?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
}

export const registerPatient = (payload: RegisterPatientPayload) =>
  apiClient
    .post<{
      patient_id: number;
      user_id: number;
      full_name: string;
      email: string;
      temporary_password: string;
    }>('/staff/patients', payload)
    .then((r) => r.data);

export const getStaffPatient = (patientId: number) =>
  apiClient.get<StaffPatientDetail>(`/staff/patients/${patientId}`).then((r) => r.data);

export const listStaffPatients = (params: { search?: string; page?: number; page_size?: number }) =>
  apiClient
    .get<Paginated<StaffPatientListItem>>('/staff/patients', { params })
    .then((r) => r.data);

export const createStaffAppointment = (payload: {
  patient_id: number;
  doctor_id: number;
  scheduled_at: string;
  reason?: string;
}) => apiClient.post('/staff/appointments', payload).then((r) => r.data);

export const listStaffAppointments = (params: {
  patient_id?: number;
  doctor_id?: number;
  date?: string;
  status?: string;
  page?: number;
  page_size?: number;
}) => apiClient.get('/staff/appointments', { params }).then((r) => r.data);

export const updateStaffAppointment = (
  appointmentId: number,
  payload: { scheduled_at?: string; doctor_id?: number; status?: string; reason?: string },
) => apiClient.patch(`/staff/appointments/${appointmentId}`, payload).then((r) => r.data);

export const recordVitals = (
  patientId: number,
  payload: {
    height_cm?: number;
    weight_kg?: number;
    blood_pressure?: string;
    temperature_c?: number;
    pulse_bpm?: number;
    recorded_for_appointment_id?: number;
  },
) => apiClient.post(`/staff/patients/${patientId}/vitals`, payload).then((r) => r.data);

export const getPatientPrescriptions = (patientId: number) =>
  apiClient.get(`/staff/patients/${patientId}/prescriptions`).then((r) => r.data);

export const getPatientLabResults = (patientId: number) =>
  apiClient.get(`/staff/patients/${patientId}/lab-results`).then((r) => r.data);

export const listStaffContactMessages = (params: {
  status?: string;
  page?: number;
  page_size?: number;
}) =>
  apiClient
    .get<Paginated<ContactMessage>>('/staff/contact-messages', { params })
    .then((r) => r.data);

export const setStaffContactMessageStatus = (id: number, status: 'Reviewed' | 'Resolved') =>
  apiClient.patch(`/staff/contact-messages/${id}/status`, { status }).then((r) => r.data);

export const getStaffDirectory = (departmentId?: number) =>
  apiClient
    .get<{ items: DirectoryDoctor[] }>('/staff/directory', {
      params: departmentId ? { department_id: departmentId } : {},
    })
    .then((r) => r.data.items);
