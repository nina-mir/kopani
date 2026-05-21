# Kopani — Integrating SQLite with Astro

A practical guide for wiring `kopani.sqlite` into an Astro/Vite frontend. Focuses on the read-mostly, static-first pattern that fits Kopani's MVP: pieces are scraped and ingested into SQLite via `ingest.py`, then Astro renders the site against that DB.

---

## The mental model

Astro's default output is static HTML. Pages are rendered at **build time**, not request time. That means when you write SQL in an `.astro` page, the query runs once on your laptop (or in CI, or on the droplet) during `npm run build`, and the result gets baked into a static `.html` file that nginx then serves with no server-side logic at all.

This matters for two reasons. First, you don't need an HTTP API between Astro and SQLite — they live in the same Node process during build. Second, you don't need a long-running server in production for the read paths. The droplet runs nginx, serves files, and the SQLite file is only touched when you re-build.

The library that makes this clean is `better-sqlite3`. It's synchronous, which sounds wrong but is exactly right here: Astro renders pages top-to-bottom on the server, and synchronous DB calls compose naturally with that flow. No `await` chains, no promise plumbing.

You only need a server at runtime if you add features that depend on request data — auth, per-user state, search-as-you-type that hits the backend. Even then, Astro can do it itself via its Node adapter. You won't need Express.

---

## Project layout

A clean structure that scales:

```
kopani-frontend/
├── astro.config.mjs
├── package.json
├── tsconfig.json
├── data/
│   └── kopani.sqlite           # the DB lives here in dev
├── public/
│   ├── search-index.json       # generated at build (see Search section)
│   └── images/
├── scripts/
│   └── build-search-index.ts   # pre-build script
├── src/
│   ├── lib/
│   │   ├── db.ts               # ← the only file that opens the DB
│   │   └── types.ts            # row types
│   ├── components/
│   │   ├── Card.astro
│   │   ├── Header.astro
│   │   └── Footer.astro
│   ├── layouts/
│   │   └── Layout.astro
│   └── pages/
│       ├── index.astro
│       ├── journals/
│       │   ├── index.astro
│       │   ├── [journal].astro
│       │   └── [journal]/[slug].astro
│       └── people/[slug].astro
└── dist/                        # built output (deploy this)
```

Keep `kopani.sqlite` outside `src/` so Vite doesn't try to process it. In production it can live elsewhere on the droplet (e.g. `/srv/kopani/data/kopani.sqlite`) and be pointed at via env var.

---

## Setup

Install the driver and its types:

```bash
npm install better-sqlite3
npm install -D @types/better-sqlite3
```

Astro/Vite needs one config tweak so it doesn't try to bundle the native binary. In `astro.config.mjs`:

```js
import { defineConfig } from 'astro/config';

export default defineConfig({
  vite: {
    optimizeDeps: { exclude: ['better-sqlite3'] },
    ssr: { external: ['better-sqlite3'] },
  },
});
```

Without this, you'll get cryptic errors about `.node` files at build time.

---

## The `db.ts` module

This is the single source of truth for database access. Every page imports query functions from here; nothing else opens the DB. Caching the connection at the module level means it's opened once per build process, not per page render.

```ts
// src/lib/db.ts
import Database from 'better-sqlite3';
import path from 'node:path';
import type {
  PieceRow, PieceWithJournal, Piece, Contributor,
  JournalRow, AuthorRow,
} from './types';

const DB_PATH =
  process.env.KOPANI_DB ?? path.join(process.cwd(), 'data', 'kopani.sqlite');

const db = new Database(DB_PATH, { readonly: true, fileMustExist: true });
db.pragma('foreign_keys = ON');
db.pragma('journal_mode = WAL'); // safe for read-only too

// ---- prepared statements (compiled once, reused on every call) ----

const stmts = {
  recentPieces: db.prepare<[number], PieceWithJournal>(`
    SELECT p.id, p.slug, p.title, p.subtitle, p.content_type,
           p.publication_date, p.publication_date_display,
           p.read_time_minutes, p.word_count_estimate,
           p.source_image_url, p.image_url,
           p.meta_description, p.ai_keywords_json,
           j.slug AS journal_slug, j.name AS journal_name
    FROM pieces p
    JOIN journals j ON j.id = p.journal_id
    WHERE p.ingestion_status NOT IN ('rejected','error','discovered')
    ORDER BY COALESCE(p.publication_date, p.created_at) DESC
    LIMIT ?
  `),

  pieceBySlug: db.prepare<[string, string], PieceWithJournal>(`
    SELECT p.*, j.slug AS journal_slug, j.name AS journal_name
    FROM pieces p
    JOIN journals j ON j.id = p.journal_id
    WHERE j.slug = ? AND p.slug = ?
  `),

  contributorsForPiece: db.prepare<[number], Contributor>(`
    SELECT a.id, a.slug, a.name, a.bio, pc.role, pc.display_order
    FROM piece_contributors pc
    JOIN authors a ON a.id = pc.author_id
    WHERE pc.piece_id = ?
    ORDER BY pc.role, pc.display_order
  `),

  piecesByJournal: db.prepare<[string], PieceWithJournal>(`
    SELECT p.*, j.slug AS journal_slug, j.name AS journal_name
    FROM pieces p
    JOIN journals j ON j.id = p.journal_id
    WHERE j.slug = ?
      AND p.ingestion_status NOT IN ('rejected','error','discovered')
    ORDER BY COALESCE(p.publication_date, p.created_at) DESC
  `),

  piecesByAuthor: db.prepare<[string], PieceWithJournal & { role: string }>(`
    SELECT p.*, j.slug AS journal_slug, j.name AS journal_name, pc.role
    FROM authors a
    JOIN piece_contributors pc ON pc.author_id = a.id
    JOIN pieces p              ON p.id = pc.piece_id
    JOIN journals j            ON j.id = p.journal_id
    WHERE a.slug = ?
      AND p.ingestion_status NOT IN ('rejected','error','discovered')
    ORDER BY COALESCE(p.publication_date, p.created_at) DESC
  `),

  allJournals: db.prepare<[], JournalRow>(`
    SELECT * FROM journals ORDER BY name
  `),

  allPieceSlugs: db.prepare<[], { journal_slug: string; slug: string }>(`
    SELECT j.slug AS journal_slug, p.slug
    FROM pieces p JOIN journals j ON j.id = p.journal_id
    WHERE p.ingestion_status NOT IN ('rejected','error','discovered')
  `),

  allAuthorSlugs: db.prepare<[], { slug: string }>(`
    SELECT slug FROM authors
  `),
};

// ---- row → object parsing ----

function parsePiece(row: PieceWithJournal): Piece {
  return {
    ...row,
    ai_keywords: row.ai_keywords_json ? JSON.parse(row.ai_keywords_json) : null,
    issue_metadata: row.issue_metadata_json ? JSON.parse(row.issue_metadata_json) : null,
  };
}

// ---- public API ----

export const getRecentPieces = (limit = 24): Piece[] =>
  stmts.recentPieces.all(limit).map(parsePiece);

export const getPiece = (journalSlug: string, slug: string) => {
  const row = stmts.pieceBySlug.get(journalSlug, slug);
  if (!row) return null;
  const contributors = stmts.contributorsForPiece.all(row.id);
  return { ...parsePiece(row), contributors };
};

export const getPiecesByJournal = (slug: string): Piece[] =>
  stmts.piecesByJournal.all(slug).map(parsePiece);

export const getPiecesByAuthor = (slug: string): Piece[] =>
  stmts.piecesByAuthor.all(slug).map(parsePiece);

export const getJournals = (): JournalRow[] => stmts.allJournals.all();

export const getAllPieceSlugs = () => stmts.allPieceSlugs.all();
export const getAllAuthorSlugs = () => stmts.allAuthorSlugs.all();

export default db;
```

Two things to notice. First, prepared statements are created once at module load and reused — that's what makes this fast even at 1200 pieces. Second, the `parsePiece` helper converts the TEXT columns that hold JSON (`ai_keywords_json`, `issue_metadata_json`) into real arrays and objects so your templates don't have to think about it.

---

## TypeScript types

These mirror the schema and live in their own file so the queries stay readable:

```ts
// src/lib/types.ts

export interface JournalRow {
  id: number;
  slug: string;
  name: string;
  homepage_url: string;
  description: string | null;
  country: string | null;
  city: string | null;
  genres_supported_json: string | null;
  issue_data_status: 'none' | 'partial' | 'good';
  issue_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface PieceRow {
  id: number;
  slug: string;
  title: string;
  subtitle: string | null;
  journal_id: number;
  original_url: string;
  content_type: string;
  content_type_raw: string | null;
  format: string;
  summary: string | null;
  meta_description: string | null;
  publication_date: string | null;
  publication_date_display: string | null;
  word_count_estimate: number | null;
  read_time_minutes: number | null;
  rights_status: string;
  image_url: string | null;
  source_image_url: string | null;
  issue_label: string | null;
  issue_url: string | null;
  issue_metadata_json: string | null;
  ai_keywords_json: string | null;
  featured: 0 | 1;
  ingestion_status: string;
  raw_json: string;
  created_at: string;
  updated_at: string;
}

export interface PieceWithJournal extends PieceRow {
  journal_slug: string;
  journal_name: string;
}

export interface Piece extends PieceWithJournal {
  ai_keywords: string[] | null;
  issue_metadata: Record<string, unknown> | null;
}

export interface AuthorRow {
  id: number;
  slug: string;
  name: string;
  bio: string | null;
}

export interface Contributor extends AuthorRow {
  role: 'author' | 'translator' | 'visual_artist';
  display_order: number;
}
```

---

## Using it in pages

### Homepage

```astro
---
// src/pages/index.astro
import Layout from '../layouts/Layout.astro';
import Card from '../components/Card.astro';
import { getRecentPieces } from '../lib/db';

const pieces = getRecentPieces(24);
---
<Layout title="Kopani">
  <main class="grid">
    {pieces.map((p) => <Card piece={p} />)}
  </main>
</Layout>
```

That's the whole homepage. SQL runs at build time, HTML is static.

### Card component

```astro
---
// src/components/Card.astro
import type { Piece } from '../lib/types';
interface Props { piece: Piece }
const { piece } = Astro.props;
const href = `/journals/${piece.journal_slug}/${piece.slug}`;
---
<a class="card" href={href}>
  <span class="journal">{piece.journal_name}</span>
  <h3>{piece.title}</h3>
  {piece.subtitle && <p class="subtitle">{piece.subtitle}</p>}
  <p class="meta">
    <span class="type">{piece.content_type}</span>
    {piece.read_time_minutes && <span>· {piece.read_time_minutes} min</span>}
    {piece.publication_date_display && <span>· {piece.publication_date_display}</span>}
  </p>
</a>
```

### Piece detail page (dynamic route)

This is the pattern for `/journals/granta/john-cena` and the 1200 others. `getStaticPaths` runs at build time and tells Astro every URL to generate.

```astro
---
// src/pages/journals/[journal]/[slug].astro
import Layout from '../../../layouts/Layout.astro';
import { getAllPieceSlugs, getPiece } from '../../../lib/db';

export function getStaticPaths() {
  return getAllPieceSlugs().map(({ journal_slug, slug }) => ({
    params: { journal: journal_slug, slug },
  }));
}

const { journal, slug } = Astro.params;
const piece = getPiece(journal!, slug!);
if (!piece) return Astro.redirect('/404');

const authors      = piece.contributors.filter((c) => c.role === 'author');
const translators  = piece.contributors.filter((c) => c.role === 'translator');
const visualArtist = piece.contributors.find((c)   => c.role === 'visual_artist');
---
<Layout title={piece.title}>
  <article>
    <h1>{piece.title}</h1>
    {piece.subtitle && <p class="subtitle">{piece.subtitle}</p>}

    <p class="byline">
      by {authors.map((a, i) => (
        <>
          <a href={`/people/${a.slug}`}>{a.name}</a>
          {i < authors.length - 1 && ', '}
        </>
      ))}
      {translators.length > 0 && (
        <>, translated by {translators.map((t) => t.name).join(', ')}</>
      )}
      {visualArtist && <>, art by <a href={`/people/${visualArtist.slug}`}>{visualArtist.name}</a></>}
    </p>

    <p class="meta">
      In <a href={`/journals/${piece.journal_slug}`}>{piece.journal_name}</a>
      {piece.publication_date_display && <> · {piece.publication_date_display}</>}
      {piece.read_time_minutes && <> · {piece.read_time_minutes} min read</>}
    </p>

    {piece.meta_description && <p class="description">{piece.meta_description}</p>}

    {piece.ai_keywords && piece.ai_keywords.length > 0 && (
      <ul class="keywords">
        {piece.ai_keywords.map((k) => <li>{k}</li>)}
      </ul>
    )}

    <a class="read-original" href={piece.original_url} target="_blank" rel="noopener">
      Read at {piece.journal_name} →
    </a>
  </article>
</Layout>
```

Notice there's no piece body on this page — Kopani never displays the text. The page is metadata plus a link out. That's a feature, not a limitation: it's why your build is so simple.

### Author / person page

```astro
---
// src/pages/people/[slug].astro
import Layout from '../../layouts/Layout.astro';
import Card from '../../components/Card.astro';
import { getAllAuthorSlugs, getPiecesByAuthor } from '../../lib/db';

export function getStaticPaths() {
  return getAllAuthorSlugs().map(({ slug }) => ({ params: { slug } }));
}

const { slug } = Astro.params;
const pieces = getPiecesByAuthor(slug!);
const name = pieces[0]?.contributors?.find((c) => c.slug === slug)?.name ?? slug;
---
<Layout title={name}>
  <h1>{name}</h1>
  <div class="grid">
    {pieces.map((p) => <Card piece={p} />)}
  </div>
</Layout>
```

### Journal page

```astro
---
// src/pages/journals/[journal].astro
import Layout from '../../layouts/Layout.astro';
import Card from '../../components/Card.astro';
import { getJournals, getPiecesByJournal } from '../../lib/db';

export function getStaticPaths() {
  return getJournals().map((j) => ({ params: { journal: j.slug }, props: { journal: j } }));
}

const { journal } = Astro.props;
const pieces = getPiecesByJournal(journal.slug);
---
<Layout title={journal.name}>
  <h1>{journal.name}</h1>
  {journal.description && <p>{journal.description}</p>}
  <div class="grid">{pieces.map((p) => <Card piece={p} />)}</div>
</Layout>
```

---

## Search and filtering

At 1200 pieces, the simplest and fastest pattern is to generate a small JSON index at build time and let the browser filter it. No backend search service, no SQLite at runtime.

Create `scripts/build-search-index.ts`:

```ts
import Database from 'better-sqlite3';
import { writeFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';

const db = new Database(
  process.env.KOPANI_DB ?? path.join(process.cwd(), 'data', 'kopani.sqlite'),
  { readonly: true },
);

const rows = db.prepare(`
  SELECT p.id, p.slug, p.title, p.subtitle, p.content_type,
         p.publication_date_display,
         j.slug AS journal_slug, j.name AS journal_name,
         GROUP_CONCAT(a.name, '|')  AS contributors,
         p.ai_keywords_json
  FROM pieces p
  JOIN journals j ON j.id = p.journal_id
  LEFT JOIN piece_contributors pc ON pc.piece_id = p.id
  LEFT JOIN authors a ON a.id = pc.author_id
  WHERE p.ingestion_status NOT IN ('rejected','error','discovered')
  GROUP BY p.id
`).all() as any[];

const index = rows.map((r) => ({
  id: r.id,
  slug: r.slug,
  title: r.title,
  subtitle: r.subtitle,
  content_type: r.content_type,
  date: r.publication_date_display,
  journal_slug: r.journal_slug,
  journal_name: r.journal_name,
  contributors: r.contributors ? r.contributors.split('|') : [],
  keywords: r.ai_keywords_json ? JSON.parse(r.ai_keywords_json) : [],
}));

mkdirSync('public', { recursive: true });
writeFileSync('public/search-index.json', JSON.stringify(index));
console.log(`wrote ${index.length} pieces to public/search-index.json`);
```

Wire it into the build:

```json
// package.json
{
  "scripts": {
    "build:index": "tsx scripts/build-search-index.ts",
    "build": "npm run build:index && astro build",
    "dev": "astro dev"
  }
}
```

(Install `tsx` as a dev dependency for that.) The index will weigh in around 300–500 KB for 1200 pieces — fine for a single fetch on first page load, and small enough to keep in memory in the browser for instant filtering.

Browser-side, fetch the index once and filter with whatever logic you want. For fancier search, `MiniSearch` or `Fuse.js` give you fuzzy matching in 5 KB.

---

## Static vs SSR — when to switch

Stay static for the entire MVP if all of these are true:

- Pages don't depend on who's viewing them.
- Data updates happen in batches (you re-run `ingest.py`, then re-build).
- Search and filtering can be browser-side over the index above.

You need SSR (or hybrid — static for most pages, server for some) once any of these become true:

- You add auth and need per-user state.
- You allow user actions that write to a database.
- The piece list updates throughout the day and you can't tolerate the delay of a rebuild.

When that day comes, switch by adding the Node adapter in `astro.config.mjs`:

```js
import node from '@astrojs/node';
export default defineConfig({
  output: 'hybrid',                    // page-by-page opt-in
  adapter: node({ mode: 'standalone' }),
  vite: { /* same as before */ },
});
```

Then individual pages or endpoints can opt out of static with `export const prerender = false;`. The `db.ts` module continues to work unchanged — `better-sqlite3` is just as happy at request time as at build time.

---

## Deployment to the DigitalOcean droplet

### Static-only deployment (recommended for MVP)

The droplet only needs nginx and your `dist/` folder. Where you build is up to you:

The simplest path is to build on the droplet itself. SSH in, clone the repo, install Node 20+, install build tools (`build-essential`, `python3`) for `better-sqlite3` to compile its native binding, then:

```bash
npm ci
KOPANI_DB=/srv/kopani/data/kopani.sqlite npm run build
sudo cp -r dist/* /var/www/kopani/
```

Nginx config is boring and short:

```nginx
server {
  listen 80;
  server_name kopani.example.com;
  root /var/www/kopani;
  index index.html;
  location / { try_files $uri $uri/ $uri.html =404; }
  location /search-index.json { add_header Cache-Control "max-age=300"; }
}
```

The SQLite file lives outside the web root (`/srv/kopani/data/`) so it's never accidentally served. The `dist/` folder doesn't contain the SQLite file at all — that's the whole point. Once HTML is generated, the DB isn't needed at runtime.

Alternative: build on your laptop or CI, then `rsync dist/ user@droplet:/var/www/kopani/`. Faster iteration, no build toolchain on the server.

### SSR deployment (if/when you switch)

You'll need Node running on the droplet behind nginx. Use `pm2` or a systemd unit to keep `node ./dist/server/entry.mjs` alive, and nginx as reverse proxy to `localhost:4321`. The SQLite file stays at `/srv/kopani/data/kopani.sqlite` and the Node process reads it directly. Still no Express needed — Astro's Node adapter is the server.

---

## The update loop

When new pieces come in, the loop is:

1. Drop new JSONs into the source folder.
2. Run `python3 ingest.py --src ./json --db data/kopani.sqlite --schema schema.sql`. The script is idempotent — re-running on existing files just updates them.
3. Run `npm run build`. This re-generates the search index and the static pages.
4. Deploy `dist/`.

Steps 2–4 can be a single shell script on the droplet, or a GitHub Action if you set up CI.

---

## Pitfalls and gotchas

**The native binding.** `better-sqlite3` is a compiled C++ module. It must be built against the same Node version and OS/libc as the environment that will run it. If you `npm install` on macOS and rsync `node_modules` to Ubuntu, it will break. Either build on the droplet, or use prebuilt binaries (npm usually does this automatically; if it doesn't, `npm rebuild better-sqlite3` on the droplet).

**Foreign keys are off by default.** `PRAGMA foreign_keys = ON` is set per connection, not stored in the file. `db.ts` does this — make sure any other code path (a one-off script, a future API route) does too.

**JSON columns are TEXT.** `ai_keywords_json` and `issue_metadata_json` come back as strings. Always `JSON.parse` before passing to templates. The `parsePiece` helper does this.

**Dates are TEXT too.** SQLite has no real date type. As long as the data is ISO format (`YYYY-MM-DD`), lexicographic sorting works correctly. Don't mix in non-ISO date strings.

**Author slug collisions.** Two real people named "Sarah Lee" would collide on slug `sarah-lee`. The ingest script merges them silently into one author row. Not a problem today, worth a manual sweep at 1200 pieces.

**Don't open the DB in a component.** Components might be rendered many times per build. Open the connection once in `db.ts` (module-level) and import query functions everywhere else.

**Don't commit the SQLite file to git** if it grows past a few MB, or if it contains anything sensitive. For Kopani it's safe to commit (it's derived data), but `.gitignore` it once it gets large and rebuild it from the JSONs in CI.

**Astro's `getStaticPaths` runs once.** If you add new pieces and don't re-run `npm run build`, the new URLs won't exist. This is the cost of static — and it's paid for many times over by the simplicity of nginx serving files.

---

## Quick checklist for getting started

1. `npm create astro@latest kopani-frontend` (pick the "Empty" or "Minimal" starter).
2. `npm install better-sqlite3 && npm install -D @types/better-sqlite3 tsx`.
3. Copy `kopani.sqlite` into `./data/`.
4. Add the `vite` config block to `astro.config.mjs`.
5. Create `src/lib/db.ts` and `src/lib/types.ts` from the templates above.
6. Build the homepage as a sanity check — if `getRecentPieces()` returns 24 rows when you visit `localhost:4321`, you're wired up.
7. Add `[journal]/[slug].astro` and one piece-detail render confirms the dynamic-routes path works.
8. Build the search index script, wire it into `npm run build`.
9. Style.
10. Deploy.

That sequence — DB module, one static page, one dynamic page, then everything else — gives you working ground truth before you commit to any visual design decisions.
