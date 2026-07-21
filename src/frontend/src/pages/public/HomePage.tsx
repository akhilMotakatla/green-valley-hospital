import { useEffect, useRef, useState, type RefObject } from 'react';
import { useScrollReveal } from '../../hooks/useScrollReveal';
import { Link } from 'react-router-dom';
import {
  Award,
  Microscope,
  Clock,
  Users,
  HeartHandshake,
  ShieldCheck,
  CalendarCheck,
  ClipboardList,
  FlaskConical,
  HeartPulse,
  Star,
  ChevronRight,
  ChevronLeft,
  CalendarPlus,
  Quote,
} from 'lucide-react';
import { getHome } from '../../api/public';
import type { HomeContent, HomeFeaturedDepartment, HomeRecentArticle } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { PageError } from '../../components/PageError';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { MosaicHero } from '../../components/MosaicHero';
import { formatDate } from '../../utils/format';
import { getDeptIcon } from '../../utils/deptIcons';

// ---- Stats ----
const STATS = [
  { value: 15000, suffix: '+', label: 'Patients Served Annually', display: '15,000+' },
  { value: 80, suffix: '+', label: 'Expert Specialists', display: '80+' },
  { value: 25, suffix: '', label: 'Years of Excellence', display: '25' },
  { value: 18, suffix: '', label: 'Medical Departments', display: '18' },
];

// ---- Why Choose Us ----
const WHY_CARDS = [
  { Icon: Award, title: 'JCI Accredited', body: 'Internationally accredited for patient safety and quality standards.' },
  { Icon: Microscope, title: 'Advanced Technology', body: 'State-of-the-art diagnostics and minimally invasive surgical suites.' },
  { Icon: Clock, title: '24/7 Emergency Care', body: 'Round-the-clock emergency services with rapid response teams.' },
  { Icon: Users, title: 'Expert Specialists', body: '80+ board-certified physicians across 18 medical specialties.' },
  { Icon: HeartHandshake, title: 'Patient-First Culture', body: 'Every care decision is guided by your comfort and well-being.' },
  { Icon: ShieldCheck, title: 'Transparent Pricing', body: 'Clear, upfront billing with no hidden charges.' },
];

// ---- Testimonials ----
const TESTIMONIALS = [
  {
    quote: 'The care I received at Green Valley was exceptional. The doctors listened, the nurses were attentive, and I felt safe throughout my recovery.',
    name: 'Sarah Mitchell',
    role: 'Cardiac Care Patient',
    avatar: 'https://randomuser.me/api/portraits/women/52.jpg',
    rating: 5,
  },
  {
    quote: 'From booking to follow-up, everything was seamless. The pediatrics team put my daughter completely at ease. We will always come back here.',
    name: 'James Okonkwo',
    role: 'Pediatrics Patient Parent',
    avatar: 'https://randomuser.me/api/portraits/men/81.jpg',
    rating: 5,
  },
  {
    quote: "Green Valley's orthopedic team got me back on my feet faster than I expected. Their rehabilitation program is truly world-class.",
    name: 'Priya Sharma',
    role: 'Orthopedics Patient',
    avatar: 'https://randomuser.me/api/portraits/women/36.jpg',
    rating: 5,
  },
];

// ---- Care Journey steps ----
const CARE_STEPS = [
  { num: 1, Icon: CalendarCheck, title: 'Book Appointment', desc: 'Choose your specialist and schedule online or by phone.' },
  { num: 2, Icon: ClipboardList, title: 'Consultation', desc: 'Meet your doctor for a thorough evaluation and diagnosis.' },
  { num: 3, Icon: FlaskConical, title: 'Diagnostics', desc: 'Advanced lab and imaging for precise results.' },
  { num: 4, Icon: HeartPulse, title: 'Treatment & Follow-up', desc: 'Personalized treatment plan and ongoing care support.' },
];

// ---- Doctor portraits (randomuser.me cycling table) ----
const DOCTOR_PORTRAITS = [
  'https://randomuser.me/api/portraits/men/32.jpg',
  'https://randomuser.me/api/portraits/men/45.jpg',
  'https://randomuser.me/api/portraits/women/28.jpg',
  'https://randomuser.me/api/portraits/women/44.jpg',
  'https://randomuser.me/api/portraits/men/67.jpg',
  'https://randomuser.me/api/portraits/women/61.jpg',
  'https://randomuser.me/api/portraits/men/12.jpg',
  'https://randomuser.me/api/portraits/women/17.jpg',
];

// ---- Counter animation hook ----
function useCountUp(target: number, duration = 1500) {
  const [count, setCount] = useState(0);
  const animatedRef = useRef(false);
  const rafRef = useRef<number>(0);

  function startAnimation() {
    if (animatedRef.current) return;
    animatedRef.current = true;
    const start = performance.now();
    function frame(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.ceil(eased * target));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(frame);
      }
    }
    rafRef.current = requestAnimationFrame(frame);
  }

  useEffect(() => () => cancelAnimationFrame(rafRef.current), []);
  return { count, startAnimation };
}

// ---- Stats Band ----
function StatsBand() {
  const bandRef = useRef<HTMLDivElement>(null);
  const [triggered, setTriggered] = useState(false);

  useEffect(() => {
    const el = bandRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) { setTriggered(true); obs.disconnect(); }
      },
      { threshold: 0.3 },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div ref={bandRef} className="stats-band-light">
      <div className="container stats-band-grid">
        {STATS.map((s) => (
          <StatItem key={s.label} stat={s} triggered={triggered} />
        ))}
      </div>
    </div>
  );
}

function StatItem({ stat, triggered }: { stat: typeof STATS[0]; triggered: boolean }) {
  const { count, startAnimation } = useCountUp(stat.value);

  useEffect(() => {
    if (triggered) startAnimation();
  }, [triggered]); // eslint-disable-line react-hooks/exhaustive-deps

  const displayCount =
    stat.value === 15000
      ? count >= 15000 ? '15,000' : count.toLocaleString()
      : count.toString();

  return (
    <div className="glass-panel" style={{ textAlign: 'center', padding: '1.75rem 1rem' }}>
      <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--color-primary-dark)', lineHeight: 1, fontFamily: 'var(--font-sans)' }}>
        {triggered ? displayCount + stat.suffix : '0' + stat.suffix}
      </div>
      <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginTop: '0.5rem', fontWeight: 500 }}>
        {stat.label}
      </div>
    </div>
  );
}

// ---- Doctor Avatar ----
function DoctorAvatar({ name, photoPath, doctorId }: { name: string; photoPath: string | null; doctorId: number }) {
  const portraitUrl = DOCTOR_PORTRAITS[doctorId % 4];
  const [primaryErr, setPrimaryErr] = useState(false);
  const [portraitErr, setPortraitErr] = useState(false);
  const initials = name.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase();

  const src = !primaryErr && photoPath ? photoPath : (!portraitErr ? portraitUrl : null);

  if (src) {
    return (
      <div style={{ width: 90, height: 90, borderRadius: '50%', overflow: 'hidden', margin: '0 auto 1rem', border: '3px solid var(--color-primary-light)' }}>
        <img
          src={src}
          alt={name}
          loading="lazy"
          onError={() => {
            if (!primaryErr && photoPath) { setPrimaryErr(true); }
            else { setPortraitErr(true); }
          }}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      </div>
    );
  }

  return (
    <div
      style={{
        width: 90, height: 90, borderRadius: '50%', margin: '0 auto 1rem',
        background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#fff', fontSize: '1.5rem', fontWeight: 700,
        border: '3px solid var(--color-primary-light)',
      }}
    >
      {initials}
    </div>
  );
}

// ---- Testimonial Avatar ----
function TestimonialAvatar({ name, avatar }: { name: string; avatar: string }) {
  const [imgErr, setImgErr] = useState(false);
  const initials = name.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase();

  if (!imgErr) {
    return (
      <img
        src={avatar}
        alt={`${name}, patient`}
        loading="lazy"
        onError={() => setImgErr(true)}
        style={{ width: 56, height: 56, borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--color-primary-light)', flexShrink: 0 }}
      />
    );
  }

  return (
    <div
      style={{
        width: 56, height: 56, borderRadius: '50%', flexShrink: 0,
        background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#fff', fontSize: '1rem', fontWeight: 700,
        border: '2px solid var(--color-primary-light)',
      }}
    >
      {initials}
    </div>
  );
}

// ---- Blog cover image ----
function BlogCoverImage({ index, title }: { index: number; title: string }) {
  const [imgErr, setImgErr] = useState(false);
  const n = (index % 2) + 1;
  const src = `/images/blog-cover-${n}.jpg`;

  if (!imgErr) {
    return (
      <img
        src={src}
        alt={`${title} — health article`}
        loading="lazy"
        onError={() => setImgErr(true)}
        style={{ width: '100%', height: 200, objectFit: 'cover', display: 'block', transition: 'transform 400ms ease' }}
      />
    );
  }

  return (
    <div
      style={{
        width: '100%', height: 200,
        background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
        display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
      }}
    >
      <Microscope size={44} style={{ opacity: 0.5 }} />
    </div>
  );
}

// ---- Dept image ----
function DeptCardImage({ name, deptSlug }: { name: string; deptSlug: string }) {
  const [imgError, setImgError] = useState(false);
  const Icon = getDeptIcon(name);

  if (!imgError) {
    return (
      <img
        src={`/images/dept-${deptSlug}.jpg`}
        alt={`${name} department`}
        loading="lazy"
        onError={() => setImgError(true)}
        className="dept-img-fallback"
        style={{ width: '100%', height: 200, objectFit: 'cover', display: 'block', transition: 'transform 400ms ease' }}
      />
    );
  }

  return (
    <div
      className="dept-img-fallback"
      style={{
        width: '100%', height: 200,
        background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
        display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
        transition: 'transform 400ms ease',
      }}
    >
      <Icon size={60} style={{ opacity: 0.6 }} />
    </div>
  );
}

// ---- Care Journey ----
function CareJourney() {
  return (
    <section style={{ background: 'var(--color-bg)', padding: '5rem 0' }} aria-labelledby="care-journey-heading">
      <div className="container">
        <div className="section-header reveal" style={{ marginBottom: '3rem' }}>
          <div className="section-label">Patient Experience</div>
          <h2 id="care-journey-heading">Your Care Journey</h2>
          <p style={{ color: 'var(--color-text-muted)', maxWidth: 520, margin: '0.75rem auto 0', fontSize: '1.0625rem' }}>
            Simple steps to exceptional care.
          </p>
          <div className="section-underline" style={{ marginTop: '1.25rem' }} />
        </div>

        <div className="care-journey-grid stagger-children">
          {CARE_STEPS.map((step, i) => (
            <div
              key={step.num}
              className="care-step reveal"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div
                style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: 'var(--color-gold)', color: '#fff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.75rem', fontWeight: 800, margin: '0 auto 0.75rem',
                  fontFamily: 'var(--font-sans)',
                }}
              >
                {step.num}
              </div>
              <div
                style={{
                  width: 72, height: 72, borderRadius: '50%',
                  background: 'var(--color-primary-light)', color: 'var(--color-primary)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  margin: '0 auto 1rem',
                }}
              >
                <step.Icon size={40} />
              </div>
              <h3 className="care-step-title">{step.title}</h3>
              <p className="care-step-desc">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---- CTA Banner ----
function CTABanner() {
  return (
    <div className="cta-banner">
      <div className="cta-banner-inner glass-panel">
        <h2 className="reveal" style={{ color: '#fff' }}>Ready to Experience World-Class Care?</h2>
        <p className="reveal" style={{ animationDelay: '150ms' }}>
          Book your appointment today and take the first step toward better health.
        </p>
        <div className="cta-banner-buttons">
          <Link
            to="/signup"
            className="btn btn-pill reveal"
            style={{
              background: 'var(--color-accent)',
              color: '#fff',
              height: 52,
              fontWeight: 700,
              paddingLeft: '2rem',
              paddingRight: '2rem',
              border: 'none',
              animationDelay: '300ms',
            }}
          >
            <CalendarPlus size={18} /> Book an Appointment
          </Link>
        </div>
      </div>
    </div>
  );
}

// ---- Blog Section ----
function RecentBlogSection({ articles }: { articles: HomeRecentArticle[] }) {
  const blogRef = useRef<HTMLElement>(null);
  useScrollReveal(blogRef as RefObject<HTMLElement | null>);

  return (
    <section ref={blogRef} style={{ background: 'var(--color-surface)', padding: '5rem 0' }} aria-labelledby="blog-heading">
      <div className="container">
        <div className="section-header reveal">
          <div className="section-label">Knowledge Hub</div>
          <h2 id="blog-heading">Health Tips &amp; News</h2>
          <p style={{ color: 'var(--color-text-muted)', margin: '0.75rem auto 0', maxWidth: 500 }}>
            Expert advice from our physicians.
          </p>
          <div className="section-underline" style={{ marginTop: '1rem' }} />
        </div>
        <div className="grid-3-up stagger-children">
          {articles.map((a, idx) => (
            <article key={a.article_id}>
              <Link to={`/blog/${a.slug}`} className="reveal" style={{ textDecoration: 'none', display: 'block' }}>
                <div
                  className="card card-hover"
                  style={{ padding: 0, overflow: 'hidden', border: '1px solid var(--color-border)' }}
                >
                  <div style={{ position: 'relative', overflow: 'hidden', borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0' }}>
                    <BlogCoverImage index={idx} title={a.title} />
                    <span className="blog-category-pill">Health Tips</span>
                  </div>
                  <div style={{ padding: '1.375rem' }}>
                    <h3 className="line-clamp-2" style={{ marginBottom: '0.5rem', fontSize: '1rem', lineHeight: 1.4 }}>
                      {a.title}
                    </h3>
                    <p className="line-clamp-3" style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', margin: '0 0 0.875rem', lineHeight: 1.65 }}>
                      {a.summary}
                    </p>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', margin: 0 }}>
                      {a.author_name}
                      {a.published_at ? ` · ${formatDate(a.published_at)}` : ''}
                    </p>
                  </div>
                </div>
              </Link>
            </article>
          ))}
        </div>
        <div style={{ textAlign: 'center', marginTop: '2.5rem' }}>
          <Link to="/blog" className="btn btn-outline btn-pill" style={{ paddingLeft: '2rem', paddingRight: '2rem' }}>
            View All Articles <ChevronRight size={16} />
          </Link>
        </div>
      </div>
    </section>
  );
}

// ---- Main HomePage ----
export function HomePage() {
  const [content, setContent] = useState<HomeContent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [testimonialIndex, setTestimonialIndex] = useState(0);
  const [touchStartX, setTouchStartX] = useState<number | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    getHome()
      .then((c) => { setContent(c); setLoading(false); })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  // Scroll reveal refs
  const whyRef         = useRef<HTMLElement>(null);
  const deptsRef       = useRef<HTMLElement>(null);
  const specialistsRef = useRef<HTMLElement>(null);
  const testimonialsRef = useRef<HTMLElement>(null);
  useScrollReveal(whyRef         as RefObject<HTMLElement | null>, !loading);
  useScrollReveal(deptsRef       as RefObject<HTMLElement | null>, !loading);
  useScrollReveal(specialistsRef as RefObject<HTMLElement | null>, !loading);
  useScrollReveal(testimonialsRef as RefObject<HTMLElement | null>, !loading);

  // Collect doctor cards from featured_departments.first_doctor
  const doctorCards: { dept: HomeFeaturedDepartment; doctor: NonNullable<HomeFeaturedDepartment['first_doctor']> }[] = [];
  if (content) {
    for (const dept of content.featured_departments) {
      if (dept.first_doctor && doctorCards.length < 8) {
        doctorCards.push({ dept, doctor: dept.first_doctor });
      }
    }
  }

  return (
    <div>
      {/* ================================================================
          HERO — masked-card mosaic
          ================================================================ */}
      <MosaicHero />

      {/* ================================================================
          STATS BAND
          ================================================================ */}
      <StatsBand />

      {loading ? (
        <div className="container" style={{ padding: '5rem 1.5rem' }}>
          <SkeletonBlock lines={8} widths={['100%', '100%', '100%', '100%', '100%', '100%', '80%', '60%']} />
        </div>
      ) : error ? (
        <div className="container" style={{ padding: '2rem 1.5rem' }}>
          <PageError message={error} onRetry={load} />
        </div>
      ) : (
        <>
          {/* ==============================================================
              WHY CHOOSE US
              ============================================================== */}
          <section ref={whyRef} style={{ background: 'var(--color-surface)', padding: '5rem 0' }} aria-labelledby="why-heading">
            <div className="container">
              <div className="section-header reveal">
                <div className="section-label">Why Us</div>
                <h2 id="why-heading">Why Choose Us</h2>
                <p style={{ color: 'var(--color-text-muted)', margin: '0.75rem auto 0', maxWidth: 520 }}>
                  Committed to your health with technology and compassion.
                </p>
                <div className="section-underline" style={{ marginTop: '1rem' }} />
              </div>
              <div className="grid-3-up stagger-children">
                {WHY_CARDS.map((card, i) => (
                  <div key={i} className="card-premium card-hover reveal" style={{ padding: '2rem' }}>
                    <div
                      style={{
                        width: 56, height: 56, borderRadius: '50%',
                        background: 'var(--color-primary-light)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        marginBottom: '1.25rem', color: 'var(--color-primary)',
                      }}
                    >
                      <card.Icon size={28} />
                    </div>
                    <h3 style={{ marginBottom: '0.6rem' }}>{card.title}</h3>
                    <p style={{ color: 'var(--color-text-muted)', margin: 0, fontSize: '0.9375rem', lineHeight: 1.7 }}>
                      {card.body}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ==============================================================
              FEATURED DEPARTMENTS
              ============================================================== */}
          {content && content.featured_departments.length > 0 && (
            <section ref={deptsRef} style={{ background: 'var(--color-bg)', padding: '5rem 0' }} aria-labelledby="depts-heading">
              <div className="container">
                <div className="section-header reveal">
                  <div className="section-label">Our Services</div>
                  <h2 id="depts-heading">Our Departments</h2>
                  <p style={{ color: 'var(--color-text-muted)', margin: '0.75rem auto 0', maxWidth: 520 }}>
                    World-class care across 18 specialties.
                  </p>
                  <div className="section-underline" style={{ marginTop: '1rem' }} />
                </div>
                <div className="grid-3-up stagger-children">
                  {content.featured_departments.map((d) => {
                    const slug = d.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
                    return (
                      <Link
                        key={d.department_id}
                        to={`/departments/${d.department_id}`}
                        className="reveal"
                        style={{ textDecoration: 'none' }}
                      >
                        <div
                          className="card card-hover"
                          style={{ padding: 0, overflow: 'hidden', border: '1px solid var(--color-border)' }}
                        >
                          <div className="dept-card-image-wrapper">
                            <DeptCardImage name={d.name} deptSlug={slug} />
                            <span className="dept-badge-pill">{d.name}</span>
                          </div>
                          <div style={{ padding: '1.375rem' }}>
                            <h3 style={{ marginBottom: '0.5rem', fontSize: '1.0625rem' }}>{d.name}</h3>
                            <p className="line-clamp-2" style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', margin: '0 0 0.875rem', lineHeight: 1.65 }}>
                              {d.description ?? 'Specialised care and expert treatment from our dedicated team.'}
                            </p>
                            <span style={{ color: 'var(--color-primary)', fontSize: '0.875rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                              Learn More <ChevronRight size={14} />
                            </span>
                          </div>
                        </div>
                      </Link>
                    );
                  })}
                </div>
              </div>
            </section>
          )}

          {/* ==============================================================
              CARE JOURNEY
              ============================================================== */}
          <CareJourney />

          {/* ==============================================================
              MEET OUR SPECIALISTS
              ============================================================== */}
          {doctorCards.length > 0 && (
            <section ref={specialistsRef} style={{ background: 'var(--color-surface)', padding: '5rem 0' }} aria-labelledby="specialists-heading">
              <div className="container">
                <div className="section-header reveal">
                  <div className="section-label">Our Team</div>
                  <h2 id="specialists-heading">Meet Our Specialists</h2>
                  <p style={{ color: 'var(--color-text-muted)', margin: '0.75rem auto 0', maxWidth: 520 }}>
                    Experienced physicians dedicated to your health.
                  </p>
                  <div className="section-underline" style={{ marginTop: '1rem' }} />
                </div>
                <div className="grid-4-up stagger-children">
                  {doctorCards.map(({ dept, doctor }) => (
                    <div
                      key={doctor.doctor_id}
                      className="card-premium card-hover reveal"
                      style={{ padding: '2rem 1.5rem', textAlign: 'center' }}
                    >
                      <DoctorAvatar name={doctor.full_name} photoPath={doctor.profile_photo_path} doctorId={doctor.doctor_id} />
                      <h3 style={{ fontSize: '1.125rem', marginBottom: '0.25rem', fontWeight: 600 }}>{doctor.full_name}</h3>
                      <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', margin: '0 0 0.5rem' }}>
                        {doctor.specialty}
                      </p>
                      <span
                        style={{
                          display: 'inline-block',
                          background: 'var(--color-primary-light)',
                          color: 'var(--color-primary-dark)',
                          borderRadius: 'var(--radius-pill)',
                          padding: '0.15rem 0.7rem',
                          fontSize: '0.7125rem',
                          fontWeight: 700,
                          marginBottom: '1.25rem',
                        }}
                      >
                        {dept.name}
                      </span>
                      <br />
                      <Link
                        to={`/departments/${dept.department_id}/doctors/${doctor.doctor_id}`}
                        className="btn btn-outline btn-pill"
                        style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}
                      >
                        View Profile →
                      </Link>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* ==============================================================
              TESTIMONIALS
              ============================================================== */}
          <section
            ref={testimonialsRef}
            style={{ background: 'var(--color-surface-alt)', padding: '5rem 0' }}
            role="region"
            aria-label="Patient Testimonials"
            onKeyDown={(e) => {
              if (e.key === 'ArrowLeft') setTestimonialIndex((i) => (i - 1 + TESTIMONIALS.length) % TESTIMONIALS.length);
              if (e.key === 'ArrowRight') setTestimonialIndex((i) => (i + 1) % TESTIMONIALS.length);
            }}
          >
            <div className="container">
              <div className="section-header reveal">
                <div className="section-label">Patient Stories</div>
                <h2>What Our Patients Say</h2>
                <div className="section-underline" style={{ marginTop: '1rem' }} />
              </div>

              {/* Desktop: 3-col grid */}
              <div className="grid-3-up stagger-children" style={{ gap: '1.5rem' }}>
                {TESTIMONIALS.map((t, i) => (
                  <div
                    key={i}
                    className="reveal"
                    style={{
                      background: 'var(--glass-bg)',
                      backdropFilter: 'var(--glass-blur)',
                      WebkitBackdropFilter: 'var(--glass-blur)',
                      border: '1px solid var(--glass-border)',
                      borderRadius: 'var(--radius-xl)',
                      padding: '2rem',
                      boxShadow: 'var(--glass-shadow)',
                    }}
                  >
                    <Quote size={32} color="var(--color-gold)" />
                    <p
                      style={{
                        fontFamily: 'var(--font-serif)',
                        fontStyle: 'italic',
                        fontSize: '1rem',
                        color: 'var(--color-text)',
                        lineHeight: 1.6,
                        margin: '1rem 0',
                        letterSpacing: '0.01em',
                      }}
                    >
                      {t.quote}
                    </p>
                    <div style={{ display: 'flex', gap: 2, marginBottom: '1rem' }}>
                      {Array.from({ length: t.rating }).map((_, s) => (
                        <Star key={s} size={16} fill="var(--color-gold)" color="var(--color-gold)" />
                      ))}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <TestimonialAvatar name={t.name} avatar={t.avatar} />
                      <div>
                        <p style={{ fontWeight: 600, fontSize: '0.9375rem', margin: 0, color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>{t.name}</p>
                        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: 0 }}>{t.role}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Mobile carousel */}
              <div className="testimonial-carousel-mobile">
                <div
                  style={{
                    display: 'flex',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      transform: `translateX(-${testimonialIndex * 100}%)`,
                      transition: 'transform 300ms ease',
                      width: '100%',
                    }}
                  >
                    {TESTIMONIALS.map((t, i) => (
                      <div
                        key={i}
                        style={{
                          minWidth: '100%',
                          background: 'var(--glass-bg)',
                          backdropFilter: 'var(--glass-blur)',
                          WebkitBackdropFilter: 'var(--glass-blur)',
                          border: '1px solid var(--glass-border)',
                          borderRadius: 'var(--radius-xl)',
                          padding: '2rem',
                          boxShadow: 'var(--glass-shadow)',
                        }}
                        onTouchStart={(e) => setTouchStartX(e.touches[0].clientX)}
                        onTouchEnd={(e) => {
                          if (touchStartX === null) return;
                          const delta = e.changedTouches[0].clientX - touchStartX;
                          if (delta < -40) setTestimonialIndex((idx) => (idx + 1) % TESTIMONIALS.length);
                          if (delta > 40) setTestimonialIndex((idx) => (idx - 1 + TESTIMONIALS.length) % TESTIMONIALS.length);
                          setTouchStartX(null);
                        }}
                      >
                        <Quote size={32} color="var(--color-gold)" />
                        <p
                          style={{
                            fontFamily: 'var(--font-serif)',
                            fontStyle: 'italic',
                            fontSize: '1rem',
                            color: 'var(--color-text)',
                            lineHeight: 1.6,
                            margin: '1rem 0',
                          }}
                        >
                          {t.quote}
                        </p>
                        <div style={{ display: 'flex', gap: 2, marginBottom: '1rem' }}>
                          {Array.from({ length: t.rating }).map((_, s) => (
                            <Star key={s} size={16} fill="var(--color-gold)" color="var(--color-gold)" />
                          ))}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <TestimonialAvatar name={t.name} avatar={t.avatar} />
                          <div>
                            <p style={{ fontWeight: 600, fontSize: '0.9375rem', margin: 0, color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>{t.name}</p>
                            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: 0 }}>{t.role}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Carousel nav */}
              <div className="testimonial-carousel-nav">
                <button
                  className="carousel-arrow"
                  onClick={() => setTestimonialIndex((i) => (i - 1 + TESTIMONIALS.length) % TESTIMONIALS.length)}
                  aria-label="Previous testimonial"
                >
                  <ChevronLeft size={18} />
                </button>
                {TESTIMONIALS.map((_, i) => (
                  <button
                    key={i}
                    className={`carousel-dot${i === testimonialIndex ? ' active' : ''}`}
                    onClick={() => setTestimonialIndex(i)}
                    aria-label={`Testimonial ${i + 1}`}
                  />
                ))}
                <button
                  className="carousel-arrow"
                  onClick={() => setTestimonialIndex((i) => (i + 1) % TESTIMONIALS.length)}
                  aria-label="Next testimonial"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>

            <style>{`
              .testimonial-carousel-mobile { display: none; }
              @media (max-width: 639px) {
                .grid-3-up.stagger-children + .testimonial-carousel-mobile { display: block; }
                .testimonial-carousel-mobile { display: block; }
              }
            `}</style>
          </section>

          {/* ==============================================================
              RECENT BLOG POSTS
              ============================================================== */}
          {content && content.recent_articles && content.recent_articles.length > 0 && (
            <RecentBlogSection articles={content.recent_articles} />
          )}
        </>
      )}

      {/* ==============================================================
          CTA BANNER (always shown)
          ============================================================== */}
      <CTABanner />
    </div>
  );
}
