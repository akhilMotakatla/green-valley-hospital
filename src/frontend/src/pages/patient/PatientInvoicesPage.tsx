import { useCallback, useEffect, useState } from 'react';
import { Receipt } from 'lucide-react';
import { getMyInvoices } from '../../api/patient';
import type { Invoice } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatCents, formatDateTime } from '../../utils/format';
import { StatusBadge } from '../../components/StatusBadge';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

export function PatientInvoicesPage() {
  const [items, setItems] = useState<Invoice[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getMyInvoices({ page: 1, page_size: 50 })
      .then((r) => { setItems(r.items); setLoading(false); })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div>
      <h1>My Billing</h1>
      {loading ? (
        <SkeletonBlock lines={5} />
      ) : error ? (
        <PageError message={error} onRetry={load} />
      ) : items.length === 0 ? (
        <div className="empty-state">
          <Receipt size={80} color="var(--color-text-light)" />
          <h3>No invoices yet</h3>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Your billing records will appear here after consultations.
          </p>
        </div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Invoice #</th>
              <th>Appointment</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {items.map((inv) => (
              <tr key={inv.invoice_id}>
                <td>{inv.invoice_id}</td>
                <td>{inv.appointment_id ?? '—'}</td>
                <td>{formatCents(inv.total_amount_cents)}</td>
                <td><StatusBadge status={inv.status} /></td>
                <td>{formatDateTime(inv.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
