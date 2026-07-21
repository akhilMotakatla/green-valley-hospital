import type { CSSProperties, ReactNode } from 'react';

interface MaskedCardProps {
  /** Shared source image URL — identical across every card in the mosaic. */
  src: string;
  backgroundSize: string;
  backgroundPosition: string;
  /** Whether position math is ready (image preloaded + container measured). */
  ready: boolean;
  className?: string;
  style?: CSSProperties;
  children?: ReactNode;
  /** Accessible label; omit for purely decorative cards whose surrounding text conveys meaning. */
  ariaLabel?: string;
}

/**
 * A single "window" card that reveals one slice of a shared background
 * photo. Combined with `useMaskPositions`, multiple `MaskedCard`s using the
 * same `src` but different `backgroundPosition` values create the illusion
 * of one large photograph cut into separate framed cards.
 */
export function MaskedCard({
  src,
  backgroundSize,
  backgroundPosition,
  ready,
  className,
  style,
  children,
  ariaLabel,
}: MaskedCardProps) {
  return (
    <div
      className={`masked-card${className ? ` ${className}` : ''}`}
      role={ariaLabel ? 'img' : undefined}
      aria-label={ariaLabel || undefined}
      aria-hidden={ariaLabel ? undefined : true}
      style={{
        backgroundImage: `url(${src})`,
        backgroundSize,
        backgroundPosition,
        backgroundRepeat: 'no-repeat',
        opacity: ready ? 1 : 0,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
