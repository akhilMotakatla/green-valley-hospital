import { apiClient } from './client';
import type {
  DoctorAppointment,
  LabOrder,
  Medicine,
  Paginated,
  PatientRecordsBundle,
  Prescription,
  VisitNote,
} from '../types';

export interface DoctorProfile {
  doctor_id: number;
  full_name: string;
  department: { department_id: number; name: string } | string;
  specialty: string;
  qualifications: string | null;
  bio: string | null;
  years_experience: number;
  consultation_hours: string | null;
}

export const getMyDoctorProfile = () =>
  apiClient.get<DoctorProfile>('/doctor/me').then((r) => r.data);

export const updateMyDoctorProfile = (payload: {
  bio?: string;
  qualifications?: string;
  consultation_hours?: string;
}) => apiClient.patch<DoctorProfile>('/doctor/me', payload).then((r) => r.data);

export const listMyAppointments = (params: {
  status?: string;
  from?: string;
  to?: string;
  page?: number;
  page_size?: number;
}) =>
  apiClient
    .get<Paginated<DoctorAppointment>>('/doctor/me/appointments', { params })
    .then((r) => r.data);

export const updateAppointmentStatus = (
  appointmentId: number,
  status: 'Completed' | 'NoShow' | 'Cancelled',
) =>
  apiClient
    .patch(`/doctor/appointments/${appointmentId}/status`, { status })
    .then((r) => r.data);

export const getPatientRecords = (patientId: number) =>
  apiClient
    .get<PatientRecordsBundle>(`/doctor/patients/${patientId}/records`)
    .then((r) => r.data);

export const createVisitNote = (
  appointmentId: number,
  payload: { diagnosis?: string; notes: string },
) =>
  apiClient
    .post<VisitNote>(`/doctor/appointments/${appointmentId}/visit-notes`, payload)
    .then((r) => r.data);

export const createPrescription = (
  appointmentId: number,
  payload: { medicines: Medicine[]; instructions?: string },
) =>
  apiClient
    .post<Prescription>(`/doctor/appointments/${appointmentId}/prescriptions`, payload)
    .then((r) => r.data);

export const createLabOrder = (
  patientId: number,
  payload: {
    test_type: 'Lab' | 'XRay' | 'Scan';
    test_subtype?: string;
    notes?: string;
    appointment_id?: number;
  },
) =>
  apiClient
    .post<LabOrder>(`/doctor/patients/${patientId}/lab-orders`, payload)
    .then((r) => r.data);

export const getLabOrderResults = (orderId: number) =>
  apiClient
    .get<{ order_id: number; status: string; results: LabOrder[] }>(
      `/doctor/lab-orders/${orderId}/results`,
    )
    .then((r) => r.data);
