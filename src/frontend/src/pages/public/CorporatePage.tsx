import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Building2, CheckCircle } from 'lucide-react';
import { getPublicPackages, submitInquiry } from '../../api/corporate';
import type { CorporatePackage } from '../../api/corporate';
import { extractErrorMessage } from '../../api/client';

export function CorporatePage() {
  const [packages, setPackages] = useState<CorporatePackage[]>([]);
  const [pkgLoading, setPkgLoading] = useState(true);

  // Inquiry form
  const [selectedPackageId, setSelectedPackageId] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [contactName, setContactName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [headcount, setHeadcount] = useState('');
  const [preferredSchedule, setPreferredSchedule] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const formRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getPublicPackages()
      .then((pkgs) => { setPackages(pkgs); setPkgLoading(false); })
      .catch(() => setPkgLoading(false));
  }, []);

  async function handleInquiry(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setSubmitError(null);
    try {
      await submitInquiry({
        company_name: companyName,
        contact_name: contactName,
        email,
        phone: phone || undefined,
        estimated_headcount: headcount ? Number(headcount) : undefined,
        package_id: selectedPackageId ? Number(selectedPackageId) : undefined,
        preferred_schedule: preferredSchedule || undefined,
      });
      setSubmitSuccess(true);
    } catch (err) {
      setSubmitError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  function scrollToForm(packageId?: number) {
    if (packageId) setSelectedPackageId(String(packageId));
    formRef.current?.scrollIntoView({ behavior: 'smooth' });
  }

  return (
    <div className="public-page">
      {/* Hero */}
      <section style={{
        background: 'linear-gradient(135deg, var(--color-primary-deeper, #1a3a2a) 0%, var(--color-primary, #2d6a4f) 100%)',
        color: '#fff',
        padding: '5rem 2rem',
        textAlign: 'center',
      }}>
        <Building2 size={56} style={{ marginBottom: '1rem', opacity: 0.9 }} />
        <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>Corporate Health Solutions for Your Team</h1>
        <p style={{ fontSize: '1.2rem', opacity: 0.85, maxWidth: 640, margin: '0 auto 2rem' }}>
          Invest in your employees' wellbeing with our comprehensive corporate health check packages.
          Tailored plans for businesses of all sizes.
        </p>
        <button className="btn btn-primary" style={{ fontSize: '1rem', padding: '0.75rem 2rem' }} onClick={() => scrollToForm()}>
          Get a Quote
        </button>
      </section>

      {/* Packages */}
      <section style={{ maxWidth: 1100, margin: '0 auto', padding: '4rem 2rem' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '2.5rem' }}>Our Health Check Packages</h2>
        {pkgLoading ? (
          <div style={{ display: 'flex', gap: '1rem' }}>
            {[1, 2, 3].map((i) => <div key={i} className="card skeleton" style={{ height: 280, flex: 1 }} />)}
          </div>
        ) : packages.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
            <p>We're preparing our corporate packages. Please contact us directly.</p>
            <a href="/contact" className="btn btn-outline" style={{ marginTop: '1rem' }}>Contact Us</a>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
            {packages.map((pkg) => (
              <div key={pkg.package_id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <span style={{
                    background: 'var(--color-accent, #c9a227)', color: '#fff',
                    padding: '2px 10px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600,
                  }}>Tier {pkg.tier_order}</span>
                  <h3 style={{ marginTop: '0.75rem', marginBottom: '0.5rem' }}>{pkg.name}</h3>
                  <p className="muted" style={{ marginBottom: '1rem' }}>{pkg.description}</p>
                </div>
                <div style={{ flex: 1 }}>
                  <strong style={{ display: 'block', marginBottom: '0.5rem' }}>What's Included:</strong>
                  <ul style={{ paddingLeft: '1.25rem', margin: 0 }}>
                    {pkg.included_services.map((svc, i) => (
                      <li key={i} style={{ marginBottom: '0.25rem' }}>{svc}</li>
                    ))}
                  </ul>
                </div>
                <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '1rem' }}>
                  <p style={{ fontWeight: 600, color: 'var(--color-primary)', marginBottom: '0.75rem' }}>
                    {pkg.price_range_display}
                  </p>
                  <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => scrollToForm(pkg.package_id)}>
                    Inquire Now
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Inquiry Form */}
      <section ref={formRef} style={{ background: 'var(--color-surface, #f8f9fa)', padding: '4rem 2rem' }}>
        <div style={{ maxWidth: 640, margin: '0 auto' }}>
          <h2 style={{ textAlign: 'center', marginBottom: '0.5rem' }}>Request a Quote</h2>
          <p className="muted" style={{ textAlign: 'center', marginBottom: '2rem' }}>
            Fill in the form below and our team will be in touch within 24 hours.
          </p>

          {submitSuccess ? (
            <div className="card" style={{ textAlign: 'center', padding: '3rem', background: '#e6f4ea' }}>
              <CheckCircle size={48} color="#28a745" style={{ marginBottom: '1rem' }} />
              <h3>Thank you!</h3>
              <p>We'll be in touch shortly to discuss your corporate health needs.</p>
            </div>
          ) : (
            <div className="card">
              {submitError && <p style={{ color: 'var(--color-danger)', marginBottom: '1rem' }}>{submitError}</p>}
              <form onSubmit={handleInquiry}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label>Company Name *</label>
                    <input
                      type="text"
                      className="form-control"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Contact Person *</label>
                    <input
                      type="text"
                      className="form-control"
                      value={contactName}
                      onChange={(e) => setContactName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Email *</label>
                    <input
                      type="email"
                      className="form-control"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Phone</label>
                    <input
                      type="tel"
                      className="form-control"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Employee Headcount</label>
                    <input
                      type="number"
                      className="form-control"
                      value={headcount}
                      onChange={(e) => setHeadcount(e.target.value)}
                      min={1}
                    />
                  </div>
                  <div className="form-group">
                    <label>Preferred Package</label>
                    <select
                      className="form-control"
                      value={selectedPackageId}
                      onChange={(e) => setSelectedPackageId(e.target.value)}
                    >
                      <option value="">No preference</option>
                      {packages.map((p) => (
                        <option key={p.package_id} value={p.package_id}>{p.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="form-group" style={{ marginTop: '0.5rem' }}>
                  <label>Preferred Schedule / Timing</label>
                  <textarea
                    className="form-control"
                    rows={3}
                    value={preferredSchedule}
                    onChange={(e) => setPreferredSchedule(e.target.value)}
                    placeholder="e.g. Weekday mornings, Q3 2026..."
                  />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }} disabled={submitting}>
                  {submitting ? 'Submitting...' : 'Submit Inquiry'}
                </button>
              </form>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
