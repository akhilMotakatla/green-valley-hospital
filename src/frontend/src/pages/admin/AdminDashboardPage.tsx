import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, UserCheck, CalendarCheck, FlaskConical, UserPlus, Plus, MessageSquare } from 'lucide-react';
import { getDashboardSummary } from '../../api/admin';
import type { DashboardSummary } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

const STAT_CONFIG = [
  {
    key: 'patient_count' as keyof DashboardSummary,
    label: 'Patients',
    icon: <Users size={36} />,
    borderColor: 'var(--color-primary)',
  },
  {
    key: 'doctor_count' as keyof DashboardSummary,
    label: 'Doctors',
    icon: <UserCheck size={36} />,
    borderColor: 'var(--color-info)',
  },
  {
    key: 'appointments_today' as keyof DashboardSummary,
    label: 'Appointments Today',
    icon: <CalendarCheck size={36} />,
    borderColor: 'var(--color-warn)',
  },
  {
    key: 'pending_lab_orders' as keyof DashboardSummary,
    label: 'Pending Lab Orders',
    icon: <FlaskConical size={36} />,
    borderColor: 'var(--color-accent)',
  },
];

export function AdminDashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getDashboardSummary()
      .then((s) => { setSummary(s); setLoading(false); })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>Admin Dashboard</h1>

      {loading ? (
        <SkeletonBlock lines={4} widths={['100%', '100%', '100%', '100%']} />
      ) : error ? (
        <PageError message={error} onRetry={load} />
      ) : summary ? (
        <>
          {/* Stat cards */}
          <div className="stat-grid">
            {STAT_CONFIG.map((cfg) => (
              <div
                key={cfg.key}
                className="stat-card"
                style={{ borderLeft: `4px solid ${cfg.borderColor}` }}
              >
                <div className="stat-icon-circle" style={{ background: 'var(--color-primary-light)', color: 'var(--color-primary)' }}>
                  {cfg.icon}
                </div>
                <div className="stat-value">{summary[cfg.key]}</div>
                <div className="stat-label">{cfg.label}</div>
              </div>
            ))}
          </div>

          {/* Quick actions */}
          <h2 style={{ marginBottom: '1rem' }}>Quick Actions</h2>
          <div className="quick-actions">
            <Link to="/admin/users" className="btn btn-outline">
              <UserPlus size={18} /> Add User
            </Link>
            <Link to="/admin/departments" className="btn btn-outline">
              <Plus size={18} /> New Department
            </Link>
            <Link to="/admin/appointments" className="btn btn-outline">
              <CalendarCheck size={18} /> View Appointments
            </Link>
            <Link to="/admin/contact-messages" className="btn btn-outline">
              <MessageSquare size={18} /> View Messages
            </Link>
          </div>
        </>
      ) : null}
    </div>
  );
}
