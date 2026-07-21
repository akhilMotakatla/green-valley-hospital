/**
 * REQ-02 — In-App Notification Center API calls.
 */
import { apiClient } from './client';
import type { Paginated } from '../types';

export interface Notification {
  notification_id: number;
  event_type: string;
  title: string;
  body: string;
  related_entity_type: string | null;
  related_entity_id: number | null;
  is_read: boolean;
  created_at: string;
}

export const getUnreadCount = () =>
  apiClient
    .get<{ unread_count: number }>('/notifications/unread-count')
    .then((r) => r.data.unread_count);

export const listNotifications = (params?: { page?: number; page_size?: number }) =>
  apiClient
    .get<Paginated<Notification>>('/notifications', { params })
    .then((r) => r.data);

export const markOneRead = (notificationId: number) =>
  apiClient
    .patch<{ notification_id: number; is_read: boolean }>(
      `/notifications/${notificationId}/read`,
    )
    .then((r) => r.data);

export const markAllRead = () =>
  apiClient
    .post<{ marked_read: number }>('/notifications/mark-all-read')
    .then((r) => r.data);
