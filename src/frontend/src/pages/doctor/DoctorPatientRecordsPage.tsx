import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { PageError } from '../../components/PageError';
import {
  createLabOrder,
  createPrescription,
  createVisitNote,
  getPatientRecords,
} from '../../api/doctor';
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

  function load() {
    if (!patientId) return;
    getPatientRecords(Number(patientId))
      .then(setRecords)
      .catch((e) => setError(extractErrorMessage(e)));
  }

  useEffect(load, [patientId]);

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

  return (
    <div>
      <h1>Patient #{patientId} — Records</h1>
      {appointmentId && <p className="muted">Context appointment: #{appointmentId}</p>}

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
