/**
 * REQ-11 — Survey submission form.
 * Two star ratings (doctor + overall) plus an optional comment.
 */
import { useState } from 'react';
import { Send } from 'lucide-react';
import { StarRating } from './StarRating';
import { submitSurvey } from '../api/surveys';
import { extractErrorMessage } from '../api/client';

interface Props {
  surveyId: number;
  onSubmitted: () => void;
}

export function SurveyForm({ surveyId, onSubmitted }: Props) {
  const [doctorStar, setDoctorStar] = useState(0);
  const [overallStar, setOverallStar] = useState(0);
  const [comment, setComment] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    if (doctorStar < 1 || overallStar < 1) {
      setError('Please rate both Doctor Experience and Overall Visit.');
      return;
    }
    if (comment.length > 1000) {
      setError('Comment must be 1000 characters or fewer.');
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await submitSurvey(surveyId, {
        doctor_star_rating: doctorStar,
        overall_star_rating: overallStar,
        comment: comment.trim() || null,
      });
      onSubmitted();
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="form" style={{ maxWidth: 480 }}>
      {error && <p className="error-text">{error}</p>}

      <div style={{ marginBottom: '1rem' }}>
        <StarRating
          label="Doctor Experience"
          value={doctorStar}
          onChange={setDoctorStar}
        />
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <StarRating
          label="Overall Visit"
          value={overallStar}
          onChange={setOverallStar}
        />
      </div>

      <label>
        Comments (optional, max 1000 characters)
        <textarea
          rows={4}
          maxLength={1000}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Share your experience…"
        />
        <span style={{ fontSize: '0.8rem', color: 'var(--color-text-light)' }}>
          {comment.length}/1000
        </span>
      </label>

      <button
        className="btn btn-primary"
        onClick={handleSubmit}
        disabled={submitting || doctorStar < 1 || overallStar < 1}
        style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
      >
        <Send size={15} />
        {submitting ? 'Submitting…' : 'Submit Survey'}
      </button>
    </div>
  );
}
