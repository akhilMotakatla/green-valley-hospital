import { AlertCircle } from 'lucide-react';

interface PageErrorProps {
  message: string;
  onRetry?: () => void;
}

export function PageError({ message, onRetry }: PageErrorProps) {
  return (
    <div
      className="card"
      style={{
        textAlign: 'center',
        padding: '2rem',
        maxWidth: 480,
        margin: '2rem auto',
      }}
    >
      <AlertCircle size={32} color="var(--color-danger)" style={{ margin: '0 auto 0.75rem' }} />
      <p style={{ color: 'var(--color-danger)', marginBottom: onRetry ? '1rem' : 0 }}>{message}</p>
      {onRetry && (
        <button className="btn btn-outline" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}
