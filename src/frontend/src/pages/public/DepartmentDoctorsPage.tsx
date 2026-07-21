import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Clock } from 'lucide-react';
import { getDepartmentDoctors } from '../../api/public';
import type { PublicDoctorListing } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { BackToTopButton } from '../../components/BackToTopButton';

function DoctorPhoto({ name, photoPath }: { name: string; photoPath: string | null }) {
  const [imgErr, setImgErr] = useState(false);

  const initials = name
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  if (!imgErr && photoPath) {
    return (
      <img
        src={photoPath}
        alt={name}
        onError={() => setImgErr(true)}
        style={{
          width: 90,
          height: 90,
          borderRadius: '50%',
          objectFit: 'cover',
          display: 'block',
          margin: '0 auto 0.75rem',
        }}
      />
    );
  }

  return (
    <div
      style={{
        width: 90,
        height: 90,
        borderRadius: '50%',
        background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '0 auto 0.75rem',
        color: '#fff',
        fontSize: '1.25rem',
        fontWeight: 700,
      }}
    >
      {initials}
    </div>
  );
}

export function DepartmentDoctorsPage() {
  const { id } = useParams();
  const [doctors, setDoctors] = useState<PublicDoctorListing[]>([]);
  const [deptName, setDeptName] = useState('');
  const [deptSlug, setDeptSlug] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [heroBgErr, setHeroBgErr] = useState(false);

  const load = () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    getDepartmentDoctors(id)
      .then((res) => {
        setDoctors(res.items);
        setDeptName(res.department.name);
        const slug = res.department.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
        setDeptSlug(slug);
        setLoading(false);
      })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  };

  useEffect(() => { load(); }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      {/* Department header banner */}
      <div className="page-hero" style={{ height: 280 }}>
        {!heroBgErr ? (
          <img
            src={deptSlug ? `/images/dept-${deptSlug}.jpg` : '/images/departments-hero.jpg'}
            alt=""
            className="hero-bg"
            onError={() => setHeroBgErr(true)}
          />
        ) : (
          <div style={{ position: 'absolute', inset: 0, background: 'var(--color-primary-dark)' }} />
        )}
        <div className="hero-overlay" style={{ background: 'rgba(9,107,93,0.78)' }} />
        <div className="hero-content">
          <h1>{deptName || 'Department'}</h1>
          <p>Meet our specialists</p>
        </div>
      </div>

      <div className="container" style={{ padding: '3rem 1.5rem' }}>
        <p style={{ marginBottom: '1.5rem' }}>
          <Link to="/departments" style={{ color: 'var(--color-primary)' }}>
            &larr; All departments
          </Link>
        </p>

        {loading ? (
          <SkeletonBlock lines={6} />
        ) : error ? (
          <PageError message={error} onRetry={load} />
        ) : (
          <>
            {doctors.length === 0 ? (
              <div className="empty-state">
                <p className="muted">No doctors listed for this department yet.</p>
              </div>
            ) : (
              <div className="grid-3-up">
                {doctors.map((doc) => (
                  <div key={doc.doctor_id} className="card" style={{ textAlign: 'center', padding: '1.5rem' }}>
                    <DoctorPhoto name={doc.full_name} photoPath={doc.profile_photo_path} />
                    <h3 style={{ marginBottom: '0.25rem' }}>{doc.full_name}</h3>
                    <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', margin: '0 0 0.75rem' }}>
                      {doc.specialty}
                    </p>
                    {doc.qualifications && (
                      <span
                        style={{
                          display: 'inline-block',
                          background: 'var(--color-surface-alt)',
                          border: '1px solid var(--color-border)',
                          borderRadius: 'var(--radius-sm)',
                          padding: '0.2rem 0.6rem',
                          fontSize: '0.75rem',
                          marginBottom: '0.75rem',
                          color: 'var(--color-text-muted)',
                        }}
                      >
                        {doc.qualifications}
                      </span>
                    )}
                    <p
                      style={{
                        fontSize: '0.875rem',
                        color: 'var(--color-text-muted)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.3rem',
                        margin: '0 0 1rem',
                      }}
                    >
                      <Clock size={14} /> {doc.years_experience} yrs experience
                    </p>
                    <Link
                      to={`/doctors/${doc.doctor_id}`}
                      className="btn btn-outline"
                      style={{ width: '100%', justifyContent: 'center' }}
                    >
                      View Full Profile
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      <BackToTopButton />
    </div>
  );
}
