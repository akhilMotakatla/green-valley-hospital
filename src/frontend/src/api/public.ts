import { apiClient } from './client';
import type {
  AboutContent,
  BlogArticleDetail,
  BlogListItem,
  ContactInfo,
  Department,
  HomeContent,
  Paginated,
  PublicDoctorListing,
  PublicDoctorProfile,
} from '../types';

export interface DepartmentDoctorsResponse {
  department: { department_id: number; name: string; description: string | null };
  items: PublicDoctorListing[];
}

export const getHome = () => apiClient.get<HomeContent>('/public/home').then((r) => r.data);

export const getAbout = () => apiClient.get<AboutContent>('/public/about').then((r) => r.data);

export const getDepartments = () =>
  apiClient.get<{ items: Department[] }>('/public/departments').then((r) => r.data.items);

export const getDepartmentDoctors = (departmentId: number | string) =>
  apiClient
    .get<DepartmentDoctorsResponse>(`/public/departments/${departmentId}/doctors`)
    .then((r) => r.data);

export const getDoctorProfile = (doctorId: number | string) =>
  apiClient.get<PublicDoctorProfile>(`/public/doctors/${doctorId}`).then((r) => r.data);

export const getContactInfo = () =>
  apiClient.get<ContactInfo>('/public/contact-info').then((r) => r.data);

export interface ContactMessagePayload {
  name: string;
  email: string;
  phone?: string;
  subject: string;
  message: string;
}

export const submitContactMessage = (payload: ContactMessagePayload) =>
  apiClient
    .post<{ message_id: number; status: string; created_at: string }>(
      '/public/contact-messages',
      payload,
    )
    .then((r) => r.data);

export const getBlogList = (page = 1, pageSize = 20) =>
  apiClient
    .get<Paginated<BlogListItem>>('/public/blog', { params: { page, page_size: pageSize } })
    .then((r) => r.data);

export const getBlogArticle = (slug: string) =>
  apiClient.get<BlogArticleDetail>(`/public/blog/${slug}`).then((r) => r.data);
