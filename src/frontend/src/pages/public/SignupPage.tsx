import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Mail, Lock, Phone, Calendar, Eye, EyeOff, Info } from 'lucide-react';
import { signup } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { Logo } from '../../components/Logo';

const PASSWORD_HINT = 'At least 8 characters, with at least one letter and one number.';

function isPasswordValid(password: string): boolean {
  return password.length >= 8 && /[A-Za-z]/.test(password) && /[0-9]/.test(password);
}

export function SignupPage() {
  const navigate = useNavigate();
  const [fullName, setFullName]             = useState('');
  const [email, setEmail]                   = useState('');
  const [password, setPassword]             = useState('');
  const [showPassword, setShowPassword]     = useState(false);
  const [phone, setPhone]                   = useState('');
  const [dob, setDob]                       = useState('');
  const [error, setError]                   = useState<string | null>(null);
  const [submitting, setSubmitting]         = useState(false);
  const [panelImgErr, setPanelImgErr]       = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!isPasswordValid(password)) {
      setError(`Invalid password. ${PASSWORD_HINT}`);
      return;
    }
    setSubmitting(true);
    try {
      await signup({ email, password, full_name: fullName, phone, date_of_birth: dob });
      navigate('/login', { state: { justSignedUp: true } });
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-split">
      {/* ---- Left panel ---- */}
      <div className="auth-panel-left">
        {!panelImgErr ? (
          <img
            src="/images/auth-panel.jpg"
            alt=""
            onError={() => setPanelImgErr(true)}
            style={{ objectFit: 'cover', width: '100%', height: '100%' }}
          />
        ) : null}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: panelImgErr
              ? 'linear-gradient(160deg, #064e43 0%, #096b5d 40%, #0e8a7a 100%)'
              : 'linear-gradient(160deg, rgba(6,78,67,0.92) 0%, rgba(9,107,93,0.78) 50%, rgba(14,138,122,0.6) 100%)',
          }}
        />
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
            Health is not just about what you&apos;re eating. It&apos;s also about what you&apos;re thinking and saying.
          </p>
          <p className="auth-panel-quote-author">— Anonymous</p>
        </div>
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
          {/* Mobile logo */}
          <div style={{ marginBottom: '1.5rem', display: 'none' }} className="auth-mobile-logo">
            <Logo variant="default" size={32} />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <div className="section-label" style={{ marginBottom: '0.75rem' }}>New Patient</div>
            <h1 style={{ marginBottom: '0.375rem', fontSize: '2rem' }}>Create Your Account</h1>
            <p style={{ color: 'var(--color-text-muted)', margin: 0, fontSize: '0.9375rem', lineHeight: 1.6 }}>
              Register to book appointments and access your health records.
            </p>
          </div>

          {/* Patient-only info banner */}
          <div
            style={{
              background: 'var(--color-primary-light)',
              border: '1px solid rgba(14,138,122,0.2)',
              borderRadius: 'var(--radius-md)',
              padding: '0.875rem 1rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.625rem',
              marginBottom: '1.5rem',
              fontSize: '0.875rem',
              color: 'var(--color-primary-dark)',
            }}
          >
            <Info size={16} style={{ flexShrink: 0, marginTop: '0.1rem' }} />
            <span>
              Patient registration only. Doctor, staff, and admin accounts are created by hospital administration.
            </span>
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

          <form className="form" onSubmit={handleSubmit} style={{ gap: '1.25rem' }}>
            <label>
              Full Name
              <div className="input-icon-wrapper">
                <span className="input-icon-left"><User size={18} /></span>
                <input value={fullName} onChange={(e) => setFullName(e.target.value)} required placeholder="Your full name" />
              </div>
            </label>

            <label>
              Email Address
              <div className="input-icon-wrapper">
                <span className="input-icon-left"><Mail size={18} /></span>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@example.com" />
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
                  placeholder="Min 8 chars, letter + number"
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
              <span className="muted text-sm">{PASSWORD_HINT}</span>
            </label>

            <div className="form-row" style={{ flexWrap: 'wrap' }}>
              <label>
                Phone Number
                <div className="input-icon-wrapper">
                  <span className="input-icon-left"><Phone size={18} /></span>
                  <input value={phone} onChange={(e) => setPhone(e.target.value)} required placeholder="+1 (555) 000-0000" />
                </div>
              </label>

              <label>
                Date of Birth
                <div className="input-icon-wrapper">
                  <span className="input-icon-left"><Calendar size={18} /></span>
                  <input type="date" value={dob} onChange={(e) => setDob(e.target.value)} required />
                </div>
              </label>
            </div>

            <button
              className="btn btn-gradient btn-pill"
              type="submit"
              disabled={submitting}
              style={{ width: '100%', height: 52, justifyContent: 'center', marginTop: '0.25rem', fontSize: '1rem' }}
            >
              {submitting ? 'Creating account…' : 'Create Account'}
            </button>
          </form>

          <p style={{ marginTop: '1.5rem', color: 'var(--color-text-muted)', fontSize: '0.9375rem', textAlign: 'center' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
              Log in
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
        @media (max-width: 480px) {
          .form-row { flex-direction: column !important; }
        }
      `}</style>
    </div>
  );
}
