import { useEffect, useState } from 'react';
import { getDepartments } from '../../api/public';
import {
  bookAppointment,
  getDoctorAvailability,
  searchDoctors,
  type PatientVisibleDoctor,
} from '../../api/patient';
import type { Department } from '../../types';
import { extractErrorMessage } from '../../api/client';

export function BookAppointmentPage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [departmentId, setDepartmentId] = useState<string>('');
  const [doctors, setDoctors] = useState<PatientVisibleDoctor[]>([]);
  const [doctorId, setDoctorId] = useState<string>('');
  const [date, setDate] = useState('');
  const [slots, setSlots] = useState<string[]>([]);
  const [selectedSlot, setSelectedSlot] = useState('');
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getDepartments().then(setDepartments).catch(() => undefined);
  }, []);

  useEffect(() => {
    searchDoctors(departmentId ? Number(departmentId) : undefined)
      .then(setDoctors)
      .catch((e) => setError(extractErrorMessage(e)));
  }, [departmentId]);

  useEffect(() => {
    setSlots([]);
    setSelectedSlot('');
    if (doctorId && date) {
      getDoctorAvailability(Number(doctorId), date)
        .then((r) => setSlots(r.available_slots))
        .catch((e) => setError(extractErrorMessage(e)));
    }
  }, [doctorId, date]);

  async function handleBook() {
    setError(null);
    setSuccess(null);
    if (!doctorId || !date || !selectedSlot) {
      setError('Select a doctor, date, and time slot.');
      return;
    }
    setSubmitting(true);
    try {
      const scheduledAt = `${date}T${selectedSlot}:00`;
      await bookAppointment({ doctor_id: Number(doctorId), scheduled_at: scheduledAt, reason: reason || undefined });
      setSuccess('Appointment booked successfully.');
      setSelectedSlot('');
      setSlots([]);
      setReason('');
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1>Book an Appointment</h1>
      {error && <p className="error-text">{error}</p>}
      {success && <p className="success-text">{success}</p>}
      <div className="form" style={{ maxWidth: 520 }}>
        <label>
          Department
          <select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
            <option value="">All departments</option>
            {departments.map((d) => (
              <option key={d.department_id} value={d.department_id}>
                {d.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Doctor
          <select value={doctorId} onChange={(e) => setDoctorId(e.target.value)}>
            <option value="">Select a doctor</option>
            {doctors.map((d) => (
              <option key={d.doctor_id} value={d.doctor_id}>
                {d.full_name} — {d.specialty} ({d.department_name})
              </option>
            ))}
          </select>
        </label>
        <label>
          Date
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </label>
        {slots.length > 0 && (
          <label>
            Available time slots
            <select value={selectedSlot} onChange={(e) => setSelectedSlot(e.target.value)}>
              <option value="">Select a time</option>
              {slots.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
        )}
        {doctorId && date && slots.length === 0 && (
          <p className="muted">No available slots for this date.</p>
        )}
        <label>
          Reason (optional)
          <textarea rows={3} value={reason} onChange={(e) => setReason(e.target.value)} />
        </label>
        <button className="btn btn-primary" onClick={handleBook} disabled={submitting}>
          {submitting ? 'Booking…' : 'Book Appointment'}
        </button>
      </div>
    </div>
  );
}
