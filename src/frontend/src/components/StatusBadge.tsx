import { Check, Clock, X, Loader } from 'lucide-react';
import { statusBadgeClass } from '../utils/format';

function StatusIcon({ status }: { status: string }) {
  const s = status.toLowerCase();
  if (s === 'completed') return <Check size={12} />;
  if (s === 'scheduled' || s === 'pending') return <Clock size={12} />;
  if (s === 'cancelled' || s === 'noshow') return <X size={12} />;
  if (s === 'inprogress') return <Loader size={12} />;
  return null;
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={statusBadgeClass(status)} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
      <StatusIcon status={status} />
      {status}
    </span>
  );
}
