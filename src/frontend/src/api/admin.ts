import { apiClient } from './client';
import type {
  AdminAppointment,
  AuditLogEntry,
  BlogListItem,
  ContactMessage,
  DashboardSummary,
  Department,
  Invoice,
  Paginated,
  Role,
  User,
} from '../types';

export const listUsers = (params: {
  role?: Role;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}) => apiClient.get<Paginated<User>>('/admin/users', { params }).then((r) => r.data);

export interface CreateUserPayload {
  email: string;
  password: string;
  role: 'Doctor' | 'Staff' | 'Lab' | 'Admin' | 'BillingSpecialist';
  full_name: string;
  phone: string;
  department_id?: number;
  specialty?: string;
  qualifications?: string;
  years_experience?: number;
  consultation_hours?: string;
  employee_id?: string;
}

export const createUser = (payload: CreateUserPayload) =>
  apiClient.post('/admin/users', payload).then((r) => r.data);

export const getUser = (userId: number) =>
  apiClient.get(`/admin/users/${userId}`).then((r) => r.data);

export const updateUser = (userId: number, payload: Record<string, unknown>) =>
  apiClient.patch(`/admin/users/${userId}`, payload).then((r) => r.data);

export const setUserStatus = (userId: number, isActive: boolean) =>
  apiClient
    .patch<{ id: number; is_active: boolean }>(`/admin/users/${userId}/status`, {
      is_active: isActive,
    })
    .then((r) => r.data);

export const setUserRole = (userId: number, role: Role, departmentId?: number) =>
  apiClient
    .patch(`/admin/users/${userId}/role`, { role, department_id: departmentId })
    .then((r) => r.data);

export const listDepartments = () =>
  apiClient.get<{ items: Department[] }>('/admin/departments').then((r) => r.data.items);

export const createDepartment = (name: string, description: string) =>
  apiClient.post<Department>('/admin/departments', { name, description }).then((r) => r.data);

export const updateDepartment = (id: number, payload: { name?: string; description?: string }) =>
  apiClient.patch<Department>(`/admin/departments/${id}`, payload).then((r) => r.data);

export const setDepartmentStatus = (id: number, isActive: boolean) =>
  apiClient
    .patch(`/admin/departments/${id}/status`, { is_active: isActive })
    .then((r) => r.data);

export const listAdminAppointments = (params: {
  department_id?: number;
  doctor_id?: number;
  date?: string;
  status?: string;
  page?: number;
  page_size?: number;
}) =>
  apiClient
    .get<Paginated<AdminAppointment>>('/admin/appointments', { params })
    .then((r) => r.data);

export const listAdminInvoices = (params: {
  patient_id?: number;
  status?: string;
  page?: number;
  page_size?: number;
}) => apiClient.get<Paginated<Invoice>>('/admin/invoices', { params }).then((r) => r.data);

export const listAdminBlog = (params: { status?: string; page?: number; page_size?: number }) =>
  apiClient.get<Paginated<BlogListItem>>('/admin/blog', { params }).then((r) => r.data);

export const createBlogArticle = (payload: {
  title: string;
  summary: string;
  body: string;
  cover_image?: File;
}) => {
  const form = new FormData();
  form.append('title', payload.title);
  form.append('summary', payload.summary);
  form.append('body', payload.body);
  if (payload.cover_image) form.append('cover_image', payload.cover_image);
  return apiClient
    .post('/admin/blog', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    .then((r) => r.data);
};

export const updateBlogArticle = (
  id: number,
  payload: { title?: string; summary?: string; body?: string },
) => apiClient.patch(`/admin/blog/${id}`, payload).then((r) => r.data);

export const publishBlogArticle = (id: number) =>
  apiClient.patch(`/admin/blog/${id}/publish`).then((r) => r.data);

export const unpublishBlogArticle = (id: number) =>
  apiClient.patch(`/admin/blog/${id}/unpublish`).then((r) => r.data);

export const deleteBlogArticle = (id: number) =>
  apiClient.delete(`/admin/blog/${id}`).then((r) => r.data);

export const listAdminContactMessages = (params: {
  status?: string;
  page?: number;
  page_size?: number;
}) =>
  apiClient
    .get<Paginated<ContactMessage>>('/admin/contact-messages', { params })
    .then((r) => r.data);

export const setContactMessageStatus = (id: number, status: 'Reviewed' | 'Resolved') =>
  apiClient.patch(`/admin/contact-messages/${id}/status`, { status }).then((r) => r.data);

export const getDashboardSummary = () =>
  apiClient.get<DashboardSummary>('/admin/dashboard/summary').then((r) => r.data);

export const getAuditLog = (params: {
  actor_user_id?: number;
  target_user_id?: number;
  page?: number;
  page_size?: number;
}) =>
  apiClient.get<Paginated<AuditLogEntry>>('/admin/audit-log', { params }).then((r) => r.data);

export const updateHomeContent = (payload: { tagline?: string; highlights?: string[] }) =>
  apiClient.patch('/admin/site-content/home', payload).then((r) => r.data);

export const updateAboutContent = (payload: {
  mission?: string;
  history?: string;
  facilities?: string;
  accreditations?: string;
}) => apiClient.patch('/admin/site-content/about', payload).then((r) => r.data);
