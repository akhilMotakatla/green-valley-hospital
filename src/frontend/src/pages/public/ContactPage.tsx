import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { MapPin, Phone, PhoneCall, Mail, Send, CheckCircle, User, AtSign, Clock } from 'lucide-react';
import { getContactInfo, submitContactMessage } from '../../api/public';
import type { ContactInfo } from '../../types';
import { extractErrorMessage } from '../../api/client';

function MapPlaceholder() {
  const [imgErr, setImgErr] = useState(false);
  return (
    <div style={{ position: 'relative', height: 240, borderRadius: 'var(--radius-lg)', overflow: 'hidden', border: '1px solid var(--color-border)', boxShadow: 'var(--shadow-sm)' }}>
      {!imgErr ? (
        <img
          src="/images/map-placeholder.jpg"
          alt=""
          onError={() => setImgErr(true)}
          style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
        />
      ) : (
        <div style={{ width: '100%', height: '100%', background: 'linear-gradient(135deg, var(--color-primary-light), var(--color-surface-alt))', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '0.75rem' }}>
          <MapPin size={44} color="var(--color-primary)" />
          <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', fontWeight: 500 }}>
            Green Valley Hospital
          </span>
        </div>
      )}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          background: 'linear-gradient(to top, rgba(6,78,67,0.85) 0%, transparent 100%)',
          color: '#fff',
          fontSize: '0.8125rem',
          padding: '1rem 0.875rem 0.625rem',
          fontWeight: 500,
        }}
      >
        Green Valley Hospital — 123 Green Valley Drive
      </div>
    </div>
  );
}

const WORKING_HOURS = [
  { days: 'Monday – Friday',   hours: '8:00 AM – 8:00 PM' },
  { days: 'Saturday',          hours: '9:00 AM – 5:00 PM' },
  { days: 'Sunday',            hours: '10:00 AM – 3:00 PM' },
  { days: 'Emergency (24/7)',  hours: 'Always Open', highlight: true },
];

export function ContactPage() {
  const [info, setInfo]       = useState<ContactInfo | null>(null);
  const [name, setName]       = useState('');
  const [email, setEmail]     = useState('');
  const [phone, setPhone]     = useState('');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError]     = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [heroBgErr, setHeroBgErr]   = useState(false);

  useEffect(() => {
    getContactInfo().then(setInfo).catch(() => undefined);
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!name || !email || !subject || !message) {
      setError('Please fill in all required fields.');
      return;
    }
    setSubmitting(true);
    try {
      await submitContactMessage({ name, email, phone: phone || undefined, subject, message });
      setSuccess(true);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  const address   = info?.address       ?? '123 Green Valley Drive, Medical District, City, State 00000';
  const genPhone  = info?.general_phone ?? '+1 (555) 000-1234';
  const emerPhone = info?.emergency_phone ?? '+1 (555) 000-9999';

  const infoRows = [
    { icon: <MapPin size={20} />,    label: 'Address',       value: address,   accent: false, color: '#0e8a7a' },
    { icon: <Phone size={20} />,     label: 'General Phone', value: genPhone,  accent: false, color: '#1d4ed8' },
    { icon: <PhoneCall size={20} />, label: 'Emergency',     value: emerPhone, accent: true,  color: '#e05c2a' },
    { icon: <Mail size={20} />,      label: 'Email',         value: 'info@greenvalleyhospital.demo', accent: false, color: '#7c3aed' },
  ];

  return (
    <div>
      {/* ---- Page hero ---- */}
      <div className="page-hero" style={{ minHeight: 'clamp(340px, 48vh, 520px)' }}>
        {!heroBgErr ? (
          <img src="/images/contact-hero.jpg" alt="" className="hero-bg" onError={() => setHeroBgErr(true)} />
        ) : (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: 'linear-gradient(135deg, var(--color-emerald-deep) 0%, var(--color-primary-dark) 100%)',
            }}
          />
        )}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: 'radial-gradient(rgba(255,255,255,0.06) 1px, transparent 1px)',
            backgroundSize: '24px 24px',
          }}
        />
        <div className="hero-overlay" style={{ background: 'linear-gradient(135deg, rgba(6,78,67,0.9) 0%, rgba(9,107,93,0.75) 100%)' }} />
        <div className="hero-content">
          <div
            style={{
              display: 'inline-block',
              background: 'rgba(201,168,76,0.18)',
              border: '1px solid rgba(201,168,76,0.35)',
              color: '#f4d578',
              borderRadius: '999px',
              padding: '0.3rem 1rem',
              fontSize: '0.75rem',
              fontWeight: 700,
              letterSpacing: '0.07em',
              textTransform: 'uppercase',
              marginBottom: '1rem',
            }}
          >
            Get In Touch
          </div>
          <h1>Contact Us</h1>
          <p>We&apos;re here to help — reach out today and our team will respond promptly</p>
        </div>
      </div>

      <div className="container" style={{ padding: '5rem 1.5rem' }}>
        <div
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3rem', alignItems: 'start' }}
          className="contact-grid"
        >
          {/* ---- Left — Info + map + hours ---- */}
          <div>
            <div style={{ marginBottom: '0.5rem' }}>
              <div className="section-label" style={{ marginBottom: '0.75rem' }}>Our Location</div>
              <h2 style={{ marginBottom: '1.75rem' }}>Get in Touch</h2>
            </div>

            {/* Contact info rows */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.375rem', marginBottom: '2rem' }}>
              {infoRows.map((row) => (
                <div key={row.label} style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
                  <div
                    style={{
                      width: 52,
                      height: 52,
                      borderRadius: '50%',
                      background: row.accent ? 'var(--color-accent-light)' : 'var(--color-primary-light)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: row.color,
                      flexShrink: 0,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                    }}
                  >
                    {row.icon}
                  </div>
                  <div>
                    <p style={{ fontWeight: 700, margin: '0 0 0.2rem', fontSize: '0.8125rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {row.label}
                    </p>
                    <p
                      style={{
                        margin: 0,
                        color: row.accent ? 'var(--color-accent)' : 'var(--color-text)',
                        fontWeight: row.accent ? 700 : 400,
                        fontSize: '0.9375rem',
                      }}
                    >
                      {row.value}
                      {row.accent && (
                        <span
                          style={{
                            marginLeft: '0.5rem',
                            background: 'var(--color-accent-light)',
                            color: 'var(--color-accent)',
                            borderRadius: 999,
                            padding: '0.1rem 0.55rem',
                            fontSize: '0.7rem',
                            fontWeight: 700,
                          }}
                        >
                          24/7 Emergency
                        </span>
                      )}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Map */}
            <div style={{ marginBottom: '2rem' }}>
              <MapPlaceholder />
            </div>

            {/* Working hours card */}
            <div
              className="card"
              style={{ padding: '1.5rem', border: '1px solid var(--color-border)', background: 'var(--color-surface-alt)' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <Clock size={18} color="var(--color-primary)" />
                <h3 style={{ margin: 0 }}>Working Hours</h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
                {WORKING_HOURS.map((wh) => (
                  <div
                    key={wh.days}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: '0.875rem',
                      padding: wh.highlight ? '0.375rem 0.75rem' : '0',
                      borderRadius: wh.highlight ? 'var(--radius-sm)' : 0,
                      background: wh.highlight ? 'var(--color-accent-light)' : 'transparent',
                      color: wh.highlight ? 'var(--color-accent)' : 'var(--color-text)',
                      fontWeight: wh.highlight ? 700 : 400,
                    }}
                  >
                    <span>{wh.days}</span>
                    <span>{wh.hours}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ---- Right — Form ---- */}
          <div>
            <div
              className="card"
              style={{ padding: '2.5rem', boxShadow: 'var(--shadow-xl)', border: '1px solid var(--color-border)' }}
            >
              {success ? (
                <div style={{ textAlign: 'center', padding: '3rem 0' }}>
                  <div
                    style={{
                      width: 72, height: 72, borderRadius: '50%',
                      background: 'rgba(30,142,90,0.18)', display: 'flex',
                      alignItems: 'center', justifyContent: 'center',
                      margin: '0 auto 1.25rem',
                      border: '1px solid rgba(30,142,90,0.35)',
                    }}
                  >
                    <CheckCircle size={36} color="#4ade80" />
                  </div>
                  <h2 style={{ marginBottom: '0.75rem' }}>Message Sent!</h2>
                  <p style={{ color: 'var(--color-text-muted)', fontSize: '1.0625rem', lineHeight: 1.65 }}>
                    Thank you — your message has been received. We&apos;ll be in touch within 24 hours.
                  </p>
                </div>
              ) : (
                <>
                  <div style={{ marginBottom: '2rem' }}>
                    <div className="section-label" style={{ marginBottom: '0.75rem' }}>Say Hello</div>
                    <h2 style={{ marginBottom: '0.25rem' }}>Send us a Message</h2>
                    <p style={{ color: 'var(--color-text-muted)', margin: 0 }}>
                      Fill in the form below and we&apos;ll get back to you shortly.
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
                    <div className="form-row" style={{ flexWrap: 'wrap' }}>
                      <label>
                        Name *
                        <div className="input-icon-wrapper">
                          <span className="input-icon-left"><User size={18} /></span>
                          <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Your full name" />
                        </div>
                      </label>
                      <label>
                        Email *
                        <div className="input-icon-wrapper">
                          <span className="input-icon-left"><AtSign size={18} /></span>
                          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@example.com" />
                        </div>
                      </label>
                    </div>
                    <label>
                      Phone (optional)
                      <div className="input-icon-wrapper">
                        <span className="input-icon-left"><Phone size={18} /></span>
                        <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+1 (555) 000-0000" />
                      </div>
                    </label>
                    <label>
                      Subject *
                      <input value={subject} onChange={(e) => setSubject(e.target.value)} required placeholder="How can we help?" />
                    </label>
                    <label>
                      Message *
                      <textarea
                        rows={5}
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        required
                        placeholder="Tell us more about how we can assist you…"
                        style={{ height: 'auto' }}
                      />
                    </label>
                    <button
                      className="btn btn-gradient btn-pill"
                      type="submit"
                      disabled={submitting}
                      style={{ width: '100%', height: 52, justifyContent: 'center', gap: '0.5rem', fontSize: '1rem' }}
                    >
                      {submitting ? 'Sending…' : <><Send size={18} /> Send Message</>}
                    </button>
                  </form>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 1023px) {
          .contact-grid { grid-template-columns: 1fr !important; }
        }
        @media (max-width: 639px) {
          .form-row { flex-direction: column !important; }
        }
      `}</style>
    </div>
  );
}
