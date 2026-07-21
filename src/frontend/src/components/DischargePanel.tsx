/**
 * REQ-10 — Discharge Summary Panel (Doctor portal).
 * Full-screen modal that doctor fills out to complete an appointment with
 * an optional discharge summary and follow-up booking.
 */
import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { getAvailableSlots } from '../api/availability';
import { createDischargeSummary, type CreateDischargeSummaryPayload } from '../api/discharge';
import { updateAppointmentStatus } from '../api/doctor';
import { extractErrorMessage } from '../api/client';
import { SlotPicker } from './SlotPicker';

interface Props {
  appointmentId: number;
  doctorId: number;
  onClose: () => void;
  /** Called on success so parent can reload the appointments list */
  onSuccess: () => void;
}

export function DischargePanel({ appointmentId, doctorId, onClose, onSuccess }: Props) {
  const [keyFindings, setKeyFindings] = useState('');
  const [patientInstructions, setPatientInstructions] = useState('');
  const [activityRestrictions, setActivityRestrictions] = useState('');
  const [medicationReminders, setMedicationReminders] = useState('');
  const [showFollowUp, setShowFollowUp] = useState(false);
  const [followUpDate, setFollowUpDate] = useState('');
  const [followUpSlots, setFollowUpSlots] = useState<string[]>([]);
  const [followUpSlotsLoading, setFollowUpSlotsLoading] = useState(false);
  const [selectedFollowUpSlot, setSelectedFollowUpSlot] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // When follow-up date changes, load available slots
  useEffect(() => {
    setFollowUpSlots([]);
    setSelectedFollowUpSlot('');
    if (!showFollowUp || !followUpDate) return;
    setFollowUpSlotsLoading(true);
    getAvailableSlots(doctorId, followUpDate)
      .then((r) => {
        setFollowUpSlots(r.slots);
        setFollowUpSlotsLoading(false);
      })
      .catch(() => setFollowUpSlotsLoading(false));
  }, [followUpDate, showFollowUp, doctorId]);

  async function handleSkip() {
    // Just mark as Completed without a discharge summary
    setSubmitting(true);
    setError(null);
    try {
      await updateAppointmentStatus(appointmentId, 'Completed');
      onSuccess();
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSave() {
    if (!keyFindings.trim()) {
      setError('Key Findings is required.');
      return;
    }
    setError(null);
    setSubmitting(true);

    const payload: CreateDischargeSummaryPayload = {
      key_findings: keyFindings.trim(),
      patient_instructions: patientInstructions.trim() || null,
      activity_restrictions: activityRestrictions.trim() || null,
      medication_reminders: medicationReminders.trim() || null,
    };

    if (showFollowUp && followUpDate && selectedFollowUpSlot) {
      payload.follow_up = {
        scheduled_at: `${followUpDate}T${selectedFollowUpSlot}:00`,
      };
    }

    try {
      await createDischargeSummary(appointmentId, payload);
      onSuccess();
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
  }

  const today = new Date().toISOString().slice(0, 10);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.5)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        overflowY: 'auto',
        padding: '2rem 1rem',
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="discharge-panel-title"
    >
      <div
        style={{
          background: 'var(--color-surface, #fff)',
          borderRadius: 12,
          padding: '2rem',
          width: '100%',
          maxWidth: 680,
          position: 'relative',
          boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--color-text-light)',
          }}
          aria-label="Close discharge panel"
        >
          <X size={22} />
        </button>

        <h2 id="discharge-panel-title" style={{ marginBottom: '1.5rem' }}>
          Complete &amp; Discharge
        </h2>

        {error && <p className="error-text" style={{ marginBottom: '1rem' }}>{error}</p>}

        <div className="form">
          <label>
            Key Findings <span style={{ color: 'var(--color-danger, #dc3545)' }}>*</span>
            <textarea
              rows={4}
              value={keyFindings}
              onChange={(e) => setKeyFindings(e.target.value)}
              placeholder="Clinical observations, examination results, diagnosis…"
            />
          </label>

          {/* Optional collapsible sections */}
          <details>
            <summary style={{ cursor: 'pointer', fontWeight: 500, marginBottom: '0.5rem' }}>
              Patient Instructions (optional)
            </summary>
            <textarea
              rows={3}
              value={patientInstructions}
              onChange={(e) => setPatientInstructions(e.target.value)}
              placeholder="Post-visit care instructions…"
            />
          </details>

          <details>
            <summary style={{ cursor: 'pointer', fontWeight: 500, marginBottom: '0.5rem' }}>
              Activity Restrictions (optional)
            </summary>
            <textarea
              rows={3}
              value={activityRestrictions}
              onChange={(e) => setActivityRestrictions(e.target.value)}
              placeholder="E.g. avoid strenuous exercise for 2 weeks…"
            />
          </details>

          <details>
            <summary style={{ cursor: 'pointer', fontWeight: 500, marginBottom: '0.5rem' }}>
              Medication Reminders (optional)
            </summary>
            <textarea
              rows={3}
              value={medicationReminders}
              onChange={(e) => setMedicationReminders(e.target.value)}
              placeholder="Drug name, dosage, frequency…"
            />
          </details>

          {/* Follow-up booking */}
          <div
            style={{
              border: '1px solid var(--color-border, #dee2e6)',
              borderRadius: 8,
              padding: '1rem',
              marginTop: '0.5rem',
            }}
          >
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={showFollowUp}
                onChange={(e) => {
                  setShowFollowUp(e.target.checked);
                  if (!e.target.checked) {
                    setFollowUpDate('');
                    setFollowUpSlots([]);
                    setSelectedFollowUpSlot('');
                  }
                }}
              />
              <strong>Book a Follow-Up Appointment</strong>
            </label>

            {showFollowUp && (
              <div style={{ marginTop: '0.75rem' }}>
                <label>
                  Follow-Up Date
                  <input
                    type="date"
                    min={today}
                    value={followUpDate}
                    onChange={(e) => setFollowUpDate(e.target.value)}
                  />
                </label>
                {followUpDate && (
                  <div style={{ marginTop: '0.5rem' }}>
                    <span
                      style={{
                        fontSize: '0.9rem',
                        fontWeight: 500,
                        display: 'block',
                        marginBottom: '0.4rem',
                      }}
                    >
                      Available slots
                    </span>
                    <SlotPicker
                      slots={followUpSlots}
                      selected={selectedFollowUpSlot}
                      onSelect={setSelectedFollowUpSlot}
                      loading={followUpSlotsLoading}
                      ready={!followUpSlotsLoading}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            gap: '0.75rem',
            justifyContent: 'flex-end',
            marginTop: '1.5rem',
            flexWrap: 'wrap',
          }}
        >
          <button
            className="btn btn-outline"
            onClick={handleSkip}
            disabled={submitting}
          >
            {submitting ? 'Saving…' : 'Skip — just mark Complete'}
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={submitting}
          >
            {submitting ? 'Saving…' : 'Save & Complete'}
          </button>
        </div>
      </div>
    </div>
  );
}
