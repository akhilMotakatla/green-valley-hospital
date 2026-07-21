import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useParams } from 'react-router-dom';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import {
  getPatientLabResults,
  getPatientPrescriptions,
  getStaffPatient,
} from '../../api/staff';
import { postVitals } from '../../api/vitals';
import { getIntakeForm } from '../../api/intake';
import type { StaffPatientDetail } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { StatusBadge } from '../../components/StatusBadge';
import { CheckCircle, Clock } from 'lucide-react';

export function StaffPatientDetailPage() {
  const { patientId } = useParams();
  const [patient, setPatient] = useState<StaffPatientDetail | null>(null);
  const [prescriptions, setPrescriptions] = useState<unknown[]>([]);
  const [labResults, setLabResults] = useState<unknown[]>([]);
  const [error, setError] = useState<string | null>(null);

  // REQ-03: Intake form statuses per appointment
  const [intakeStatuses, setIntakeStatuses] = useState<Record<number, boolean | null>>({});

  // REQ-04 Vitals fields (new schema: separate BP columns)
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [systolic, setSystolic] = useState('');
  const [diastolic, setDiastolic] = useState('');
  const [temp, setTemp] = useState('');
  const [pulse, setPulse] = useState('');
  const [vitalsMsg, setVitalsMsg] = useState<string | null>(null);
  const [vitalsError, setVitalsError] = useState<string | null>(null);

  useEffect(() => {
    if (!patientId) return;
    getStaffPatient(Number(patientId))
      .then((p) => {
        setPatient(p);
        // REQ-03: Load intake status for each upcoming appointment
        p.upcoming_appointments.forEach((a) => {
          getIntakeForm(a.appointment_id)
            .then((form) => {
              const submitted = form?.submitted_at != null;
              setIntakeStatuses((prev) => ({ ...prev, [a.appointment_id]: submitted }));
            })
            .catch(() => setIntakeStatuses((prev) => ({ ...prev, [a.appointment_id]: null })));
        });
      })
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
    setVitalsError(null);
    if (!patientId) return;

    // Client-side BP both-or-neither
    if ((systolic && !diastolic) || (!systolic && diastolic)) {
      setVitalsError('Both Systolic BP and Diastolic BP must be provided together.');
      return;
    }

    try {
      await postVitals(Number(patientId), {
        height_cm: height ? Number(height) : undefined,
        weight_kg: weight ? Number(weight) : undefined,
        systolic_bp: systolic ? Number(systolic) : undefined,
        diastolic_bp: diastolic ? Number(diastolic) : undefined,
        temperature_celsius: temp ? Number(temp) : undefined,
        pulse_bpm: pulse ? Number(pulse) : undefined,
      });
      setVitalsMsg('Vitals recorded successfully.');
      setHeight('');
      setWeight('');
      setSystolic('');
      setDiastolic('');
      setTemp('');
      setPulse('');
    } catch (err) {
      setVitalsError(extractErrorMessage(err));
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
              <th>Intake Form</th>
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
                <td>
                  {intakeStatuses[a.appointment_id] === true ? (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--color-success, #28a745)', fontSize: '0.8rem' }}>
                      <CheckCircle size={13} /> Submitted
                    </span>
                  ) : intakeStatuses[a.appointment_id] === false ? (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--color-warning, #f0ad4e)', fontSize: '0.8rem' }}>
                      <Clock size={13} /> Not submitted
                    </span>
                  ) : (
                    <span className="muted" style={{ fontSize: '0.8rem' }}>—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* REQ-04: Record Vitals (updated to use new vitals endpoint) */}
      <section className="section card">
        <h2>Record Vitals</h2>
        {vitalsMsg && <p style={{ color: 'var(--color-success, #28a745)' }}>{vitalsMsg}</p>}
        {vitalsError && <p style={{ color: 'var(--color-danger)' }}>{vitalsError}</p>}
        <form className="form" onSubmit={handleVitals}>
          <div className="form-row">
            <label>
              Height (cm)
              <input type="number" step="0.1" value={height} onChange={(e) => setHeight(e.target.value)} placeholder="e.g. 170" />
            </label>
            <label>
              Weight (kg)
              <input type="number" step="0.1" value={weight} onChange={(e) => setWeight(e.target.value)} placeholder="e.g. 70.5" />
            </label>
          </div>
          <div className="form-row">
            <label>
              Systolic BP (mmHg)
              <input type="number" value={systolic} onChange={(e) => setSystolic(e.target.value)} placeholder="e.g. 120" />
            </label>
            <label>
              Diastolic BP (mmHg)
              <input type="number" value={diastolic} onChange={(e) => setDiastolic(e.target.value)} placeholder="e.g. 80" />
            </label>
          </div>
          <div className="form-row">
            <label>
              Temperature (°C)
              <input type="number" step="0.1" value={temp} onChange={(e) => setTemp(e.target.value)} placeholder="e.g. 37.0" />
            </label>
            <label>
              Pulse (bpm)
              <input type="number" value={pulse} onChange={(e) => setPulse(e.target.value)} placeholder="e.g. 72" />
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
