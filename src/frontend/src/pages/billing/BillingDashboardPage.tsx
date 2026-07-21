import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Receipt, AlertCircle, TrendingUp, Users } from 'lucide-react';
import { getBillingDashboard } from '../../api/billing';
import { extractErrorMessage } from '../../api/client';
import { formatCents } from '../../utils/format';
import type { BillingDashboard } from '../../types';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

export function BillingDashboardPage() {
  const [data, setData] = useState<BillingDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    setError(null);
    getBillingDashboard()
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  const tiles = data
    ? [
        {
          icon: <Receipt size={28} />,
          value: data.outstanding_invoices,
          label: 'Outstanding Invoices',
          link: '/billing/invoices?status=Pending',
          color: 'var(--color-warning)',
        },
        {
          icon: <AlertCircle size={28} />,
          value: data.awaiting_claims,
          label: 'Awaiting Insurance Claims',
          link: '/billing/invoices?has_insurance_claim=1',
          color: 'var(--color-danger)',
        },
        {
          icon: <TrendingUp size={28} />,
          value: formatCents(data.collected_this_month_cents),
          label: 'Collected This Month',
          link: '/billing/invoices?status=Paid',
          color: 'var(--color-success)',
        },
        {
          icon: <Users size={28} />,
          value: data.total_patients_billed,
          label: 'Total Patients Billed',
          link: '/billing/patients',
          color: 'var(--color-primary)',
        },
      ]
    : [];

  return (
    <div>
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <h2 style={{ margin: 0 }}>Billing Dashboard</h2>
      </div>

      {loading ? (
        <SkeletonBlock lines={4} />
      ) : error ? (
        <PageError message={error} onRetry={load} />
      ) : (
        <div className="billing-tiles">
          {tiles.map((t) => (
            <Link key={t.label} to={t.link} style={{ textDecoration: 'none' }}>
              <div className="billing-tile">
                <div className="billing-tile__icon" style={{ color: t.color }}>
                  {t.icon}
                </div>
                <div className="billing-tile__value">{t.value}</div>
                <div className="billing-tile__label">{t.label}</div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
