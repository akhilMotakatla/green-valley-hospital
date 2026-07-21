import { useEffect, useState, useCallback } from 'react';
import { Plus, Trash2, Send, Edit2, X, Check } from 'lucide-react';
import {
  getBillingInvoices,
  createInvoice,
  updateInvoice,
  deleteInvoice,
  resendInvoiceNotification,
} from '../../api/billing';
import type { InvoiceListParams } from '../../api/billing';
import { extractErrorMessage } from '../../api/client';
import { formatCents, formatDateTime } from '../../utils/format';
import type { BillingInvoiceListItem } from '../../types';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { Pager } from '../../components/Pager';

const STATUS_OPTIONS = ['', 'Pending', 'Paid', 'Waived'] as const;

function statusBadgeClass(status: string) {
  if (status === 'Paid') return 'badge-status-paid';
  if (status === 'Waived') return 'badge-status-waived';
  return 'badge-status-pending';
}

interface NewInvoiceForm {
  patient_id: string;
  appointment_id: string;
  description: string;
  amount_cents: string;
  has_insurance_claim: boolean;
}

const EMPTY_FORM: NewInvoiceForm = {
  patient_id: '',
  appointment_id: '',
  description: '',
  amount_cents: '',
  has_insurance_claim: false,
};

export function BillingInvoicesPage() {
  const [items, setItems] = useState<BillingInvoiceListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;

  const [filterStatus, setFilterStatus] = useState<'' | 'Pending' | 'Paid' | 'Waived'>('');
  const [filterInsurance, setFilterInsurance] = useState<'' | '0' | '1'>('');
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<NewInvoiceForm>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editStatus, setEditStatus] = useState<'Pending' | 'Paid' | 'Waived'>('Pending');
  const [editInsurance, setEditInsurance] = useState(false);
  const [editSubmitting, setEditSubmitting] = useState(false);

  const [resendingId, setResendingId] = useState<number | null>(null);
  const [resendMsg, setResendMsg] = useState<string | null>(null);

  const [deletingId, setDeletingId] = useState<number | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const params: InvoiceListParams = { page, page_size: PAGE_SIZE };
    if (filterStatus) params.status = filterStatus;
    if (filterInsurance === '1') params.has_insurance_claim = 1;
    if (search) params.search = search;
    getBillingInvoices(params)
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
        setTotalPages(r.total_pages);
        setLoading(false);
      })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, [page, filterStatus, filterInsurance, search]);

  useEffect(() => { load(); }, [load]);

  function applySearch() {
    setSearch(searchInput);
    setPage(1);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    const patId = parseInt(form.patient_id, 10);
    const amtCents = parseInt(form.amount_cents, 10);
    if (!patId || !form.description || !amtCents) {
      setFormError('Patient ID, description, and amount are required.');
      return;
    }
    setSubmitting(true);
    try {
      await createInvoice({
        patient_id: patId,
        appointment_id: form.appointment_id ? parseInt(form.appointment_id, 10) : null,
        line_items: [{ description: form.description, amount_cents: amtCents }],
        total_amount_cents: amtCents,
        has_insurance_claim: form.has_insurance_claim ? 1 : 0,
      });
      setShowCreate(false);
      setForm(EMPTY_FORM);
      setPage(1);
      load();
    } catch (err) {
      setFormError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEditSave(invoiceId: number) {
    setEditSubmitting(true);
    try {
      await updateInvoice(invoiceId, {
        status: editStatus,
        has_insurance_claim: editInsurance ? 1 : 0,
      });
      setEditingId(null);
      load();
    } catch (err) {
      alert(extractErrorMessage(err));
    } finally {
      setEditSubmitting(false);
    }
  }

  async function handleDelete(invoiceId: number) {
    if (!window.confirm('Delete this pending invoice? This cannot be undone.')) return;
    setDeletingId(invoiceId);
    try {
      await deleteInvoice(invoiceId);
      load();
    } catch (err) {
      alert(extractErrorMessage(err));
    } finally {
      setDeletingId(null);
    }
  }

  async function handleResend(invoiceId: number) {
    setResendingId(invoiceId);
    setResendMsg(null);
    try {
      await resendInvoiceNotification(invoiceId);
      setResendMsg('Notification resent successfully.');
    } catch (err) {
      setResendMsg('Error: ' + extractErrorMessage(err));
    } finally {
      setResendingId(null);
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0 }}>Invoices</h2>
        <button className="btn btn-primary" onClick={() => { setShowCreate(true); setFormError(null); setForm(EMPTY_FORM); }}>
          <Plus size={16} /> New Invoice
        </button>
      </div>

      {/* Create modal */}
      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Invoice</h3>
              <button className="icon-btn" onClick={() => setShowCreate(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {formError && <div className="alert alert-danger">{formError}</div>}
                <label>
                  Patient ID <span style={{ color: 'red' }}>*</span>
                  <input type="number" value={form.patient_id} onChange={(e) => setForm({ ...form, patient_id: e.target.value })} required />
                </label>
                <label>
                  Appointment ID (optional)
                  <input type="number" value={form.appointment_id} onChange={(e) => setForm({ ...form, appointment_id: e.target.value })} />
                </label>
                <label>
                  Description <span style={{ color: 'red' }}>*</span>
                  <input type="text" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
                </label>
                <label>
                  Amount (cents) <span style={{ color: 'red' }}>*</span>
                  <input type="number" min={1} value={form.amount_cents} onChange={(e) => setForm({ ...form, amount_cents: e.target.value })} required />
                  {form.amount_cents && <small className="muted">{formatCents(parseInt(form.amount_cents, 10) || 0)}</small>}
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input type="checkbox" checked={form.has_insurance_claim} onChange={(e) => setForm({ ...form, has_insurance_claim: e.target.checked })} />
                  Has Insurance Claim
                </label>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-outline" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Creating…' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="billing-filters">
        <select value={filterStatus} onChange={(e) => { setFilterStatus(e.target.value as typeof filterStatus); setPage(1); }}>
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s || 'All Statuses'}</option>)}
        </select>
        <select value={filterInsurance} onChange={(e) => { setFilterInsurance(e.target.value as '' | '0' | '1'); setPage(1); }}>
          <option value="">All Claims</option>
          <option value="1">Insurance Claimed</option>
          <option value="0">No Claim</option>
        </select>
        <div style={{ display: 'flex', gap: '0.5rem', flex: 1 }}>
          <input
            type="search"
            placeholder="Search patient name or invoice ID…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && applySearch()}
            style={{ flex: 1 }}
          />
          <button className="btn btn-outline" onClick={applySearch}>Search</button>
        </div>
      </div>

      {resendMsg && (
        <div className={`alert ${resendMsg.startsWith('Error') ? 'alert-danger' : 'alert-success'}`} style={{ marginBottom: '1rem' }}>
          {resendMsg}
          <button className="icon-btn" style={{ marginLeft: 'auto' }} onClick={() => setResendMsg(null)}><X size={14} /></button>
        </div>
      )}

      {loading ? (
        <SkeletonBlock lines={8} />
      ) : error ? (
        <PageError message={error} onRetry={load} />
      ) : items.length === 0 ? (
        <p className="muted">No invoices found.</p>
      ) : (
        <div className="billing-ledger-wrapper">
          <table className="billing-ledger">
            <thead>
              <tr>
                <th>ID</th>
                <th>Patient</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Insurance</th>
                <th>Appt Date</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((inv) => (
                <tr key={inv.invoice_id}>
                  <td>#{inv.invoice_id}</td>
                  <td>{inv.patient_name}</td>
                  <td>{formatCents(inv.total_amount_cents)}</td>
                  <td>
                    {editingId === inv.invoice_id ? (
                      <select value={editStatus} onChange={(e) => setEditStatus(e.target.value as typeof editStatus)}>
                        <option>Pending</option>
                        <option>Paid</option>
                        <option>Waived</option>
                      </select>
                    ) : (
                      <span className={`badge ${statusBadgeClass(inv.status)}`}>{inv.status}</span>
                    )}
                  </td>
                  <td>
                    {editingId === inv.invoice_id ? (
                      <input type="checkbox" checked={editInsurance} onChange={(e) => setEditInsurance(e.target.checked)} />
                    ) : (
                      <span className={inv.has_insurance_claim ? 'badge badge-insurance' : 'muted'}>
                        {inv.has_insurance_claim ? 'Yes' : 'No'}
                      </span>
                    )}
                  </td>
                  <td>{inv.appointment_date ? formatDateTime(inv.appointment_date) : '—'}</td>
                  <td>{formatDateTime(inv.created_at)}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                      {editingId === inv.invoice_id ? (
                        <>
                          <button className="btn btn-primary btn-sm" disabled={editSubmitting} onClick={() => handleEditSave(inv.invoice_id)}>
                            <Check size={13} />
                          </button>
                          <button className="btn btn-outline btn-sm" onClick={() => setEditingId(null)}>
                            <X size={13} />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            className="btn btn-outline btn-sm"
                            title="Edit status / insurance"
                            onClick={() => {
                              setEditingId(inv.invoice_id);
                              setEditStatus(inv.status);
                              setEditInsurance(!!inv.has_insurance_claim);
                            }}
                          >
                            <Edit2 size={13} />
                          </button>
                          <button
                            className="btn btn-outline btn-sm"
                            title="Resend notification"
                            disabled={resendingId === inv.invoice_id}
                            onClick={() => handleResend(inv.invoice_id)}
                          >
                            <Send size={13} />
                          </button>
                          {inv.status === 'Pending' && (
                            <button
                              className="btn btn-danger btn-sm"
                              title="Delete invoice"
                              disabled={deletingId === inv.invoice_id}
                              onClick={() => handleDelete(inv.invoice_id)}
                            >
                              <Trash2 size={13} />
                            </button>
                          )}
                        </>
                      )}
                    </div>
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
