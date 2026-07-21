import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { CalendarPlus, Stethoscope, Award, Clock, FileText } from 'lucide-react';
import { getDoctorProfile } from '../../api/public';
import type { PublicDoctorProfile } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

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
          width: 200,
          height: 200,
          borderRadius: '50%',
          objectFit: 'cover',
          display: 'block',
          margin: '0 auto',
        }}
      />
    );
  }

  return (
    <div
      style={{
        width: 200,
        height: 200,
        borderRadius: '50%',
        background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '0 auto',
        color: '#fff',
        fontSize: '2.5rem',
        fontWeight: 700,
      }}
    >
      {initials}
    </div>
  );
}

export function DoctorProfilePage() {
  const { id } = useParams();
  const { isAuthenticated, user } = useAuth();
  const [doctor, setDoctor] = useState<PublicDoctorProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    getDoctorProfile(id)
      .then((d) => { setDoctor(d); setLoading(false); })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  };

  useEffect(() => { load(); }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  const bookLink =
    isAuthenticated && user?.role === 'Patient'
      ? `/patient/book?doctor_id=${id}`
      : '/signup';

  if (loading) {
    return (
      <div className="container" style={{ padding: '4rem 1.5rem' }}>
        <SkeletonBlock lines={8} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container" style={{ padding: '2rem 1.5rem' }}>
        <PageError message={error} onRetry={load} />
      </div>
    );
  }

  if (!doctor) return null;

  return (
    <div className="container" style={{ padding: '3rem 1.5rem' }}>
      <p style={{ marginBottom: '1.5rem' }}>
        <Link to={`/departments/${doctor.department.department_id}`} style={{ color: 'var(--color-primary)' }}>
          &larr; Back to {doctor.department.name}
        </Link>
      </p>

      {/* Two-column profile */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 30%) 1fr',
          gap: '2rem',
          alignItems: 'start',
          marginBottom: '2rem',
        }}
        className="profile-grid"
      >
        {/* Left column */}
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
          <DoctorPhoto name={doctor.full_name} photoPath={doctor.profile_photo_path} />
          <div style={{ marginTop: '1rem' }}>
            <span
              style={{
                display: 'inline-block',
                background: 'var(--color-primary-light)',
                color: 'var(--color-primary-dark)',
                borderRadius: 999,
                padding: '0.25rem 0.75rem',
                fontSize: '0.8125rem',
                fontWeight: 600,
                marginBottom: '0.5rem',
              }}
            >
              {doctor.department.name}
            </span>
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', margin: 0 }}>
              {doctor.specialty}
            </p>
          </div>
        </div>

        {/* Right column */}
        <div className="card" style={{ padding: '2rem' }}>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '0.25rem' }}>{doctor.full_name}</h1>
          <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>{doctor.specialty}</p>

          {doctor.bio && (
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--color-primary)' }}>
                <Stethoscope size={18} />
                <strong style={{ color: 'var(--color-text)' }}>Bio</strong>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid var(--color-border)', margin: '0 0 0.75rem' }} />
              <p style={{ color: 'var(--color-text-muted)', margin: 0 }}>{doctor.bio}</p>
            </div>
          )}

          {doctor.qualifications && (
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <Award size={18} color="var(--color-primary)" />
                <strong>Qualifications</strong>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid var(--color-border)', margin: '0 0 0.75rem' }} />
              <p style={{ color: 'var(--color-text-muted)', margin: 0 }}>{doctor.qualifications}</p>
            </div>
          )}

          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <FileText size={18} color="var(--color-primary)" />
              <strong>Experience</strong>
            </div>
            <hr style={{ border: 'none', borderTop: '1px solid var(--color-border)', margin: '0 0 0.75rem' }} />
            <p style={{ color: 'var(--color-text-muted)', margin: 0 }}>{doctor.years_experience} years of experience</p>
          </div>

          {doctor.consultation_hours && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <Clock size={18} color="var(--color-primary)" />
                <strong>Consultation Hours</strong>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid var(--color-border)', margin: '0 0 0.75rem' }} />
              <p style={{ color: 'var(--color-text-muted)', margin: 0 }}>{doctor.consultation_hours}</p>
            </div>
          )}
        </div>
      </div>

      {/* Book appointment CTA strip */}
      <div
        className="glass-panel"
        style={{
          padding: '1.75rem 2rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <p style={{ margin: 0, fontWeight: 500, color: 'var(--color-text)' }}>
          Ready to consult with <strong>{doctor.full_name}</strong>? Book your appointment today.
        </p>
        <Link to={bookLink} className="btn btn-accent" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
          <CalendarPlus size={18} /> Book Appointment
        </Link>
      </div>

      <style>{`
        @media (max-width: 767px) {
          .profile-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}
