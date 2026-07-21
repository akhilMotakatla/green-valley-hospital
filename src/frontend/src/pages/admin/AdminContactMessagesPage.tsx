import { useCallback, useEffect, useState } from 'react';
import { listAdminContactMessages, setContactMessageStatus } from '../../api/admin';
import type { ContactMessage } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { StatusBadge } from '../../components/StatusBadge';

export function AdminContactMessagesPage() {
  const [items, setItems] = useState<ContactMessage[]>([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    listAdminContactMessages({ status: statusFilter || undefined, page: 1, page_size: 50 })
      .then((r) => setItems(r.items))
      .catch((e) => setError(extractErrorMessage(e)));
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleStatus(id: number, status: 'Reviewed' | 'Resolved') {
    try {
      await setContactMessageStatus(id, status);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <h1>Contact Messages</h1>
      <div className="toolbar">
        <label>
          Status
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All</option>
            <option value="New">New</option>
            <option value="Reviewed">Reviewed</option>
            <option value="Resolved">Resolved</option>
          </select>
        </label>
      </div>
      {error && <p className="error-text">{error}</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Subject</th>
            <th>Message</th>
            <th>Status</th>
            <th>Received</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((m) => (
            <tr key={m.message_id}>
              <td>
                {m.name}
                <br />
                <span className="muted">{m.email}</span>
              </td>
              <td>{m.subject}</td>
              <td>{m.message}</td>
              <td>
                <StatusBadge status={m.status} />
              </td>
              <td>{formatDateTime(m.created_at)}</td>
              <td style={{ display: 'flex', gap: '0.4rem' }}>
                {m.status !== 'Reviewed' && (
                  <button className="btn btn-outline" onClick={() => handleStatus(m.message_id, 'Reviewed')}>
                    Mark Reviewed
                  </button>
                )}
                {m.status !== 'Resolved' && (
                  <button className="btn btn-primary" onClick={() => handleStatus(m.message_id, 'Resolved')}>
                    Mark Resolved
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && <p className="muted">No messages.</p>}
    </div>
  );
}
