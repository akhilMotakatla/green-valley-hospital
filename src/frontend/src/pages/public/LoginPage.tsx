import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { extractErrorMessage } from '../../api/client';
import { Logo } from '../../components/Logo';
import type { Role } from '../../types';

const roleHome: Record<Role, string> = {
  Admin: '/admin',
  Doctor: '/doctor',
  Patient: '/patient',
  Staff: '/staff',
  Lab: '/lab',
  BillingSpecialist: '/billing/dashboard',
};

export function LoginPage() {
  const { login } = useAuth();
  const navigate  = useNavigate();
  const location  = useLocation();
  const [email, setEmail]               = useState('');
  const [password, setPassword]         = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError]               = useState<string | null>(null);
  const [submitting, setSubmitting]     = useState(false);
  const [panelImgErr, setPanelImgErr]   = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const user = await login(email, password);
      const from = (location.state as { from?: { pathname?: string } } | null)?.from;
      navigate(from?.pathname ?? roleHome[user.role] ?? '/', { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-split">
      {/* ---- Left panel — rich gradient + quote ---- */}
      <div className="auth-panel-left">
        {!panelImgErr ? (
          <img
            src="/images/auth-panel.jpg"
            alt=""
            onError={() => setPanelImgErr(true)}
            style={{ objectFit: 'cover', width: '100%', height: '100%' }}
          />
        ) : null}
        {/* Deep gradient overlay */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: panelImgErr
              ? 'linear-gradient(160deg, #064e43 0%, #096b5d 40%, #0e8a7a 100%)'
              : 'linear-gradient(160deg, rgba(6,78,67,0.92) 0%, rgba(9,107,93,0.78) 50%, rgba(14,138,122,0.6) 100%)',
          }}
        />
        {/* Dot pattern */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: 'radial-gradient(rgba(255,255,255,0.07) 1px, transparent 1px)',
            backgroundSize: '22px 22px',
          }}
        />
        {/* Quote */}
        <div className="auth-panel-quote">
          <span className="auth-panel-quote-mark">&ldquo;</span>
          <p className="auth-panel-quote-text">
            The art of medicine consists of amusing the patient while nature cures the disease.
          </p>
          <p className="auth-panel-quote-author">— Voltaire</p>
        </div>
        {/* Bottom branding */}
        <div
          style={{
            position: 'absolute',
            bottom: '2rem',
            left: '2.5rem',
            right: '2.5rem',
            zIndex: 2,
          }}
        >
          <Logo variant="white" size={36} />
          <p style={{ color: 'rgba(255,255,255,0.72)', marginTop: '0.5rem', fontSize: '0.875rem' }}>
            Compassionate care, every day.
          </p>
        </div>
      </div>

      {/* ---- Right panel — form ---- */}
      <div className="auth-panel-right">
        <div className="auth-form-container">
          {/* Mobile-only logo */}
          <div style={{ marginBottom: '1.5rem', display: 'none' }} className="auth-mobile-logo">
            <Logo variant="default" size={32} />
          </div>

          {/* Header */}
          <div style={{ marginBottom: '2rem' }}>
            <div className="section-label" style={{ marginBottom: '0.75rem' }}>Patient Portal</div>
            <h1 style={{ marginBottom: '0.375rem', fontSize: '2rem' }}>Welcome Back</h1>
            <p style={{ color: 'var(--color-text-muted)', margin: 0, fontSize: '1rem', lineHeight: 1.6 }}>
              Log in to your Green Valley account to manage your appointments and records.
            </p>
          </div>

          {error && (
            <div
              style={{
                background: 'rgba(224,73,58,0.14)',
                border: '1px solid rgba(224,73,58,0.35)',
                borderRadius: 'var(--radius-md)',
                padding: '0.75rem 1rem',
                marginBottom: '1.25rem',
              }}
            >
              <p className="error-text" style={{ margin: 0, color: '#ff8a7a' }}>{error}</p>
            </div>
          )}

          <form className="form" onSubmit={handleSubmit} style={{ gap: '1.375rem' }}>
            <label>
              Email Address
              <div className="input-icon-wrapper">
                <span className="input-icon-left"><Mail size={18} /></span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="you@example.com"
                />
              </div>
            </label>

            <label>
              Password
              <div className="input-icon-wrapper">
                <span className="input-icon-left"><Lock size={18} /></span>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="Your password"
                  className="with-right-icon"
                />
                <button
                  type="button"
                  className="input-icon-right"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </label>

            <button
              className="btn btn-gradient btn-pill"
              type="submit"
              disabled={submitting}
              style={{ width: '100%', height: 52, justifyContent: 'center', marginTop: '0.25rem', fontSize: '1rem' }}
            >
              {submitting ? 'Signing in…' : 'Sign In'}
            </button>
          </form>

          <p style={{ marginTop: '1.5rem', color: 'var(--color-text-muted)', fontSize: '0.9375rem', textAlign: 'center' }}>
            New patient?{' '}
            <Link to="/signup" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
              Create an account
            </Link>
          </p>

          <p style={{ marginTop: '0.75rem', color: 'var(--color-text-muted)', fontSize: '0.875rem', textAlign: 'center' }}>
            <Link to="/" style={{ color: 'var(--color-text-muted)' }}>
              ← Back to Home
            </Link>
          </p>
        </div>
      </div>

      <style>{`
        @media (max-width: 767px) {
          .auth-mobile-logo { display: block !important; }
        }
      `}</style>
    </div>
  );
}
