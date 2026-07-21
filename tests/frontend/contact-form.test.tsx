import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ContactPage } from '@/pages/public/ContactPage';
import * as publicApi from '@/api/public';

// Section 6 (VI-CONTACT-4) updated the contact form label format.
// Labels now read "Name *", "Email *", "Subject *", "Message *" (space before asterisk).
// The old regex /name\*/i matched "name*" (no space) and did not match "Name *".
// Updated regexes use /name \*/i (with space) to match the actual rendered labels.

describe('ContactPage form', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(publicApi, 'getContactInfo').mockResolvedValue({
      address: '123 Green Valley Road',
      general_phone: '+1-555-0100',
      emergency_phone: '+1-555-0911',
    });
  });

  it('renders the contact form fields', async () => {
    render(<ContactPage />);
    // Wait for the async getContactInfo() call to settle so the component
    // finishes its initial render before we start querying.
    await waitFor(() => expect(screen.getByLabelText(/name \*/i)).toBeInTheDocument());
    expect(screen.getByLabelText(/email \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/subject \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/message \*/i)).toBeInTheDocument();
  });

  it('submits valid data and shows an on-screen success confirmation', async () => {
    const user = userEvent.setup();
    const submitSpy = vi.spyOn(publicApi, 'submitContactMessage').mockResolvedValue({
      message_id: 1,
      status: 'New',
      created_at: '2026-07-18T00:00:00',
    });

    render(<ContactPage />);

    await waitFor(() => expect(screen.getByLabelText(/name \*/i)).toBeInTheDocument());

    await user.type(screen.getByLabelText(/name \*/i), 'Jane Visitor');
    await user.type(screen.getByLabelText(/email \*/i), 'jane@example.com');
    await user.type(screen.getByLabelText(/subject \*/i), 'General question');
    await user.type(screen.getByLabelText(/message \*/i), 'Hello, I have a question.');

    await user.click(screen.getByRole('button', { name: /send message/i }));

    await waitFor(() =>
      expect(submitSpy).toHaveBeenCalledWith({
        name: 'Jane Visitor',
        email: 'jane@example.com',
        phone: undefined,
        subject: 'General question',
        message: 'Hello, I have a question.',
      }),
    );
    await waitFor(() => expect(screen.getByText(/thank you/i)).toBeInTheDocument());
  });

  it('blocks submission client-side when a required field is missing', async () => {
    const user = userEvent.setup();
    const submitSpy = vi.spyOn(publicApi, 'submitContactMessage').mockResolvedValue({
      message_id: 1,
      status: 'New',
      created_at: '2026-07-18T00:00:00',
    });

    render(<ContactPage />);

    await waitFor(() => expect(screen.getByLabelText(/name \*/i)).toBeInTheDocument());

    // Fill everything except the message field.
    await user.type(screen.getByLabelText(/name \*/i), 'Jane Visitor');
    await user.type(screen.getByLabelText(/email \*/i), 'jane@example.com');
    await user.type(screen.getByLabelText(/subject \*/i), 'General question');
    // message intentionally left blank

    await user.click(screen.getByRole('button', { name: /send message/i }));

    // The frontend handleSubmit guard fires before calling the API.
    expect(submitSpy).not.toHaveBeenCalled();
  });
});
