import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/auth/AuthContext';
import { LoginPage } from '@/pages/public/LoginPage';
import * as authApi from '@/api/auth';

function renderLoginPage() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/patient" element={<div>Patient Home</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

// Section 6 (VI-AUTH-2) renamed the submit button text from "Login" to "Sign In"
// and added a show/hide password toggle button with aria-label "Show password".
// Tests are updated to reflect the new UI:
//   - Button query uses /sign in/i instead of /login/i
//   - Password input is queried via getByPlaceholderText to avoid ambiguity with
//     the toggle button whose aria-label also contains the word "password".

describe('LoginPage', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('renders email and password fields and a submit button', () => {
    renderLoginPage();
    // Email input is inside an implicit <label>Email</label>
    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument();
    // Password input: use placeholder text to avoid matching the toggle button
    // aria-label "Show password" which also contains the word "password".
    expect(screen.getByPlaceholderText(/your password/i)).toBeInTheDocument();
    // VI-AUTH-2: submit button text is "Sign In" (was "Login" in skeleton)
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('submits credentials and navigates to the role home on success', async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, 'login').mockResolvedValue({
      access_token: 'fake-token',
      token_type: 'bearer',
      expires_in: 3600,
      role: 'Patient',
      user_id: 42,
    });

    renderLoginPage();

    await user.type(screen.getByLabelText(/^email$/i), 'patient@example.com');
    await user.type(screen.getByPlaceholderText(/your password/i), 'Passw0rd1');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(authApi.login).toHaveBeenCalledWith('patient@example.com', 'Passw0rd1'));
    await waitFor(() => expect(screen.getByText('Patient Home')).toBeInTheDocument());
  });

  it('shows an error message when login fails', async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, 'login').mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: 'Invalid email or password' } },
    });

    renderLoginPage();

    await user.type(screen.getByLabelText(/^email$/i), 'wrong@example.com');
    await user.type(screen.getByPlaceholderText(/your password/i), 'wrongpass');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument());
  });
});
