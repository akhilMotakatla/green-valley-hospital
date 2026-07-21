import { useCallback, useEffect, useState } from 'react';
import { FileText, Receipt, FlaskConical, Download, X } from 'lucide-react';
import { getMyRecords, exportPDF } from '../../api/patient';
import type { PatientRecordsBundle } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

export function PatientRecordsPage() {
  const [records, setRecords] = useState<PatientRecordsBundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // REQ-08: PDF export state
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportStartDate, setExportStartDate] = useState('');
  const [exportEndDate, setExportEndDate] = useState('');
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  async function handleExport(startDate?: string, endDate?: string) {
    setExporting(true);
    setExportError(null);
    try {
      const blob = await exportPDF(startDate, endDate);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `GVH_MedicalRecord_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setShowExportModal(false);
      setExportStartDate('');
      setExportEndDate('');
    } catch (err) {
      const msg = extractErrorMessage(err);
      if (msg.includes('503') || msg.includes('unavailable') || msg.includes('GTK3')) {
        setExportError('PDF export is currently unavailable. Please try again later.');
      } else {
        setExportError('PDF generation failed. Please try again.');
      }
    } finally {
      setExporting(false);
    }
  }

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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ margin: 0 }}>My Medical Records</h1>
        <button className="btn btn-outline" onClick={() => setShowExportModal(true)}>
          <Download size={16} style={{ marginRight: '0.4rem' }} />
          Export PDF
        </button>
      </div>

      {/* REQ-08: PDF Export Modal */}
      {showExportModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div className="card" style={{ width: '100%', maxWidth: 420 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0 }}>Download My Records</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowExportModal(false)}>
                <X size={18} />
              </button>
            </div>
            <p className="muted">Optionally filter by date range. Leave blank to export all records.</p>
            {exportError && <p style={{ color: 'var(--color-danger)', marginBottom: '0.5rem' }}>{exportError}</p>}
            <div className="form-group">
              <label>From Date (optional)</label>
              <input
                type="date"
                className="form-control"
                value={exportStartDate}
                onChange={(e) => setExportStartDate(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>To Date (optional)</label>
              <input
                type="date"
                className="form-control"
                value={exportEndDate}
                onChange={(e) => setExportEndDate(e.target.value)}
              />
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
              <button
                className="btn btn-primary"
                disabled={exporting}
                onClick={() => handleExport(exportStartDate || undefined, exportEndDate || undefined)}
              >
                {exporting ? 'Generating...' : (exportStartDate || exportEndDate ? 'Export Selected Range' : 'Export All Records')}
              </button>
              <button className="btn btn-outline" onClick={() => setShowExportModal(false)} disabled={exporting}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

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
