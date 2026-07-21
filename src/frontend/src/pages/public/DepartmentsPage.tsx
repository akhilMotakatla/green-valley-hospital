import { useEffect, useRef, useState, type RefObject } from 'react';
import { Link } from 'react-router-dom';
import { Search, ChevronRight } from 'lucide-react';
import { getDepartments } from '../../api/public';
import type { Department } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { getDeptIcon } from '../../utils/deptIcons';
import { useScrollReveal } from '../../hooks/useScrollReveal';

function DeptCardImage({ name, slug }: { name: string; slug: string }) {
  const [imgErr, setImgErr] = useState(false);
  const Icon = getDeptIcon(name);

  if (!imgErr) {
    return (
      <img
        src={`/images/dept-${slug}.jpg`}
        alt={`${name} department`}
        loading="lazy"
        onError={() => setImgErr(true)}
        style={{
          width: '100%',
          height: 200,
          objectFit: 'cover',
          borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0',
          display: 'block',
          transition: 'transform 400ms ease',
        }}
      />
    );
  }

  return (
    <div
      style={{
        width: '100%',
        height: 200,
        borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0',
        background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        transition: 'transform 400ms ease',
      }}
    >
      <Icon size={60} style={{ opacity: 0.6 }} />
    </div>
  );
}

export function DepartmentsPage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [heroBgErr, setHeroBgErr] = useState(false);
  const deptsRef = useRef<HTMLDivElement>(null);
  useScrollReveal(deptsRef as RefObject<HTMLElement | null>, !loading);

  const load = () => {
    setLoading(true);
    setError(null);
    getDepartments()
      .then((d) => { setDepartments(d); setLoading(false); })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  const q = query.toLowerCase();
  const filtered = departments.filter(
    (d) =>
      d.name.toLowerCase().includes(q) ||
      (d.description ?? '').toLowerCase().includes(q),
  );

  return (
    <div>
      {/* Page hero */}
      <div className="page-hero" style={{ height: 'clamp(360px, 46vh, 520px)' }}>
        {!heroBgErr ? (
          <img
            src="/images/departments-hero.jpg"
            alt=""
            className="hero-bg"
            onError={() => setHeroBgErr(true)}
          />
        ) : (
          <div style={{ position: 'absolute', inset: 0, background: 'var(--color-primary-dark)' }} />
        )}
        <div className="hero-overlay" style={{ background: 'rgba(9,107,93,0.78)' }} />
        <div className="hero-content">
          <h1>Our Departments &amp; Specialties</h1>
          <p>World-class care across 18 specialties</p>
        </div>
      </div>

      <div className="container" style={{ padding: '3rem 1.5rem' }}>
        {/* Search */}
        <div style={{ marginBottom: '2rem' }}>
          <div className="input-icon-wrapper" style={{ maxWidth: 420 }}>
            <span className="input-icon-left"><Search size={18} /></span>
            <input
              type="search"
              placeholder="Search departments…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </div>

        {loading ? (
          <SkeletonBlock lines={6} />
        ) : error ? (
          <PageError message={error} onRetry={load} />
        ) : (
          <>
            {filtered.length === 0 ? (
              <p className="muted">No departments match your search.</p>
            ) : (
              <div ref={deptsRef} className="grid-3-up stagger-children">
                {filtered.map((d) => {
                  const slug = d.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
                  const Icon = getDeptIcon(d.name);
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
                          <DeptCardImage name={d.name} slug={slug} />
                        </div>
                        <div style={{ padding: '1.25rem' }}>
                          <div
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.5rem',
                              marginBottom: '0.5rem',
                              color: 'var(--color-primary)',
                            }}
                          >
                            <Icon size={20} />
                            <h3 style={{ margin: 0 }}>{d.name}</h3>
                          </div>
                          <p
                            className="line-clamp-2"
                            style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', margin: '0 0 1rem' }}
                          >
                            {d.description ?? 'Specialised care and expert treatment.'}
                          </p>
                          <button className="btn btn-outline btn-sm" style={{ width: '100%', justifyContent: 'center' }}>
                            View Doctors <ChevronRight size={14} />
                          </button>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
