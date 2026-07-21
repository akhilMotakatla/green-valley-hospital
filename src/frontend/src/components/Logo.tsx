interface LogoProps {
  variant?: 'default' | 'white';
  size?: number;
}

export function Logo({ variant = 'default', size = 36 }: LogoProps) {
  const isWhite = variant === 'white';
  const circleFill = isWhite ? '#fff' : 'var(--color-primary)';
  const plusColor  = isWhite ? 'var(--color-primary)' : '#fff';
  const nameColor  = isWhite ? '#fff' : 'var(--color-text)';
  const subColor   = isWhite ? 'rgba(255,255,255,0.75)' : 'var(--color-text-muted)';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 36 36"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        style={{ flexShrink: 0 }}
      >
        <circle cx="18" cy="18" r="18" fill={circleFill} />
        {/* Medical cross */}
        <rect x="15" y="9"  width="6" height="18" rx="2" fill={plusColor} />
        <rect x="9"  y="15" width="18" height="6"  rx="2" fill={plusColor} />
      </svg>
      <span style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
        <span style={{
          fontFamily: "'Playfair Display', Georgia, serif",
          fontWeight: 700,
          fontSize: '1.0625rem',
          color: nameColor,
          letterSpacing: '-0.01em',
        }}>
          Green Valley
        </span>
        <span style={{
          fontFamily: "'Inter', sans-serif",
          fontWeight: 500,
          fontSize: '0.7rem',
          color: subColor,
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
        }}>
          Hospital
        </span>
      </span>
    </div>
  );
}
