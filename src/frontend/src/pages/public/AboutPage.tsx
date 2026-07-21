import { useEffect, useRef, useState, type RefObject } from 'react';
import { useScrollReveal } from '../../hooks/useScrollReveal';
import { Target, Eye, Heart, Award, Users, Building2, UserCheck, Star } from 'lucide-react';
import { getAbout } from '../../api/public';
import type { AboutContent } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { BackToTopButton } from '../../components/BackToTopButton';

// Static stats for the about stats row
const ABOUT_STATS = [
  { icon: <Users size={26} />, value: '15,000+', label: 'Patients Treated' },
  { icon: <UserCheck size={26} />, value: '80+', label: 'Specialist Doctors' },
  { icon: <Award size={26} />, value: '25', label: 'Years of Service' },
  { icon: <Building2 size={26} />, value: '18', label: 'Departments' },
];

// Facility images
const FACILITIES = [
  { file: 'facility-icu.jpg',        label: 'Intensive Care Unit' },
  { file: 'facility-er.jpg',         label: 'Emergency Room' },
  { file: 'facility-lab.jpg',        label: 'Clinical Laboratory' },
  { file: 'facility-maternity.jpg',  label: 'Maternity Ward' },
  { file: 'facility-outpatient.jpg', label: 'Outpatient Centre' },
  { file: 'facility-pharmacy.jpg',   label: 'Hospital Pharmacy' },
];

// Static timeline milestones
const TIMELINE_MILESTONES = [
  { year: '1999', text: 'Green Valley Hospital founded with 50 beds and 3 departments.' },
  { year: '2005', text: 'Expanded to 200 beds; Cardiology and Neurology centers established.' },
  { year: '2012', text: 'Achieved NABH accreditation; opened dedicated Cancer Care wing.' },
  { year: '2019', text: 'Launched 24/7 Emergency & Trauma center; added advanced MRI and CT facilities.' },
];

function FacilityImg({ file, label }: { file: string; label: string }) {
  const [err, setErr] = useState(false);
  if (!err) {
    return (
      <div>
        <div style={{ overflow: 'hidden', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-md)' }}>
          <img
            src={`/images/${file}`}
            alt={label}
            onError={() => setErr(true)}
            style={{ width: '100%', height: 220, objectFit: 'cover', display: 'block', transition: 'transform 300ms ease' }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLImageElement).style.transform = 'scale(1.04)'; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLImageElement).style.transform = ''; }}
          />
        </div>
        <p style={{ textAlign: 'center', fontSize: '0.875rem', color: 'var(--color-text-muted)', marginTop: '0.625rem', fontWeight: 500 }}>
          {label}
        </p>
      </div>
    );
  }
  return (
    <div>
      <div
        style={{
          width: '100%',
          height: 220,
          borderRadius: 'var(--radius-md)',
          background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: '0.875rem',
          fontWeight: 600,
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        {label}
      </div>
      <p style={{ textAlign: 'center', fontSize: '0.875rem', color: 'var(--color-text-muted)', marginTop: '0.625rem', fontWeight: 500 }}>
        {label}
      </p>
    </div>
  );
}

export function AboutPage() {
  const [content, setContent] = useState<AboutContent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [heroBgErr, setHeroBgErr] = useState(false);

  const purposeRef = useRef<HTMLElement>(null);
  const statsRef = useRef<HTMLDivElement>(null);
  const facilitiesRef = useRef<HTMLElement>(null);
  const accreditationsRef = useRef<HTMLElement>(null);
  const historyRef = useRef<HTMLElement>(null);
  useScrollReveal(purposeRef         as RefObject<HTMLElement | null>, !loading);
  useScrollReveal(facilitiesRef      as RefObject<HTMLElement | null>, !loading);
  useScrollReveal(accreditationsRef  as RefObject<HTMLElement | null>, !loading);
  useScrollReveal(historyRef         as RefObject<HTMLElement | null>, !loading);

  const load = () => {
    setLoading(true);
    setError(null);
    getAbout()
      .then((c) => { setContent(c); setLoading(false); })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  // Reveal stats on scroll
  useEffect(() => {
    const el = statsRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        el.querySelectorAll('.reveal').forEach((n) => n.classList.add('visible'));
        obs.disconnect();
      }
    }, { threshold: 0.2 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div>
      {/* ---- Premium page hero ---- */}
      <div
        className="page-hero"
        style={{ minHeight: '62vh', height: 'clamp(420px, 62vh, 680px)' }}
      >
        {!heroBgErr ? (
          <img
            src="/images/about-hero.jpg"
            alt=""
            className="hero-bg"
            onError={() => setHeroBgErr(true)}
          />
        ) : (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: 'linear-gradient(135deg, var(--color-emerald-deep) 0%, var(--color-primary-dark) 50%, var(--color-primary) 100%)',
            }}
          />
        )}
        {/* Dot pattern overlay */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: 'radial-gradient(rgba(255,255,255,0.06) 1px, transparent 1px)',
            backgroundSize: '24px 24px',
          }}
        />
        <div className="hero-overlay" style={{ background: 'linear-gradient(135deg, rgba(6,78,67,0.9) 0%, rgba(9,107,93,0.72) 100%)' }} />
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
            Our Story
          </div>
          <h1>About Green Valley Hospital</h1>
          <p>Serving our community with compassion and excellence since 1999</p>
        </div>
      </div>

      {loading ? (
        <div className="container" style={{ padding: '5rem 1.5rem' }}>
          <SkeletonBlock lines={10} />
        </div>
      ) : error ? (
        <div className="container" style={{ padding: '2rem 1.5rem' }}>
          <PageError message={error} onRetry={load} />
        </div>
      ) : content ? (
        <>
          {/* ---- Stats row ---- */}
          <div
            ref={statsRef}
            style={{
              background: 'linear-gradient(135deg, #02100c 0%, #0a2b24 100%)',
              padding: '4rem 1.5rem',
            }}
          >
            <div
              className="container"
              style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1.5rem' }}
            >
              {ABOUT_STATS.map((s) => (
                <div key={s.label} className="stat-item-glass reveal" style={{ textAlign: 'center' }}>
                  <div style={{ color: 'rgba(255,255,255,0.65)', display: 'flex', justifyContent: 'center', marginBottom: '0.625rem' }}>
                    {s.icon}
                  </div>
                  <div style={{ fontSize: '2.5rem', fontWeight: 800, color: '#fff', lineHeight: 1, fontFamily: "'Inter', sans-serif" }}>
                    {s.value}
                  </div>
                  <div style={{ fontSize: '0.875rem', color: 'rgba(255,255,255,0.65)', marginTop: '0.45rem', fontWeight: 500 }}>
                    {s.label}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ---- Mission / Vision / Values ---- */}
          <section ref={purposeRef} style={{ background: 'var(--color-surface)', padding: '7rem 0' }}>
            <div className="container">
              <div className="section-header reveal">
                <div className="section-label">Our Foundation</div>
                <h2>Our Purpose</h2>
                <div className="section-underline" style={{ marginTop: '1rem' }} />
              </div>
              <div className="grid-3-up stagger-children">
                {[
                  {
                    icon: <Target size={28} />,
                    title: 'Our Mission',
                    body: content.mission,
                    list: null as string[] | null,
                    bg: 'rgba(23,168,146,0.14)',
                    color: '#5fe8cd',
                  },
                  {
                    icon: <Eye size={28} />,
                    title: 'Our Vision',
                    body: 'To be the most trusted healthcare partner in the region, setting the standard for clinical excellence and patient experience.',
                    list: null as string[] | null,
                    bg: 'rgba(94,169,255,0.14)',
                    color: '#8fbfff',
                  },
                  {
                    icon: <Heart size={28} />,
                    title: 'Our Values',
                    body: null as string | null,
                    list: ['Compassion', 'Integrity', 'Excellence', 'Innovation', 'Community'],
                    bg: 'rgba(203,166,104,0.16)',
                    color: 'var(--color-gold)',
                  },
                ].map((card) => (
                  <div key={card.title} className="card-glass reveal" style={{ padding: '2.25rem' }}>
                    <div
                      style={{
                        width: 60,
                        height: 60,
                        borderRadius: '50%',
                        background: card.bg,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginBottom: '1.25rem',
                        color: card.color,
                      }}
                    >
                      {card.icon}
                    </div>
                    <h3 style={{ marginBottom: '0.875rem', fontSize: '1.125rem' }}>{card.title}</h3>
                    {card.body && (
                      <p style={{ color: 'var(--color-text-muted)', margin: 0, lineHeight: 1.75 }}>{card.body}</p>
                    )}
                    {card.list && (
                      <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--color-text-muted)', lineHeight: 2 }}>
                        {card.list.map((item) => <li key={item}>{item}</li>)}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ---- Facility gallery ---- */}
          <section ref={facilitiesRef} style={{ background: 'var(--color-bg)', padding: '7rem 0' }}>
            <div className="container">
              <div className="section-header reveal">
                <div className="section-label">World-Class Infrastructure</div>
                <h2>Our Facilities</h2>
                <div className="section-underline" style={{ marginTop: '1rem' }} />
              </div>
              <div className="grid-3-up stagger-children">
                {FACILITIES.map((f) => (
                  <div key={f.file} className="reveal">
                    <FacilityImg file={f.file} label={f.label} />
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ---- Accreditations ---- */}
          <section ref={accreditationsRef} style={{ background: 'var(--color-surface)', padding: '5rem 0' }}>
            <div className="container">
              <div className="section-header reveal">
                <div className="section-label">Certified Excellence</div>
                <h2>Accreditations</h2>
                <div className="section-underline" style={{ marginTop: '1rem' }} />
              </div>
              <div className="stagger-children" style={{ display: 'flex', flexWrap: 'wrap', gap: '1.25rem', justifyContent: 'center' }}>
                {content.accreditations
                  .split(',')
                  .map((s) => s.trim())
                  .filter(Boolean)
                  .map((acc) => (
                    <div
                      key={acc}
                      className="reveal"
                      style={{
                        minWidth: 150,
                        minHeight: 90,
                        background: 'var(--color-primary-light)',
                        border: '1px solid rgba(14,138,122,0.2)',
                        borderRadius: 'var(--radius-lg)',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.5rem',
                        padding: '1rem 1.25rem',
                        textAlign: 'center',
                        transition: 'transform 200ms ease, box-shadow 200ms ease',
                      }}
                      onMouseEnter={(e) => {
                        const el = e.currentTarget as HTMLElement;
                        el.style.transform = 'translateY(-3px)';
                        el.style.boxShadow = 'var(--shadow-colored)';
                      }}
                      onMouseLeave={(e) => {
                        const el = e.currentTarget as HTMLElement;
                        el.style.transform = '';
                        el.style.boxShadow = '';
                      }}
                    >
                      <Star size={22} fill="var(--color-gold)" color="var(--color-gold)" />
                      <span style={{ fontSize: '0.8125rem', color: 'var(--color-primary-dark)', fontWeight: 700 }}>
                        {acc}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          </section>

          {/* ---- History timeline ---- */}
          <section ref={historyRef} style={{ background: 'var(--color-bg)', padding: '7rem 0' }}>
            <div className="container">
              <div className="section-header reveal">
                <div className="section-label">Our Legacy</div>
                <h2>Our History</h2>
                <div className="section-underline" style={{ marginTop: '1rem' }} />
              </div>
              <Timeline milestones={[...TIMELINE_MILESTONES, { year: 'Today', text: content.history }]} />
            </div>
          </section>
        </>
      ) : null}

      <BackToTopButton />
    </div>
  );
}

function Timeline({ milestones }: { milestones: { year: string; text: string }[] }) {
  return (
    <div style={{ position: 'relative', maxWidth: 800, margin: '0 auto' }}>
      {/* Vertical line */}
      <div
        style={{
          position: 'absolute',
          left: '50%',
          top: 0,
          bottom: 0,
          width: 2,
          background: 'linear-gradient(to bottom, var(--color-primary), var(--color-primary-light))',
          transform: 'translateX(-50%)',
        }}
      />
      {milestones.map((m, i) => {
        const isLeft = i % 2 === 0;
        return (
          <div
            key={m.year}
            style={{
              display: 'flex',
              justifyContent: isLeft ? 'flex-start' : 'flex-end',
              marginBottom: '2.5rem',
              position: 'relative',
            }}
          >
            {/* Year circle */}
            <div
              style={{
                position: 'absolute',
                left: '50%',
                top: '1rem',
                transform: 'translateX(-50%)',
                width: 52,
                height: 52,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.65rem',
                fontWeight: 800,
                zIndex: 1,
                border: '3px solid var(--color-surface)',
                boxShadow: '0 4px 14px rgba(14,138,122,0.3)',
              }}
            >
              {m.year}
            </div>
            {/* Card */}
            <div
              className={`card ${isLeft ? 'reveal-left' : 'reveal-right'}`}
              style={{
                width: 'calc(50% - 44px)',
                padding: '1.375rem',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.9375rem', lineHeight: 1.7 }}>{m.text}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
