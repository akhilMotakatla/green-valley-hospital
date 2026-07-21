/**
 * REQ-11 — Doctor Ratings Page.
 * Shows the doctor's average rating and anonymised patient comments.
 */
import { useEffect, useState } from 'react';
import { Star } from 'lucide-react';
import { getDoctorRatings, type DoctorRatings } from '../../api/surveys';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { StarRating } from '../../components/StarRating';

function noop(_: number) {
  // read-only display
}

export function DoctorRatingsPage() {
  const [ratings, setRatings] = useState<DoctorRatings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getDoctorRatings()
      .then((r) => {
        setRatings(r);
        setLoading(false);
      })
      .catch((e) => {
        setError(extractErrorMessage(e));
        setLoading(false);
      });
  }, []);

  return (
    <div>
      <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Star size={24} />
        My Ratings
      </h1>

      {loading ? (
        <SkeletonBlock lines={4} />
      ) : error ? (
        <PageError message={error} />
      ) : !ratings ? null : (
        <div style={{ maxWidth: 640 }}>
          {/* Summary card */}
          <div
            style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 12,
              padding: '1.5rem',
              marginBottom: '1.5rem',
              display: 'flex',
              gap: '2rem',
              flexWrap: 'wrap',
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{ fontSize: '3rem', fontWeight: 700, lineHeight: 1 }}>
                {ratings.average_doctor_rating !== null
                  ? ratings.average_doctor_rating.toFixed(1)
                  : '—'}
              </div>
              <div style={{ color: 'var(--color-text-light)', marginTop: '0.25rem' }}>
                Average Rating
              </div>
            </div>
            {ratings.average_doctor_rating !== null && (
              <StarRating
                value={Math.round(ratings.average_doctor_rating)}
                onChange={noop}
                disabled
              />
            )}
            <div>
              <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>{ratings.total_reviews}</div>
              <div style={{ color: 'var(--color-text-light)' }}>
                {ratings.total_reviews === 1 ? 'Review' : 'Reviews'}
              </div>
            </div>
          </div>

          {/* Comments */}
          <h2 style={{ fontSize: '1.1rem', marginBottom: '0.75rem' }}>Patient Comments</h2>
          {ratings.comments.length === 0 ? (
            <p style={{ color: 'var(--color-text-light)' }}>No comments yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {ratings.comments.map((c, i) => (
                <div
                  key={i}
                  style={{
                    background: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 8,
                    padding: '0.9rem 1rem',
                  }}
                >
                  <p style={{ margin: 0 }}>{c.comment}</p>
                  <p style={{ margin: '0.4rem 0 0', fontSize: '0.8rem', color: 'var(--color-text-light)' }}>
                    {c.submitted_at.slice(0, 10)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
