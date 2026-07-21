/**
 * REQ-01 updated: uses /doctors/{id}/available-slots (schedule-aware) instead
 * of the old fixed 09:00-17:00 availability endpoint, and renders slot selection
 * via the shared SlotPicker component.
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDepartments } from '../../api/public';
import { bookAppointment, searchDoctors, type PatientVisibleDoctor } from '../../api/patient';
import { getAvailableSlots } from '../../api/availability';
import { joinWaitlist } from '../../api/waitlist';
import type { Department } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { SlotPicker } from '../../components/SlotPicker';

export function BookAppointmentPage() {
  const navigate = useNavigate();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [departmentId, setDepartmentId] = useState<string>('');
  const [doctors, setDoctors] = useState<PatientVisibleDoctor[]>([]);
  const [doctorId, setDoctorId] = useState<string>('');
  const [date, setDate] = useState('');
  const [slots, setSlots] = useState<string[]>([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState('');
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [joiningWaitlist, setJoiningWaitlist] = useState(false);

  useEffect(() => {
    getDepartments().then(setDepartments).catch(() => undefined);
  }, []);

  useEffect(() => {
    searchDoctors(departmentId ? Number(departmentId) : undefined)
      .then(setDoctors)
      .catch((e) => setError(extractErrorMessage(e)));
  }, [departmentId]);

  // REQ-01: fetch schedule-aware available slots whenever doctor or date changes
  useEffect(() => {
    setSlots([]);
    setSelectedSlot('');
    if (!doctorId || !date) return;

    setSlotsLoading(true);
    getAvailableSlots(Number(doctorId), date)
      .then((r) => {
        setSlots(r.slots);
        setSlotsLoading(false);
      })
      .catch((e) => {
        setError(extractErrorMessage(e));
        setSlotsLoading(false);
      });
  }, [doctorId, date]);

  async function handleJoinWaitlist() {
    if (!doctorId || !date) return;
    setJoiningWaitlist(true);
    setError(null);
    try {
      await joinWaitlist({ doctor_id: Number(doctorId), preferred_date: date });
      setSuccess(`You've joined the waitlist for ${date}. We'll notify you when a slot opens.`);
      setTimeout(() => navigate('/patient/waitlist'), 1500);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setJoiningWaitlist(false);
    }
  }

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
      await bookAppointment({
        doctor_id: Number(doctorId),
        scheduled_at: scheduledAt,
        reason: reason || undefined,
      });
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
          <select
            value={doctorId}
            onChange={(e) => {
              setDoctorId(e.target.value);
              setSlots([]);
              setSelectedSlot('');
            }}
          >
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
          <input
            type="date"
            value={date}
            onChange={(e) => {
              setDate(e.target.value);
              setSelectedSlot('');
            }}
          />
        </label>

        {/* REQ-01: slot picker replaces free-form time input */}
        {(doctorId && date) && (
          <div>
            <span style={{ fontSize: '0.9rem', fontWeight: 500, display: 'block', marginBottom: '0.4rem' }}>
              Available time slots
            </span>
            <SlotPicker
              slots={slots}
              selected={selectedSlot}
              onSelect={setSelectedSlot}
              loading={slotsLoading}
              ready={!slotsLoading}
              onJoinWaitlist={handleJoinWaitlist}
              joiningWaitlist={joiningWaitlist}
            />
          </div>
        )}

        <label>
          Reason (optional)
          <textarea rows={3} value={reason} onChange={(e) => setReason(e.target.value)} />
        </label>

        <button
          className="btn btn-primary"
          onClick={handleBook}
          disabled={submitting || !selectedSlot}
        >
          {submitting ? 'Booking…' : 'Book Appointment'}
        </button>
      </div>
    </div>
  );
}
