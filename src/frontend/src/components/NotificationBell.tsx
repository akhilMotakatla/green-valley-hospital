/**
 * REQ-02 — Notification bell with unread count badge.
 *
 * Polls GET /notifications/unread-count on mount and every 60 seconds
 * (poll-on-login pattern — the endpoint also fires deferred notifications).
 * Click toggles the NotificationPanel dropdown.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { Bell } from 'lucide-react';
import { getUnreadCount } from '../api/notifications';
import { NotificationPanel } from './NotificationPanel';

const POLL_INTERVAL_MS = 60_000; // 60 seconds

export function NotificationBell() {
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const fetchCount = useCallback(async () => {
    try {
      const count = await getUnreadCount();
      setUnread(count);
    } catch {
      // silent — don't disrupt the UI for a count fetch failure
    }
  }, []);

  // Poll for unread count
  useEffect(() => {
    fetchCount();
    const id = setInterval(fetchCount, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [fetchCount]);

  // Close panel on outside click
  useEffect(() => {
    if (!open) return;
    function handleOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, [open]);

  // Close panel on Escape
  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open]);

  function handleMarkAllRead() {
    setUnread(0);
  }

  return (
    <div ref={wrapperRef} style={{ position: 'relative', display: 'inline-flex' }}>
      <button
        className="topbar-icon-btn notif-bell-btn"
        aria-label={
          unread > 0
            ? `Notifications — ${unread} unread`
            : 'Notifications — no unread'
        }
        aria-haspopup="dialog"
        aria-expanded={open}
        title="Notifications"
        onClick={() => {
          setOpen((v) => !v);
          // Refresh count when opening
          if (!open) fetchCount();
        }}
      >
        <Bell size={18} aria-hidden="true" />
        {unread > 0 && (
          <span className="notif-badge" aria-hidden="true">
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      {open && (
        <NotificationPanel
          onClose={() => setOpen(false)}
          onMarkAllRead={handleMarkAllRead}
        />
      )}
    </div>
  );
}
