import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { ArrowRightLeft, AlertCircle } from 'lucide-react';
import {
  acceptReferral,
  completeReferral,
  declineReferral,
  getReceivedReferrals,
  getSentReferrals,
} from '../../api/referrals';
import type { Referral } from '../../api/referrals';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { StatusBadge } from '../../components/StatusBadge';
import { formatDateTime } from '../../utils/format';

type Tab = 'received' | 'sent';

export function DoctorReferralsPage() {
  const [tab, setTab] = useState<Tab>('received');
  const [received, setReceived] = useState<Referral[]>([]);
  const [sent, setSent] = useState<Referral[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Action modals
  const [actionReferral, setActionReferral] = useState<Referral | null>(null);
  const [actionType, setActionType] = useState<'accept' | 'decline' | null>(null);
  const [actionNote, setActionNote] = useState('');
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getReceivedReferrals({ page: 1, page_size: 50 }),
      getSentReferrals({ page: 1, page_size: 50 }),
    ])
      .then(([recv, snt]) => {
        setReceived(recv.items);
        setSent(snt.items);
        setLoading(false);
      })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleAction(e: FormEvent) {
    e.preventDefault();
    if (!actionReferral) return;
    setActionError(null);
    try {
      if (actionType === 'accept') {
        await acceptReferral(actionReferral.referral_id, actionNote || undefined);
      } else if (actionType === 'decline') {
        if (!actionNote) { setActionError('A decline reason is required.'); return; }
        await declineReferral(actionReferral.referral_id, actionNote);
      }
      setActionMsg('Action completed.');
      setActionReferral(null);
      setActionType(null);
      setActionNote('');
      load();
    } catch (err) {
      setActionError(extractErrorMessage(err));
    }
  }

  async function handleComplete(referralId: number) {
    try {
      await completeReferral(referralId);
      load();
    } catch (err) {
      alert(extractErrorMessage(err));
    }
  }

  if (loading) return <SkeletonBlock lines={6} />;
  if (error) return <div className="card"><p style={{ color: 'var(--color-danger)' }}>{error}</p></div>;

  const urgencyBadge = (urgency: string) =>
    urgency === 'Urgent' ? (
      <span style={{
        background: '#f39c12', color: '#fff', padding: '2px 8px',
        borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600,
      }}>
        <AlertCircle size={12} style={{ marginRight: 4, verticalAlign: 'middle' }} />
        Urgent
      </span>
    ) : (
      <span style={{
        background: '#ecf0f1', color: '#666', padding: '2px 8px',
        borderRadius: '12px', fontSize: '0.75rem',
      }}>Routine</span>
    );

  return (
    <div>
      <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <ArrowRightLeft size={24} /> Referrals
      </h1>

      {actionMsg && (
        <div className="card" style={{ background: '#e6f4ea', border: '1px solid #c3e6cb', marginBottom: '1rem' }}>
          {actionMsg}
        </div>
      )}

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <button
          className={`btn ${tab === 'received' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setTab('received')}
        >
          Received ({received.filter((r) => r.status === 'Pending').length} pending)
        </button>
        <button
          className={`btn ${tab === 'sent' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setTab('sent')}
        >
          Sent ({sent.length})
        </button>
      </div>

      {tab === 'received' && (
        <div>
          {received.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
              <p className="muted">No incoming referrals.</p>
            </div>
          ) : (
            received.map((r) => (
              <div key={r.referral_id} className="card section" style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    {urgencyBadge(r.urgency)}{' '}
                    <StatusBadge status={r.status} />
                    <p style={{ marginTop: '0.5rem' }}>
                      <strong>Patient:</strong> {r.patient_name ?? `#${r.patient_id}`}
                    </p>
                    <p>
                      <strong>From:</strong> Dr. {r.referring_doctor_name}
                    </p>
                    <p className="muted">{formatDateTime(r.created_at)}</p>
                    {r.receiving_doctor_note && (
                      <p><strong>Note:</strong> {r.receiving_doctor_note}</p>
                    )}
                  </div>
                  {r.status === 'Pending' && (
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => { setActionReferral(r); setActionType('accept'); setActionNote(''); setActionError(null); }}
                      >Accept</button>
                      <button
                        className="btn btn-outline btn-sm"
                        style={{ color: 'var(--color-danger)', borderColor: 'var(--color-danger)' }}
                        onClick={() => { setActionReferral(r); setActionType('decline'); setActionNote(''); setActionError(null); }}
                      >Decline</button>
                    </div>
                  )}
                  {r.status === 'Accepted' && (
                    <button className="btn btn-outline btn-sm" onClick={() => handleComplete(r.referral_id)}>
                      Mark Complete
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {tab === 'sent' && (
        <div>
          {sent.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
              <p className="muted">No sent referrals.</p>
            </div>
          ) : (
            sent.map((r) => (
              <div key={r.referral_id} className="card section" style={{ marginBottom: '1rem' }}>
                {urgencyBadge(r.urgency)}{' '}
                <StatusBadge status={r.status} />
                <p style={{ marginTop: '0.5rem' }}>
                  <strong>Patient:</strong> {r.patient_name ?? `#${r.patient_id}`}
                </p>
                <p>
                  <strong>To:</strong> {r.receiving_department_name}
                  {r.receiving_doctor_name && ` — Dr. ${r.receiving_doctor_name}`}
                </p>
                <p className="muted">{formatDateTime(r.created_at)}</p>
                {r.receiving_doctor_note && (
                  <p><strong>Doctor's note:</strong> {r.receiving_doctor_note}</p>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Accept/Decline modal */}
      {actionReferral && actionType && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div className="card" style={{ width: '100%', maxWidth: 440 }}>
            <h3 style={{ marginBottom: '1rem' }}>
              {actionType === 'accept' ? 'Accept Referral' : 'Decline Referral'}
            </h3>
            {actionError && <p style={{ color: 'var(--color-danger)', marginBottom: '0.5rem' }}>{actionError}</p>}
            <form onSubmit={handleAction}>
              <div className="form-group">
                <label>{actionType === 'decline' ? 'Decline Reason *' : 'Note (optional)'}</label>
                <textarea
                  className="form-control"
                  rows={3}
                  value={actionNote}
                  onChange={(e) => setActionNote(e.target.value)}
                  required={actionType === 'decline'}
                  placeholder={actionType === 'decline' ? 'Reason for declining...' : 'Optional note...'}
                />
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="submit" className={`btn ${actionType === 'accept' ? 'btn-primary' : 'btn-outline'}`}>
                  {actionType === 'accept' ? 'Accept' : 'Decline'}
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => { setActionReferral(null); setActionType(null); }}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
