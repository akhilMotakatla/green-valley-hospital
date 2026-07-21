import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/auth/AuthContext';
import { RequireAuth } from '@/auth/RequireAuth';
import { setToken } from '@/api/client';
import { makeValidToken, makeFakeJwt } from './helpers/fakeJwt';

function renderGuarded(initialPath: string, roles: Array<'Admin' | 'Doctor' | 'Patient' | 'Staff' | 'Lab'>) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <Routes>
          <Route
            path="/protected"
            element={
              <RequireAuth roles={roles}>
                <div>Secret Content</div>
              </RequireAuth>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/unauthorized" element={<div>Unauthorized Page</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe('RequireAuth route guard', () => {
  beforeEach(() => {
    setToken(null);
  });

  it('redirects an unauthenticated visitor to /login', async () => {
    renderGuarded('/protected', ['Admin']);
    await waitFor(() => expect(screen.getByText('Login Page')).toBeInTheDocument());
    expect(screen.queryByText('Secret Content')).not.toBeInTheDocument();
  });

  it('redirects a wrong-role user to /unauthorized', async () => {
    setToken(makeValidToken({ role: 'Patient' }));
    renderGuarded('/protected', ['Admin']);
    await waitFor(() => expect(screen.getByText('Unauthorized Page')).toBeInTheDocument());
    expect(screen.queryByText('Secret Content')).not.toBeInTheDocument();
  });

  it('renders protected content for a matching role', async () => {
    setToken(makeValidToken({ role: 'Admin' }));
    renderGuarded('/protected', ['Admin']);
    await waitFor(() => expect(screen.getByText('Secret Content')).toBeInTheDocument());
  });

  it('treats an expired token as unauthenticated and redirects to /login', async () => {
    const expiredPayload = {
      sub: '1',
      role: 'Patient',
      email: 'user@example.com',
      iat: 0,
      exp: 1, // long expired
    };
    // Build directly since makeValidToken always issues a fresh exp.
    setToken(makeFakeJwt(expiredPayload));
    renderGuarded('/protected', ['Patient']);
    await waitFor(() => expect(screen.getByText('Login Page')).toBeInTheDocument());
  });
});
