-- ============================================================================
-- Kopani MVP database schema (SQLite)
-- v2 — see db_schema_kopani_mvp_v2.md for prose explanation
-- ============================================================================
-- Apply with:
--   sqlite3 kopani.sqlite < schema.sql
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- journals
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS journals (
  id                    INTEGER PRIMARY KEY,
  slug                  TEXT    NOT NULL UNIQUE,
  name                  TEXT    NOT NULL,
  homepage_url          TEXT    NOT NULL UNIQUE,
  description           TEXT,
  country               TEXT,
  city                  TEXT,
  genres_supported_json TEXT,                              -- JSON array
  issue_data_status     TEXT    NOT NULL DEFAULT 'none'
                        CHECK (issue_data_status IN ('none','partial','good')),
  issue_notes           TEXT,
  created_at            TEXT    NOT NULL DEFAULT (datetime('now')),
  updated_at            TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- pieces
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pieces (
  id                       INTEGER PRIMARY KEY,
  slug                     TEXT    NOT NULL,
  title                    TEXT    NOT NULL,
  subtitle                 TEXT,
  journal_id               INTEGER NOT NULL REFERENCES journals(id),
  original_url             TEXT    NOT NULL UNIQUE,
  content_type             TEXT    NOT NULL,    -- normalized; free-text
  content_type_raw         TEXT,                -- original from source, kept for audit
  format                   TEXT    NOT NULL DEFAULT 'text/html',
  summary                  TEXT,                -- Kopani-written blurb (future use)
  meta_description         TEXT,                -- source's own blurb / og:description
  publication_date         TEXT,                -- ISO YYYY-MM-DD if known
  publication_date_display TEXT,                -- human-readable, e.g. "Spring 2019"
  word_count_estimate      INTEGER,
  read_time_minutes        INTEGER,
  rights_status            TEXT    NOT NULL DEFAULT 'unknown'
                           CHECK (rights_status IN ('unknown','all_rights_reserved',
                                                    'partner_approved','public_domain','other')),
  image_url                TEXT,                -- Kopani-owned image
  source_image_url         TEXT,                -- original image on source site (reference only)
  issue_label              TEXT,
  issue_url                TEXT,
  issue_metadata_json      TEXT,                -- JSON object
  ai_keywords_json         TEXT,                -- JSON array of strings, from AI processing
  featured                 INTEGER NOT NULL DEFAULT 0 CHECK (featured IN (0,1)),
  ingestion_status         TEXT    NOT NULL DEFAULT 'normalized',
  raw_json                 TEXT    NOT NULL,    -- full scraped JSON blob
  created_at               TEXT    NOT NULL DEFAULT (datetime('now')),
  updated_at               TEXT    NOT NULL DEFAULT (datetime('now')),
  UNIQUE (journal_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_pieces_journal       ON pieces(journal_id);
CREATE INDEX IF NOT EXISTS idx_pieces_status        ON pieces(ingestion_status);
CREATE INDEX IF NOT EXISTS idx_pieces_pubdate       ON pieces(publication_date);
CREATE INDEX IF NOT EXISTS idx_pieces_content_type  ON pieces(content_type);
CREATE INDEX IF NOT EXISTS idx_pieces_featured      ON pieces(featured) WHERE featured = 1;

-- ---------------------------------------------------------------------------
-- authors  (anyone who contributed to a piece: writer, translator, artist)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS authors (
  id          INTEGER PRIMARY KEY,
  name        TEXT    NOT NULL,
  slug        TEXT    NOT NULL UNIQUE,
  bio         TEXT,
  created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
  updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- piece_contributors  (junction: who did what on which piece)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS piece_contributors (
  piece_id       INTEGER NOT NULL REFERENCES pieces(id)  ON DELETE CASCADE,
  author_id      INTEGER NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
  role           TEXT    NOT NULL
                 CHECK (role IN ('author','translator','visual_artist')),
  display_order  INTEGER NOT NULL DEFAULT 1,
  created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (piece_id, author_id, role)
);

CREATE INDEX IF NOT EXISTS idx_pc_author ON piece_contributors(author_id);
CREATE INDEX IF NOT EXISTS idx_pc_role   ON piece_contributors(role);

-- ---------------------------------------------------------------------------
-- themes  (curated editorial vocabulary — NOT the AI-derived keywords)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS themes (
  id           INTEGER PRIMARY KEY,
  name         TEXT    NOT NULL UNIQUE,
  slug         TEXT    NOT NULL UNIQUE,
  description  TEXT,
  created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
  updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS piece_themes (
  piece_id   INTEGER NOT NULL REFERENCES pieces(id)  ON DELETE CASCADE,
  theme_id   INTEGER NOT NULL REFERENCES themes(id)  ON DELETE CASCADE,
  PRIMARY KEY (piece_id, theme_id)
);

CREATE INDEX IF NOT EXISTS idx_pt_theme ON piece_themes(theme_id);
