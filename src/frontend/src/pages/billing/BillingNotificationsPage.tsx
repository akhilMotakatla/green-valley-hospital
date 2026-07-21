import { useEffect, useState, useCallback } from 'react';
import { X } from 'lucide-react';
import { getBillingNotifications, getBillingNotification } from '../../api/billing';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import type { BillingNotification } from '../../types';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { Pager } from '../../components/Pager';

export function BillingNotificationsPage() {
  const [items, setItems] = useState<BillingNotification[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [detail, setDetail] = useState<BillingNotification | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getBillingNotifications({ page, page_size: PAGE_SIZE })
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
        setTotalPages(r.total_pages);
        setLoading(false);
      })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, [page]);

  useEffect(() => { load(); }, [load]);

  async function openDetail(notificationId: number) {
    setDetail(null);
    setDetailError(null);
    setDetailLoading(true);
    try {
      const n = await getBillingNotification(notificationId);
      setDetail(n);
    } catch (e) {
      setDetailError(extractErrorMessage(e));
    } finally {
      setDetailLoading(false);
    }
  }

  function triggerLabel(event: string) {
    if (event === 'invoice_status_change') return 'Status Change';
    if (event === 'manual_resend') return 'Manual Resend';
    return event;
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0 }}>Email Notification Log</h2>
      </div>

      {/* Detail modal */}
      {(detail || detailLoading || detailError) && (
        <div className="modal-overlay" onClick={() => { setDetail(null); setDetailError(null); }}>
          <div className="modal" style={{ maxWidth: 700 }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Notification Detail</h3>
              <button className="icon-btn" onClick={() => { setDetail(null); setDetailError(null); }}>
                <X size={18} />
              </button>
            </div>
            <div className="modal-body">
              {detailLoading && <SkeletonBlock lines={4} />}
              {detailError && <p className="text-danger">{detailError}</p>}
              {detail && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div><strong>Subject:</strong> {detail.subject}</div>
                  <div><strong>Recipient:</strong> {detail.recipient_name}</div>
                  <div><strong>Sent At:</strong> {formatDateTime(detail.sent_at)}</div>
                  <div><strong>Trigger:</strong> {triggerLabel(detail.trigger_event)}</div>
                  {detail.related_invoice_id && (
                    <div><strong>Invoice:</strong> #{detail.related_invoice_id}</div>
                  )}
                  <div><strong>Status:</strong> {detail.status}</div>
                  {detail.body_html && (
                    <div>
                      <strong>Email Preview:</strong>
                      <div
                        style={{
                          marginTop: '0.5rem',
                          border: '1px solid var(--color-border)',
                          borderRadius: 'var(--radius-md)',
                          padding: '1rem',
                          background: '#fff',
                          maxHeight: 320,
                          overflowY: 'auto',
                          fontSize: '0.875rem',
                        }}
                        dangerouslySetInnerHTML={{ __html: detail.body_html }}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-outline" onClick={() => { setDetail(null); setDetailError(null); }}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <SkeletonBlock lines={8} />
      ) : error ? (
        <PageError message={error} onRetry={load} />
      ) : items.length === 0 ? (
        <p className="muted">No notifications logged yet.</p>
      ) : (
        <div className="billing-ledger-wrapper">
          <table className="billing-ledger">
            <thead>
              <tr>
                <th>ID</th>
                <th>Recipient</th>
                <th>Subject</th>
                <th>Invoice</th>
                <th>Trigger</th>
                <th>Sent At</th>
                <th>Status</th>
                <th>Detail</th>
              </tr>
            </thead>
            <tbody>
              {items.map((n) => (
                <tr key={n.notification_id}>
                  <td>#{n.notification_id}</td>
                  <td>{n.recipient_name}</td>
                  <td style={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {n.subject}
                  </td>
                  <td>{n.related_invoice_id ? `#${n.related_invoice_id}` : '—'}</td>
                  <td>{triggerLabel(n.trigger_event)}</td>
                  <td>{formatDateTime(n.sent_at)}</td>
                  <td>
                    <span className={`badge badge-${n.status.toLowerCase()}`}>{n.status}</span>
                  </td>
                  <td>
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={() => openDetail(n.notification_id)}
                    >
                      View
                    </button>
                  </td>
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
