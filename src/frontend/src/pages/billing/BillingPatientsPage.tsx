import { useEffect, useState, useCallback } from 'react';
import { Search } from 'lucide-react';
import { getBillingPatients } from '../../api/billing';
import { extractErrorMessage } from '../../api/client';
import { formatDate } from '../../utils/format';
import type { BillingPatient } from '../../types';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { Pager } from '../../components/Pager';

export function BillingPatientsPage() {
  const [items, setItems] = useState<BillingPatient[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;

  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const params: { search?: string; page: number; page_size: number } = { page, page_size: PAGE_SIZE };
    if (search) params.search = search;
    getBillingPatients(params)
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
        setTotalPages(r.total_pages);
        setLoading(false);
      })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, [page, search]);

  useEffect(() => { load(); }, [load]);

  function applySearch() {
    setSearch(searchInput);
    setPage(1);
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ margin: '0 0 1rem' }}>Patients (Billing View)</h2>
        <div style={{ display: 'flex', gap: '0.5rem', maxWidth: 480 }}>
          <div className="input-icon-wrapper" style={{ flex: 1 }}>
            <span className="input-icon-left"><Search size={16} /></span>
            <input
              type="search"
              placeholder="Search by patient name…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && applySearch()}
            />
          </div>
          <button className="btn btn-outline" onClick={applySearch}>Search</button>
        </div>
      </div>

      {loading ? (
        <SkeletonBlock lines={8} />
      ) : error ? (
        <PageError message={error} onRetry={load} />
      ) : items.length === 0 ? (
        <p className="muted">No patients found.</p>
      ) : (
        <div className="billing-ledger-wrapper">
          <table className="billing-ledger">
            <thead>
              <tr>
                <th>ID</th>
                <th>Full Name</th>
                <th>Date of Birth</th>
                <th>Phone</th>
                <th>Email</th>
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.patient_id}>
                  <td>{p.patient_id}</td>
                  <td>{p.full_name}</td>
                  <td>{formatDate(p.date_of_birth)}</td>
                  <td>{p.phone ?? '—'}</td>
                  <td>{p.email}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pager page={page} pageSize={PAGE_SIZE} total={total} totalPages={totalPages} onPageChange={setPage} />
    </div>
  );
}
