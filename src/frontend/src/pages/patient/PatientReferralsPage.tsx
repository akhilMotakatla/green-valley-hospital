import { useCallback, useEffect, useState } from 'react';
import { ArrowRightLeft, AlertCircle } from 'lucide-react';
import { getMyReferrals } from '../../api/referrals';
import type { Referral } from '../../api/referrals';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { StatusBadge } from '../../components/StatusBadge';
import { formatDateTime } from '../../utils/format';

export function PatientReferralsPage() {
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    getMyReferrals({ page: 1, page_size: 50 })
      .then((r) => { setReferrals(r.items); setLoading(false); })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <SkeletonBlock lines={5} />;
  if (error) return <div className="card"><p style={{ color: 'var(--color-danger)' }}>{error}</p></div>;

  return (
    <div>
      <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <ArrowRightLeft size={24} /> My Referrals
      </h1>

      {referrals.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <ArrowRightLeft size={48} color="var(--color-text-light)" />
          <p className="muted" style={{ marginTop: '1rem' }}>No referrals have been made for you yet.</p>
        </div>
      ) : (
        referrals.map((r) => (
          <div key={r.referral_id} className="card section" style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.5rem' }}>
                  {r.urgency === 'Urgent' && (
                    <span style={{
                      background: '#f39c12', color: '#fff', padding: '2px 8px',
                      borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600,
                    }}>
                      <AlertCircle size={12} style={{ marginRight: 4, verticalAlign: 'middle' }} />
                      Urgent
                    </span>
                  )}
                  <StatusBadge status={r.status} />
                </div>
                <p>
                  <strong>Referred to:</strong> {r.receiving_department_name}
                  {r.receiving_doctor_name && <> — Dr. {r.receiving_doctor_name}</>}
                </p>
                <p>
                  <strong>Referring Doctor:</strong> Dr. {r.referring_doctor_name}
                </p>
                {r.receiving_doctor_note && (
                  <p><strong>Doctor's note:</strong> {r.receiving_doctor_note}</p>
                )}
                <p className="muted">{formatDateTime(r.created_at)}</p>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
