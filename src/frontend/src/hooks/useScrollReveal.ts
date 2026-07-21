import { useEffect } from 'react';
import type { RefObject } from 'react';

/**
 * Wires up an IntersectionObserver that adds the `visible` class to any
 * `.reveal`, `.reveal-left`, or `.reveal-right` descendants of `ref` when
 * they scroll into view.
 *
 * `trigger` must be passed whenever the section is conditionally rendered
 * based on async data (e.g. pass `!loading`).  The effect re-runs whenever
 * `trigger` changes, so when loading flips to false and the section appears
 * in the DOM the observer is created against the real element rather than a
 * null ref captured at mount time.
 */
export function useScrollReveal(ref: RefObject<HTMLElement | null>, trigger?: unknown) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const targets = el.querySelectorAll('.reveal, .reveal-left, .reveal-right');
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            requestAnimationFrame(() => entry.target.classList.add('visible'));
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 },
    );
    // Apply stagger delays to children of .stagger-children
    el.querySelectorAll('.stagger-children').forEach((parent) => {
      Array.from(parent.querySelectorAll('.reveal')).forEach((child, i) => {
        (child as HTMLElement).style.setProperty('--stagger-delay', `${i * 80}ms`);
      });
    });
    targets.forEach((t) => observer.observe(t));
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ref, trigger]);
}
