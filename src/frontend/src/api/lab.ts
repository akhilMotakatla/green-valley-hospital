import { apiClient } from './client';
import type { LabOrder, Paginated } from '../types';

export const listLabOrders = (params: {
  test_type?: string;
  status?: string;
  page?: number;
  page_size?: number;
}) => apiClient.get<Paginated<LabOrder>>('/lab/orders', { params }).then((r) => r.data);

export const setLabOrderStatus = (orderId: number, status: 'InProgress' | 'Completed') =>
  apiClient.patch(`/lab/orders/${orderId}/status`, { status }).then((r) => r.data);

export const submitLabResult = (
  orderId: number,
  payload: { result_data: string; file?: File },
) => {
  const form = new FormData();
  form.append('result_data', payload.result_data);
  if (payload.file) form.append('file', payload.file);
  return apiClient
    .post(`/lab/orders/${orderId}/results`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data);
};

export const amendLabResult = (
  orderId: number,
  payload: { result_data: string; file?: File },
) => {
  const form = new FormData();
  form.append('result_data', payload.result_data);
  if (payload.file) form.append('file', payload.file);
  return apiClient
    .post(`/lab/orders/${orderId}/results/amend`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data);
};

export const getLabOrderResults = (orderId: number) =>
  apiClient
    .get<{ order_id: number; results: LabOrder[] }>(`/lab/orders/${orderId}/results`)
    .then((r) => r.data);
