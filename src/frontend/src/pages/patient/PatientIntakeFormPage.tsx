import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ClipboardList, CheckCircle, Pencil } from 'lucide-react';
import { getIntakeForm, patchIntakeForm } from '../../api/intake';
import type { IntakeForm } from '../../api/intake';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { formatDateTime } from '../../utils/format';

export function PatientIntakeFormPage() {
  const { id } = useParams<{ id: string }>();
  const appointmentId = Number(id);

  const [form, setForm] = useState<IntakeForm | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);

  // Form fields
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [symptomDuration, setSymptomDuration] = useState('');
  const [allergies, setAllergies] = useState('');
  const [medications, setMedications] = useState('');
  const [painScale, setPainScale] = useState<number>(5);
  const [additionalNotes, setAdditionalNotes] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getIntakeForm(appointmentId)
      .then((f) => {
        setForm(f);
        if (f.chief_complaint) setChiefComplaint(f.chief_complaint);
        if (f.symptom_duration) setSymptomDuration(f.symptom_duration);
        if (f.allergies) setAllergies(f.allergies);
        if (f.current_medications) setMedications(f.current_medications);
        if (f.pain_scale) setPainScale(f.pain_scale);
        if (f.additional_notes) setAdditionalNotes(f.additional_notes);
        setLoading(false);
      })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, [appointmentId]);

  useEffect(() => { load(); }, [load]);

  async function handleSave(e: FormEvent, submit: boolean) {
    e.preventDefault();
    setSaving(true);
    setSaveMsg(null);
    setSaveError(null);
    try {
      const updated = await patchIntakeForm(appointmentId, {
        chief_complaint: chiefComplaint || undefined,
        symptom_duration: symptomDuration || undefined,
        allergies: allergies || undefined,
        current_medications: medications || undefined,
        pain_scale: painScale,
        additional_notes: additionalNotes || undefined,
        submit,
      });
      setForm(updated);
      setSaveMsg(submit ? 'Form submitted successfully.' : `Draft saved at ${new Date().toLocaleTimeString()}.`);
      if (submit) setEditing(false);
    } catch (err) {
      setSaveError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <SkeletonBlock lines={8} />;
  if (error) return <PageError message={error} onRetry={load} />;
  if (!form) return null;

  const isReadOnly = form.submitted_at && !editing;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ClipboardList size={24} /> Pre-Visit Intake Form
        </h1>
        <Link to="/patient" className="btn btn-outline btn-sm">Back to Appointments</Link>
      </div>

      {form.submitted_at && !editing && (
        <div className="card" style={{ background: 'var(--color-success-bg, #e6f4ea)', border: '1px solid #c3e6cb', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle size={18} color="var(--color-success, #28a745)" />
            <strong>Submitted on {formatDateTime(form.submitted_at)}</strong>
            <button
              className="btn btn-outline btn-sm"
              style={{ marginLeft: 'auto' }}
              onClick={() => setEditing(true)}
            >
              <Pencil size={14} /> Edit
            </button>
          </div>
        </div>
      )}

      <div className="card">
        <form onSubmit={(e) => handleSave(e, true)}>
          <div className="form-group">
            <label htmlFor="chief_complaint">
              Chief Complaint <span style={{ color: 'var(--color-danger)' }}>*</span>
            </label>
            <textarea
              id="chief_complaint"
              className="form-control"
              rows={3}
              value={chiefComplaint}
              onChange={(e) => setChiefComplaint(e.target.value)}
              placeholder="Describe your main symptoms or reason for visit"
              disabled={!!isReadOnly}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="symptom_duration">
              Symptom Duration <span style={{ color: 'var(--color-danger)' }}>*</span>
            </label>
            <input
              id="symptom_duration"
              type="text"
              className="form-control"
              value={symptomDuration}
              onChange={(e) => setSymptomDuration(e.target.value)}
              placeholder="e.g. 3 days, 2 weeks"
              disabled={!!isReadOnly}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="pain_scale">
              Pain Scale: <strong>{painScale}/10</strong>
            </label>
            <input
              id="pain_scale"
              type="range"
              min={1}
              max={10}
              step={1}
              value={painScale}
              onChange={(e) => setPainScale(Number(e.target.value))}
              disabled={!!isReadOnly}
              aria-label={`Pain scale: ${painScale} out of 10`}
              aria-valuemin={1}
              aria-valuemax={10}
              aria-valuenow={painScale}
              style={{ width: '100%' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--color-text-light)' }}>
              <span>1 (No Pain)</span>
              <span>10 (Worst Pain)</span>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="allergies">Allergies (optional)</label>
            <textarea
              id="allergies"
              className="form-control"
              rows={2}
              value={allergies}
              onChange={(e) => setAllergies(e.target.value)}
              placeholder="List any known allergies"
              disabled={!!isReadOnly}
            />
          </div>

          <div className="form-group">
            <label htmlFor="current_medications">Current Medications (optional)</label>
            <textarea
              id="current_medications"
              className="form-control"
              rows={2}
              value={medications}
              onChange={(e) => setMedications(e.target.value)}
              placeholder="List any current medications"
              disabled={!!isReadOnly}
            />
          </div>

          <div className="form-group">
            <label htmlFor="additional_notes">Additional Notes (optional)</label>
            <textarea
              id="additional_notes"
              className="form-control"
              rows={3}
              value={additionalNotes}
              onChange={(e) => setAdditionalNotes(e.target.value)}
              placeholder="Any other information you'd like to share"
              disabled={!!isReadOnly}
            />
          </div>

          {saveMsg && (
            <div style={{ marginBottom: '1rem', color: 'var(--color-success, #28a745)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle size={16} /> {saveMsg}
            </div>
          )}
          {saveError && (
            <div style={{ marginBottom: '1rem', color: 'var(--color-danger)' }}>
              {saveError}
            </div>
          )}

          {!isReadOnly && (
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                type="button"
                className="btn btn-outline"
                disabled={saving}
                onClick={(e) => handleSave(e as unknown as FormEvent, false)}
              >
                {saving ? 'Saving...' : 'Save Draft'}
              </button>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? 'Submitting...' : 'Submit'}
              </button>
              {editing && (
                <button type="button" className="btn btn-ghost" onClick={() => setEditing(false)}>
                  Cancel
                </button>
              )}
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
