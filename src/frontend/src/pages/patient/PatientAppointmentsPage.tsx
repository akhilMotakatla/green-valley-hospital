import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CalendarCheck } from 'lucide-react';
import { cancelMyAppointment, listMyAppointments } from '../../api/patient';
import type { PatientAppointment } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { StatusBadge } from '../../components/StatusBadge';
import { Pager } from '../../components/Pager';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { useAuth } from '../../auth/AuthContext';

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

export function PatientAppointmentsPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<PatientAppointment[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const pageSize = 10;

  const load = useCallback(() => {
    setLoading(true);
    listMyAppointments({ status: status || undefined, page, page_size: pageSize })
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
        setLoading(false);
      })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, [status, page]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCancel(id: number) {
    setError(null);
    setBusyId(id);
    try {
      await cancelMyAppointment(id);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  const upcomingCount = items.filter((a) => a.status === 'Scheduled').length;

  return (
    <div>
      {/* Greeting card */}
      <div
        className="card"
        style={{
          background: 'var(--color-primary-light)',
          padding: '1.5rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1.25rem',
        }}
      >
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: 'var(--color-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            flexShrink: 0,
          }}
        >
          <CalendarCheck size={28} />
        </div>
        <div>
          <h2 style={{ margin: 0 }}>
            {getGreeting()}, {user?.email ?? 'Patient'}!
          </h2>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--color-text-muted)' }}>
            {upcomingCount > 0
              ? `You have ${upcomingCount} upcoming appointment${upcomingCount > 1 ? 's' : ''}.`
              : 'No upcoming appointments scheduled.'}
          </p>
        </div>
      </div>

      <div className="toolbar">
        <label>
          Status
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All</option>
            <option value="Scheduled">Scheduled</option>
            <option value="Completed">Completed</option>
            <option value="Cancelled">Cancelled</option>
            <option value="NoShow">No-show</option>
          </select>
        </label>
      </div>

      {error && <PageError message={error} onRetry={load} />}

      {loading ? (
        <SkeletonBlock lines={5} />
      ) : items.length === 0 ? (
        <div className="empty-state">
          <CalendarCheck size={80} color="var(--color-text-light)" />
          <h3>No appointments yet</h3>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Book your first appointment with one of our specialists.
          </p>
          <Link to="/patient/book" className="btn btn-primary">
            Book your first appointment
          </Link>
        </div>
      ) : (
        <>
          <table className="data-table">
            <thead>
              <tr>
                <th>Doctor</th>
                <th>Scheduled</th>
                <th>Reason</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.appointment_id}>
                  <td>{a.doctor_name}</td>
                  <td>{formatDateTime(a.scheduled_at)}</td>
                  <td>{a.reason}</td>
                  <td>
                    <StatusBadge status={a.status} />
                  </td>
                  <td>
                    {a.status === 'Scheduled' && (
                      <button
                        className="btn btn-outline btn-sm"
                        disabled={busyId === a.appointment_id}
                        onClick={() => handleCancel(a.appointment_id)}
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pager page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
