/**
 * REQ-11 — Admin Surveys Moderation Page.
 * Lists all surveys with filter controls; admin can remove comments.
 */
import { useCallback, useEffect, useState } from 'react';
import { Star } from 'lucide-react';
import { adminGetSurveys, adminRemoveSurveyComment, type AdminSurvey } from '../../api/surveys';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { Pager } from '../../components/Pager';

const PAGE_SIZE = 15;

export function AdminSurveysPage() {
  const [items, setItems] = useState<AdminSurvey[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submittedOnly, setSubmittedOnly] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [removingId, setRemovingId] = useState<number | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    adminGetSurveys({
      page,
      page_size: PAGE_SIZE,
      submitted_only: submittedOnly || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    })
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
        setLoading(false);
      })
      .catch((e) => {
        setError(extractErrorMessage(e));
        setLoading(false);
      });
  }, [page, submittedOnly, startDate, endDate]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleRemoveComment(surveyId: number) {
    setRemovingId(surveyId);
    try {
      await adminRemoveSurveyComment(surveyId);
      // update locally
      setItems((prev) =>
        prev.map((s) =>
          s.survey_id === surveyId ? { ...s, comment: null, is_comment_removed: true } : s,
        ),
      );
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setRemovingId(null);
    }
  }

  function stars(n: number | null) {
    if (n === null) return '—';
    return '★'.repeat(n) + '☆'.repeat(5 - n);
  }

  return (
    <div>
      <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Star size={24} />
        Survey Moderation
      </h1>

      {/* Filters */}
      <div className="toolbar" style={{ marginBottom: '1rem' }}>
        <label>
          <input
            type="checkbox"
            checked={submittedOnly}
            onChange={(e) => {
              setSubmittedOnly(e.target.checked);
              setPage(1);
            }}
            style={{ marginRight: '0.4rem' }}
          />
          Submitted only
        </label>

        <label>
          From
          <input
            type="date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setPage(1);
            }}
          />
        </label>

        <label>
          To
          <input
            type="date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setPage(1);
            }}
          />
        </label>
      </div>

      {error && <PageError message={error} onRetry={load} />}

      {loading ? (
        <SkeletonBlock lines={6} />
      ) : items.length === 0 ? (
        <p style={{ color: 'var(--color-text-light)' }}>No surveys found.</p>
      ) : (
        <>
          <table className="data-table">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Appt Date</th>
                <th>Doctor ★</th>
                <th>Overall ★</th>
                <th>Comment</th>
                <th>Submitted</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((s) => (
                <tr key={s.survey_id}>
                  <td>{s.patient_name ?? s.patient_id}</td>
                  <td>{s.doctor_name ?? s.doctor_id}</td>
                  <td>{s.appointment_date?.slice(0, 10) ?? '—'}</td>
                  <td style={{ color: '#f59e0b' }}>{stars(s.doctor_star_rating)}</td>
                  <td style={{ color: '#f59e0b' }}>{stars(s.overall_star_rating)}</td>
                  <td style={{ maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {s.is_comment_removed ? (
                      <em style={{ color: 'var(--color-text-light)' }}>[removed]</em>
                    ) : (
                      s.comment ?? '—'
                    )}
                  </td>
                  <td>{s.submitted_at?.slice(0, 10) ?? '—'}</td>
                  <td>
                    {s.comment && !s.is_comment_removed && (
                      <button
                        className="btn btn-danger btn-sm"
                        disabled={removingId === s.survey_id}
                        onClick={() => handleRemoveComment(s.survey_id)}
                      >
                        {removingId === s.survey_id ? '…' : 'Remove Comment'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pager page={page} pageSize={PAGE_SIZE} total={total} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
