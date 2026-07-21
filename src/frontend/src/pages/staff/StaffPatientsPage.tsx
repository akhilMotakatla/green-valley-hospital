import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Users } from 'lucide-react';
import { listStaffPatients } from '../../api/staff';
import type { StaffPatientListItem } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { Pager } from '../../components/Pager';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

export function StaffPatientsPage() {
  const [items, setItems] = useState<StaffPatientListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [error, setError] = useState<string | null>(null);
  const pageSize = 15;

  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    listStaffPatients({ search: search || undefined, page, page_size: pageSize })
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
        setLoading(false);
      })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, [search, page]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div>
      <h1>Patients</h1>
      <div className="toolbar">
        <label>
          Search
          <input
            placeholder="Name or email"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </label>
        <Link to="/staff/register" className="btn btn-primary" style={{ alignSelf: 'flex-end' }}>
          Register Walk-in Patient
        </Link>
      </div>
      {error && <PageError message={error} onRetry={load} />}
      {loading ? (
        <SkeletonBlock lines={5} />
      ) : items.length === 0 && !error ? (
        <div className="empty-state">
          <Users size={80} color="var(--color-text-light)" />
          <h3>No patients found</h3>
        </div>
      ) : (
        <>
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.patient_id}>
                  <td>{p.full_name}</td>
                  <td>{p.email}</td>
                  <td>{p.phone}</td>
                  <td>
                    <Link className="btn btn-outline btn-sm" to={`/staff/patients/${p.patient_id}`}>View</Link>
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
