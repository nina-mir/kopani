# Kopani MVP Database Schema (SQLite) — v2

A living reference for Kopani's MVP data model.
Companion files: `schema.sql` (DDL), `ingest.py` (loader).

---

## What changed since v1

| Area | v1 | v2 |
|---|---|---|
| Body storage | Not specified | Lives inside `pieces.raw_json` (full scraped JSON, byte-for-byte). No separate `body_text` / `body_html` columns — by design. |
| Translators | Not modeled | First-class. Stored in `authors`, linked via `piece_contributors` with `role = 'translator'`. |
| Visual artists | Not modeled | First-class. Same mechanism, `role = 'visual_artist'`. 17 % of pieces (21/125) have one — too much data to lose. |
| Junction table | `piece_authors (piece_id, author_id, author_order)` | Renamed `piece_contributors`. Adds `role` column, PK is `(piece_id, author_id, role)`. `author_order` → `display_order`. |
| AI keywords | Conflated with `themes` | Separate. New `pieces.ai_keywords_json` TEXT column holds the raw AI-extracted array. `themes` stays clean for curated editorial vocabulary. |
| Content type | Strict enum | Free-text column normalized at ingest by `CONTENT_TYPE_MAP` in `ingest.py`. Original value preserved in `pieces.content_type_raw`. |
| Raw audit blob | None | `pieces.raw_json TEXT NOT NULL` stores the full scraped JSON. Re-deriving fields later requires no re-scrape. Queryable via SQLite JSON functions. |
| Slug uniqueness | Global `UNIQUE(slug)` on pieces | `UNIQUE(journal_id, slug)`. Lets two journals coexist with same-slug pieces; aligns with URL pattern `/journals/{j}/{slug}`. |
| Source metadata | Only `source_image_url` | Adds `pieces.meta_description` (the source's own blurb, distinct from Kopani-written `summary`). Adds `pieces.subtitle` for The Offing. |
| Foreign keys | Implied | Declared via `REFERENCES` + `ON DELETE CASCADE` on junctions. Run `PRAGMA foreign_keys = ON` per connection. |
| Subworks | Open question | Not modeled. Container pieces ("4 Poems") stored as single rows; subwork detail remains accessible inside `raw_json`. |
| Editor notes | Open question | Not added. If needed later, a single `ALTER TABLE ADD COLUMN editor_notes TEXT` will do. |

The six-table backbone (journals · pieces · authors · piece_contributors · themes · piece_themes) is unchanged in spirit.

---

## Tables

### `journals`
One row per literary journal.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | |
| `slug` | TEXT NOT NULL UNIQUE | e.g. `"new-orleans-review"` |
| `name` | TEXT NOT NULL | |
| `homepage_url` | TEXT NOT NULL UNIQUE | |
| `description` | TEXT | |
| `country`, `city` | TEXT | |
| `genres_supported_json` | TEXT | JSON array, e.g. `["poetry","fiction"]` |
| `issue_data_status` | TEXT NOT NULL DEFAULT 'none' | CHECK: `'none' \| 'partial' \| 'good'` |
| `issue_notes` | TEXT | |
| `created_at`, `updated_at` | TEXT | ISO 8601, defaulted by SQLite |

### `pieces`
One row per piece. Body lives in `raw_json`.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | |
| `slug` | TEXT NOT NULL | UNIQUE within `(journal_id, slug)` |
| `title` | TEXT NOT NULL | |
| `subtitle` | TEXT | Mainly populated for The Offing |
| `journal_id` | INTEGER NOT NULL FK | → `journals.id` |
| `original_url` | TEXT NOT NULL UNIQUE | Canonical URL on source site |
| `content_type` | TEXT NOT NULL | Normalized. Current observed values: `poetry`, `essay`, `fiction`, `nonfiction`, `art`, `youth_portfolio`, `table_talk`, `podcast`, `art_review`, `book_review`, `interview`, `review`, `other` |
| `content_type_raw` | TEXT | Original string from source, kept for audit |
| `format` | TEXT NOT NULL DEFAULT 'text/html' | `text/html` / `application/pdf` / `audio` |
| `summary` | TEXT | **Kopani-written** blurb (future) |
| `meta_description` | TEXT | Source's own blurb / `og:description` |
| `publication_date` | TEXT | ISO `YYYY-MM-DD` if known; often NULL for season-only journals |
| `publication_date_display` | TEXT | Human-readable: `"Spring 2019"`, `"F/W 2019"`, `"26 NOV 2015"` |
| `word_count_estimate` | INTEGER | Computed at ingest from `content.text` |
| `read_time_minutes` | INTEGER | Parsed from source if present, else NULL |
| `rights_status` | TEXT NOT NULL DEFAULT 'unknown' | CHECK enum (see schema.sql) |
| `image_url` | TEXT | Kopani-owned image |
| `source_image_url` | TEXT | Source-side image URL — reference only, do not display |
| `issue_label`, `issue_url`, `issue_metadata_json` | TEXT | Flat issue fields; promote to table later if needed |
| `ai_keywords_json` | TEXT | **JSON array** of AI-derived keyword strings (e.g. `["Riyadh","desert","surveillance"]`) |
| `featured` | INTEGER NOT NULL DEFAULT 0 | 0 / 1 |
| `ingestion_status` | TEXT NOT NULL | `discovered` / `scraped` / `normalized` / `needs_review` / `ready` / `published` / `rejected` / `error` |
| `raw_json` | TEXT NOT NULL | **Full original scraped JSON.** Body text/HTML and any non-promoted fields are in here. |
| `created_at`, `updated_at` | TEXT | |

Indexes: `journal_id`, `ingestion_status`, `publication_date`, `content_type`, partial index on `featured = 1`.

### `authors`
One row per **person** (writer, translator, visual artist — anyone who contributed).
Renamed semantically but the table name stays `authors` to keep queries familiar.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | |
| `name` | TEXT NOT NULL | |
| `slug` | TEXT NOT NULL UNIQUE | Slugified name; collisions handled in code |
| `bio` | TEXT | One canonical bio (snapshot from the first piece that supplied one) |
| `created_at`, `updated_at` | TEXT | |

### `piece_contributors`
Junction. **A person's relationship to a specific piece.**

| Column | Type | Notes |
|---|---|---|
| `piece_id` | INTEGER NOT NULL FK | → `pieces.id`, `ON DELETE CASCADE` |
| `author_id` | INTEGER NOT NULL FK | → `authors.id`, `ON DELETE CASCADE` |
| `role` | TEXT NOT NULL | CHECK: `'author' \| 'translator' \| 'visual_artist'` |
| `display_order` | INTEGER NOT NULL DEFAULT 1 | Order within a role on a given piece |
| `created_at` | TEXT | |

**PRIMARY KEY** `(piece_id, author_id, role)` — a person can play more than one role on the same piece (rare but possible).

### `themes`
Curated editorial vocabulary. **Empty at MVP launch** — populate as Kopani's editors add curated tags.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | |
| `name` | TEXT NOT NULL UNIQUE | e.g. `"grief"` |
| `slug` | TEXT NOT NULL UNIQUE | |
| `description` | TEXT | |
| `created_at`, `updated_at` | TEXT | |

### `piece_themes`
Junction. PK `(piece_id, theme_id)`. Cascading deletes from both sides.

---

## Why `role` lives on the junction, not on `authors`

A given person can be the **author** of one piece and the **translator** of another. Role is therefore a property of the *relationship*, not the person. Putting it on `piece_contributors` keeps `authors` clean as a pure people table and avoids duplicating rows per role.

---

## Why `themes` and `ai_keywords_json` are separate

`themes` is your **editorial vocabulary** — a small, curated set of tags Kopani's editors maintain ("grief", "exile", "the body"). Each one is reusable across many pieces and has a description.

`ai_keywords_json` is the **raw AI extraction** — per-piece, often one-off, sometimes noisy ("April", "Saudi Arabia", "Tuesday morning"). Stuffing these into `themes` would explode the theme list with thousands of single-use entries.

Two consequences worth noting:

1. Today, 42 pieces have AI keywords (the 15 Threepenny + 27 Evergreen files). The other 83 have `NULL`. When you process the remaining journals later, you'll just `UPDATE pieces SET ai_keywords_json = ? WHERE id = ?`.
2. If editors ever decide an AI keyword deserves promotion to a curated theme, that's a manual one-row insert into `themes` and a few rows into `piece_themes`. No schema change.

---

## Why `raw_json` instead of `body_text` / `body_html` columns

You said Kopani never displays piece bodies — copyright. So the body's only job is to feed *internal* derivations (word count, reading time, keyword extraction). Storing the full original blob:

- preserves everything the scraper captured, including fields we haven't promoted to columns,
- lets you re-derive anything later via `json_extract(raw_json, '$.path.to.field')` without touching the source sites,
- avoids the awkward question of "which body — the cleaned text, the raw HTML, the paragraphs?" — they're all in there,
- costs almost nothing: the test ingest of all 125 pieces produces a **3.4 MB** database.

Example query against the blob:

```sql
SELECT title,
       json_extract(raw_json, '$.scrape_meta.scraper_version') AS scraper_v
FROM pieces
WHERE json_extract(raw_json, '$.derived.visual_artist') IS NOT NULL;
```

---

## Common query patterns

### Latest published pieces for homepage
```sql
SELECT p.id, p.title, p.publication_date, j.slug AS journal
FROM pieces p JOIN journals j ON j.id = p.journal_id
WHERE p.ingestion_status = 'published'
ORDER BY COALESCE(p.publication_date, p.created_at) DESC
LIMIT 20;
```

### All pieces by a person, with their role on each
```sql
SELECT p.title, pc.role, j.slug AS journal
FROM authors a
JOIN piece_contributors pc ON pc.author_id = a.id
JOIN pieces p              ON p.id = pc.piece_id
JOIN journals j            ON j.id = p.journal_id
WHERE a.slug = 'tara-bergin'
ORDER BY p.publication_date DESC;
```

### All pieces with a given AI keyword (case-insensitive)
```sql
SELECT p.id, p.title
FROM pieces p, json_each(p.ai_keywords_json) k
WHERE LOWER(k.value) = 'memory';
```

### All translated pieces, with author + translator
```sql
SELECT p.title,
       MAX(CASE WHEN pc.role='author'     THEN a.name END) AS author,
       MAX(CASE WHEN pc.role='translator' THEN a.name END) AS translator
FROM pieces p
JOIN piece_contributors pc ON pc.piece_id = p.id
JOIN authors a              ON a.id       = pc.author_id
GROUP BY p.id
HAVING translator IS NOT NULL
ORDER BY p.title;
```

---

## Operational notes

- **Foreign keys**: SQLite does not enforce them unless `PRAGMA foreign_keys = ON;` is set on each connection. `ingest.py` does this; the frontend must too.
- **Re-running ingest**: idempotent. Existing pieces match on `original_url` and update in place; their contributors are wiped and re-linked.
- **Hosting**: A single SQLite file on a DigitalOcean droplet is the right call for this dataset size. WAL mode (`PRAGMA journal_mode = WAL;`) is worth turning on if anything other than the ingest writes to the DB.
- **Auth**: Keep user accounts in a separate store (separate SQLite file is fine). Nothing in this schema references users.

---

## Verified ingest results (125 source files)

```
journals             : 5
pieces               : 125
authors              : 147
piece_contributors   : 156    (126 authors + 9 translators + 21 visual artists)
themes               : 0      (curated; populate manually)
piece_themes         : 0

content_type distribution
  poetry           42    nonfiction        9
  essay            35    art               7
  fiction          18    youth_portfolio   5
  table_talk        3    podcast           2
  art_review        1    book_review       1
  interview         1    review            1

pieces with ai_keywords_json : 42  (Threepenny 15 + Evergreen 27)

Database file size           : ~3.4 MB
```
