/**
 * REQ-11 — Interactive 1-5 star rating input.
 */
import { useState } from 'react';
import { Star } from 'lucide-react';

interface Props {
  value: number;
  onChange: (value: number) => void;
  label?: string;
  disabled?: boolean;
}

export function StarRating({ value, onChange, label, disabled = false }: Props) {
  const [hovered, setHovered] = useState(0);

  return (
    <div>
      {label && (
        <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>{label}</div>
      )}
      <div style={{ display: 'flex', gap: '0.25rem' }} role="group" aria-label={label}>
        {[1, 2, 3, 4, 5].map((star) => {
          const filled = star <= (hovered || value);
          return (
            <button
              key={star}
              type="button"
              aria-label={`${star} star${star !== 1 ? 's' : ''}`}
              aria-pressed={star === value}
              disabled={disabled}
              onClick={() => !disabled && onChange(star)}
              onMouseEnter={() => !disabled && setHovered(star)}
              onMouseLeave={() => !disabled && setHovered(0)}
              style={{
                background: 'none',
                border: 'none',
                cursor: disabled ? 'default' : 'pointer',
                padding: '0.15rem',
                color: filled ? '#f59e0b' : 'var(--color-text-light)',
                transition: 'color 0.1s',
              }}
            >
              <Star
                size={22}
                fill={filled ? '#f59e0b' : 'none'}
                stroke={filled ? '#f59e0b' : 'currentColor'}
              />
            </button>
          );
        })}
        {value > 0 && (
          <span style={{ alignSelf: 'center', marginLeft: '0.4rem', fontSize: '0.85rem', color: 'var(--color-text-light)' }}>
            {value}/5
          </span>
        )}
      </div>
    </div>
  );
}
