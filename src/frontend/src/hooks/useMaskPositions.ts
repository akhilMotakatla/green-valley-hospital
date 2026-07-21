import { useImageWidth } from './useImageWidth';

export interface MosaicCardSpec {
  /** Unique key for the card. */
  id: string;
  /** Horizontal offset of the card's top-left corner within the mosaic canvas, in px. */
  x: number;
  /** Vertical offset of the card's top-left corner within the mosaic canvas, in px. */
  y: number;
  /** Card width, in px. Currently unused in the math (canvasWidth drives scale) but kept for callers. */
  width: number;
  /** Card height, in px. */
  height: number;
}

export interface MaskPosition {
  backgroundSize: string;
  backgroundPosition: string;
}

export interface UseMaskPositionsResult {
  positions: Record<string, MaskPosition>;
  ready: boolean;
}

/**
 * Computes shared `backgroundSize` / `backgroundPosition` values for a set
 * of "window" cards that together form a mosaic revealing slices of one
 * large source image (`imageSrc`). Every card is given the EXACT same
 * `backgroundSize` — only `backgroundPosition` differs, offset by each
 * card's position within a shared virtual canvas — which is what produces
 * the illusion of a single photograph cut into separate framed cards.
 *
 * `canvasWidth` / `canvasHeight` describe the total virtual mosaic area
 * (e.g. all rows + gaps of the hero section). `focalX` (0-1) lets the
 * caller bias which horizontal slice of the source photo is centered —
 * useful for re-framing the same photo differently on mobile vs desktop.
 */
export function useMaskPositions(
  imageSrc: string,
  cards: MosaicCardSpec[],
  canvasWidth: number,
  canvasHeight: number,
  focalX = 0.5,
): UseMaskPositionsResult {
  const { naturalWidth, naturalHeight, loaded } = useImageWidth(imageSrc);
  const ready = loaded && canvasWidth > 0 && canvasHeight > 0 && naturalWidth > 0;
  const positions: Record<string, MaskPosition> = {};

  if (ready) {
    const naturalRatio = naturalWidth / naturalHeight;
    const canvasRatio = canvasWidth / canvasHeight;

    let bgWidth: number;
    let bgHeight: number;
    if (naturalRatio > canvasRatio) {
      // Source photo is relatively wider than the mosaic canvas — fit to
      // canvas height, letting width overflow (cropped left/right).
      bgHeight = canvasHeight;
      bgWidth = canvasHeight * naturalRatio;
    } else {
      // Source photo is relatively taller — fit to canvas width, letting
      // height overflow (cropped top/bottom).
      bgWidth = canvasWidth;
      bgHeight = canvasWidth / naturalRatio;
    }

    const offsetX = focalX * (canvasWidth - bgWidth);
    const offsetY = (canvasHeight - bgHeight) / 2;

    for (const card of cards) {
      positions[card.id] = {
        backgroundSize: `${bgWidth}px ${bgHeight}px`,
        backgroundPosition: `${offsetX - card.x}px ${offsetY - card.y}px`,
      };
    }
  }

  return { positions, ready };
}
