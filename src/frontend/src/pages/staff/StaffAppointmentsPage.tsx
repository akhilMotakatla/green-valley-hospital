import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import {
  createStaffAppointment,
  listStaffAppointments,
  updateStaffAppointment,
} from '../../api/staff';
import { getStaffDirectory } from '../../api/staff';
import type { DirectoryDoctor } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { StatusBadge } from '../../components/StatusBadge';

interface StaffAppt {
  appointment_id: number;
  patient_id: number;
  patient_name?: string;
  doctor_id: number;
  doctor_name?: string;
  scheduled_at: string;
  status: string;
  reason?: string;
}

export function StaffAppointmentsPage() {
  const [items, setItems] = useState<StaffAppt[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [doctors, setDoctors] = useState<DirectoryDoctor[]>([]);

  const [patientId, setPatientId] = useState('');
  const [doctorId, setDoctorId] = useState('');
  const [scheduledAt, setScheduledAt] = useState('');
  const [reason, setReason] = useState('');
  const [createMsg, setCreateMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    listStaffAppointments({ page: 1, page_size: 50 })
      .then((r) => setItems((r as { items: StaffAppt[] }).items))
      .catch((e) => setError(extractErrorMessage(e)));
  }, []);

  useEffect(() => {
    load();
    getStaffDirectory().then(setDoctors).catch(() => undefined);
  }, [load]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setCreateMsg(null);
    try {
      await createStaffAppointment({
        patient_id: Number(patientId),
        doctor_id: Number(doctorId),
        scheduled_at: scheduledAt,
        reason: reason || undefined,
      });
      setCreateMsg('Appointment created.');
      setPatientId('');
      setDoctorId('');
      setScheduledAt('');
      setReason('');
      load();
    } catch (err) {
      setCreateMsg(extractErrorMessage(err));
    }
  }

  async function handleStatusChange(id: number, status: string) {
    try {
      await updateStaffAppointment(id, { status });
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <h1>Appointments (Front Desk)</h1>

      <section className="section card">
        <h2>Book / Reschedule for a Patient</h2>
        {createMsg && (
          <p className={createMsg.includes('created') ? 'success-text' : 'error-text'}>{createMsg}</p>
        )}
        <form className="form" onSubmit={handleCreate}>
          <label>
            Patient ID
            <input value={patientId} onChange={(e) => setPatientId(e.target.value)} required />
          </label>
          <label>
            Doctor
            <select value={doctorId} onChange={(e) => setDoctorId(e.target.value)} required>
              <option value="">Select doctor</option>
              {doctors.map((d) => (
                <option key={d.doctor_id} value={d.doctor_id}>
                  {d.full_name} — {d.specialty}
                </option>
              ))}
            </select>
          </label>
          <label>
            Scheduled at
            <input
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              required
            />
          </label>
          <label>
            Reason
            <input value={reason} onChange={(e) => setReason(e.target.value)} />
          </label>
          <button className="btn btn-primary" type="submit">
            Book Appointment
          </button>
        </form>
      </section>

      {error && <p className="error-text">{error}</p>}
      <h2>All Appointments</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Patient</th>
            <th>Doctor</th>
            <th>Scheduled</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((a) => (
            <tr key={a.appointment_id}>
              <td>{a.patient_name ?? a.patient_id}</td>
              <td>{a.doctor_name ?? a.doctor_id}</td>
              <td>{formatDateTime(a.scheduled_at)}</td>
              <td>
                <StatusBadge status={a.status} />
              </td>
              <td style={{ display: 'flex', gap: '0.4rem' }}>
                {a.status === 'Scheduled' && (
                  <>
                    <button className="btn btn-outline" onClick={() => handleStatusChange(a.appointment_id, 'Completed')}>
                      Complete
                    </button>
                    <button className="btn btn-danger" onClick={() => handleStatusChange(a.appointment_id, 'Cancelled')}>
                      Cancel
                    </button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && <p className="muted">No appointments found.</p>}
    </div>
  );
}
