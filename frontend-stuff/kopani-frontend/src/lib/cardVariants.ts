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