/**
 * REQ-10 — Patient Discharge Summary Page.
 * Read-only view of a discharge summary for one of the patient's appointments.
 */
import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { FileText, ArrowLeft } from 'lucide-react';
import { getMyDischargeSummaryForAppointment, type DischargeSummary } from '../../api/discharge';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div style={{ marginBottom: '1rem' }}>
      <div
        style={{
          fontWeight: 600,
          fontSize: '0.85rem',
          color: 'var(--color-text-light)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginBottom: '0.25rem',
        }}
      >
        {label}
      </div>
      <div
        style={{
          background: 'var(--color-surface-alt, #f8f9fa)',
          padding: '0.75rem 1rem',
          borderRadius: 6,
          border: '1px solid var(--color-border, #dee2e6)',
          whiteSpace: 'pre-wrap',
        }}
      >
        {value}
      </div>
    </div>
  );
}

export function PatientDischargeSummaryPage() {
  const { id } = useParams<{ id: string }>();
  const [summary, setSummary] = useState<DischargeSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getMyDischargeSummaryForAppointment(Number(id))
      .then((s) => {
        setSummary(s);
        setLoading(false);
      })
      .catch((e) => {
        setError(extractErrorMessage(e));
        setLoading(false);
      });
  }, [id]);

  return (
    <div>
      <div style={{ marginBottom: '1rem' }}>
        <Link to="/patient" className="btn btn-outline btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
          <ArrowLeft size={14} /> Back to Appointments
        </Link>
      </div>

      <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <FileText size={24} />
        Discharge Summary
      </h1>

      {loading ? (
        <SkeletonBlock lines={6} />
      ) : error ? (
        <PageError message={error} />
      ) : !summary ? (
        <p>No discharge summary found for this appointment.</p>
      ) : (
        <div style={{ maxWidth: 680, marginTop: '1.5rem' }}>
          {summary.doctor_name && (
            <p style={{ color: 'var(--color-text-light)', marginBottom: '1rem' }}>
              Prepared by <strong>{summary.doctor_name}</strong> on{' '}
              {summary.created_at?.slice(0, 10)}
            </p>
          )}

          <Field label="Key Findings" value={summary.key_findings} />
          <Field label="Patient Instructions" value={summary.patient_instructions} />
          <Field label="Activity Restrictions" value={summary.activity_restrictions} />
          <Field label="Medication Reminders" value={summary.medication_reminders} />

          {summary.follow_up_appointment_id && (
            <div
              style={{
                background: 'rgba(13,110,253,0.05)',
                border: '1px solid rgba(13,110,253,0.3)',
                borderRadius: 8,
                padding: '1rem',
                marginTop: '1rem',
              }}
            >
              <strong>Follow-Up Appointment Booked</strong>
              <p style={{ margin: '0.5rem 0 0', color: 'var(--color-text-light)', fontSize: '0.9rem' }}>
                A follow-up appointment (ID: {summary.follow_up_appointment_id}) has been scheduled.
                View it in your{' '}
                <Link to="/patient">appointments list</Link>.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
