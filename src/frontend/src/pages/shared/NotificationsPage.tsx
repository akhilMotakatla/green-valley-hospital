/**
 * REQ-02 — Full notification inbox page.
 * Route: /notifications (all authenticated roles)
 */
import { useCallback, useEffect, useState } from 'react';
import { Bell, CheckCheck } from 'lucide-react';
import {
  listNotifications,
  markAllRead,
  markOneRead,
  type Notification,
} from '../../api/notifications';
import { extractErrorMessage } from '../../api/client';
import { Pager } from '../../components/Pager';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

const PAGE_SIZE = 20;

export function NotificationsPage() {
  const [items, setItems] = useState<Notification[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [markingAll, setMarkingAll] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await listNotifications({ page, page_size: PAGE_SIZE });
      setItems(r.items);
      setTotal(r.total);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleMarkOne(id: number) {
    setBusyId(id);
    try {
      await markOneRead(id);
      setItems((prev) =>
        prev.map((n) => (n.notification_id === id ? { ...n, is_read: true } : n)),
      );
    } finally {
      setBusyId(null);
    }
  }

  async function handleMarkAll() {
    setMarkingAll(true);
    try {
      await markAllRead();
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } finally {
      setMarkingAll(false);
    }
  }

  const hasUnread = items.some((n) => !n.is_read);

  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem',
          marginBottom: '1.25rem',
        }}
      >
        <h1 style={{ margin: 0 }}>Notifications</h1>
        {hasUnread && (
          <button
            className="btn btn-outline btn-sm"
            onClick={handleMarkAll}
            disabled={markingAll}
          >
            <CheckCheck size={15} />
            {markingAll ? 'Marking…' : 'Mark all as read'}
          </button>
        )}
      </div>

      {error && <PageError message={error} onRetry={load} />}

      {loading ? (
        <SkeletonBlock lines={8} />
      ) : items.length === 0 && !error ? (
        <div className="empty-state">
          <Bell size={80} color="var(--color-text-light)" aria-hidden="true" />
          <h3>No notifications yet</h3>
          <p>
            Notifications about appointments, lab results, invoices, and more
            will appear here.
          </p>
        </div>
      ) : (
        <>
          <ul className="notif-page-list" role="list">
            {items.map((n) => (
              <li
                key={n.notification_id}
                className={`notif-page-item${n.is_read ? '' : ' notif-page-item--unread'}`}
                role="listitem"
              >
                {!n.is_read && (
                  <span className="notif-unread-dot" aria-label="Unread" />
                )}
                <div className="notif-page-content">
                  <div className="notif-page-row">
                    <p className="notif-title">{n.title}</p>
                    <span className="notif-time">{relativeTime(n.created_at)}</span>
                  </div>
                  <p className="notif-body">{n.body}</p>
                  {n.event_type && (
                    <span className="notif-type-badge">{n.event_type}</span>
                  )}
                </div>
                {!n.is_read && (
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => handleMarkOne(n.notification_id)}
                    disabled={busyId === n.notification_id}
                    aria-label="Mark as read"
                    style={{ flexShrink: 0 }}
                  >
                    Mark read
                  </button>
                )}
              </li>
            ))}
          </ul>
          <Pager page={page} pageSize={PAGE_SIZE} total={total} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
