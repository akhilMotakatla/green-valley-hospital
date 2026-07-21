import { apiClient } from './client';
import type {
  BillingDashboard,
  BillingInvoice,
  BillingInvoiceListItem,
  BillingPatient,
  BillingAppointment,
  BillingNotification,
  LineItem,
  Paginated,
} from '../types';

export async function getBillingDashboard(): Promise<BillingDashboard> {
  const res = await apiClient.get<BillingDashboard>('/billing/dashboard');
  return res.data;
}

export interface InvoiceListParams {
  status?: 'Pending' | 'Paid' | 'Waived';
  has_insurance_claim?: 0 | 1;
  search?: string;
  page?: number;
  page_size?: number;
}

export async function getBillingInvoices(
  params: InvoiceListParams = {},
): Promise<Paginated<BillingInvoiceListItem>> {
  const res = await apiClient.get<Paginated<BillingInvoiceListItem>>('/billing/invoices', { params });
  return res.data;
}

export async function getBillingInvoice(invoice_id: number): Promise<BillingInvoice> {
  const res = await apiClient.get<BillingInvoice>(`/billing/invoices/${invoice_id}`);
  return res.data;
}

export interface CreateInvoiceBody {
  patient_id: number;
  appointment_id?: number | null;
  line_items: LineItem[];
  total_amount_cents: number;
  has_insurance_claim?: number;
}

export async function createInvoice(body: CreateInvoiceBody): Promise<BillingInvoice> {
  const res = await apiClient.post<BillingInvoice>('/billing/invoices', body);
  return res.data;
}

export interface UpdateInvoiceBody {
  status?: 'Pending' | 'Paid' | 'Waived';
  has_insurance_claim?: number;
  line_items?: LineItem[];
  total_amount_cents?: number;
}

export async function updateInvoice(
  invoice_id: number,
  body: UpdateInvoiceBody,
): Promise<BillingInvoice> {
  const res = await apiClient.patch<BillingInvoice>(`/billing/invoices/${invoice_id}`, body);
  return res.data;
}

export async function deleteInvoice(invoice_id: number): Promise<void> {
  await apiClient.delete(`/billing/invoices/${invoice_id}`);
}

export async function resendInvoiceNotification(
  invoice_id: number,
): Promise<{ notification_id: number; status: string; sent_at: string }> {
  const res = await apiClient.post(`/billing/invoices/${invoice_id}/resend-notification`);
  return res.data;
}

export interface PatientListParams {
  search?: string;
  page?: number;
  page_size?: number;
}

export async function getBillingPatients(
  params: PatientListParams = {},
): Promise<Paginated<BillingPatient>> {
  const res = await apiClient.get<Paginated<BillingPatient>>('/billing/patients', { params });
  return res.data;
}

export interface AppointmentListParams {
  patient_id?: number;
  status?: string;
  page?: number;
  page_size?: number;
}

export async function getBillingAppointments(
  params: AppointmentListParams = {},
): Promise<Paginated<BillingAppointment>> {
  const res = await apiClient.get<Paginated<BillingAppointment>>('/billing/appointments', { params });
  return res.data;
}

export async function getBillingNotifications(
  params: { page?: number; page_size?: number } = {},
): Promise<Paginated<BillingNotification>> {
  const res = await apiClient.get<Paginated<BillingNotification>>('/billing/notifications', { params });
  return res.data;
}

export async function getBillingNotification(notification_id: number): Promise<BillingNotification> {
  const res = await apiClient.get<BillingNotification>(`/billing/notifications/${notification_id}`);
  return res.data;
}
