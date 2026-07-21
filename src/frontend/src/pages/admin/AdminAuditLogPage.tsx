import { useCallback, useEffect, useState } from 'react';
import { getAuditLog } from '../../api/admin';
import type { AuditLogEntry } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { Pager } from '../../components/Pager';

export function AdminAuditLogPage() {
  const [items, setItems] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const pageSize = 20;

  const load = useCallback(() => {
    getAuditLog({ page, page_size: pageSize })
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
      })
      .catch((e) => setError(extractErrorMessage(e)));
  }, [page]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div>
      <h1>Audit Log</h1>
      {error && <p className="error-text">{error}</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Actor</th>
            <th>Action</th>
            <th>Target</th>
            <th>Details</th>
            <th>When</th>
          </tr>
        </thead>
        <tbody>
          {items.map((e) => (
            <tr key={e.log_id}>
              <td>{e.actor_name}</td>
              <td>{e.action}</td>
              <td>{e.target_name ?? '—'}</td>
              <td>{e.details}</td>
              <td>{formatDateTime(e.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && <p className="muted">No audit entries.</p>}
      <Pager page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
    </div>
  );
}
