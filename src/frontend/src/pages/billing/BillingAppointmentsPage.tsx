import { useEffect, useState, useCallback } from 'react';
import { getBillingAppointments } from '../../api/billing';
import type { AppointmentListParams } from '../../api/billing';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import type { BillingAppointment } from '../../types';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { Pager } from '../../components/Pager';

const STATUS_OPTIONS = ['', 'Scheduled', 'Completed', 'Cancelled', 'NoShow'] as const;
type StatusOption = (typeof STATUS_OPTIONS)[number];

function statusBadge(status: string) {
  const map: Record<string, string> = {
    Scheduled: 'badge-scheduled',
    Completed: 'badge-completed',
    Cancelled: 'badge-cancelled',
    NoShow: 'badge-noshow',
  };
  return `badge ${map[status] ?? ''}`;
}

export function BillingAppointmentsPage() {
  const [items, setItems] = useState<BillingAppointment[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;

  const [filterStatus, setFilterStatus] = useState<StatusOption>('');
  const [patientIdInput, setPatientIdInput] = useState('');
  const [patientId, setPatientId] = useState<number | undefined>(undefined);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const params: AppointmentListParams = { page, page_size: PAGE_SIZE };
    if (filterStatus) params.status = filterStatus;
    if (patientId) params.patient_id = patientId;
    getBillingAppointments(params)
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
        setTotalPages(r.total_pages);
        setLoading(false);
      })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, [page, filterStatus, patientId]);

  useEffect(() => { load(); }, [load]);

  function applyFilter() {
    const id = parseInt(patientIdInput, 10);
    setPatientId(isNaN(id) ? undefined : id);
    setPage(1);
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ margin: '0 0 1rem' }}>Appointments (Billing Reference)</h2>
        <div className="billing-filters">
          <select
            value={filterStatus}
            onChange={(e) => { setFilterStatus(e.target.value as StatusOption); setPage(1); }}
          >
            {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s || 'All Statuses'}</option>)}
          </select>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="number"
              placeholder="Filter by patient ID…"
              value={patientIdInput}
              onChange={(e) => setPatientIdInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && applyFilter()}
              style={{ width: 200 }}
            />
            <button className="btn btn-outline" onClick={applyFilter}>Apply</button>
            {patientId && (
              <button className="btn btn-outline" onClick={() => { setPatientIdInput(''); setPatientId(undefined); setPage(1); }}>
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {loading ? (
        <SkeletonBlock lines={8} />
      ) : error ? (
        <PageError message={error} onRetry={load} />
      ) : items.length === 0 ? (
        <p className="muted">No appointments found.</p>
      ) : (
        <div className="billing-ledger-wrapper">
          <table className="billing-ledger">
            <thead>
              <tr>
                <th>Appt ID</th>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Department</th>
                <th>Scheduled At</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.appointment_id}>
                  <td>#{a.appointment_id}</td>
                  <td>{a.patient_name} <span className="muted" style={{ fontSize: '0.8rem' }}>(#{a.patient_id})</span></td>
                  <td>{a.doctor_name}</td>
                  <td>{a.department_name}</td>
                  <td>{formatDateTime(a.scheduled_at)}</td>
                  <td><span className={statusBadge(a.status)}>{a.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pager page={page} pageSize={PAGE_SIZE} total={total} totalPages={totalPages} onPageChange={setPage} />
    </div>
  );
}
