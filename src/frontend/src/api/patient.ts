import { apiClient } from './client';
import type {
  Invoice,
  Paginated,
  PatientAppointment,
  PatientRecordsBundle,
} from '../types';

export interface PatientProfile {
  patient_id: number;
  full_name: string;
  email: string;
  phone: string | null;
  date_of_birth: string;
  gender: string | null;
  address: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
}

export const getMyPatientProfile = () =>
  apiClient.get<PatientProfile>('/patients/me').then((r) => r.data);

export const updateMyPatientProfile = (payload: {
  phone?: string;
  address?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  date_of_birth?: string;
}) => apiClient.patch<PatientProfile>('/patients/me', payload).then((r) => r.data);

export interface PatientVisibleDoctor {
  doctor_id: number;
  full_name: string;
  specialty: string;
  department_name: string;
  years_experience: number;
}

export const searchDoctors = (departmentId?: number) =>
  apiClient
    .get<{ items: PatientVisibleDoctor[] }>('/patients/doctors', {
      params: departmentId ? { department_id: departmentId } : {},
    })
    .then((r) => r.data.items);

export const getDoctorAvailability = (doctorId: number, date: string) =>
  apiClient
    .get<{ doctor_id: number; date: string; available_slots: string[] }>(
      `/patients/doctors/${doctorId}/availability`,
      { params: { date } },
    )
    .then((r) => r.data);

export const bookAppointment = (payload: {
  doctor_id: number;
  scheduled_at: string;
  reason?: string;
}) => apiClient.post('/patients/me/appointments', payload).then((r) => r.data);

export const listMyAppointments = (params: { status?: string; page?: number; page_size?: number }) =>
  apiClient
    .get<Paginated<PatientAppointment>>('/patients/me/appointments', { params })
    .then((r) => r.data);

export const cancelMyAppointment = (appointmentId: number) =>
  apiClient
    .delete<{ appointment_id: number; status: string }>(
      `/patients/me/appointments/${appointmentId}`,
    )
    .then((r) => r.data);

export const getMyRecords = () =>
  apiClient.get<PatientRecordsBundle>('/patients/me/records').then((r) => r.data);

export const getMyInvoices = (params: { status?: string; page?: number; page_size?: number }) =>
  apiClient.get<Paginated<Invoice>>('/patients/me/invoices', { params }).then((r) => r.data);

/**
 * REQ-08: Export patient medical records as PDF.
 * Returns a Blob with Content-Type application/pdf.
 */
export const exportPDF = (startDate?: string, endDate?: string) => {
  const params: Record<string, string> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  return apiClient
    .get('/patients/me/export-pdf', {
      params,
      responseType: 'blob',
    })
    .then((r) => r.data as Blob);
};
