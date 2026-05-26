// src/lib/db.ts
import Database from 'better-sqlite3';
import path from 'node:path';

const DB_PATH =
  process.env.KOPANI_DB ?? path.join(process.cwd(), 'data', 'kopani.sqlite');

// const db = new Database(DB_PATH, { readonly: true, fileMustExist: true });
// db.pragma('foreign_keys = ON');
// db.pragma('journal_mode = WAL'); // safe for read-only too

const db = new Database(DB_PATH, { readonly: true, fileMustExist: true });
db.pragma('foreign_keys = ON');

// ---------------------------------------------------------------------------
// Shape the Card expects (mirrors PieceCard in Card.improved.astro)
// ---------------------------------------------------------------------------
export type CardContributor = { name: string; href?: string };

export interface PieceCardData {
  title: string;
  subtitle?: string;
  dek?: string;
  contentType: string;
  href: string;
  originalUrl: string;   // piece url on the publishing journal
  journalName: string;
  journalUrl: string;
  authors: CardContributor[];
  translators?: CardContributor[];
  visualArtists?: CardContributor[];
  dateLabel?: string;
  issueLabel?: string;
  readTimeMinutes?: number;
  wordCountEstimate?: number;
  imageUrl?: string;
  aiKeywords?: string[];
  featured?: boolean;
}

// ---------------------------------------------------------------------------
// Raw row types
// ---------------------------------------------------------------------------
interface IdFlagsRow { id: number; has_tr: number; has_va: number; }

interface PieceJoinRow {
  id: number;
  slug: string;
  title: string;
  subtitle: string | null;
  summary: string | null;
  meta_description: string | null;
  content_type: string;
  original_url: string;
  publication_date: string | null;
  publication_date_display: string | null;
  issue_label: string | null;
  read_time_minutes: number | null;
  word_count_estimate: number | null;
  image_url: string | null;
  ai_keywords_json: string | null;
  featured: number;
  journal_slug: string;
  journal_name: string;
  journal_url: string;
}

interface ContributorRow {
  slug: string;
  name: string;
  role: 'author' | 'translator' | 'visual_artist';
  display_order: number;
}

// ---------------------------------------------------------------------------
// Prepared statements (compiled once)
// ---------------------------------------------------------------------------
const allIdFlagsStmt = db.prepare(`
  SELECT p.id AS id,
         MAX(pc.role = 'translator')    AS has_tr,
         MAX(pc.role = 'visual_artist') AS has_va
  FROM pieces p
  LEFT JOIN piece_contributors pc ON pc.piece_id = p.id
  GROUP BY p.id
`);

const contributorsStmt = db.prepare(`
  SELECT a.slug AS slug, a.name AS name,
         pc.role AS role, pc.display_order AS display_order
  FROM piece_contributors pc
  JOIN authors a ON a.id = pc.author_id
  WHERE pc.piece_id = ?
  ORDER BY pc.role, pc.display_order
`);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function shuffle<T>(arr: T[]): T[] {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

const pickRandom = <T>(arr: T[], n: number): T[] => shuffle(arr).slice(0, n);

const clean = <T>(v: T | null): T | undefined => (v == null ? undefined : v);

function mapPiece(row: PieceJoinRow): PieceCardData {
  const contribs = contributorsStmt.all(row.id) as ContributorRow[];

  const byRole = (role: ContributorRow['role']): CardContributor[] =>
    contribs
      .filter((c) => c.role === role)
      .map((c) => ({ name: c.name, href: `/authors/${c.slug}` }));

  let aiKeywords: string[] = [];
  if (row.ai_keywords_json) {
    try { aiKeywords = JSON.parse(row.ai_keywords_json); } catch { aiKeywords = []; }
  }

  return {
    title: row.title,
    subtitle: clean(row.subtitle),
    dek: clean(row.summary) ?? clean(row.meta_description),
    contentType: row.content_type, // rendered uppercase by the Card's CSS
    href: `/journals/${row.journal_slug}/${row.slug}`,
    journalName: row.journal_name,
    journalUrl: row.journal_url,
    originalUrl: row.original_url, // url for the piece directed to the canonical url on the journal
    authors: byRole('author'),
    translators: byRole('translator'),
    visualArtists: byRole('visual_artist'),
    dateLabel: clean(row.publication_date_display) ?? clean(row.publication_date),
    issueLabel: clean(row.issue_label),
    readTimeMinutes: clean(row.read_time_minutes),
    wordCountEstimate: clean(row.word_count_estimate),
    imageUrl: clean(row.image_url), // Kopani-owned only; mostly NULL → fallback texture
    aiKeywords,
    featured: row.featured === 1,
  };
}

// ---------------------------------------------------------------------------
// Stratified random sample
// Guarantees a mix of: both / translator-only / visual-only / neither.
// Rare buckets take what's available; the rest is topped up at random.
// Tweak the quotas freely — they sum to `total`.
// ---------------------------------------------------------------------------
export function getRandomPieceCards(total = 50): PieceCardData[] {
  const rows = allIdFlagsStmt.all() as IdFlagsRow[];

  const both: number[] = [];
  const tr: number[] = [];
  const va: number[] = [];
  const neither: number[] = [];
  for (const r of rows) {
    if (r.has_tr && r.has_va) both.push(r.id);
    else if (r.has_tr) tr.push(r.id);
    else if (r.has_va) va.push(r.id);
    else neither.push(r.id);
  }

  const quotas: Array<[number[], number]> = [
    [both, 10],
    [tr, 10],
    [va, 12],
    [neither, 18],
  ];

  const chosen: number[] = [];
  const seen = new Set<number>();
  for (const [bucket, q] of quotas) {
    for (const id of pickRandom(bucket, q)) {
      if (!seen.has(id)) { chosen.push(id); seen.add(id); }
    }
  }

  // Top up to `total` from anything not yet picked.
  if (chosen.length < total) {
    const leftover = rows.map((r) => r.id).filter((id) => !seen.has(id));
    for (const id of pickRandom(leftover, total - chosen.length)) {
      chosen.push(id); seen.add(id);
    }
  }

  const finalIds = shuffle(chosen.slice(0, total)); // interleave variants

  if (finalIds.length === 0) return [];

  const placeholders = finalIds.map(() => '?').join(',');
  const pieceRows = db.prepare(`
    SELECT p.id, p.slug, p.title, p.subtitle, p.summary, p.meta_description,
           p.original_url,
           p.content_type, p.publication_date, p.publication_date_display,
           p.issue_label, p.read_time_minutes, p.word_count_estimate,
           p.image_url, p.ai_keywords_json, p.featured,
           j.slug AS journal_slug, j.name AS journal_name, j.homepage_url AS journal_url
    FROM pieces p
    JOIN journals j ON j.id = p.journal_id
    WHERE p.id IN (${placeholders})
  `).all(...finalIds) as PieceJoinRow[];

  // Re-order rows to match our shuffled id order.
  const byId = new Map(pieceRows.map((r) => [r.id, r]));
  return finalIds
    .map((id) => byId.get(id))
    .filter((r): r is PieceJoinRow => r != null)
    .map(mapPiece);
}




export function getPiecesByContentType(type: string): PieceCardData[] {

  const pieceRows = db.prepare(`
    SELECT p.id, p.slug, p.title, p.subtitle, p.summary, p.meta_description,
           p.original_url,
           p.content_type, p.publication_date, p.publication_date_display,
           p.issue_label, p.read_time_minutes, p.word_count_estimate,
           p.image_url, p.ai_keywords_json, p.featured,
           j.slug AS journal_slug, j.name AS journal_name, j.homepage_url AS journal_url
    FROM pieces p
    JOIN journals j ON j.id = p.journal_id
    WHERE p.content_type = ? ORDER BY COALESCE(p.publication_date, p.created_at) DESC  
    `).all(type) as PieceJoinRow[];

  return pieceRows.map(mapPiece)

}

export default db;