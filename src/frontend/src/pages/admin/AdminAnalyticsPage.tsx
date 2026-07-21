/**
 * REQ-06 — Admin Analytics Dashboard (/admin/analytics).
 *
 * Five chart sections load independently (parallel fetches, each has its own
 * loading / error state).  Date range and granularity are shared at the top
 * of the page; changing them re-fetches all sections simultaneously.
 *
 * Charts use Recharts (already in package.json ^2.15).
 */
import { useCallback, useEffect, useState } from 'react';
import { BarChart2, Download } from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  getAppointmentAnalytics,
  getNoShowRate,
  getRevenueAnalytics,
  getDepartmentVolume,
  getPatientAcquisition,
  downloadAnalyticsCsv,
} from '../../api/analytics';
import type {
  AppointmentAnalytics,
  NoShowAnalytics,
  RevenueAnalytics,
  DepartmentVolumeAnalytics,
  PatientAcquisitionAnalytics,
  Granularity,
  AnalyticsMetric,
} from '../../api/analytics';
import { extractErrorMessage } from '../../api/client';

// ---------------------------------------------------------------------------
// Date helpers
// ---------------------------------------------------------------------------

function toIso(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function presetRange(kind: '7d' | '30d' | '90d' | '12m'): [string, string] {
  const today = new Date();
  const from = new Date(today);
  if (kind === '7d') from.setDate(today.getDate() - 7);
  else if (kind === '30d') from.setDate(today.getDate() - 30);
  else if (kind === '90d') from.setDate(today.getDate() - 90);
  else from.setFullYear(today.getFullYear() - 1);
  return [toIso(from), toIso(today)];
}

const DEFAULT_FROM = presetRange('30d')[0];
const DEFAULT_TO = presetRange('30d')[1];

// ---------------------------------------------------------------------------
// Small sub-components
// ---------------------------------------------------------------------------

function ChartSkeleton() {
  return (
    <div
      style={{
        height: 260,
        background: 'linear-gradient(90deg, var(--color-surface-alt, #f0f0f0) 25%, var(--color-border, #e0e0e0) 50%, var(--color-surface-alt, #f0f0f0) 75%)',
        backgroundSize: '400% 100%',
        animation: 'shimmer 1.4s infinite',
        borderRadius: 8,
      }}
      aria-label="Loading chart…"
    />
  );
}

function ChartError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div
      style={{
        padding: '1.5rem',
        background: '#fff0f0',
        border: '1px solid #f5a0a0',
        borderRadius: 8,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
        color: '#c53030',
      }}
    >
      <span>{message}</span>
      <button className="btn btn-secondary" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}

function StatTile({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div
      style={{
        flex: '1 1 160px',
        padding: '1rem',
        background: 'var(--color-surface-alt, #f7f7f7)',
        border: '1px solid var(--color-border, #e0e0e0)',
        borderRadius: 8,
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '1.4rem', fontWeight: 700, color: color ?? 'inherit' }}>
        {value}
      </div>
      <div style={{ fontSize: '0.8rem', color: 'var(--color-text-light, #666)', marginTop: 4 }}>
        {label}
      </div>
    </div>
  );
}

function SectionCard({
  title,
  children,
  onExport,
  exporting,
}: {
  title: string;
  children: React.ReactNode;
  onExport?: () => void;
  exporting?: boolean;
}) {
  return (
    <div
      style={{
        background: 'var(--color-surface, #fff)',
        border: '1px solid var(--color-border, #e0e0e0)',
        borderRadius: 10,
        padding: '1.5rem',
        marginBottom: '1.5rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1rem',
        }}
      >
        <h2 style={{ margin: 0, fontSize: '1.1rem' }}>{title}</h2>
        {onExport && (
          <button
            className="btn btn-secondary"
            onClick={onExport}
            disabled={exporting}
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
          >
            <Download size={14} />
            {exporting ? 'Downloading…' : 'Export CSV'}
          </button>
        )}
      </div>
      {children}
    </div>
  );
}

const FEW_DATA_NOTE = (
  <p
    style={{
      fontSize: '0.85rem',
      color: 'var(--color-text-light, #666)',
      marginTop: '0.5rem',
    }}
  >
    More data will appear as appointments are recorded.
  </p>
);

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export function AdminAnalyticsPage() {
  // Shared date range state (ISO strings)
  const [fromDate, setFromDate] = useState(DEFAULT_FROM);
  const [toDate, setToDate] = useState(DEFAULT_TO);
  const [granularity, setGranularity] = useState<Granularity>('month');
  const [activePreset, setActivePreset] = useState<'7d' | '30d' | '90d' | '12m'>('30d');

  // Per-chart state
  const [apptData, setApptData] = useState<AppointmentAnalytics | null>(null);
  const [apptLoading, setApptLoading] = useState(true);
  const [apptError, setApptError] = useState<string | null>(null);

  const [noShowData, setNoShowData] = useState<NoShowAnalytics | null>(null);
  const [noShowLoading, setNoShowLoading] = useState(true);
  const [noShowError, setNoShowError] = useState<string | null>(null);

  const [revenueData, setRevenueData] = useState<RevenueAnalytics | null>(null);
  const [revenueLoading, setRevenueLoading] = useState(true);
  const [revenueError, setRevenueError] = useState<string | null>(null);

  const [deptData, setDeptData] = useState<DepartmentVolumeAnalytics | null>(null);
  const [deptLoading, setDeptLoading] = useState(true);
  const [deptError, setDeptError] = useState<string | null>(null);

  const [acqData, setAcqData] = useState<PatientAcquisitionAnalytics | null>(null);
  const [acqLoading, setAcqLoading] = useState(true);
  const [acqError, setAcqError] = useState<string | null>(null);

  // Export state per metric
  const [exporting, setExporting] = useState<AnalyticsMetric | null>(null);

  // ---------------------------------------------------------------------------
  // Fetch helpers
  // ---------------------------------------------------------------------------

  const fetchAppt = useCallback(() => {
    setApptLoading(true);
    setApptError(null);
    getAppointmentAnalytics({ from_date: fromDate, to_date: toDate, granularity })
      .then((d) => { setApptData(d); setApptLoading(false); })
      .catch((e) => { setApptError(extractErrorMessage(e)); setApptLoading(false); });
  }, [fromDate, toDate, granularity]);

  const fetchNoShow = useCallback(() => {
    setNoShowLoading(true);
    setNoShowError(null);
    getNoShowRate({ from_date: fromDate, to_date: toDate, granularity })
      .then((d) => { setNoShowData(d); setNoShowLoading(false); })
      .catch((e) => { setNoShowError(extractErrorMessage(e)); setNoShowLoading(false); });
  }, [fromDate, toDate, granularity]);

  const fetchRevenue = useCallback(() => {
    setRevenueLoading(true);
    setRevenueError(null);
    getRevenueAnalytics({ from_date: fromDate, to_date: toDate })
      .then((d) => { setRevenueData(d); setRevenueLoading(false); })
      .catch((e) => { setRevenueError(extractErrorMessage(e)); setRevenueLoading(false); });
  }, [fromDate, toDate]);

  const fetchDept = useCallback(() => {
    setDeptLoading(true);
    setDeptError(null);
    getDepartmentVolume({ from_date: fromDate, to_date: toDate })
      .then((d) => { setDeptData(d); setDeptLoading(false); })
      .catch((e) => { setDeptError(extractErrorMessage(e)); setDeptLoading(false); });
  }, [fromDate, toDate]);

  const fetchAcq = useCallback(() => {
    setAcqLoading(true);
    setAcqError(null);
    getPatientAcquisition({ from_date: fromDate, to_date: toDate })
      .then((d) => { setAcqData(d); setAcqLoading(false); })
      .catch((e) => { setAcqError(extractErrorMessage(e)); setAcqLoading(false); });
  }, [fromDate, toDate]);

  // Fire all 5 fetches simultaneously when date range / granularity changes
  useEffect(() => {
    fetchAppt();
    fetchNoShow();
    fetchRevenue();
    fetchDept();
    fetchAcq();
  }, [fetchAppt, fetchNoShow, fetchRevenue, fetchDept, fetchAcq]);

  // ---------------------------------------------------------------------------
  // Preset button handler
  // ---------------------------------------------------------------------------

  function applyPreset(kind: '7d' | '30d' | '90d' | '12m') {
    const [f, t] = presetRange(kind);
    setActivePreset(kind);
    setFromDate(f);
    setToDate(t);
  }

  // ---------------------------------------------------------------------------
  // Export handler
  // ---------------------------------------------------------------------------

  async function handleExport(metric: AnalyticsMetric) {
    setExporting(metric);
    try {
      const gran = metric === 'appointments' || metric === 'no_show_rate'
        ? granularity
        : undefined;
      await downloadAnalyticsCsv(metric, fromDate, toDate, gran);
    } catch (e) {
      alert('CSV export failed: ' + extractErrorMessage(e));
    } finally {
      setExporting(null);
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  const presets: { key: '7d' | '30d' | '90d' | '12m'; label: string }[] = [
    { key: '7d', label: '7 days' },
    { key: '30d', label: '30 days' },
    { key: '90d', label: '90 days' },
    { key: '12m', label: '12 months' },
  ];

  return (
    <div>
      <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <BarChart2 size={24} />
        Analytics Dashboard
      </h1>

      {/* ------------------------------------------------------------------ */}
      {/* Date range controls                                                  */}
      {/* ------------------------------------------------------------------ */}
      <div
        style={{
          background: 'var(--color-surface, #fff)',
          border: '1px solid var(--color-border, #e0e0e0)',
          borderRadius: 10,
          padding: '1.25rem',
          marginBottom: '1.5rem',
        }}
      >
        {/* Presets */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
          {presets.map((p) => (
            <button
              key={p.key}
              className={activePreset === p.key ? 'btn btn-primary' : 'btn btn-secondary'}
              onClick={() => applyPreset(p.key)}
              style={{ fontSize: '0.85rem' }}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Custom date inputs */}
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.9rem' }}>
            From
            <input
              type="date"
              value={fromDate}
              max={toDate}
              onChange={(e) => {
                setFromDate(e.target.value);
                setActivePreset('30d'); // clear preset highlight on custom input
              }}
            />
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.9rem' }}>
            To
            <input
              type="date"
              value={toDate}
              min={fromDate}
              onChange={(e) => {
                setToDate(e.target.value);
                setActivePreset('30d');
              }}
            />
          </label>

          {/* Granularity toggle (shown for all charts but primarily affects chart 1 & 2) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.9rem', marginLeft: 'auto' }}>
            <span style={{ color: 'var(--color-text-light, #666)' }}>Granularity:</span>
            {(['day', 'week', 'month'] as Granularity[]).map((g) => (
              <button
                key={g}
                className={granularity === g ? 'btn btn-primary' : 'btn btn-secondary'}
                onClick={() => setGranularity(g)}
                style={{ fontSize: '0.8rem', padding: '0.2rem 0.6rem', textTransform: 'capitalize' }}
              >
                {g.charAt(0).toUpperCase() + g.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Chart 1 — Appointment Volume                                         */}
      {/* ------------------------------------------------------------------ */}
      <SectionCard
        title="Appointment Volume"
        onExport={() => handleExport('appointments')}
        exporting={exporting === 'appointments'}
      >
        {apptLoading ? (
          <ChartSkeleton />
        ) : apptError ? (
          <ChartError message={apptError} onRetry={fetchAppt} />
        ) : !apptData || apptData.series.length === 0 ? (
          <p style={{ color: 'var(--color-text-light, #666)', padding: '2rem 0', textAlign: 'center' }}>
            No appointment data for the selected period.
          </p>
        ) : (
          <>
            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-light, #666)', marginBottom: '0.5rem' }}>
              Total: <strong>{apptData.total.toLocaleString()}</strong> appointments
            </p>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={apptData.series} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border, #e0e0e0)" />
                <XAxis dataKey="period" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#4F86C6" name="Appointments" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            {apptData.series.length < 3 && FEW_DATA_NOTE}
          </>
        )}
      </SectionCard>

      {/* ------------------------------------------------------------------ */}
      {/* Chart 2 — No-Show Rate                                               */}
      {/* ------------------------------------------------------------------ */}
      <SectionCard
        title="No-Show Rate"
        onExport={() => handleExport('no_show_rate')}
        exporting={exporting === 'no_show_rate'}
      >
        {noShowLoading ? (
          <ChartSkeleton />
        ) : noShowError ? (
          <ChartError message={noShowError} onRetry={fetchNoShow} />
        ) : !noShowData || noShowData.series.length === 0 ? (
          <p style={{ color: 'var(--color-text-light, #666)', padding: '2rem 0', textAlign: 'center' }}>
            No data for the selected period.
          </p>
        ) : (
          <>
            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-light, #666)', marginBottom: '0.5rem' }}>
              Overall no-show rate:{' '}
              <strong>{(noShowData.overall_rate * 100).toFixed(1)}%</strong>
            </p>
            <ResponsiveContainer width="100%" height={260}>
              <ComposedChart
                data={noShowData.series.map((d) => ({
                  ...d,
                  rate_pct: +(d.rate * 100).toFixed(2),
                }))}
                margin={{ top: 4, right: 40, bottom: 4, left: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border, #e0e0e0)" />
                <XAxis dataKey="period" tick={{ fontSize: 12 }} />
                <YAxis
                  yAxisId="left"
                  orientation="left"
                  tick={{ fontSize: 12 }}
                  label={{ value: 'Total', angle: -90, position: 'insideLeft', fontSize: 11, offset: 10 }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  domain={[0, 100]}
                  unit="%"
                  tick={{ fontSize: 12 }}
                  label={{ value: 'No-Show %', angle: 90, position: 'insideRight', fontSize: 11, offset: 10 }}
                />
                <Tooltip
                  formatter={(value: number, name: string) =>
                    name === 'No-Show %' ? [`${value}%`, name] : [value, name]
                  }
                />
                <Legend />
                <Bar yAxisId="left" dataKey="total" fill="#4F86C6" name="Total Appointments" radius={[3, 3, 0, 0]} />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="rate_pct"
                  stroke="#E05252"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  name="No-Show %"
                />
              </ComposedChart>
            </ResponsiveContainer>
            {noShowData.series.length < 3 && FEW_DATA_NOTE}
          </>
        )}
      </SectionCard>

      {/* ------------------------------------------------------------------ */}
      {/* Chart 3 — Revenue Summary                                            */}
      {/* ------------------------------------------------------------------ */}
      <SectionCard
        title="Revenue Summary"
        onExport={() => handleExport('revenue')}
        exporting={exporting === 'revenue'}
      >
        {revenueLoading ? (
          <ChartSkeleton />
        ) : revenueError ? (
          <ChartError message={revenueError} onRetry={fetchRevenue} />
        ) : !revenueData || revenueData.series.length === 0 ? (
          <p style={{ color: 'var(--color-text-light, #666)', padding: '2rem 0', textAlign: 'center' }}>
            No revenue data for the selected period.
          </p>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={revenueData.series} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border, #e0e0e0)" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(v: number) => `$${v.toLocaleString()}`}
                />
                <Tooltip
                  formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
                />
                <Legend />
                <Bar
                  dataKey="collected"
                  stackId="rev"
                  fill="#34C759"
                  name="Collected"
                  radius={[0, 0, 0, 0]}
                />
                <Bar
                  dataKey="outstanding"
                  stackId="rev"
                  fill="#FF9500"
                  name="Outstanding"
                  radius={[3, 3, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>

            {/* Summary stat tiles */}
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '1rem' }}>
              <StatTile
                label="Total Invoiced"
                value={`$${revenueData.total_invoiced.toLocaleString()}`}
              />
              <StatTile
                label="Total Collected"
                value={`$${revenueData.total_collected.toLocaleString()}`}
                color="#34C759"
              />
              <StatTile
                label="Total Outstanding"
                value={`$${revenueData.total_outstanding.toLocaleString()}`}
                color="#FF9500"
              />
            </div>
          </>
        )}
      </SectionCard>

      {/* ------------------------------------------------------------------ */}
      {/* Chart 4 — Department Volume                                          */}
      {/* ------------------------------------------------------------------ */}
      <SectionCard
        title="Department Appointment Volume"
        onExport={() => handleExport('department_volume')}
        exporting={exporting === 'department_volume'}
      >
        {deptLoading ? (
          <ChartSkeleton />
        ) : deptError ? (
          <ChartError message={deptError} onRetry={fetchDept} />
        ) : !deptData || deptData.departments.length === 0 ? (
          <p style={{ color: 'var(--color-text-light, #666)', padding: '2rem 0', textAlign: 'center' }}>
            No department data for the selected period.
          </p>
        ) : (
          <ResponsiveContainer
            width="100%"
            height={Math.max(220, deptData.departments.length * 38 + 40)}
          >
            <BarChart
              data={deptData.departments}
              layout="vertical"
              margin={{ top: 4, right: 40, bottom: 4, left: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border, #e0e0e0)" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis
                type="category"
                dataKey="name"
                width={130}
                tick={{ fontSize: 12 }}
              />
              <Tooltip />
              <Bar dataKey="count" fill="#5AC8FA" name="Appointments" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </SectionCard>

      {/* ------------------------------------------------------------------ */}
      {/* Chart 5 — Patient Acquisition                                        */}
      {/* ------------------------------------------------------------------ */}
      <SectionCard
        title="Patient Acquisition"
        onExport={() => handleExport('patient_acquisition')}
        exporting={exporting === 'patient_acquisition'}
      >
        {acqLoading ? (
          <ChartSkeleton />
        ) : acqError ? (
          <ChartError message={acqError} onRetry={fetchAcq} />
        ) : !acqData || acqData.series.length === 0 ? (
          <p style={{ color: 'var(--color-text-light, #666)', padding: '2rem 0', textAlign: 'center' }}>
            No patient registration data for the selected period.
          </p>
        ) : (
          <>
            {/* Stat tile above chart */}
            <div style={{ marginBottom: '0.75rem' }}>
              <StatTile
                label="Total New Patients"
                value={acqData.total_new.toLocaleString()}
                color="#4F86C6"
              />
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart
                data={acqData.series}
                margin={{ top: 4, right: 16, bottom: 4, left: 0 }}
              >
                <defs>
                  <linearGradient id="acqGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4F86C6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#4F86C6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border, #e0e0e0)" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="new_patients"
                  stroke="#4F86C6"
                  strokeWidth={2}
                  fill="url(#acqGrad)"
                  name="New Patients"
                  dot={{ r: 3 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </>
        )}
      </SectionCard>
    </div>
  );
}
