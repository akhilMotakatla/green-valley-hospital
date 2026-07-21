import { useEffect, useRef, useState, type RefObject } from 'react';

/**
 * IntersectionObserver-driven reveal for a fixed number of sibling elements
 * that need per-index stagger rather than DOM-order stagger (e.g. mosaic
 * hero cards). Returns a `boolean[]` of length `count`; index `i` flips to
 * `true` (and stays true) once `ref`'s element crosses `threshold`, with
 * each subsequent index delayed by 120ms. Fires once.
 */
export function useStaggeredReveal(
  ref: RefObject<HTMLElement | null>,
  count: number,
  threshold = 0.15,
): boolean[] {
  const [visible, setVisible] = useState<boolean[]>(() => Array(count).fill(false));
  const firedRef = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisible(Array(count).fill(true));
      return;
    }

    const timers: ReturnType<typeof setTimeout>[] = [];
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !firedRef.current) {
            firedRef.current = true;
            for (let i = 0; i < count; i++) {
              timers.push(
                setTimeout(() => {
                  setVisible((prev) => {
                    const next = [...prev];
                    next[i] = true;
                    return next;
                  });
                }, i * 120),
              );
            }
            observer.disconnect();
          }
        });
      },
      { threshold },
    );
    observer.observe(el);
    return () => {
      observer.disconnect();
      timers.forEach(clearTimeout);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ref, count, threshold]);

  return visible;
}
