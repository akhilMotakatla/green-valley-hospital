import { useCallback, useEffect, useState } from 'react';
import { listAdminInvoices } from '../../api/admin';
import type { Invoice } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatCents, formatDateTime } from '../../utils/format';
import { StatusBadge } from '../../components/StatusBadge';
import { Pager } from '../../components/Pager';

export function AdminInvoicesPage() {
  const [items, setItems] = useState<Invoice[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const [error, setError] = useState<string | null>(null);
  const pageSize = 15;

  const load = useCallback(() => {
    listAdminInvoices({ status: status || undefined, page, page_size: pageSize })
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
      })
      .catch((e) => setError(extractErrorMessage(e)));
  }, [status, page]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div>
      <h1>Billing / Invoices</h1>
      <div className="toolbar">
        <label>
          Status
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All</option>
            <option value="Pending">Pending</option>
            <option value="Paid">Paid</option>
            <option value="Waived">Waived</option>
          </select>
        </label>
      </div>
      {error && <p className="error-text">{error}</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Invoice #</th>
            <th>Patient</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {items.map((inv) => (
            <tr key={inv.invoice_id}>
              <td>{inv.invoice_id}</td>
              <td>{inv.patient_name}</td>
              <td>{formatCents(inv.total_amount_cents)}</td>
              <td>
                <StatusBadge status={inv.status} />
              </td>
              <td>{formatDateTime(inv.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && <p className="muted">No invoices found.</p>}
      <Pager page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
    </div>
  );
}
