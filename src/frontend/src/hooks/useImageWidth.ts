import { useEffect, useState } from 'react';

interface ImageDimensions {
  naturalWidth: number;
  naturalHeight: number;
  loaded: boolean;
}

/**
 * Preloads `src` via the native `Image()` constructor and reports its
 * natural pixel dimensions once decoded. Used by the masked-card mosaic
 * hero to compute correct backgroundSize / backgroundPosition math before
 * the browser paints the CSS background-image on each card.
 */
export function useImageWidth(src: string): ImageDimensions {
  const [dims, setDims] = useState<ImageDimensions>({
    naturalWidth: 0,
    naturalHeight: 0,
    loaded: false,
  });

  useEffect(() => {
    let cancelled = false;
    setDims({ naturalWidth: 0, naturalHeight: 0, loaded: false });
    const img = new Image();
    img.onload = () => {
      if (!cancelled) {
        setDims({ naturalWidth: img.naturalWidth, naturalHeight: img.naturalHeight, loaded: true });
      }
    };
    // If the source image 404s or fails to decode, fall back to a sane
    // 16:9-ish aspect ratio rather than leaving `loaded` false forever —
    // callers rely on `loaded` to reveal content (headline text, CTAs),
    // not just the photo itself, so a failed image must not hide the page.
    img.onerror = () => {
      if (!cancelled) {
        setDims({ naturalWidth: 1600, naturalHeight: 700, loaded: true });
      }
    };
    img.src = src;
    return () => {
      cancelled = true;
    };
  }, [src]);

  return dims;
}
