import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BookAppointmentPage } from '@/pages/patient/BookAppointmentPage';
import * as publicApi from '@/api/public';
import * as patientApi from '@/api/patient';

describe('BookAppointmentPage form', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(publicApi, 'getDepartments').mockResolvedValue([
      { department_id: 1, name: 'Cardiology', description: null },
    ]);
    vi.spyOn(patientApi, 'searchDoctors').mockResolvedValue([
      { doctor_id: 7, full_name: 'Dr. Jane Smith', specialty: 'Cardiology', department_name: 'Cardiology', years_experience: 10 },
    ]);
    vi.spyOn(patientApi, 'getDoctorAvailability').mockResolvedValue({
      doctor_id: 7,
      date: '2030-01-01',
      available_slots: ['09:00', '09:30'],
    });
  });

  it('lets a patient select a doctor, date, and slot, then books successfully', async () => {
    const user = userEvent.setup();
    const bookSpy = vi.spyOn(patientApi, 'bookAppointment').mockResolvedValue({
      appointment_id: 99,
      patient_id: 1,
      doctor_id: 7,
      scheduled_at: '2030-01-01T09:00:00',
      status: 'Scheduled',
      reason: null,
      created_at: '2026-07-18T00:00:00',
    });

    render(<BookAppointmentPage />);

    await waitFor(() => expect(screen.getByText(/dr\. jane smith/i)).toBeInTheDocument());

    await user.selectOptions(screen.getByLabelText(/doctor/i), '7');
    await user.type(screen.getByLabelText(/date/i), '2030-01-01');

    await waitFor(() => expect(screen.getByLabelText(/available time slots/i)).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText(/available time slots/i), '09:00');

    await user.click(screen.getByRole('button', { name: /book appointment/i }));

    await waitFor(() =>
      expect(bookSpy).toHaveBeenCalledWith({
        doctor_id: 7,
        scheduled_at: '2030-01-01T09:00:00',
        reason: undefined,
      }),
    );
    await waitFor(() => expect(screen.getByText(/booked successfully/i)).toBeInTheDocument());
  });

  it('shows a validation error when submitting without selecting a slot', async () => {
    const user = userEvent.setup();
    const bookSpy = vi.spyOn(patientApi, 'bookAppointment');

    render(<BookAppointmentPage />);
    await waitFor(() => expect(screen.getByText(/dr\. jane smith/i)).toBeInTheDocument());

    await user.click(screen.getByRole('button', { name: /book appointment/i }));

    expect(screen.getByText(/select a doctor, date, and time slot/i)).toBeInTheDocument();
    expect(bookSpy).not.toHaveBeenCalled();
  });

  it('surfaces a 409 conflict error from the API when the slot is already booked', async () => {
    const user = userEvent.setup();
    vi.spyOn(patientApi, 'bookAppointment').mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: 'This time slot is already booked for the selected doctor' } },
    });

    render(<BookAppointmentPage />);
    await waitFor(() => expect(screen.getByText(/dr\. jane smith/i)).toBeInTheDocument());

    await user.selectOptions(screen.getByLabelText(/doctor/i), '7');
    await user.type(screen.getByLabelText(/date/i), '2030-01-01');
    await waitFor(() => expect(screen.getByLabelText(/available time slots/i)).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText(/available time slots/i), '09:00');
    await user.click(screen.getByRole('button', { name: /book appointment/i }));

    await waitFor(() => expect(screen.getByText(/already booked/i)).toBeInTheDocument());
  });
});
