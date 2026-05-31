// src/lib/searchShared.ts

/**
 * Shared search helpers for Kopani.
 *
 * Keep this file pure:
 * - no SQLite
 * - no better-sqlite3
 * - no Astro imports
 * - no browser-only globals
 *
 * It is safe to import from:
 * - src/lib/db.ts
 * - src/pages/search-index.json.ts
 * - browser/client-side search scripts
 */

export const WORDS_PER_MINUTE = 250;

export type SearchContributor = {
  name: string;
  href?: string;
};

export type SearchSort =
  | "relevance"
  | "title-az"
  | "shortest"
  | "longest";

export interface SearchSourcePiece {
  title: string;
  subtitle?: string;
  dek?: string;
  contentType: string;
  href: string;
  originalUrl: string;
  journalName: string;
  journalUrl?: string;
  authors: SearchContributor[];
  translators?: SearchContributor[];
  visualArtists?: SearchContributor[];
  dateLabel?: string;
  issueLabel?: string;
  readTimeMinutes?: number;
  wordCountEstimate?: number;
  imageUrl?: string;
  aiKeywords?: string[];
  featured?: boolean;
}

export interface SearchIndexItem {
  title: string;
  subtitle?: string;
  dek?: string;
  contentType: string;
  contentTypeLabel: string;
  href: string;
  originalUrl: string;
  journalName: string;
  journalUrl?: string;
  authors: SearchContributor[];
  translators: SearchContributor[];
  visualArtists: SearchContributor[];
  byline: string;
  dateLabel?: string;
  issueLabel?: string;
  readTimeMinutes?: number;
  wordCountEstimate?: number;
  readingSortMinutes: number | null;
  imageUrl?: string;
  aiKeywords: string[];
  featured?: boolean;

  /**
   * Lowercased, normalized searchable text.
   *
   * This is what the browser searches against.
   * It intentionally excludes full body text.
   */
  searchText: string;
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function cleanString(value: string | null | undefined): string | undefined {
  if (!isNonEmptyString(value)) return undefined;
  return value.trim();
}

function cleanStringArray(values: Array<string | null | undefined>): string[] {
  return values
    .map((value) => cleanString(value))
    .filter((value): value is string => Boolean(value));
}

function cleanContributors(
  contributors: SearchContributor[] | undefined,
): SearchContributor[] {
  if (!contributors) return [];

  return contributors
    .map((contributor) => {
      const name = cleanString(contributor.name);
      if (!name) return null;

      return {
        name,
        href: cleanString(contributor.href),
      };
    })
    .filter((contributor): contributor is SearchContributor =>
      Boolean(contributor),
    );
}

function getContributorNames(
  contributors: SearchContributor[] | undefined,
): string[] {
  return cleanContributors(contributors).map((contributor) => contributor.name);
}

function toPositiveInteger(value: number | null | undefined): number | null {
  if (typeof value !== "number") return null;
  if (!Number.isFinite(value)) return null;
  if (value <= 0) return null;

  return Math.round(value);
}

/**
 * Normalizes text for simple substring search.
 *
 * Examples:
 * - "Café" becomes "cafe"
 * - "New-Orleans Review" becomes "new orleans review"
 * - repeated spaces collapse to one space
 */
export function normalizeSearchText(value: unknown): string {
  if (value == null) return "";

  const text = Array.isArray(value) ? value.join(" ") : String(value);

  return text
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[’‘]/g, "'")
    .replace(/[“”]/g, '"')
    .replace(/[_-]+/g, " ")
    .replace(/[^\p{Letter}\p{Number}'" ]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

/**
 * Turns database content types into readable labels.
 *
 * Examples:
 * - "poetry" -> "Poetry"
 * - "book_review" -> "Book Review"
 * - "youth_portfolio" -> "Youth Portfolio"
 */
export function formatContentTypeLabel(contentType: string | undefined): string {
  const normalized = cleanString(contentType);

  if (!normalized) return "Other";

  return normalized
    .replace(/[_-]+/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Creates the one searchable text string for a piece.
 *
 * This intentionally searches metadata only:
 * - title
 * - subtitle
 * - dek / summary / meta description
 * - journal
 * - content type
 * - authors
 * - translators
 * - visual artists
 * - keywords
 *
 * It does not search full body text.
 */
export function buildSearchText(piece: SearchSourcePiece): string {
  const parts = cleanStringArray([
    piece.title,
    piece.subtitle,
    piece.dek,
    piece.contentType,
    formatContentTypeLabel(piece.contentType),
    piece.journalName,
    ...getContributorNames(piece.authors),
    ...getContributorNames(piece.translators),
    ...getContributorNames(piece.visualArtists),
    ...(piece.aiKeywords ?? []),
  ]);

  return normalizeSearchText(parts.join(" "));
}

/**
 * Internal read-time sort key.
 *
 * Prefer source read time when available.
 * Fall back to an estimate from word count.
 * Return null only when neither value exists.
 */
export function getReadingSortMinutes(
  piece: Pick<SearchSourcePiece, "readTimeMinutes" | "wordCountEstimate">,
): number | null {
  const readTime = toPositiveInteger(piece.readTimeMinutes);

  if (readTime !== null) return readTime;

  const wordCount = toPositiveInteger(piece.wordCountEstimate);

  if (wordCount !== null) {
    return Math.max(1, Math.ceil(wordCount / WORDS_PER_MINUTE));
  }

  return null;
}

export function buildByline(authors: SearchContributor[] | undefined): string {
  return getContributorNames(authors).join(", ");
}

/**
 * Converts a DB/card-shaped piece into a compact search-index item.
 */
export function buildSearchIndexItem(
  piece: SearchSourcePiece,
): SearchIndexItem {
  const authors = cleanContributors(piece.authors);
  const translators = cleanContributors(piece.translators);
  const visualArtists = cleanContributors(piece.visualArtists);
  const aiKeywords = cleanStringArray(piece.aiKeywords ?? []);

  const normalizedPiece: SearchSourcePiece = {
    ...piece,
    title: cleanString(piece.title) ?? "Untitled",
    subtitle: cleanString(piece.subtitle),
    dek: cleanString(piece.dek),
    contentType: cleanString(piece.contentType) ?? "other",
    href: cleanString(piece.href) ?? "/",
    originalUrl: cleanString(piece.originalUrl) ?? "",
    journalName: cleanString(piece.journalName) ?? "Unknown journal",
    journalUrl: cleanString(piece.journalUrl),
    authors,
    translators,
    visualArtists,
    dateLabel: cleanString(piece.dateLabel),
    issueLabel: cleanString(piece.issueLabel),
    imageUrl: cleanString(piece.imageUrl),
    aiKeywords,
    featured: piece.featured,
  };

  return {
    title: normalizedPiece.title,
    subtitle: normalizedPiece.subtitle,
    dek: normalizedPiece.dek,
    contentType: normalizedPiece.contentType,
    contentTypeLabel: formatContentTypeLabel(normalizedPiece.contentType),
    href: normalizedPiece.href,
    originalUrl: normalizedPiece.originalUrl,
    journalName: normalizedPiece.journalName,
    journalUrl: normalizedPiece.journalUrl,
    authors,
    translators,
    visualArtists,
    byline: buildByline(authors),
    dateLabel: normalizedPiece.dateLabel,
    issueLabel: normalizedPiece.issueLabel,
    readTimeMinutes: normalizedPiece.readTimeMinutes,
    wordCountEstimate: normalizedPiece.wordCountEstimate,
    readingSortMinutes: getReadingSortMinutes(normalizedPiece),
    imageUrl: normalizedPiece.imageUrl,
    aiKeywords,
    featured: normalizedPiece.featured,
    searchText: buildSearchText(normalizedPiece),
  };
}

/**
 * Splits a user query into normalized tokens.
 *
 * "new orleans poetry" becomes:
 * ["new", "orleans", "poetry"]
 */
export function getSearchTokens(query: string): string[] {
  const normalizedQuery = normalizeSearchText(query);

  if (!normalizedQuery) return [];

  return normalizedQuery.split(" ").filter(Boolean);
}

/**
 * Basic AND search.
 *
 * Every token in the user's query must appear somewhere in searchText.
 */
export function matchesSearchQuery(
  item: Pick<SearchIndexItem, "searchText">,
  query: string,
): boolean {
  const tokens = getSearchTokens(query);

  if (tokens.length === 0) return true;

  return tokens.every((token) => item.searchText.includes(token));
}

/**
 * A small relevance score for default result ordering.
 *
 * This is intentionally simple. It keeps exact/strong title matches near
 * the top without adding Fuse.js or another search dependency.
 */
export function getSearchMatchScore(
  item: Pick<
    SearchIndexItem,
    | "title"
    | "subtitle"
    | "dek"
    | "journalName"
    | "contentType"
    | "contentTypeLabel"
    | "byline"
    | "aiKeywords"
    | "searchText"
  >,
  query: string,
): number {
  const normalizedQuery = normalizeSearchText(query);
  const tokens = getSearchTokens(query);

  if (!normalizedQuery || tokens.length === 0) return 0;

  const title = normalizeSearchText(item.title);
  const subtitle = normalizeSearchText(item.subtitle);
  const dek = normalizeSearchText(item.dek);
  const journal = normalizeSearchText(item.journalName);
  const contentType = normalizeSearchText(
    `${item.contentType} ${item.contentTypeLabel}`,
  );
  const byline = normalizeSearchText(item.byline);
  const keywords = normalizeSearchText(item.aiKeywords.join(" "));

  let score = 0;

  if (title === normalizedQuery) score += 1000;
  if (title.includes(normalizedQuery)) score += 250;
  if (subtitle.includes(normalizedQuery)) score += 180;
  if (byline.includes(normalizedQuery)) score += 160;
  if (journal.includes(normalizedQuery)) score += 120;
  if (keywords.includes(normalizedQuery)) score += 100;
  if (contentType.includes(normalizedQuery)) score += 80;
  if (dek.includes(normalizedQuery)) score += 60;

  for (const token of tokens) {
    if (title.includes(token)) score += 30;
    if (subtitle.includes(token)) score += 20;
    if (byline.includes(token)) score += 18;
    if (journal.includes(token)) score += 14;
    if (keywords.includes(token)) score += 12;
    if (contentType.includes(token)) score += 10;
    if (dek.includes(token)) score += 6;
    if (item.searchText.includes(token)) score += 1;
  }

  return score;
}

function compareTitleAsc(
  a: Pick<SearchIndexItem, "title">,
  b: Pick<SearchIndexItem, "title">,
): number {
  return normalizeSearchText(a.title).localeCompare(normalizeSearchText(b.title));
}

function compareNullableNumbers(
  a: number | null | undefined,
  b: number | null | undefined,
  direction: "asc" | "desc",
): number {
  const aNumber = typeof a === "number" && Number.isFinite(a) ? a : null;
  const bNumber = typeof b === "number" && Number.isFinite(b) ? b : null;

  // Unknown values always go to the bottom.
  if (aNumber === null && bNumber === null) return 0;
  if (aNumber === null) return 1;
  if (bNumber === null) return -1;

  return direction === "asc" ? aNumber - bNumber : bNumber - aNumber;
}

/**
 * Filters and sorts search-index items.
 *
 * This returns a new array and does not mutate the original index.
 */
export function getSearchResults(
  items: SearchIndexItem[],
  query: string,
  sort: SearchSort = "relevance",
): SearchIndexItem[] {
  const matches = items.filter((item) => matchesSearchQuery(item, query));

  return sortSearchResults(matches, sort, query);
}

/**
 * Sorts search results.
 *
 * - relevance: best lightweight match score first
 * - title-az: title A to Z
 * - shortest: shortest reading time first
 * - longest: longest reading time first
 *
 * Missing reading times always sort to the bottom.
 */
export function sortSearchResults(
  items: SearchIndexItem[],
  sort: SearchSort = "relevance",
  query = "",
): SearchIndexItem[] {
  const results = [...items];

  if (sort === "title-az") {
    return results.sort(compareTitleAsc);
  }

  if (sort === "shortest") {
    return results.sort((a, b) => {
      const byReadingTime = compareNullableNumbers(
        a.readingSortMinutes,
        b.readingSortMinutes,
        "asc",
      );

      return byReadingTime || compareTitleAsc(a, b);
    });
  }

  if (sort === "longest") {
    return results.sort((a, b) => {
      const byReadingTime = compareNullableNumbers(
        a.readingSortMinutes,
        b.readingSortMinutes,
        "desc",
      );

      return byReadingTime || compareTitleAsc(a, b);
    });
  }

  const normalizedQuery = normalizeSearchText(query);

  if (!normalizedQuery) {
    return results;
  }

  return results.sort((a, b) => {
    const byScore =
      getSearchMatchScore(b, normalizedQuery) -
      getSearchMatchScore(a, normalizedQuery);

    return byScore || compareTitleAsc(a, b);
  });
}