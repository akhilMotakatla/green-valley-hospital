import { useEffect, useState } from 'react';

const SESSION_KEY = 'gvh_splash_shown';
const COUNT_DURATION_MS = 2000;
const FADE_DURATION_MS = 500;

/**
 * Full-viewport splash overlay shown once per browser session (gated via
 * sessionStorage so it doesn't replay on every in-app route navigation).
 * Counts 0 -> 100 over ~2s, then fades out and unmounts.
 */
export function SplashScreen() {
  const [shouldRender, setShouldRender] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    try {
      return sessionStorage.getItem(SESSION_KEY) !== '1';
    } catch {
      return true;
    }
  });
  const [count, setCount] = useState(0);
  const [fadingOut, setFadingOut] = useState(false);

  useEffect(() => {
    if (!shouldRender) return;

    try {
      sessionStorage.setItem(SESSION_KEY, '1');
    } catch {
      /* sessionStorage unavailable — splash will simply replay; non-fatal */
    }

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setCount(100);
      setFadingOut(true);
      const t = setTimeout(() => setShouldRender(false), 50);
      return () => clearTimeout(t);
    }

    const start = performance.now();
    let raf = 0;
    let fadeTimer: ReturnType<typeof setTimeout>;

    function tick(now: number) {
      const progress = Math.min((now - start) / COUNT_DURATION_MS, 1);
      setCount(Math.round(progress * 100));
      if (progress < 1) {
        raf = requestAnimationFrame(tick);
      } else {
        setFadingOut(true);
        fadeTimer = setTimeout(() => setShouldRender(false), FADE_DURATION_MS);
      }
    }
    raf = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(fadeTimer);
    };
  }, [shouldRender]);

  if (!shouldRender) return null;

  return (
    <div className={`splash-screen${fadingOut ? ' splash-screen--fade-out' : ''}`} aria-hidden="true">
      <span className="splash-screen-counter">{count}</span>
    </div>
  );
}
