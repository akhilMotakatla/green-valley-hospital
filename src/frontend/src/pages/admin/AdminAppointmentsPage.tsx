import { useCallback, useEffect, useState } from 'react';
import { listAdminAppointments } from '../../api/admin';
import type { AdminAppointment } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { StatusBadge } from '../../components/StatusBadge';
import { Pager } from '../../components/Pager';

export function AdminAppointmentsPage() {
  const [items, setItems] = useState<AdminAppointment[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const [date, setDate] = useState('');
  const [error, setError] = useState<string | null>(null);
  const pageSize = 15;

  const load = useCallback(() => {
    listAdminAppointments({
      status: status || undefined,
      date: date || undefined,
      page,
      page_size: pageSize,
    })
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
      })
      .catch((e) => setError(extractErrorMessage(e)));
  }, [status, date, page]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div>
      <h1>All Appointments</h1>
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
        <label>
          Date
          <input
            type="date"
            value={date}
            onChange={(e) => {
              setDate(e.target.value);
              setPage(1);
            }}
          />
        </label>
      </div>
      {error && <p className="error-text">{error}</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Patient</th>
            <th>Doctor</th>
            <th>Department</th>
            <th>Scheduled</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((a) => (
            <tr key={a.appointment_id}>
              <td>{a.patient_name}</td>
              <td>{a.doctor_name}</td>
              <td>{a.department_name}</td>
              <td>{formatDateTime(a.scheduled_at)}</td>
              <td>
                <StatusBadge status={a.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && <p className="muted">No appointments found.</p>}
      <Pager page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
    </div>
  );
}
