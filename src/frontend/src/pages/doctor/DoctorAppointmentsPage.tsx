import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CalendarCheck } from 'lucide-react';
import { listMyAppointments, updateAppointmentStatus } from '../../api/doctor';
import type { DoctorAppointment } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { StatusBadge } from '../../components/StatusBadge';
import { Pager } from '../../components/Pager';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

export function DoctorAppointmentsPage() {
  const [items, setItems] = useState<DoctorAppointment[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const pageSize = 10;

  const [loading, setLoading] = useState(true);

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

  async function handleStatusChange(id: number, newStatus: 'Completed' | 'NoShow' | 'Cancelled') {
    setError(null);
    setBusyId(id);
    try {
      await updateAppointmentStatus(id, newStatus);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <h1>My Appointments</h1>
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
      ) : items.length === 0 && !error ? (
        <div className="empty-state">
          <CalendarCheck size={80} color="var(--color-text-light)" />
          <h3>No appointments found</h3>
        </div>
      ) : (
        <>
          <table className="data-table">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Scheduled</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.appointment_id}>
                  <td>{a.patient_name}</td>
                  <td>{formatDateTime(a.scheduled_at)}</td>
                  <td>{a.reason}</td>
                  <td><StatusBadge status={a.status} /></td>
                  <td style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                    <Link className="btn btn-outline btn-sm" to={`/doctor/patients/${a.patient_id}?appointmentId=${a.appointment_id}`}>
                      Patient Records
                    </Link>
                    {a.status === 'Scheduled' && (
                      <>
                        <button className="btn btn-primary btn-sm" disabled={busyId === a.appointment_id} onClick={() => handleStatusChange(a.appointment_id, 'Completed')}>Complete</button>
                        <button className="btn btn-outline btn-sm" disabled={busyId === a.appointment_id} onClick={() => handleStatusChange(a.appointment_id, 'NoShow')}>No-show</button>
                        <button className="btn btn-danger btn-sm" disabled={busyId === a.appointment_id} onClick={() => handleStatusChange(a.appointment_id, 'Cancelled')}>Cancel</button>
                      </>
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
