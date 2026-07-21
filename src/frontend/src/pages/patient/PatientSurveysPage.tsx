/**
 * REQ-11 — Patient Surveys Page.
 * Lists all surveys for the patient: pending ones show the SurveyForm,
 * submitted ones show a read-only summary, expired ones show a notice.
 */
import { useEffect, useState } from 'react';
import { Star } from 'lucide-react';
import { getMySurveys, type PatientSurvey } from '../../api/surveys';
import { extractErrorMessage } from '../../api/client';
import { SurveyForm } from '../../components/SurveyForm';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { StatusBadge } from '../../components/StatusBadge';

export function PatientSurveysPage() {
  const [surveys, setSurveys] = useState<PatientSurvey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  function load() {
    setLoading(true);
    getMySurveys()
      .then((items) => {
        setSurveys(items);
        setLoading(false);
      })
      .catch((e) => {
        setError(extractErrorMessage(e));
        setLoading(false);
      });
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Star size={24} />
        My Surveys
      </h1>
      <p style={{ color: 'var(--color-text-light)', marginBottom: '1.5rem' }}>
        Rate your appointments and share your experience.
      </p>

      {loading ? (
        <SkeletonBlock lines={5} />
      ) : error ? (
        <PageError message={error} onRetry={load} />
      ) : surveys.length === 0 ? (
        <div className="empty-state">
          <Star size={64} color="var(--color-text-light)" />
          <h3>No surveys yet</h3>
          <p>Surveys appear here after your appointments are completed.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {surveys.map((s) => (
            <div
              key={s.survey_id}
              style={{
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 10,
                padding: '1.25rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div>
                  <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
                    {s.doctor_name ? `Dr. ${s.doctor_name}` : 'Doctor'} — Appointment on{' '}
                    {s.appointment_date?.slice(0, 10) ?? '—'}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--color-text-light)' }}>
                    Expires: {s.expires_at.slice(0, 10)}
                  </div>
                </div>
                <StatusBadge status={s.status === 'submitted' ? 'Completed' : s.status === 'expired' ? 'Cancelled' : 'Scheduled'} />
              </div>

              {s.status === 'pending' && (
                <div style={{ marginTop: '1rem' }}>
                  {expanded === s.survey_id ? (
                    <>
                      <SurveyForm
                        surveyId={s.survey_id}
                        onSubmitted={() => {
                          setExpanded(null);
                          load();
                        }}
                      />
                      <button
                        className="btn btn-outline btn-sm"
                        style={{ marginTop: '0.5rem' }}
                        onClick={() => setExpanded(null)}
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => setExpanded(s.survey_id)}
                    >
                      Rate this appointment
                    </button>
                  )}
                </div>
              )}

              {s.status === 'submitted' && (
                <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: 'var(--color-text-light)' }}>
                  Submitted on {s.submitted_at?.slice(0, 10)}. Thank you for your feedback!
                </p>
              )}

              {s.status === 'expired' && (
                <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: 'var(--color-danger, #dc3545)' }}>
                  This survey has expired and can no longer be completed.
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
