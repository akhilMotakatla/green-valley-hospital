import { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Search, Building2, UserCircle } from 'lucide-react';
import { publicSearch } from '../../api/search';
import type { SearchResults } from '../../api/search';
import { extractErrorMessage } from '../../api/client';

function DeptCard({ dept }: { dept: SearchResults['departments'][0] }) {
  return (
    <div className="card" style={{ marginBottom: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
          <Building2 size={16} />
          <strong>{dept.name}</strong>
          <span className="muted" style={{ fontSize: '0.75rem' }}>
            {dept.match_type === 'symptom_tag' ? `Tag: "${dept.matched_tag}"` : dept.match_type}
          </span>
        </div>
        {dept.description && <p className="muted" style={{ margin: 0 }}>{dept.description.slice(0, 120)}{dept.description.length > 120 ? '…' : ''}</p>}
      </div>
      <Link to={`/departments/${dept.department_id}`} className="btn btn-outline btn-sm" style={{ flexShrink: 0 }}>
        View Department
      </Link>
    </div>
  );
}

function DocCard({ doc }: { doc: SearchResults['doctors'][0] }) {
  return (
    <div className="card" style={{ marginBottom: '0.75rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
      {doc.profile_photo_path ? (
        <img
          src={`/${doc.profile_photo_path}`}
          alt={`Dr. ${doc.full_name}`}
          style={{ width: 56, height: 56, borderRadius: '50%', objectFit: 'cover', flexShrink: 0 }}
        />
      ) : (
        <div style={{ width: 56, height: 56, borderRadius: '50%', background: '#e0e0e0', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <UserCircle size={32} color="#999" />
        </div>
      )}
      <div style={{ flex: 1 }}>
        <strong>Dr. {doc.full_name}</strong>
        <p className="muted" style={{ margin: '2px 0' }}>{doc.specialty} — {doc.department_name}</p>
        {doc.bio && <p className="muted" style={{ margin: 0, fontSize: '0.8rem' }}>{doc.bio.slice(0, 100)}{doc.bio.length > 100 ? '…' : ''}</p>}
      </div>
      <Link to={`/doctors/${doc.doctor_id}`} className="btn btn-outline btn-sm" style={{ flexShrink: 0 }}>
        View Profile
      </Link>
    </div>
  );
}

export function SearchPage() {
  const [searchParams] = useSearchParams();
  const q = searchParams.get('q') ?? '';
  const [results, setResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const doSearch = useCallback(() => {
    if (q.length < 2) return;
    setLoading(true);
    setError(null);
    publicSearch(q)
      .then((r) => { setResults(r); setLoading(false); })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, [q]);

  useEffect(() => { doSearch(); }, [doSearch]);

  const total = results ? results.total : 0;

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <Search size={28} />
        <h1 style={{ margin: 0 }}>
          {q ? `Search results for "${q}"` : 'Search'}
        </h1>
      </div>

      {loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {[1, 2, 3].map((i) => (
            <div key={i} className="card skeleton" style={{ height: 72 }} />
          ))}
        </div>
      )}

      {error && (
        <div className="card" style={{ color: 'var(--color-danger)', padding: '1rem' }}>{error}</div>
      )}

      {!loading && results && (
        <>
          <p className="muted" style={{ marginBottom: '1.5rem' }}>
            {total} result{total !== 1 ? 's' : ''} for &ldquo;{q}&rdquo;
          </p>

          {results.departments.length > 0 && (
            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ marginBottom: '1rem' }}>Departments ({results.departments.length})</h2>
              {results.departments.map((d) => <DeptCard key={d.department_id} dept={d} />)}
            </section>
          )}

          {results.doctors.length > 0 && (
            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ marginBottom: '1rem' }}>Doctors ({results.doctors.length})</h2>
              {results.doctors.map((d) => <DocCard key={d.doctor_id} doc={d} />)}
            </section>
          )}

          {total === 0 && (
            <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
              <Search size={48} color="#ccc" />
              <p style={{ marginTop: '1rem' }}>No results found for &ldquo;{q}&rdquo;</p>
              <p className="muted">Try different keywords, or</p>
              <Link to="/departments" className="btn btn-outline" style={{ marginTop: '0.5rem' }}>
                Browse All Departments
              </Link>
            </div>
          )}
        </>
      )}

      {!loading && !results && q.length < 2 && q.length > 0 && (
        <p className="muted">Please enter at least 2 characters to search.</p>
      )}
    </div>
  );
}
