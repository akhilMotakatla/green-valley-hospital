import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { login as apiLogin } from '../api/auth';
import { getToken, setToken as persistToken } from '../api/client';
import type { JwtClaims, Role } from '../types';

interface AuthUser {
  userId: number;
  role: Role;
  email: string;
  fullName: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function decodeToken(token: string): AuthUser | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1])) as JwtClaims;
    if (payload.exp * 1000 < Date.now()) return null;
    return {
      userId: typeof payload.sub === 'string' ? parseInt(payload.sub, 10) : payload.sub,
      role: payload.role,
      email: payload.email,
      fullName: payload.full_name ?? '',
    };
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const existing = getToken();
    if (existing) {
      const decoded = decodeToken(existing);
      if (decoded) {
        setTokenState(existing);
        setUser(decoded);
      } else {
        persistToken(null);
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await apiLogin(email, password);
    persistToken(res.access_token);
    const decoded = decodeToken(res.access_token);
    const authUser: AuthUser = decoded ?? { userId: res.user_id, role: res.role, email, fullName: '' };
    setTokenState(res.access_token);
    setUser(authUser);
    return authUser;
  }, []);

  const logout = useCallback(() => {
    persistToken(null);
    setTokenState(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: !!user,
      loading,
      login,
      logout,
    }),
    [user, token, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
