import { useCallback, useEffect, useState } from 'react';
import { FileText, Receipt, FlaskConical } from 'lucide-react';
import { getMyRecords } from '../../api/patient';
import type { PatientRecordsBundle } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

export function PatientRecordsPage() {
  const [records, setRecords] = useState<PatientRecordsBundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getMyRecords()
      .then((r) => { setRecords(r); setLoading(false); })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <SkeletonBlock lines={6} />;
  if (error) return <PageError message={error} onRetry={load} />;
  if (!records) return null;

  return (
    <div>
      <h1>My Medical Records</h1>

      <section className="section">
        <h2>Visit Notes</h2>
        {records.visit_notes.length === 0 && (
          <div className="empty-state" style={{ padding: '2rem 0' }}>
            <FileText size={60} color="var(--color-text-light)" />
            <p className="muted">No visit notes yet.</p>
          </div>
        )}
        {records.visit_notes.map((v) => (
          <div className="card section" key={v.record_id}>
            <p className="muted">{formatDateTime(v.created_at)}</p>
            <p>
              <strong>Diagnosis:</strong> {v.diagnosis || '—'}
            </p>
            <p>{v.notes}</p>
          </div>
        ))}
      </section>

      <section className="section">
        <h2>Prescriptions</h2>
        {records.prescriptions.length === 0 && (
          <div className="empty-state" style={{ padding: '2rem 0' }}>
            <Receipt size={60} color="var(--color-text-light)" />
            <p className="muted">No prescriptions yet.</p>
          </div>
        )}
        {records.prescriptions.map((p) => (
          <div className="card section" key={p.prescription_id}>
            <p className="muted">{formatDateTime(p.created_at)}</p>
            <ul>
              {p.medicines.map((m, idx) => (
                <li key={idx}>
                  {m.name} — {m.dosage}, {m.frequency}, {m.duration}
                </li>
              ))}
            </ul>
            {p.instructions && <p>{p.instructions}</p>}
          </div>
        ))}
      </section>

      <section className="section">
        <h2>Lab / X-ray / Scan Results</h2>
        {records.lab_results.length === 0 ? (
          <div className="empty-state" style={{ padding: '2rem 0' }}>
            <FlaskConical size={60} color="var(--color-text-light)" />
            <p className="muted">No lab results yet.</p>
          </div>
        ) : (
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.875rem', background: 'var(--color-surface-alt)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
            {JSON.stringify(records.lab_results, null, 2)}
          </pre>
        )}
      </section>
    </div>
  );
}
