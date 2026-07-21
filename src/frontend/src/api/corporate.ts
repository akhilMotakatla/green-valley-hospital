import { apiClient } from './client';
import type { Paginated } from '../types';

export interface CorporatePackage {
  package_id: number;
  name: string;
  tier_order: number;
  description: string;
  included_services: string[];
  price_range_display: string;
  is_active?: boolean;
  created_at?: string;
}

export interface CorporateInquiry {
  inquiry_id: number;
  company_name: string;
  contact_name: string;
  email: string;
  phone: string | null;
  headcount: number | null;
  package_id: number | null;
  package_name: string | null;
  preferred_schedule: string | null;
  status: string;
  notes: string | null;
  deal_value_cents: number | null;
  created_at: string;
  updated_at: string;
}

export interface InquiryCreate {
  company_name: string;
  contact_name: string;
  email: string;
  phone?: string;
  estimated_headcount?: number;
  package_id?: number;
  preferred_schedule?: string;
}

export const getPublicPackages = () =>
  apiClient.get<{ items: CorporatePackage[] }>('/public/corporate/packages').then((r) => r.data.items);

export const submitInquiry = (payload: InquiryCreate) =>
  apiClient.post<{ inquiry_id: number; message: string }>('/public/corporate/inquiries', payload).then((r) => r.data);

// Admin endpoints
export const adminListPackages = () =>
  apiClient.get<{ items: CorporatePackage[] }>('/admin/corporate/packages').then((r) => r.data.items);

export const adminCreatePackage = (payload: Omit<CorporatePackage, 'package_id' | 'created_at'>) =>
  apiClient.post<CorporatePackage>('/admin/corporate/packages', {
    ...payload,
    included_services: payload.included_services,
  }).then((r) => r.data);

export const adminUpdatePackage = (packageId: number, payload: Partial<CorporatePackage>) =>
  apiClient.put<CorporatePackage>(`/admin/corporate/packages/${packageId}`, payload).then((r) => r.data);

export const adminDeactivatePackage = (packageId: number) =>
  apiClient.delete<{ package_id: number; is_active: boolean }>(`/admin/corporate/packages/${packageId}`).then((r) => r.data);

export const adminListInquiries = (params?: { status?: string; page?: number; page_size?: number }) =>
  apiClient
    .get<Paginated<CorporateInquiry> & { pipeline_total_cents: number }>('/admin/corporate/inquiries', { params })
    .then((r) => r.data);

export const adminGetInquiry = (inquiryId: number) =>
  apiClient.get<CorporateInquiry>(`/admin/corporate/inquiries/${inquiryId}`).then((r) => r.data);

export const adminPatchInquiry = (inquiryId: number, payload: { status?: string; notes?: string; deal_value_cents?: number }) =>
  apiClient.patch<CorporateInquiry>(`/admin/corporate/inquiries/${inquiryId}`, payload).then((r) => r.data);

export const adminPipelineSummary = () =>
  apiClient
    .get<{ total_closed_won_value: number; count_by_status: Record<string, number> }>('/admin/corporate/pipeline-summary')
    .then((r) => r.data);
