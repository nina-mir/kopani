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
 * One card per row of three gets the gauge.  (changed a bit since we are doing index % 6 now. See below!)
 *
 * Assumption:
 * The parent grid renders cards in rows of 3 on desktop.
 */
export function shouldUseReadTimeGauge(index?: number): boolean {
  if (typeof index !== "number") return false;

  return index % 6 === 0 || index % 6 === 4;
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

//  stage 3 artifact tab+spine

export type CardSpineName =
  | "fiction"
  | "nonfiction"
  | "poetry"
  | "interview"
  | "translation"
  | "art"
  | "default";

export type CardSpineVariant = {
  cardClass: string;
  spineClass: string;
  tabLabel: string;
  spineLabel: string;
};

/**
 * Stage 3:
 * Decide whether this card should receive the spine + tab artifact.
 *
 * Current cadence:
 * 0 → gauge
 * 1 → plain
 * 2 → spine
 * 3 → plain
 * 4 → gauge
 * 5 → plain
 *
 * This keeps artifacts from stacking too much while testing.
 */
export function shouldUseSpineArtifact(index?: number): boolean {
  if (typeof index !== "number") return false;

  return index % 6 === 2;
}

const CONTENT_TYPE_TO_SPINE: Record<string, CardSpineName> = {
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
  youth_portfolio: "art",
};

const SPINE_LABELS: Record<CardSpineName, string> = {
  fiction: "Fiction",
  nonfiction: "Essay",
  poetry: "Poetry",
  interview: "Interview",
  translation: "Translation",
  art: "Art",
  default: "Kopani",
};

/**
 * Return all classes/labels needed to render the spine + tab.
 */
export function getSpineVariant(
  contentType?: string,
  issueLabel?: string,
  dateLabel?: string
): CardSpineVariant {
  const key = normalizeContentType(contentType);
  const spine = CONTENT_TYPE_TO_SPINE[key] ?? "default";
  const tabLabel = SPINE_LABELS[spine];

  const shortDate =
    issueLabel ??
    dateLabel ??
    "Filed";

  return {
    cardClass: "kopani-card--spined",
    spineClass: `kopani-card-spine kopani-card-spine--${spine}`,
    tabLabel,
    spineLabel: `${tabLabel} · ${shortDate}`,
  };
}