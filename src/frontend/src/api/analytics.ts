/**
 * REQ-06 — Analytics API client functions.
 *
 * All endpoints are Admin-only (backend returns 403 for any other role).
 * The downloadAnalyticsCsv function fetches the CSV as a blob and triggers
 * a browser file download without navigating away from the page.
 */
import { apiClient } from './client';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type Granularity = 'day' | 'week' | 'month';

export type AnalyticsMetric =
  | 'appointments'
  | 'no_show_rate'
  | 'revenue'
  | 'department_volume'
  | 'patient_acquisition';

export interface AppointmentPeriod {
  period: string;
  count: number;
}

export interface AppointmentAnalytics {
  series: AppointmentPeriod[];
  total: number;
}

export interface NoShowPeriod {
  period: string;
  total: number;
  no_shows: number;
  rate: number; // 0.0–1.0 fraction; multiply by 100 for percent display
}

export interface NoShowAnalytics {
  series: NoShowPeriod[];
  overall_rate: number;
}

export interface RevenuePeriod {
  month: string;
  invoiced: number;   // dollars
  collected: number;  // dollars
  outstanding: number; // dollars
}

export interface RevenueAnalytics {
  series: RevenuePeriod[];
  total_invoiced: number;
  total_collected: number;
  total_outstanding: number;
}

export interface DepartmentVolumeItem {
  department_id: number;
  name: string;
  count: number;
}

export interface DepartmentVolumeAnalytics {
  departments: DepartmentVolumeItem[];
}

export interface PatientAcquisitionPeriod {
  month: string;
  new_patients: number;
}

export interface PatientAcquisitionAnalytics {
  series: PatientAcquisitionPeriod[];
  total_new: number;
}

// ---------------------------------------------------------------------------
// Date-range param helpers
// ---------------------------------------------------------------------------

interface DateRangeParams {
  from_date: string;
  to_date: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export const getAppointmentAnalytics = (
  params: DateRangeParams & { granularity?: Granularity },
) =>
  apiClient
    .get<AppointmentAnalytics>('/admin/analytics/appointments', { params })
    .then((r) => r.data);

export const getNoShowRate = (
  params: DateRangeParams & { granularity?: Granularity },
) =>
  apiClient
    .get<NoShowAnalytics>('/admin/analytics/no-show-rate', { params })
    .then((r) => r.data);

export const getRevenueAnalytics = (params: DateRangeParams) =>
  apiClient
    .get<RevenueAnalytics>('/admin/analytics/revenue', { params })
    .then((r) => r.data);

export const getDepartmentVolume = (params: DateRangeParams) =>
  apiClient
    .get<DepartmentVolumeAnalytics>('/admin/analytics/department-volume', { params })
    .then((r) => r.data);

export const getPatientAcquisition = (params: DateRangeParams) =>
  apiClient
    .get<PatientAcquisitionAnalytics>('/admin/analytics/patient-acquisition', { params })
    .then((r) => r.data);

/**
 * Request a CSV export and trigger a browser file download.
 * Uses responseType:'blob' so the binary content is never parsed as JSON.
 */
export const downloadAnalyticsCsv = async (
  metric: AnalyticsMetric,
  from_date: string,
  to_date: string,
  granularity?: Granularity,
): Promise<void> => {
  const params: Record<string, string> = { metric, from_date, to_date };
  if (granularity) params.granularity = granularity;

  const response = await apiClient.get('/admin/analytics/export-csv', {
    params,
    responseType: 'blob',
  });

  const url = window.URL.createObjectURL(new Blob([response.data as BlobPart]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `analytics_${metric}_${from_date}_${to_date}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
