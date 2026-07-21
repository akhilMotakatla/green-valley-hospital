import { apiClient } from './client';

export interface DepartmentResult {
  department_id: number;
  name: string;
  description: string | null;
  match_type: string;
  matched_tag?: string;
  rank: number;
}

export interface DoctorResult {
  doctor_id: number;
  full_name: string | null;
  specialty: string | null;
  bio: string | null;
  department_name: string | null;
  profile_photo_path: string | null;
  match_type: string;
}

export interface SearchResults {
  query: string;
  departments: DepartmentResult[];
  doctors: DoctorResult[];
  total: number;
}

export interface SymptomTag {
  tag_id: number;
  department_id: number;
  tag_text: string;
  created_at: string;
}

export const publicSearch = (q: string) =>
  apiClient.get<SearchResults>('/public/search', { params: { q } }).then((r) => r.data);

export const adminListTags = (departmentId: number) =>
  apiClient.get<SymptomTag[]>(`/admin/departments/${departmentId}/tags`).then((r) => r.data);

export const adminAddTag = (departmentId: number, tag_text: string) =>
  apiClient
    .post<SymptomTag>(`/admin/departments/${departmentId}/tags`, { tag_text })
    .then((r) => r.data);

export const adminDeleteTag = (departmentId: number, tagId: number) =>
  apiClient.delete(`/admin/departments/${departmentId}/tags/${tagId}`);

export const adminUpdateTag = (departmentId: number, tagId: number, tag_text: string) =>
  apiClient
    .put<SymptomTag>(`/admin/departments/${departmentId}/tags/${tagId}`, { tag_text })
    .then((r) => r.data);
