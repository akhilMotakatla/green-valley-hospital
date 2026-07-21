import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { FlaskConical } from 'lucide-react';
import {
  amendLabResult,
  getLabOrderResults,
  listLabOrders,
  setLabOrderStatus,
  submitLabResult,
} from '../../api/lab';
import type { LabOrder } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { StatusBadge } from '../../components/StatusBadge';
import { Pager } from '../../components/Pager';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

export function LabOrdersPage() {
  const [items, setItems] = useState<LabOrder[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [testType, setTestType] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [activeOrderId, setActiveOrderId] = useState<number | null>(null);
  const [resultData, setResultData] = useState('');
  const [resultFile, setResultFile] = useState<File | null>(null);
  const [resultMsg, setResultMsg] = useState<string | null>(null);
  const [existingResults, setExistingResults] = useState<LabOrder[]>([]);
  const pageSize = 15;

  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    listLabOrders({
      test_type: testType || undefined,
      status: status || undefined,
      page,
      page_size: pageSize,
    })
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
        setLoading(false);
      })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, [testType, status, page]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleStatus(orderId: number, newStatus: 'InProgress' | 'Completed') {
    try {
      await setLabOrderStatus(orderId, newStatus);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  function openResultForm(orderId: number) {
    setActiveOrderId(orderId);
    setResultData('');
    setResultFile(null);
    setResultMsg(null);
    getLabOrderResults(orderId)
      .then((r) => setExistingResults(r.results))
      .catch(() => setExistingResults([]));
  }

  async function handleSubmitResult(e: FormEvent, amend: boolean) {
    e.preventDefault();
    if (!activeOrderId) return;
    setResultMsg(null);
    try {
      const fn = amend ? amendLabResult : submitLabResult;
      await fn(activeOrderId, { result_data: resultData, file: resultFile ?? undefined });
      setResultMsg('Result saved.');
      setResultData('');
      setResultFile(null);
      load();
      const r = await getLabOrderResults(activeOrderId);
      setExistingResults(r.results);
    } catch (err) {
      setResultMsg(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <h1>Lab / X-ray / Scan Order Queue</h1>
      <div className="toolbar">
        <label>
          Test type
          <select
            value={testType}
            onChange={(e) => {
              setTestType(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All</option>
            <option value="Lab">Lab</option>
            <option value="XRay">X-Ray</option>
            <option value="Scan">Scan</option>
          </select>
        </label>
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
            <option value="InProgress">In Progress</option>
            <option value="Completed">Completed</option>
          </select>
        </label>
      </div>
      {error && <PageError message={error} onRetry={load} />}
      {loading ? (
        <SkeletonBlock lines={5} />
      ) : items.length === 0 && !error ? (
        <div className="empty-state">
          <FlaskConical size={80} color="var(--color-text-light)" />
          <h3>No orders found</h3>
        </div>
      ) : (
        <>
        <table className="data-table">
        <thead>
          <tr>
            <th>Patient</th>
            <th>DOB</th>
            <th>Ordering Doctor</th>
            <th>Test</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((o) => (
            <tr key={o.order_id}>
              <td>{o.patient_name}</td>
              <td>{o.patient_dob}</td>
              <td>{o.ordering_doctor_name}</td>
              <td>
                {o.test_type} {o.test_subtype ? `(${o.test_subtype})` : ''}
              </td>
              <td>
                <StatusBadge status={o.status} />
              </td>
              <td style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {o.status === 'Pending' && (
                  <button className="btn btn-outline" onClick={() => handleStatus(o.order_id, 'InProgress')}>
                    Start
                  </button>
                )}
                {o.status !== 'Completed' && (
                  <button className="btn btn-outline" onClick={() => handleStatus(o.order_id, 'Completed')}>
                    Mark Completed
                  </button>
                )}
                <button className="btn btn-primary" onClick={() => openResultForm(o.order_id)}>
                  Enter Result
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <Pager page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
        </>
      )}

      {activeOrderId && (
        <section className="section card">
          <h2>Result for Order #{activeOrderId}</h2>
          {existingResults.length > 0 && (
            <div className="section">
              <h3>Existing versions</h3>
              <ul>
                {existingResults.map((r) => (
                  <li key={r.order_id}>
                    v{(r as unknown as { version?: number }).version} —{' '}
                    {(r as unknown as { result_data?: string }).result_data} —{' '}
                    {formatDateTime((r as unknown as { finalized_at?: string }).finalized_at ?? '')}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {resultMsg && (
            <p className={resultMsg.includes('saved') ? 'success-text' : 'error-text'}>{resultMsg}</p>
          )}
          <form
            className="form"
            onSubmit={(e) => handleSubmitResult(e, existingResults.length > 0)}
          >
            <label>
              Result data
              <textarea rows={3} value={resultData} onChange={(e) => setResultData(e.target.value)} required />
            </label>
            <label>
              Attachment (optional)
              <input type="file" onChange={(e) => setResultFile(e.target.files?.[0] ?? null)} />
            </label>
            <button className="btn btn-primary" type="submit">
              {existingResults.length > 0 ? 'Save Amended Result' : 'Save Result (finalize)'}
            </button>
            {existingResults.length > 0 && (
              <p className="muted">A finalized result already exists — this will create a new versioned entry.</p>
            )}
          </form>
        </section>
      )}
    </div>
  );
}
