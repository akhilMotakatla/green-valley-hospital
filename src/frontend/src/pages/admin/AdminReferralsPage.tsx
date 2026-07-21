import { useCallback, useEffect, useState } from 'react';
import { ArrowRightLeft, AlertCircle } from 'lucide-react';
import { adminListReferrals } from '../../api/referrals';
import type { Referral } from '../../api/referrals';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { StatusBadge } from '../../components/StatusBadge';
import { formatDateTime } from '../../utils/format';

const STATUSES = ['', 'Pending', 'Accepted', 'Declined', 'AppointmentBooked', 'Completed'];

export function AdminReferralsPage() {
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [total, setTotal] = useState(0);

  const load = useCallback(() => {
    setLoading(true);
    adminListReferrals({ status: statusFilter || undefined, page: 1, page_size: 50 })
      .then((r) => { setReferrals(r.items); setTotal(r.total); setLoading(false); })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, [statusFilter]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <SkeletonBlock lines={6} />;
  if (error) return <div className="card"><p style={{ color: 'var(--color-danger)' }}>{error}</p></div>;

  return (
    <div>
      <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <ArrowRightLeft size={24} /> All Referrals ({total})
      </h1>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', alignItems: 'center' }}>
        <label style={{ fontWeight: 600 }}>Filter by status:</label>
        <select
          className="form-control"
          style={{ maxWidth: 200 }}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s || 'All'}</option>
          ))}
        </select>
      </div>

      {referrals.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
          <p className="muted">No referrals found.</p>
        </div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Patient</th>
              <th>From Doctor</th>
              <th>To Department</th>
              <th>To Doctor</th>
              <th>Urgency</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {referrals.map((r) => (
              <tr key={r.referral_id}>
                <td>#{r.referral_id}</td>
                <td>{r.patient_name ?? `#${r.patient_id}`}</td>
                <td>Dr. {r.referring_doctor_name}</td>
                <td>{r.receiving_department_name}</td>
                <td>{r.receiving_doctor_name ? `Dr. ${r.receiving_doctor_name}` : '—'}</td>
                <td>
                  {r.urgency === 'Urgent' ? (
                    <span style={{ color: '#e67e22', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                      <AlertCircle size={14} /> Urgent
                    </span>
                  ) : (
                    <span className="muted">Routine</span>
                  )}
                </td>
                <td><StatusBadge status={r.status} /></td>
                <td>{formatDateTime(r.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
