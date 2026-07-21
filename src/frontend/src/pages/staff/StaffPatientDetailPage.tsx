import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useParams } from 'react-router-dom';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import {
  getPatientLabResults,
  getPatientPrescriptions,
  getStaffPatient,
  recordVitals,
} from '../../api/staff';
import type { StaffPatientDetail } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { StatusBadge } from '../../components/StatusBadge';

export function StaffPatientDetailPage() {
  const { patientId } = useParams();
  const [patient, setPatient] = useState<StaffPatientDetail | null>(null);
  const [prescriptions, setPrescriptions] = useState<unknown[]>([]);
  const [labResults, setLabResults] = useState<unknown[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [bp, setBp] = useState('');
  const [temp, setTemp] = useState('');
  const [pulse, setPulse] = useState('');
  const [vitalsMsg, setVitalsMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!patientId) return;
    getStaffPatient(Number(patientId))
      .then(setPatient)
      .catch((e) => setError(extractErrorMessage(e)));
    getPatientPrescriptions(Number(patientId))
      .then((r) => setPrescriptions((r as { items?: unknown[] }).items ?? []))
      .catch(() => undefined);
    getPatientLabResults(Number(patientId))
      .then((r) => setLabResults((r as { items?: unknown[] }).items ?? []))
      .catch(() => undefined);
  }, [patientId]);

  async function handleVitals(e: FormEvent) {
    e.preventDefault();
    setVitalsMsg(null);
    if (!patientId) return;
    try {
      await recordVitals(Number(patientId), {
        height_cm: height ? Number(height) : undefined,
        weight_kg: weight ? Number(weight) : undefined,
        blood_pressure: bp || undefined,
        temperature_c: temp ? Number(temp) : undefined,
        pulse_bpm: pulse ? Number(pulse) : undefined,
      });
      setVitalsMsg('Vitals recorded.');
      setHeight('');
      setWeight('');
      setBp('');
      setTemp('');
      setPulse('');
    } catch (err) {
      setVitalsMsg(extractErrorMessage(err));
    }
  }

  if (error) return <PageError message={error} />;
  if (!patient) return <SkeletonBlock lines={6} />;

  return (
    <div>
      <h1>{patient.full_name}</h1>
      <div className="card section" style={{ maxWidth: 480 }}>
        <p>
          <strong>Email:</strong> {patient.email}
        </p>
        <p>
          <strong>Phone:</strong> {patient.phone}
        </p>
        <p>
          <strong>DOB:</strong> {patient.date_of_birth}
        </p>
      </div>

      <section className="section">
        <h2>Upcoming Appointments</h2>
        {patient.upcoming_appointments.length === 0 && <p className="muted">None.</p>}
        <table className="data-table">
          <thead>
            <tr>
              <th>Scheduled</th>
              <th>Reason</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {patient.upcoming_appointments.map((a) => (
              <tr key={a.appointment_id}>
                <td>{formatDateTime(a.scheduled_at)}</td>
                <td>{a.reason}</td>
                <td>
                  <StatusBadge status={a.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="section card">
        <h2>Record Vitals</h2>
        {vitalsMsg && (
          <p className={vitalsMsg.includes('recorded') ? 'success-text' : 'error-text'}>{vitalsMsg}</p>
        )}
        <form className="form" onSubmit={handleVitals}>
          <div className="form-row">
            <label>
              Height (cm)
              <input value={height} onChange={(e) => setHeight(e.target.value)} />
            </label>
            <label>
              Weight (kg)
              <input value={weight} onChange={(e) => setWeight(e.target.value)} />
            </label>
          </div>
          <div className="form-row">
            <label>
              Blood pressure
              <input value={bp} onChange={(e) => setBp(e.target.value)} placeholder="120/80" />
            </label>
            <label>
              Temperature (C)
              <input value={temp} onChange={(e) => setTemp(e.target.value)} />
            </label>
            <label>
              Pulse (bpm)
              <input value={pulse} onChange={(e) => setPulse(e.target.value)} />
            </label>
          </div>
          <button className="btn btn-primary" type="submit">
            Save Vitals
          </button>
        </form>
      </section>

      <section className="section">
        <h2>Prescriptions (read-only)</h2>
        {prescriptions.length === 0 ? (
          <p className="muted">None on file.</p>
        ) : (
          <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(prescriptions, null, 2)}</pre>
        )}
      </section>

      <section className="section">
        <h2>Lab Results (read-only)</h2>
        {labResults.length === 0 ? (
          <p className="muted">None on file.</p>
        ) : (
          <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(labResults, null, 2)}</pre>
        )}
      </section>
    </div>
  );
}
