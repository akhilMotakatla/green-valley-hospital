/**
 * REQ-01 updated: booking form now shows a date picker + SlotPicker when
 * a doctor and date are selected, instead of the free-form datetime-local
 * input. Falls back to a time-only input when no slots are configured for
 * that doctor/date (front-desk override — staff are not bound by slot
 * windows per architecture.md §4.1).
 */
import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import {
  createStaffAppointment,
  listStaffAppointments,
  updateStaffAppointment,
} from '../../api/staff';
import { getStaffDirectory } from '../../api/staff';
import { getAvailableSlots } from '../../api/availability';
import type { DirectoryDoctor } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { StatusBadge } from '../../components/StatusBadge';
import { SlotPicker } from '../../components/SlotPicker';

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

  // Booking form
  const [patientId, setPatientId] = useState('');
  const [doctorId, setDoctorId] = useState('');
  const [date, setDate] = useState('');
  const [slots, setSlots] = useState<string[]>([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState('');
  // Fallback manual time when no slots available
  const [manualTime, setManualTime] = useState('09:00');
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

  // REQ-01: fetch available slots when doctor + date are chosen
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
      .catch(() => {
        // Non-fatal: fall back to manual time input
        setSlots([]);
        setSlotsLoading(false);
      });
  }, [doctorId, date]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setCreateMsg(null);

    if (!date) {
      setCreateMsg('Please select a date.');
      return;
    }

    // If slots are available, require selection from them; otherwise use manual time
    const timeStr = slots.length > 0 ? selectedSlot : manualTime;
    if (!timeStr) {
      setCreateMsg('Please select or enter a time.');
      return;
    }

    try {
      const scheduledAt = `${date}T${timeStr}:00`;
      await createStaffAppointment({
        patient_id: Number(patientId),
        doctor_id: Number(doctorId),
        scheduled_at: scheduledAt,
        reason: reason || undefined,
      });
      setCreateMsg('Appointment created.');
      setPatientId('');
      setDoctorId('');
      setDate('');
      setSlots([]);
      setSelectedSlot('');
      setManualTime('09:00');
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

  const slotsReady = !slotsLoading && !!doctorId && !!date;

  return (
    <div>
      <h1>Appointments (Front Desk)</h1>

      <section className="section card">
        <h2>Book / Reschedule for a Patient</h2>
        {createMsg && (
          <p className={createMsg.includes('created') ? 'success-text' : 'error-text'}>
            {createMsg}
          </p>
        )}
        <form className="form" onSubmit={handleCreate}>
          <label>
            Patient ID
            <input value={patientId} onChange={(e) => setPatientId(e.target.value)} required />
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
              required
            >
              <option value="">Select doctor</option>
              {doctors.map((d) => (
                <option key={d.doctor_id} value={d.doctor_id}>
                  {d.full_name} — {d.specialty}
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
              required
            />
          </label>

          {/* REQ-01: SlotPicker when doctor + date selected */}
          {doctorId && date && (
            <div>
              <span
                style={{ fontSize: '0.9rem', fontWeight: 500, display: 'block', marginBottom: '0.4rem' }}
              >
                {slotsLoading
                  ? 'Loading available slots…'
                  : slots.length > 0
                    ? 'Available time slots'
                    : 'No configured slots — enter time manually'}
              </span>

              {slots.length > 0 ? (
                <SlotPicker
                  slots={slots}
                  selected={selectedSlot}
                  onSelect={setSelectedSlot}
                  loading={slotsLoading}
                  ready={slotsReady}
                />
              ) : (
                !slotsLoading && (
                  /* Front-desk override: free time input when no schedule configured */
                  <input
                    type="time"
                    value={manualTime}
                    onChange={(e) => setManualTime(e.target.value)}
                    required
                    style={{ width: '140px' }}
                  />
                )
              )}
            </div>
          )}

          <label>
            Reason
            <input value={reason} onChange={(e) => setReason(e.target.value)} />
          </label>

          <button
            className="btn btn-primary"
            type="submit"
            disabled={slotsLoading || (slots.length > 0 && !selectedSlot)}
          >
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
                    <button
                      className="btn btn-outline"
                      onClick={() => handleStatusChange(a.appointment_id, 'Completed')}
                    >
                      Complete
                    </button>
                    <button
                      className="btn btn-danger"
                      onClick={() => handleStatusChange(a.appointment_id, 'Cancelled')}
                    >
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
