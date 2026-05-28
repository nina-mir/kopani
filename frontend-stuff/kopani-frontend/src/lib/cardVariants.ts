/**
 * Card visual variant helpers.
 *
 * Stage 1:
 * Decide which fallback texture class a card should use based on content type.
 *
 * Keep this file boring and declarative. Future card-variation rules can live here.
 */

export type CardTextureName =
  | "fiction"
  | "nonfiction"
  | "poetry"
  | "interview"
  | "translation"
  | "art"
  | "default";

const CONTENT_TYPE_TO_TEXTURE: Record<string, CardTextureName> = {
  fiction: "fiction",
  nonfiction: "nonfiction",
  essay: "nonfiction",
  review: "nonfiction",
  book_review: "nonfiction",
  art_review: "nonfiction",
  poetry: "poetry",
  interview: "interview",
  translation: "translation",
  art: "art",
  visual_art: "art",
  youth_portfolio: "poetry",
};

/**
 * Normalize loose database/source content types into a safe lookup key.
 */
function normalizeContentType(contentType?: string): string {
  return (contentType ?? "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/-/g, "_");
}

/**
 * Returns the CSS class used by the card fallback texture layer.
 */
export function getCardTextureClass(contentType?: string): string {
  const key = normalizeContentType(contentType);
  const texture = CONTENT_TYPE_TO_TEXTURE[key] ?? "default";

  return `kopani-card-texture kopani-card-texture--${texture}`;
}

/**
 * Decide whether this card should use a read-time gauge.
 *
 * Stage 2 rule:
 * One card per row of three gets the gauge.
 *
 * Assumption:
 * The parent grid renders cards in rows of 3 on desktop.
 */
export function shouldUseReadTimeGauge(index?: number): boolean {
  if (typeof index !== "number") return false;

  return index % 3 === 0;
}

/**
 * Convert read time into a gauge percentage.
 *
 * Scale:
 * 0 min  = 0%
 * 5 min  = 20%
 * 10 min = 40%
 * 15 min = 60%
 * 20 min = 80%
 * 25+    = 100%
 */
export function getReadTimeGaugePercent(readTimeMinutes?: number): number {
  if (!readTimeMinutes || readTimeMinutes <= 0) return 0;

  const percent = (readTimeMinutes / 25) * 100;

  return Math.min(Math.round(percent), 100);
}

/**
 * Human label for the gauge.
 */
export function getReadTimeGaugeLabel(readTimeMinutes?: number): string {
  if (!readTimeMinutes || readTimeMinutes <= 0) return "unknown";

  if (readTimeMinutes >= 20) return `${readTimeMinutes} min · long`;
  if (readTimeMinutes <= 5) return `${readTimeMinutes} min · brief`;

  return `${readTimeMinutes} min`;
}