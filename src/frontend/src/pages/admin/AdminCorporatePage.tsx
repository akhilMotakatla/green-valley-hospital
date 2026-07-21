import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Building2, Plus, Edit2, Trash2 } from 'lucide-react';
import {
  adminCreatePackage,
  adminDeactivatePackage,
  adminListInquiries,
  adminListPackages,
  adminPatchInquiry,
  adminPipelineSummary,
  adminUpdatePackage,
} from '../../api/corporate';
import type { CorporateInquiry, CorporatePackage } from '../../api/corporate';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { StatusBadge } from '../../components/StatusBadge';
import { formatDateTime } from '../../utils/format';

type Tab = 'packages' | 'inquiries';

const INQUIRY_STATUSES = ['New', 'Contacted', 'ProposalSent', 'ClosedWon', 'ClosedLost'];

export function AdminCorporatePage() {
  const [tab, setTab] = useState<Tab>('packages');
  const [packages, setPackages] = useState<CorporatePackage[]>([]);
  const [inquiries, setInquiries] = useState<CorporateInquiry[]>([]);
  const [pipelineTotal, setPipelineTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Package modal
  const [showPkgModal, setShowPkgModal] = useState(false);
  const [editingPkg, setEditingPkg] = useState<CorporatePackage | null>(null);
  const [pkgName, setPkgName] = useState('');
  const [pkgTierOrder, setPkgTierOrder] = useState('1');
  const [pkgDesc, setPkgDesc] = useState('');
  const [pkgServices, setPkgServices] = useState('');
  const [pkgPrice, setPkgPrice] = useState('');
  const [pkgMsg, setPkgMsg] = useState<string | null>(null);
  const [pkgError, setPkgError] = useState<string | null>(null);

  // Inquiry detail
  const [expandedInquiry, setExpandedInquiry] = useState<number | null>(null);
  const [inquiryStatus, setInquiryStatus] = useState<Record<number, string>>({});
  const [inquiryNotes, setInquiryNotes] = useState<Record<number, string>>({});
  const [inquiryDealValue, setInquiryDealValue] = useState<Record<number, string>>({});
  const [statusFilter, setStatusFilter] = useState('');
  const [savingInquiry, setSavingInquiry] = useState<number | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      adminListPackages(),
      adminListInquiries({ status: statusFilter || undefined, page: 1, page_size: 50 }),
      adminPipelineSummary(),
    ])
      .then(([pkgs, inqData, pipeline]) => {
        setPackages(pkgs);
        setInquiries(inqData.items);
        setPipelineTotal(pipeline.total_closed_won_value);
        setLoading(false);
      })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, [statusFilter]);

  useEffect(() => { load(); }, [load]);

  function openCreatePkg() {
    setEditingPkg(null);
    setPkgName(''); setPkgTierOrder('1'); setPkgDesc(''); setPkgServices(''); setPkgPrice('');
    setPkgMsg(null); setPkgError(null);
    setShowPkgModal(true);
  }

  function openEditPkg(pkg: CorporatePackage) {
    setEditingPkg(pkg);
    setPkgName(pkg.name);
    setPkgTierOrder(String(pkg.tier_order));
    setPkgDesc(pkg.description);
    setPkgServices(pkg.included_services.join(', '));
    setPkgPrice(pkg.price_range_display);
    setPkgMsg(null); setPkgError(null);
    setShowPkgModal(true);
  }

  async function handleSavePkg(e: FormEvent) {
    e.preventDefault();
    setPkgError(null);
    const services = pkgServices.split(',').map((s) => s.trim()).filter(Boolean);
    const payload = {
      name: pkgName,
      tier_order: Number(pkgTierOrder),
      description: pkgDesc,
      included_services: services,
      price_range_display: pkgPrice,
      is_active: true,
    };
    try {
      if (editingPkg) {
        await adminUpdatePackage(editingPkg.package_id, payload);
        setPkgMsg('Package updated.');
      } else {
        await adminCreatePackage(payload);
        setPkgMsg('Package created.');
      }
      load();
      setTimeout(() => { setShowPkgModal(false); setPkgMsg(null); }, 1200);
    } catch (err) {
      setPkgError(extractErrorMessage(err));
    }
  }

  async function handleDeactivate(pkg: CorporatePackage) {
    if (!confirm(`Deactivate "${pkg.name}"? It will no longer appear on the public page.`)) return;
    try {
      await adminDeactivatePackage(pkg.package_id);
      load();
    } catch (err) {
      alert(extractErrorMessage(err));
    }
  }

  async function handleSaveInquiry(inquiryId: number) {
    setSavingInquiry(inquiryId);
    try {
      const dealCents = inquiryDealValue[inquiryId]
        ? Math.round(Number(inquiryDealValue[inquiryId]) * 100)
        : undefined;
      await adminPatchInquiry(inquiryId, {
        status: inquiryStatus[inquiryId],
        notes: inquiryNotes[inquiryId],
        deal_value_cents: dealCents,
      });
      load();
    } catch (err) {
      alert(extractErrorMessage(err));
    } finally {
      setSavingInquiry(null);
    }
  }

  function toggleInquiry(id: number, inq: CorporateInquiry) {
    if (expandedInquiry === id) {
      setExpandedInquiry(null);
    } else {
      setExpandedInquiry(id);
      setInquiryStatus((prev) => ({ ...prev, [id]: inq.status }));
      setInquiryNotes((prev) => ({ ...prev, [id]: inq.notes ?? '' }));
      setInquiryDealValue((prev) => ({
        ...prev,
        [id]: inq.deal_value_cents ? String(inq.deal_value_cents / 100) : '',
      }));
    }
  }

  if (loading) return <SkeletonBlock lines={6} />;
  if (error) return <div className="card"><p style={{ color: 'var(--color-danger)' }}>{error}</p></div>;

  return (
    <div>
      <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <Building2 size={24} /> Corporate Packages
      </h1>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <button className={`btn ${tab === 'packages' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setTab('packages')}>
          Packages ({packages.length})
        </button>
        <button className={`btn ${tab === 'inquiries' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setTab('inquiries')}>
          Inquiries ({inquiries.length})
        </button>
      </div>

      {/* ---- Packages Tab ---- */}
      {tab === 'packages' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={openCreatePkg}>
              <Plus size={16} style={{ marginRight: '0.4rem' }} /> New Package
            </button>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Tier</th>
                <th>Name</th>
                <th>Price Range</th>
                <th>Active</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {packages.map((pkg) => (
                <tr key={pkg.package_id}>
                  <td>{pkg.tier_order}</td>
                  <td><strong>{pkg.name}</strong></td>
                  <td>{pkg.price_range_display}</td>
                  <td>{pkg.is_active ? <StatusBadge status="Active" /> : <StatusBadge status="Inactive" />}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button className="btn btn-outline btn-sm" onClick={() => openEditPkg(pkg)}>
                        <Edit2 size={14} />
                      </button>
                      {pkg.is_active && (
                        <button className="btn btn-outline btn-sm" style={{ color: 'var(--color-danger)' }} onClick={() => handleDeactivate(pkg)}>
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ---- Inquiries Tab ---- */}
      {tab === 'inquiries' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <label style={{ fontWeight: 600 }}>Filter:</label>
              <select
                className="form-control"
                style={{ maxWidth: 180 }}
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Statuses</option>
                {INQUIRY_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="card" style={{ padding: '0.5rem 1rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
              <strong>Pipeline (Closed Won):</strong>
              <span style={{ color: 'var(--color-primary)', fontWeight: 700, fontSize: '1.1rem' }}>
                ${(pipelineTotal / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Company</th>
                <th>Contact</th>
                <th>Headcount</th>
                <th>Package</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {inquiries.map((inq) => (
                <>
                  <tr
                    key={inq.inquiry_id}
                    style={{ cursor: 'pointer' }}
                    onClick={() => toggleInquiry(inq.inquiry_id, inq)}
                  >
                    <td>#{inq.inquiry_id}</td>
                    <td><strong>{inq.company_name}</strong></td>
                    <td>{inq.contact_name}</td>
                    <td>{inq.headcount ?? '—'}</td>
                    <td>{inq.package_name ?? '—'}</td>
                    <td><StatusBadge status={inq.status} /></td>
                    <td>{formatDateTime(inq.created_at)}</td>
                  </tr>
                  {expandedInquiry === inq.inquiry_id && (
                    <tr key={`${inq.inquiry_id}-detail`}>
                      <td colSpan={7} style={{ background: '#f8f9fa', padding: '1.5rem' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                          <div>
                            <p><strong>Email:</strong> {inq.email}</p>
                            <p><strong>Phone:</strong> {inq.phone ?? '—'}</p>
                            <p><strong>Schedule:</strong> {inq.preferred_schedule ?? '—'}</p>
                          </div>
                          <div>
                            <div className="form-group">
                              <label>Status</label>
                              <select
                                className="form-control"
                                value={inquiryStatus[inq.inquiry_id] ?? inq.status}
                                onChange={(e) => setInquiryStatus((p) => ({ ...p, [inq.inquiry_id]: e.target.value }))}
                              >
                                {INQUIRY_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                              </select>
                            </div>
                            <div className="form-group">
                              <label>Deal Value (USD)</label>
                              <input
                                type="number"
                                step="0.01"
                                className="form-control"
                                value={inquiryDealValue[inq.inquiry_id] ?? ''}
                                onChange={(e) => setInquiryDealValue((p) => ({ ...p, [inq.inquiry_id]: e.target.value }))}
                                placeholder="e.g. 15000.00"
                              />
                            </div>
                          </div>
                          <div>
                            <div className="form-group">
                              <label>Notes</label>
                              <textarea
                                className="form-control"
                                rows={3}
                                value={inquiryNotes[inq.inquiry_id] ?? ''}
                                onChange={(e) => setInquiryNotes((p) => ({ ...p, [inq.inquiry_id]: e.target.value }))}
                              />
                            </div>
                            <button
                              className="btn btn-primary btn-sm"
                              onClick={() => handleSaveInquiry(inq.inquiry_id)}
                              disabled={savingInquiry === inq.inquiry_id}
                            >
                              {savingInquiry === inq.inquiry_id ? 'Saving...' : 'Save Changes'}
                            </button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Package Create/Edit Modal */}
      {showPkgModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div className="card" style={{ width: '100%', maxWidth: 520, maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0 }}>{editingPkg ? 'Edit Package' : 'New Package'}</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowPkgModal(false)}>✕</button>
            </div>
            {pkgMsg && <p style={{ color: 'var(--color-success, #28a745)' }}>{pkgMsg}</p>}
            {pkgError && <p style={{ color: 'var(--color-danger)' }}>{pkgError}</p>}
            <form onSubmit={handleSavePkg}>
              <div className="form-group">
                <label>Name *</label>
                <input className="form-control" value={pkgName} onChange={(e) => setPkgName(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Tier Order *</label>
                <input type="number" className="form-control" value={pkgTierOrder} onChange={(e) => setPkgTierOrder(e.target.value)} required min={1} />
              </div>
              <div className="form-group">
                <label>Description *</label>
                <textarea className="form-control" rows={3} value={pkgDesc} onChange={(e) => setPkgDesc(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Included Services (comma-separated) *</label>
                <textarea
                  className="form-control"
                  rows={3}
                  value={pkgServices}
                  onChange={(e) => setPkgServices(e.target.value)}
                  placeholder="Blood panel, ECG, BMI assessment, Eye exam..."
                  required
                />
              </div>
              <div className="form-group">
                <label>Price Range Display *</label>
                <input className="form-control" value={pkgPrice} onChange={(e) => setPkgPrice(e.target.value)} placeholder="$500–$800 per employee" required />
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="submit" className="btn btn-primary">Save</button>
                <button type="button" className="btn btn-outline" onClick={() => setShowPkgModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
