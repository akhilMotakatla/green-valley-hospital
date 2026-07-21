/**
 * REQ-09 — Staff Waitlist Management Page.
 * Staff selects a doctor, views their waitlist, and can remove entries.
 */
import { useCallback, useEffect, useState } from 'react';
import { Clock } from 'lucide-react';
import { searchDoctors, type PatientVisibleDoctor } from '../../api/patient';
import { staffGetWaitlist, staffRemoveWaitlistEntry, type StaffWaitlistEntry } from '../../api/waitlist';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { Pager } from '../../components/Pager';

export function StaffWaitlistPage() {
  const [doctors, setDoctors] = useState<PatientVisibleDoctor[]>([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState<string>('');
  const [dateFilter, setDateFilter] = useState('');
  const [entries, setEntries] = useState<StaffWaitlistEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    searchDoctors().then(setDoctors).catch(() => undefined);
  }, []);

  const load = useCallback(() => {
    if (!selectedDoctorId) return;
    setLoading(true);
    setError(null);
    staffGetWaitlist(Number(selectedDoctorId), {
      date: dateFilter || undefined,
      page,
      page_size: pageSize,
    })
      .then((r) => {
        setEntries(r.items);
        setTotal(r.total);
        setLoading(false);
      })
      .catch((e) => {
        setError(extractErrorMessage(e));
        setLoading(false);
      });
  }, [selectedDoctorId, dateFilter, page]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleRemove(entryId: number) {
    const reason = prompt('Reason for removal (optional):');
    if (reason === null) return; // cancelled
    setBusyId(entryId);
    try {
      await staffRemoveWaitlistEntry(entryId, reason || undefined);
      setToast('Entry removed.');
      load();
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <h1>Waitlist Management</h1>

      {toast && (
        <div className="success-text" style={{ marginBottom: '1rem' }}>
          {toast}
        </div>
      )}
      {error && <PageError message={error} onRetry={load} />}

      <div className="toolbar" style={{ gap: '1rem', flexWrap: 'wrap' }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          Doctor
          <select
            value={selectedDoctorId}
            onChange={(e) => {
              setSelectedDoctorId(e.target.value);
              setPage(1);
            }}
            style={{ minWidth: 220 }}
          >
            <option value="">Select a doctor…</option>
            {doctors.map((d) => (
              <option key={d.doctor_id} value={d.doctor_id}>
                {d.full_name} — {d.specialty}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          Filter by date
          <input
            type="date"
            value={dateFilter}
            onChange={(e) => {
              setDateFilter(e.target.value);
              setPage(1);
            }}
          />
        </label>
      </div>

      {!selectedDoctorId ? (
        <div className="empty-state" style={{ marginTop: '2rem' }}>
          <Clock size={64} color="var(--color-text-light)" />
          <h3>Select a doctor to view their waitlist</h3>
        </div>
      ) : loading ? (
        <SkeletonBlock lines={5} />
      ) : entries.length === 0 ? (
        <div className="empty-state" style={{ marginTop: '2rem' }}>
          <Clock size={64} color="var(--color-text-light)" />
          <h3>No patients currently on this waitlist</h3>
        </div>
      ) : (
        <>
          <table className="data-table" style={{ marginTop: '1rem' }}>
            <thead>
              <tr>
                <th>Patient</th>
                <th>Preferred Date</th>
                <th>Position</th>
                <th>Status</th>
                <th>Joined</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.entry_id}>
                  <td>{e.patient_name}</td>
                  <td>{e.preferred_date}</td>
                  <td>{e.position ?? '—'}</td>
                  <td>
                    <span
                      style={{
                        padding: '0.15rem 0.5rem',
                        borderRadius: 99,
                        fontSize: '0.8rem',
                        background: e.status === 'Notified' ? '#0d6efd' : '#6c757d',
                        color: '#fff',
                      }}
                    >
                      {e.status}
                    </span>
                  </td>
                  <td>{e.created_at?.slice(0, 10)}</td>
                  <td>
                    <button
                      className="btn btn-danger btn-sm"
                      disabled={busyId === e.entry_id}
                      onClick={() => handleRemove(e.entry_id)}
                    >
                      {busyId === e.entry_id ? 'Removing…' : 'Remove'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pager page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
