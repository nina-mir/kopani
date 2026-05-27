# Kopani MVP – SQLite Schema (DDL + Indexes)

This document contains the **SQLite `CREATE TABLE` statements** and recommended **indexes** for the Kopani MVP schema.

It corresponds to the six-table model described in `db_schema_kopani_mvp.md`:

- `journals`
- `pieces`
- `authors`
- `piece_authors`
- `themes`
- `piece_themes`

> Notes:
> - `TEXT` timestamps are assumed to be ISO strings (`YYYY-MM-DDTHH:MM:SSZ` or similar).
> - Enum-like fields use plain `TEXT` with `CHECK` constraints where helpful, not real enums.
> - Foreign key enforcement in SQLite requires `PRAGMA foreign_keys = ON;` in your application.

---

## 0. Recommended PRAGMA

```sql
PRAGMA foreign_keys = ON;
```

Call this once per connection in your app.

---

## 1. journals

```sql
CREATE TABLE journals (
    id                   INTEGER PRIMARY KEY,
    slug                 TEXT NOT NULL UNIQUE,
    name                 TEXT NOT NULL,
    homepage_url         TEXT NOT NULL UNIQUE,
    description          TEXT,
    country              TEXT,
    city                 TEXT,
    genres_supported_json TEXT,
    issue_data_status    TEXT NOT NULL DEFAULT 'none',
    issue_notes          TEXT,
    created_at           TEXT NOT NULL,
    updated_at           TEXT NOT NULL,
    CHECK (issue_data_status IN ('none', 'partial', 'good'))
);
```

### Indexes for `journals`

```sql
-- Look up by slug (already UNIQUE, but explicit index is okay)
CREATE INDEX IF NOT EXISTS idx_journals_slug
    ON journals(slug);

-- If you ever query by country/city:
CREATE INDEX IF NOT EXISTS idx_journals_country_city
    ON journals(country, city);
```

---

## 2. pieces

```sql
CREATE TABLE pieces (
    id                       INTEGER PRIMARY KEY,
    slug                     TEXT NOT NULL UNIQUE,
    title                    TEXT NOT NULL,
    journal_id               INTEGER NOT NULL,
    original_url             TEXT NOT NULL UNIQUE,
    content_type             TEXT NOT NULL,
    format                   TEXT NOT NULL DEFAULT 'text/html',
    summary                  TEXT,
    publication_date         TEXT,    -- ISO date, e.g. '2025-06-15'
    publication_date_display TEXT,
    word_count_estimate      INTEGER,
    read_time_minutes        INTEGER,
    rights_status            TEXT NOT NULL DEFAULT 'unknown',
    image_url                TEXT,
    source_image_url         TEXT,
    issue_label              TEXT,
    issue_url                TEXT,
    issue_metadata_json      TEXT,
    featured                 INTEGER NOT NULL DEFAULT 0,
    ingestion_status         TEXT NOT NULL,
    created_at               TEXT NOT NULL,
    updated_at               TEXT NOT NULL,

    FOREIGN KEY (journal_id) REFERENCES journals(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CHECK (featured IN (0, 1)),
    CHECK (content_type IN (
        'poem',
        'short_story',
        'flash_fiction',
        'essay',
        'review',
        'interview',
        'hybrid',
        'other'
    )),
    CHECK (rights_status IN (
        'unknown',
        'all_rights_reserved',
        'partner_approved',
        'public_domain',
        'other'
    )),
    CHECK (ingestion_status IN (
        'discovered',
        'scraped',
        'normalized',
        'needs_review',
        'ready',
        'published',
        'rejected',
        'error'
    ))
);
```

### Indexes for `pieces`

```sql
-- Filter by journal and sort by date
CREATE INDEX IF NOT EXISTS idx_pieces_journal_date
    ON pieces(journal_id, publication_date DESC);

-- Homepage queries: featured + published recently
CREATE INDEX IF NOT EXISTS idx_pieces_featured_date
    ON pieces(featured, ingestion_status, publication_date DESC);

-- Fast lookup by ingestion_status alone
CREATE INDEX IF NOT EXISTS idx_pieces_ingestion_status
    ON pieces(ingestion_status);

-- Title search (basic LIKE)
CREATE INDEX IF NOT EXISTS idx_pieces_title
    ON pieces(title);
```

---

## 3. authors

```sql
CREATE TABLE authors (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    slug       TEXT NOT NULL UNIQUE,
    bio        TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Indexes for `authors`

```sql
-- Lookup by slug
CREATE INDEX IF NOT EXISTS idx_authors_slug
    ON authors(slug);

-- Optional: if you often search by name
CREATE INDEX IF NOT EXISTS idx_authors_name
    ON authors(name);
```

---

## 4. piece_authors

Many-to-many between `pieces` and `authors`, with ordering.

```sql
CREATE TABLE piece_authors (
    piece_id     INTEGER NOT NULL,
    author_id    INTEGER NOT NULL,
    author_order INTEGER NOT NULL,

    PRIMARY KEY (piece_id, author_id),

    FOREIGN KEY (piece_id) REFERENCES pieces(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);
```

Optional constraint to prevent duplicate order values for a piece:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_piece_authors_piece_order
    ON piece_authors(piece_id, author_order);
```

### Indexes for `piece_authors`

```sql
-- Find all authors for a piece in order
CREATE INDEX IF NOT EXISTS idx_piece_authors_piece
    ON piece_authors(piece_id, author_order);

-- Find all pieces by an author
CREATE INDEX IF NOT EXISTS idx_piece_authors_author
    ON piece_authors(author_id, piece_id);
```

---

## 5. themes

```sql
CREATE TABLE themes (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    slug        TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
```

### Indexes for `themes`

```sql
-- Lookup by slug
CREATE INDEX IF NOT EXISTS idx_themes_slug
    ON themes(slug);
```

---

## 6. piece_themes

Many-to-many between `pieces` and `themes`.

```sql
CREATE TABLE piece_themes (
    piece_id INTEGER NOT NULL,
    theme_id INTEGER NOT NULL,

    PRIMARY KEY (piece_id, theme_id),

    FOREIGN KEY (piece_id) REFERENCES pieces(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (theme_id) REFERENCES themes(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);
```

### Indexes for `piece_themes`

```sql
-- Find all themes for a piece
CREATE INDEX IF NOT EXISTS idx_piece_themes_piece
    ON piece_themes(piece_id, theme_id);

-- Find all pieces for a theme
CREATE INDEX IF NOT EXISTS idx_piece_themes_theme
    ON piece_themes(theme_id, piece_id);
```

---

## 7. Suggested creation order

To avoid foreign-key errors:

1. `CREATE TABLE journals`
2. `CREATE TABLE pieces`
3. `CREATE TABLE authors`
4. `CREATE TABLE piece_authors`
5. `CREATE TABLE themes`
6. `CREATE TABLE piece_themes`
7. Then create all indexes.

You can put everything in a single migration file, or break it into multiple migration steps as your project evolves.

---

## 8. Quick sanity checks

After applying this schema, you should be able to:

- Insert a `journal`
- Insert a `piece` that references that `journal`
- Insert an `author` and link it via `piece_authors`
- Insert a `theme` and link it via `piece_themes`
- Run queries like:
  - “All published pieces for journal X”
  - “All pieces by author Y”
  - “All pieces tagged with theme Z”

This schema is intentionally minimalist but solid for a one-person MVP.