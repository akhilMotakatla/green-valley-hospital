import { useEffect, useState, type RefObject } from 'react';

/**
 * Measures the current pixel width of `ref`'s element via ResizeObserver.
 * Used alongside `useMaskPositions` so the masked-card mosaic hero can
 * recompute its shared background math whenever the section is resized
 * (window resize, orientation change, sidebar toggling, etc.).
 */
export function useContainerWidth(ref: RefObject<HTMLElement | null>): number {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setWidth(entry.contentRect.width);
      }
    });
    observer.observe(el);
    setWidth(el.getBoundingClientRect().width);
    return () => observer.disconnect();
  }, [ref]);

  return width;
}
