/**
 * REQ-09 — Countdown timer for waitlist confirmation deadline.
 * Updates every second. Shows hours:minutes:seconds remaining.
 */
import { useEffect, useState } from 'react';
import { Clock } from 'lucide-react';

interface Props {
  deadline: string; // ISO-8601 UTC timestamp
}

function getSecondsRemaining(deadline: string): number {
  const deadlineMs = new Date(deadline).getTime();
  const nowMs = Date.now();
  return Math.max(0, Math.floor((deadlineMs - nowMs) / 1000));
}

function formatCountdown(seconds: number): string {
  if (seconds <= 0) return 'Expired';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) {
    return `${h}h ${m.toString().padStart(2, '0')}m ${s.toString().padStart(2, '0')}s`;
  }
  return `${m}m ${s.toString().padStart(2, '0')}s`;
}

export function WaitlistCountdown({ deadline }: Props) {
  const [seconds, setSeconds] = useState(() => getSecondsRemaining(deadline));

  useEffect(() => {
    setSeconds(getSecondsRemaining(deadline));
    const interval = setInterval(() => {
      setSeconds(getSecondsRemaining(deadline));
    }, 1000);
    return () => clearInterval(interval);
  }, [deadline]);

  const expired = seconds <= 0;
  const urgent = seconds > 0 && seconds < 3600; // less than 1 hour

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.3rem',
        fontWeight: 600,
        color: expired ? 'var(--color-danger, #dc3545)' : urgent ? '#e67e22' : 'var(--color-primary, #0d6efd)',
        fontVariantNumeric: 'tabular-nums',
      }}
      role="timer"
      aria-live="off"
      aria-label={`Time remaining: ${formatCountdown(seconds)}`}
    >
      <Clock size={14} aria-hidden="true" />
      {formatCountdown(seconds)}
    </span>
  );
}
