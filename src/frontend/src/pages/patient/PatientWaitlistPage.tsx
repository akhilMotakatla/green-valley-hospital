/**
 * REQ-09 — Patient Waitlist Page.
 * Lists active waitlist entries (Waiting or Notified).
 * Notified entries show a countdown and "Confirm Appointment" button.
 */
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, CheckCircle } from 'lucide-react';
import {
  getMyWaitlist,
  leaveWaitlist,
  confirmWaitlistSlot,
  type WaitlistEntry,
} from '../../api/waitlist';
import { extractErrorMessage } from '../../api/client';
import { WaitlistCountdown } from '../../components/WaitlistCountdown';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

export function PatientWaitlistPage() {
  const [entries, setEntries] = useState<WaitlistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const navigate = useNavigate();

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getMyWaitlist()
      .then((items) => {
        setEntries(items);
        setLoading(false);
      })
      .catch((e) => {
        setError(extractErrorMessage(e));
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleLeave(entryId: number) {
    if (!confirm('Remove yourself from this waitlist?')) return;
    setBusyId(entryId);
    try {
      await leaveWaitlist(entryId);
      setToast('Removed from waitlist.');
      load();
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setBusyId(null);
    }
  }

  async function handleConfirm(entryId: number) {
    setBusyId(entryId);
    setError(null);
    try {
      await confirmWaitlistSlot(entryId);
      setToast('Appointment booked! Redirecting to your appointments…');
      setTimeout(() => navigate('/patient'), 1500);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <h1>My Waitlist</h1>

      {toast && (
        <div className="success-text" style={{ marginBottom: '1rem' }}>
          {toast}
        </div>
      )}
      {error && <PageError message={error} onRetry={load} />}

      {loading ? (
        <SkeletonBlock lines={4} />
      ) : entries.length === 0 ? (
        <div className="empty-state">
          <Clock size={64} color="var(--color-text-light)" />
          <h3>You're not on any waitlist</h3>
          <p>When you join a waitlist from the booking page, your entries appear here.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {entries.map((entry) => {
            const isNotified = entry.status === 'Notified';
            return (
              <div
                key={entry.entry_id}
                style={{
                  border: `2px solid ${isNotified ? 'var(--color-primary, #0d6efd)' : 'var(--color-border, #dee2e6)'}`,
                  borderRadius: 8,
                  padding: '1.25rem',
                  background: isNotified ? 'rgba(13,110,253,0.05)' : undefined,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                  }}
                >
                  <div>
                    <strong>{entry.doctor_name}</strong>
                    <span
                      style={{
                        marginLeft: '0.5rem',
                        color: 'var(--color-text-light)',
                        fontSize: '0.9rem',
                      }}
                    >
                      {entry.department_name}
                    </span>
                  </div>
                  <span
                    className={`badge ${isNotified ? 'badge-primary' : 'badge-secondary'}`}
                    style={{
                      padding: '0.2rem 0.6rem',
                      borderRadius: 99,
                      fontSize: '0.8rem',
                      background: isNotified ? 'var(--color-primary, #0d6efd)' : '#6c757d',
                      color: '#fff',
                    }}
                  >
                    {isNotified ? 'Slot Available!' : `Waiting — Position ${entry.position ?? '—'}`}
                  </span>
                </div>

                <div
                  style={{
                    marginTop: '0.5rem',
                    color: 'var(--color-text-light)',
                    fontSize: '0.9rem',
                  }}
                >
                  Preferred date: <strong>{entry.preferred_date}</strong>
                  {entry.held_slot_time && (
                    <> &mdash; slot time: <strong>{entry.held_slot_time}</strong></>
                  )}
                </div>

                {isNotified && entry.confirmation_deadline && (
                  <div style={{ marginTop: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.9rem' }}>
                      Confirm within:{' '}
                      <WaitlistCountdown deadline={entry.confirmation_deadline} />
                    </span>
                    <button
                      className="btn btn-primary btn-sm"
                      disabled={busyId === entry.entry_id}
                      onClick={() => handleConfirm(entry.entry_id)}
                      style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                    >
                      <CheckCircle size={15} />
                      {busyId === entry.entry_id ? 'Booking…' : 'Confirm Appointment'}
                    </button>
                  </div>
                )}

                <div style={{ marginTop: '0.75rem' }}>
                  <button
                    className="btn btn-outline btn-sm"
                    disabled={busyId === entry.entry_id}
                    onClick={() => handleLeave(entry.entry_id)}
                  >
                    Leave Waitlist
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
