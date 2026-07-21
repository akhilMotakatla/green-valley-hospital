import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { ArrowRightLeft, Activity, ClipboardList } from 'lucide-react';
import { PageError } from '../../components/PageError';
import { VitalsChart } from '../../components/VitalsChart';
import {
  createLabOrder,
  createPrescription,
  createVisitNote,
  getPatientRecords,
} from '../../api/doctor';
import { getPatientVitals } from '../../api/vitals';
import { createReferral } from '../../api/referrals';
import { getIntakeForm } from '../../api/intake';
import type { IntakeForm } from '../../api/intake';
import type { VitalsRecord } from '../../api/vitals';
import type { Medicine, PatientRecordsBundle } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';

const emptyMedicine: Medicine = { name: '', dosage: '', frequency: '', duration: '' };

export function DoctorPatientRecordsPage() {
  const { patientId } = useParams();
  const [searchParams] = useSearchParams();
  const appointmentId = searchParams.get('appointmentId');

  const [records, setRecords] = useState<PatientRecordsBundle | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [diagnosis, setDiagnosis] = useState('');
  const [notes, setNotes] = useState('');
  const [noteMsg, setNoteMsg] = useState<string | null>(null);

  const [medicines, setMedicines] = useState<Medicine[]>([{ ...emptyMedicine }]);
  const [instructions, setInstructions] = useState('');
  const [rxMsg, setRxMsg] = useState<string | null>(null);

  const [testType, setTestType] = useState<'Lab' | 'XRay' | 'Scan'>('Lab');
  const [testSubtype, setTestSubtype] = useState('');
  const [orderNotes, setOrderNotes] = useState('');
  const [orderMsg, setOrderMsg] = useState<string | null>(null);

  // REQ-04: Vitals trend
  const [vitals, setVitals] = useState<VitalsRecord[]>([]);

  // REQ-03: Intake form read-only view
  const [intakeForm, setIntakeForm] = useState<IntakeForm | null>(null);

  // REQ-05: Referral create modal
  const [showReferralModal, setShowReferralModal] = useState(false);
  const [refDeptId, setRefDeptId] = useState('');
  const [refDoctorId, setRefDoctorId] = useState('');
  const [refReason, setRefReason] = useState('');
  const [refUrgency, setRefUrgency] = useState<'Routine' | 'Urgent'>('Routine');
  const [refMsg, setRefMsg] = useState<string | null>(null);
  const [refError, setRefError] = useState<string | null>(null);
  const [depts, setDepts] = useState<{ department_id: number; name: string }[]>([]);

  function load() {
    if (!patientId) return;
    getPatientRecords(Number(patientId))
      .then(setRecords)
      .catch((e) => setError(extractErrorMessage(e)));
    getPatientVitals(Number(patientId), 1, 100)
      .then((r) => setVitals(r.items))
      .catch(() => undefined);
    if (appointmentId) {
      getIntakeForm(Number(appointmentId))
        .then(setIntakeForm)
        .catch(() => setIntakeForm({ submitted: false }));
    }
  }

  useEffect(load, [patientId]);

  // Load departments for referral modal
  useEffect(() => {
    if (!showReferralModal) return;
    import('../../api/client').then(({ apiClient }) => {
      apiClient.get<{ items: { department_id: number; name: string }[] }>('/admin/departments').then((r) => {
        setDepts(r.data.items ?? []);
      }).catch(() => undefined);
    });
  }, [showReferralModal]);

  async function handleCreateReferral(e: FormEvent) {
    e.preventDefault();
    setRefMsg(null);
    setRefError(null);
    if (!patientId || !refDeptId || !refReason) {
      setRefError('Department and reason are required.');
      return;
    }
    try {
      await createReferral({
        patient_id: Number(patientId),
        to_department_id: Number(refDeptId),
        to_doctor_id: refDoctorId ? Number(refDoctorId) : undefined,
        reason: refReason,
        urgency: refUrgency,
      });
      setRefMsg('Referral sent successfully.');
      setRefDeptId('');
      setRefDoctorId('');
      setRefReason('');
      setRefUrgency('Routine');
      setTimeout(() => { setShowReferralModal(false); setRefMsg(null); }, 1500);
    } catch (err) {
      setRefError(extractErrorMessage(err));
    }
  }

  async function handleVisitNoteSubmit(e: FormEvent) {
    e.preventDefault();
    setNoteMsg(null);
    if (!appointmentId) {
      setNoteMsg('Open this page from a specific appointment to add a visit note.');
      return;
    }
    try {
      await createVisitNote(Number(appointmentId), { diagnosis: diagnosis || undefined, notes });
      setNoteMsg('Visit note added.');
      setDiagnosis('');
      setNotes('');
      load();
    } catch (err) {
      setNoteMsg(extractErrorMessage(err));
    }
  }

  async function handlePrescriptionSubmit(e: FormEvent) {
    e.preventDefault();
    setRxMsg(null);
    if (!appointmentId) {
      setRxMsg('Open this page from a specific appointment to add a prescription.');
      return;
    }
    try {
      await createPrescription(Number(appointmentId), {
        medicines: medicines.filter((m) => m.name),
        instructions: instructions || undefined,
      });
      setRxMsg('Prescription created.');
      setMedicines([{ ...emptyMedicine }]);
      setInstructions('');
      load();
    } catch (err) {
      setRxMsg(extractErrorMessage(err));
    }
  }

  async function handleLabOrderSubmit(e: FormEvent) {
    e.preventDefault();
    setOrderMsg(null);
    if (!patientId) return;
    try {
      await createLabOrder(Number(patientId), {
        test_type: testType,
        test_subtype: testSubtype || undefined,
        notes: orderNotes || undefined,
        appointment_id: appointmentId ? Number(appointmentId) : undefined,
      });
      setOrderMsg('Lab order created.');
      setTestSubtype('');
      setOrderNotes('');
    } catch (err) {
      setOrderMsg(extractErrorMessage(err));
    }
  }

  function updateMedicine(idx: number, field: keyof Medicine, value: string) {
    setMedicines((prev) => prev.map((m, i) => (i === idx ? { ...m, [field]: value } : m)));
  }

  if (error) return <PageError message={error} />;

  // Prepare vitals chart data
  const vitalsChartData = vitals.map((v) => ({
    date: v.recorded_at.slice(0, 10),
    systolic_bp: v.systolic_bp,
    diastolic_bp: v.diastolic_bp,
    weight_kg: v.weight_kg,
    pulse_bpm: v.pulse_bpm,
    temperature_celsius: v.temperature_celsius,
  }));

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1>Patient #{patientId} — Records</h1>
        <button className="btn btn-outline" onClick={() => setShowReferralModal(true)}>
          <ArrowRightLeft size={16} style={{ marginRight: '0.4rem' }} />
          Create Referral
        </button>
      </div>

      {/* REQ-05: Referral modal */}
      {showReferralModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div className="card" style={{ width: '100%', maxWidth: 520, maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0 }}>Create Referral</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowReferralModal(false)}>✕</button>
            </div>
            {refMsg && <p style={{ color: 'var(--color-success, #28a745)' }}>{refMsg}</p>}
            {refError && <p style={{ color: 'var(--color-danger)' }}>{refError}</p>}
            <form className="form" onSubmit={handleCreateReferral}>
              <div className="form-group">
                <label>Receiving Department *</label>
                <select className="form-control" value={refDeptId} onChange={(e) => setRefDeptId(e.target.value)} required>
                  <option value="">Select department...</option>
                  {depts.map((d) => (
                    <option key={d.department_id} value={d.department_id}>{d.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Receiving Doctor (optional)</label>
                <input
                  type="number"
                  className="form-control"
                  value={refDoctorId}
                  onChange={(e) => setRefDoctorId(e.target.value)}
                  placeholder="Doctor ID (optional)"
                />
              </div>
              <div className="form-group">
                <label>Clinical Reason *</label>
                <textarea
                  className="form-control"
                  rows={3}
                  value={refReason}
                  onChange={(e) => setRefReason(e.target.value)}
                  required
                  placeholder="Reason for referral..."
                />
              </div>
              <div className="form-group">
                <label>Urgency</label>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <input type="radio" value="Routine" checked={refUrgency === 'Routine'} onChange={() => setRefUrgency('Routine')} />
                    Routine
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#e67e22' }}>
                    <input type="radio" value="Urgent" checked={refUrgency === 'Urgent'} onChange={() => setRefUrgency('Urgent')} />
                    Urgent
                  </label>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="submit" className="btn btn-primary">Send Referral</button>
                <button type="button" className="btn btn-outline" onClick={() => setShowReferralModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {appointmentId && <p className="muted">Context appointment: #{appointmentId}</p>}

      {/* REQ-04: Vitals Trend Charts */}
      <section className="section">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Activity size={20} /> Vitals History
        </h2>
        {vitals.length === 0 ? (
          <div className="card" style={{ padding: '1.5rem', textAlign: 'center' }}>
            <p className="muted">No vitals recorded yet.</p>
          </div>
        ) : (
          <>
            {vitals.length >= 1 && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                {/* Most recent readings summary */}
                {(() => {
                  const last = vitals[vitals.length - 1];
                  return (
                    <div className="card" style={{ padding: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                      <strong style={{ width: '100%' }}>Most Recent ({last.recorded_at.slice(0,10)})</strong>
                      {last.systolic_bp != null && <span>BP: {last.systolic_bp}/{last.diastolic_bp} mmHg</span>}
                      {last.weight_kg != null && <span>Weight: {last.weight_kg} kg</span>}
                      {last.pulse_bpm != null && <span>Pulse: {last.pulse_bpm} bpm</span>}
                      {last.temperature_celsius != null && <span>Temp: {last.temperature_celsius} °C</span>}
                    </div>
                  );
                })()}
              </div>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
              <VitalsChart
                data={vitalsChartData}
                xKey="date"
                title="Blood Pressure"
                unit="mmHg"
                ariaLabel="Blood pressure trend chart showing systolic and diastolic readings over time"
                lines={[
                  { key: 'systolic_bp', label: 'Systolic', color: '#e74c3c', strokeDasharray: undefined },
                  { key: 'diastolic_bp', label: 'Diastolic', color: '#3498db', strokeDasharray: '4 4' },
                ]}
              />
              <VitalsChart
                data={vitalsChartData}
                xKey="date"
                title="Weight"
                unit="kg"
                ariaLabel="Weight trend chart over time"
                lines={[{ key: 'weight_kg', label: 'Weight', color: '#2ecc71' }]}
              />
              <VitalsChart
                data={vitalsChartData}
                xKey="date"
                title="Pulse"
                unit="bpm"
                ariaLabel="Pulse trend chart over time"
                lines={[{ key: 'pulse_bpm', label: 'Pulse', color: '#9b59b6' }]}
              />
              <VitalsChart
                data={vitalsChartData}
                xKey="date"
                title="Temperature"
                unit="°C"
                ariaLabel="Temperature trend chart over time"
                lines={[{ key: 'temperature_celsius', label: 'Temperature', color: '#f39c12' }]}
              />
            </div>
          </>
        )}
      </section>

      {/* REQ-03: Intake Form (read-only) */}
      {appointmentId && (
        <section className="section card">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <ClipboardList size={20} /> Pre-Visit Intake Form
          </h2>
          {!intakeForm || !intakeForm.submitted_at ? (
            <p className="muted">Patient has not yet submitted the intake form.</p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <p><strong>Chief Complaint:</strong> {intakeForm.chief_complaint ?? '—'}</p>
                <p><strong>Symptom Duration:</strong> {intakeForm.symptom_duration ?? '—'}</p>
                <p><strong>Pain Scale:</strong> {intakeForm.pain_scale != null ? `${intakeForm.pain_scale}/10` : '—'}</p>
              </div>
              <div>
                <p><strong>Allergies:</strong> {intakeForm.allergies ?? '—'}</p>
                <p><strong>Current Medications:</strong> {intakeForm.current_medications ?? '—'}</p>
                <p><strong>Additional Notes:</strong> {intakeForm.additional_notes ?? '—'}</p>
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <p className="muted" style={{ fontSize: '0.8rem' }}>Submitted: {formatDateTime(intakeForm.submitted_at)}</p>
              </div>
            </div>
          )}
        </section>
      )}

      {records && (
        <>
          <section className="section">
            <h2>Visit Notes</h2>
            {records.visit_notes.length === 0 && <p className="muted">None yet.</p>}
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
            {records.prescriptions.length === 0 && <p className="muted">None yet.</p>}
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
              </div>
            ))}
          </section>

          <section className="section">
            <h2>Lab Results</h2>
            {records.lab_results.length === 0 ? (
              <p className="muted">None yet.</p>
            ) : (
              <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(records.lab_results, null, 2)}</pre>
            )}
          </section>
        </>
      )}

      <section className="section card">
        <h2>Add Visit Note</h2>
        {noteMsg && <p className={noteMsg.includes('added') ? 'success-text' : 'error-text'}>{noteMsg}</p>}
        <form className="form" onSubmit={handleVisitNoteSubmit}>
          <label>
            Diagnosis
            <input value={diagnosis} onChange={(e) => setDiagnosis(e.target.value)} />
          </label>
          <label>
            Notes
            <textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} required />
          </label>
          <button className="btn btn-primary" type="submit">
            Save Visit Note
          </button>
        </form>
      </section>

      <section className="section card">
        <h2>Create Prescription</h2>
        {rxMsg && <p className={rxMsg.includes('created') ? 'success-text' : 'error-text'}>{rxMsg}</p>}
        <form className="form" onSubmit={handlePrescriptionSubmit}>
          {medicines.map((m, idx) => (
            <div className="form-row" key={idx}>
              <input
                placeholder="Medicine name"
                value={m.name}
                onChange={(e) => updateMedicine(idx, 'name', e.target.value)}
              />
              <input
                placeholder="Dosage"
                value={m.dosage}
                onChange={(e) => updateMedicine(idx, 'dosage', e.target.value)}
              />
              <input
                placeholder="Frequency"
                value={m.frequency}
                onChange={(e) => updateMedicine(idx, 'frequency', e.target.value)}
              />
              <input
                placeholder="Duration"
                value={m.duration}
                onChange={(e) => updateMedicine(idx, 'duration', e.target.value)}
              />
            </div>
          ))}
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => setMedicines((prev) => [...prev, { ...emptyMedicine }])}
          >
            + Add medicine
          </button>
          <label>
            Instructions
            <textarea rows={2} value={instructions} onChange={(e) => setInstructions(e.target.value)} />
          </label>
          <button className="btn btn-primary" type="submit">
            Save Prescription
          </button>
        </form>
      </section>

      <section className="section card">
        <h2>Order Lab / X-ray / Scan</h2>
        {orderMsg && <p className={orderMsg.includes('created') ? 'success-text' : 'error-text'}>{orderMsg}</p>}
        <form className="form" onSubmit={handleLabOrderSubmit}>
          <label>
            Test type
            <select value={testType} onChange={(e) => setTestType(e.target.value as 'Lab' | 'XRay' | 'Scan')}>
              <option value="Lab">Lab</option>
              <option value="XRay">X-Ray</option>
              <option value="Scan">Scan</option>
            </select>
          </label>
          <label>
            Subtype (optional)
            <input value={testSubtype} onChange={(e) => setTestSubtype(e.target.value)} />
          </label>
          <label>
            Notes for lab
            <textarea rows={2} value={orderNotes} onChange={(e) => setOrderNotes(e.target.value)} />
          </label>
          <button className="btn btn-primary" type="submit">
            Create Order
          </button>
        </form>
      </section>
    </div>
  );
}
