/**
 * REQ-11 — Patient Satisfaction Survey & Doctor Ratings API calls.
 */
import { apiClient } from './client';

export interface PatientSurvey {
  survey_id: number;
  appointment_id: number;
  appointment_date: string | null;
  doctor_name: string | null;
  trigger_after: string;
  expires_at: string;
  submitted_at: string | null;
  status: 'pending' | 'submitted' | 'expired';
}

export interface SurveySubmitPayload {
  doctor_star_rating: number;
  overall_star_rating: number;
  comment?: string | null;
}

export interface DoctorRatings {
  average_doctor_rating: number | null;
  total_reviews: number;
  comments: { comment: string; submitted_at: string }[];
}

export interface AdminSurvey {
  survey_id: number;
  appointment_id: number;
  appointment_date: string | null;
  patient_id: number;
  patient_name: string | null;
  doctor_id: number;
  doctor_name: string | null;
  doctor_star_rating: number | null;
  overall_star_rating: number | null;
  comment: string | null;
  is_comment_removed: boolean;
  submitted_at: string | null;
  status: string;
}

// Patient
export const getMySurveys = () =>
  apiClient
    .get<{ items: PatientSurvey[] }>('/patients/me/surveys')
    .then((r) => r.data.items);

export const submitSurvey = (surveyId: number, payload: SurveySubmitPayload) =>
  apiClient
    .post<{ survey_id: number; submitted_at: string }>(
      `/patients/me/surveys/${surveyId}`,
      payload,
    )
    .then((r) => r.data);

// Doctor
export const getDoctorRatings = () =>
  apiClient.get<DoctorRatings>('/doctor/ratings').then((r) => r.data);

// Admin
export const adminGetSurveys = (params?: {
  doctor_id?: number;
  start_date?: string;
  end_date?: string;
  submitted_only?: boolean;
  page?: number;
  page_size?: number;
}) =>
  apiClient
    .get<{
      items: AdminSurvey[];
      total: number;
      page: number;
      page_size: number;
      total_pages: number;
    }>('/admin/surveys', { params })
    .then((r) => r.data);

export const adminRemoveSurveyComment = (surveyId: number) =>
  apiClient
    .patch<{ survey_id: number; is_comment_removed: boolean; comment: null }>(
      `/admin/surveys/${surveyId}/remove-comment`,
    )
    .then((r) => r.data);
