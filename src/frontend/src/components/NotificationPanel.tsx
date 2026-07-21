/**
 * REQ-02 — Notification dropdown panel.
 *
 * Shown when the user clicks the NotificationBell. Displays up to 10
 * most recent notifications with read/unread distinction and a
 * "Mark all read" button. Includes a link to the full NotificationsPage.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bell, CheckCheck } from 'lucide-react';
import {
  listNotifications,
  markAllRead,
  markOneRead,
  type Notification,
} from '../api/notifications';
import { extractErrorMessage } from '../api/client';

interface Props {
  onClose: () => void;
  onMarkAllRead: () => void;
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function NotificationPanel({ onClose, onMarkAllRead }: Props) {
  const [items, setItems] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [markingAll, setMarkingAll] = useState(false);

  useEffect(() => {
    setLoading(true);
    listNotifications({ page: 1, page_size: 20 })
      .then((r) => {
        setItems(r.items);
        setLoading(false);
      })
      .catch((e) => {
        setError(extractErrorMessage(e));
        setLoading(false);
      });
  }, []);

  async function handleMarkOne(id: number) {
    await markOneRead(id);
    setItems((prev) =>
      prev.map((n) => (n.notification_id === id ? { ...n, is_read: true } : n)),
    );
  }

  async function handleMarkAll() {
    setMarkingAll(true);
    try {
      await markAllRead();
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
      onMarkAllRead();
    } finally {
      setMarkingAll(false);
    }
  }

  const hasUnread = items.some((n) => !n.is_read);

  return (
    <div
      className="notif-panel"
      role="dialog"
      aria-label="Notifications"
      aria-modal="true"
    >
      {/* Header */}
      <div className="notif-panel-header">
        <span className="notif-panel-title">Notifications</span>
        {hasUnread && (
          <button
            className="btn btn-ghost btn-sm notif-mark-all-btn"
            onClick={handleMarkAll}
            disabled={markingAll}
            aria-label="Mark all notifications as read"
          >
            <CheckCheck size={14} />
            {markingAll ? 'Marking…' : 'Mark all read'}
          </button>
        )}
      </div>

      {/* Body */}
      <div className="notif-panel-body">
        {loading ? (
          <div className="notif-panel-empty">Loading…</div>
        ) : error ? (
          <div className="notif-panel-empty notif-panel-error">{error}</div>
        ) : items.length === 0 ? (
          <div className="notif-panel-empty">
            <Bell size={32} aria-hidden="true" />
            <p>No notifications yet</p>
          </div>
        ) : (
          <ul className="notif-list" role="list">
            {items.map((n) => (
              <li
                key={n.notification_id}
                className={`notif-item${n.is_read ? '' : ' notif-item--unread'}`}
                onClick={() => {
                  if (!n.is_read) handleMarkOne(n.notification_id);
                }}
                role="listitem"
              >
                {!n.is_read && <span className="notif-unread-dot" aria-label="Unread" />}
                <div className="notif-content">
                  <p className="notif-title">{n.title}</p>
                  <p className="notif-body">{n.body}</p>
                  <span className="notif-time">{relativeTime(n.created_at)}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer */}
      <div className="notif-panel-footer">
        <Link
          to="/notifications"
          className="notif-see-all-link"
          onClick={onClose}
        >
          See all notifications
        </Link>
      </div>
    </div>
  );
}
