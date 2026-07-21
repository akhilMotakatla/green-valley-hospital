import { useEffect, useState } from 'react';

/**
 * Tracks whether the viewport is at or below `breakpoint` (px) using
 * `matchMedia`, so components can re-frame layout (and, for the mosaic
 * hero, re-frame which slice of a shared photo is in view) per breakpoint.
 */
export function useIsMobile(breakpoint = 767): boolean {
  const [isMobile, setIsMobile] = useState<boolean>(() =>
    typeof window !== 'undefined' ? window.innerWidth <= breakpoint : false,
  );

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${breakpoint}px)`);
    function onChange() {
      setIsMobile(mql.matches);
    }
    onChange();
    mql.addEventListener('change', onChange);
    return () => mql.removeEventListener('change', onChange);
  }, [breakpoint]);

  return isMobile;
}
