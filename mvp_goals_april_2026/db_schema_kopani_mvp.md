# Kopani MVP Database Schema (SQLite)

This document describes the **canonical database structure** for Kopani’s MVP, including:
- Tables
- Fields and types
- Acceptable values / enums
- Design considerations
- Example values
- A diagram of relationships (in ASCII)

The goal is to keep this as a **living reference** that can survive into later stages.

---

## Overview

Kopani’s MVP data model has six tables:

- `journals`
- `pieces`
- `authors`
- `piece_authors` (junction: many-to-many)
- `themes`
- `piece_themes` (junction: many-to-many)

We intentionally **do not model “issues” as a separate table** in the MVP. Issue-related information is stored as simple fields on `pieces` and notes/status on `journals`.

Primary key strategy:

- Each main entity table has a **surrogate integer primary key** (`id INTEGER PRIMARY KEY`).
- Junction tables use **composite primary keys** on their foreign keys (`PRIMARY KEY (piece_id, author_id)` etc.).

---

## 1. journals

One row per **literary journal**.

### 1.1. Table definition (conceptual)

- `id` – INTEGER PRIMARY KEY
- `slug` – TEXT, NOT NULL, UNIQUE
- `name` – TEXT, NOT NULL
- `homepage_url` – TEXT, NOT NULL, UNIQUE
- `description` – TEXT, NULL
- `country` – TEXT, NULL
- `city` – TEXT, NULL
- `genres_supported_json` – TEXT, NULL (JSON array)
- `issue_data_status` – TEXT, NOT NULL, default `'none'`
- `issue_notes` – TEXT, NULL
- `created_at` – TEXT (ISO datetime), NOT NULL
- `updated_at` – TEXT (ISO datetime), NOT NULL

### 1.2. Field details and examples

**`id`**
- Type: INTEGER PRIMARY KEY
- Meaning: Internal journal identifier.
- Example: `1`

**`slug`**
- Type: TEXT, UNIQUE
- Meaning: URL-friendly identifier.
- Example: `"new-orleans-review"`

**`name`**
- Type: TEXT
- Meaning: Human-readable name of the journal.
- Example: `"New Orleans Review"`

**`homepage_url`**
- Type: TEXT, UNIQUE
- Meaning: Journal’s main URL.
- Example: `"https://www.neworleansreview.org"`

**`description`**
- Type: TEXT, nullable
- Meaning: Short description.
- Example: `"A journal of contemporary literature and culture based in New Orleans."`

**`country` / `city`**
- Type: TEXT, nullable
- Meaning: Location metadata when known.
- Example: `"United States"`, `"New Orleans"`

**`genres_supported_json`**
- Type: TEXT containing JSON array
- Meaning: High-level genres the journal publishes.
- Example:
  - Stored as: `["poetry", "fiction", "nonfiction"]`
  - In DB: `"[""poetry"",""fiction"",""nonfiction""]"`

**`issue_data_status`**
- Type: TEXT
- Meaning: How good Kopani’s issue information is for this journal.
- Acceptable values (enum-ish):
  - `'none'` – no issue-level data
  - `'partial'` – some issues identified or parsed
  - `'good'` – reasonably complete for recent years

**Examples:**
- `"none"`
- `"partial"`

**`issue_notes`**
- Type: TEXT, nullable
- Meaning: Free-form notes about issues.
- Example: `"Issue landing pages exist from 2020 onwards; older issues in PDFs only."`

**`created_at` / `updated_at`**
- Type: TEXT (ISO 8601)
- Meaning: Timestamps when journal row was created/updated.
- Example: `"2026-04-11T18:30:00Z"`

---

## 2. pieces

One row per **piece of writing** (poem, story, essay, etc.).

### 2.1. Table definition (conceptual)

- `id` – INTEGER PRIMARY KEY
- `slug` – TEXT, NOT NULL, UNIQUE
- `title` – TEXT, NOT NULL
- `journal_id` – INTEGER, NOT NULL (FK → journals.id)
- `original_url` – TEXT, NOT NULL, UNIQUE
- `content_type` – TEXT, NOT NULL
- `format` – TEXT, NOT NULL, default `'text/html'`
- `summary` – TEXT, NULL
- `publication_date` – TEXT, NULL (ISO date `YYYY-MM-DD`)
- `publication_date_display` – TEXT, NULL
- `word_count_estimate` – INTEGER, NULL
- `read_time_minutes` – INTEGER, NULL
- `rights_status` – TEXT, NOT NULL, default `'unknown'`
- `image_url` – TEXT, NULL
- `source_image_url` – TEXT, NULL
- `issue_label` – TEXT, NULL
- `issue_url` – TEXT, NULL
- `issue_metadata_json` – TEXT, NULL
- `featured` – INTEGER (0/1), NOT NULL, default 0
- `ingestion_status` – TEXT, NOT NULL
- `created_at` – TEXT, NOT NULL
- `updated_at` – TEXT, NOT NULL

### 2.2. Field details and examples

**`id`**
- Type: INTEGER PRIMARY KEY
- Example: `101`

**`slug`**
- Type: TEXT, UNIQUE
- Meaning: URL path segment for Kopani.
- Example: `"a-world-of-objects"`

**`title`**
- Type: TEXT
- Example: `"A World of Objects"`

**`journal_id`**
- Type: INTEGER (FK)
- Meaning: Links to `journals.id`.
- Example: `1` (which is New Orleans Review)

**`original_url`**
- Type: TEXT, UNIQUE
- Meaning: Canonical URL on the journal site.
- Example: `"https://www.neworleansreview.org/a-world-of-objects/"`

**`content_type`**
- Type: TEXT
- Meaning: Controlled vocabulary for form/genre.
- Recommended acceptable values:
  - `'poem'`
  - `'short_story'`
  - `'flash_fiction'`
  - `'essay'`
  - `'review'`
  - `'interview'`
  - `'hybrid'`
  - `'other'`
- Example: `"essay"`

**`format`**
- Type: TEXT
- Meaning: Technical delivery format.
- Typical values:
  - `'text/html'` (default)
  - `'application/pdf'`
  - `'audio'` (if you ever add audio)
- Example: `"text/html"`

**`summary`**
- Type: TEXT, nullable
- Meaning: Short **original Kopani blurb**, not copied from the journal.
- Example:
  `"A tightly observed essay in which everyday objects become charged with memory and grief."`
- If not yet written: `NULL`

**`publication_date`**
- Type: TEXT, nullable
- Meaning: Normalized date if known (ISO `YYYY-MM-DD`).
- Example: `"2025-06-15"`
- If only approximate or unknown: `NULL`

**`publication_date_display`**
- Type: TEXT, nullable
- Meaning: Human-readable date/season string.
- Example: `"Summer 2025"`
- If not available: `NULL`

**`word_count_estimate`**
- Type: INTEGER, nullable
- Meaning: Approximate word count.
- Example: `2300`

**`read_time_minutes`**
- Type: INTEGER, nullable
- Meaning: Approximate read time.
- Example: `10`

**`rights_status`**
- Type: TEXT
- Meaning: Kopani’s understanding of rights.
- Suggested values:
  - `'unknown'`
  - `'all_rights_reserved'`
  - `'partner_approved'`
  - `'public_domain'` (rare)
  - `'other'`
- Example: `"all_rights_reserved"`

**`image_url`**
- Type: TEXT, nullable
- Meaning: URL of an image **you own or have rights to display** (Kopani-side).
- Example: `"https://kopani.local/assets/pieces/nor-objects.jpg"`
- If none: `NULL`

**`source_image_url`**
- Type: TEXT, nullable
- Meaning: Original piece’s image URL on the journal site (for internal reference).
- Example: `"https://www.neworleansreview.org/wp-content/uploads/2025/05/object.jpg"`

**`issue_label`**
- Type: TEXT, nullable
- Meaning: Free-text label for issue if known.
- Example: `"Issue 53: Summer 2025"`

**`issue_url`**
- Type: TEXT, nullable
- Meaning: URL of the journal’s issue page.
- Example: `"https://www.neworleansreview.org/issue-53-summer-2025/"`

**`issue_metadata_json`**
- Type: TEXT, nullable
- Meaning: JSON blob with any structured issue info you may want to store without committing to a separate `issues` table.
- Example:
  ```json
  {
    "number": 53,
    "season": "Summer",
    "year": 2025
  }
  ```

**`featured`**
- Type: INTEGER (0 or 1)
- Meaning: Whether the piece is currently featured in a prominent slot.
- Acceptable values:
  - `0` – not featured
  - `1` – featured
- Example: `1`

**`ingestion_status`**
- Type: TEXT
- Meaning: Position of the piece in your scraping/curation pipeline.
- Suggested enum-like values:
  - `'discovered'` – URL found
  - `'scraped'` – raw metadata extracted
  - `'normalized'` – mapped into canonical schema
  - `'needs_review'` – requires manual check/fix
  - `'ready'` – good enough to choose for publishing
  - `'published'` – live on Kopani
  - `'rejected'` – intentionally not using this piece
  - `'error'` – ingestion failure
- Example: `"published"`

**`created_at` / `updated_at`**
- Type: TEXT (ISO)
- Meaning: Row creation and update timestamps.

---

## 3. authors

One row per **author**.

### 3.1. Table definition (conceptual)

- `id` – INTEGER PRIMARY KEY
- `name` – TEXT, NOT NULL
- `slug` – TEXT, NOT NULL, UNIQUE
- `bio` – TEXT, NULL
- `created_at` – TEXT, NOT NULL
- `updated_at` – TEXT, NOT NULL

### 3.2. Field details and examples

**`name`**
- Type: TEXT
- Example: `"Emily Farranto"`

**`slug`**
- Type: TEXT, UNIQUE
- Example: `"emily-farranto"`

**`bio`**
- Type: TEXT, nullable
- Example: `"Emily Farranto is a writer based in New Orleans. Her work appears in..."`

---

## 4. piece_authors

Junction table for the many-to-many relationship between `pieces` and `authors`.

### 4.1. Table definition (conceptual)

- `piece_id` – INTEGER, NOT NULL (FK → pieces.id)
- `author_id` – INTEGER, NOT NULL (FK → authors.id)
- `author_order` – INTEGER, NOT NULL
- `PRIMARY KEY (piece_id, author_id)`
- Optional: `UNIQUE(piece_id, author_order)` to prevent two authors with the same order for a piece.

### 4.2. Field details and examples

For a piece with two authors:

```text
piece_id | author_id | author_order
-------- | --------- | ------------
101      | 201       | 1
101      | 202       | 2
```

That allows you to:
- display names in order,
- query all pieces by a given author,
- query all authors for a given piece.

---

## 5. themes

One row per **controlled theme/subject**.

### 5.1. Table definition (conceptual)

- `id` – INTEGER PRIMARY KEY
- `name` – TEXT, NOT NULL, UNIQUE
- `slug` – TEXT, NOT NULL, UNIQUE
- `description` – TEXT, NULL
- `created_at` – TEXT, NOT NULL
- `updated_at` – TEXT, NOT NULL

### 5.2. Field details and examples

**`name`**
- Example: `"grief"`

**`slug`**
- Example: `"grief"`

**`description`**
- Example: `"Works that center on loss, mourning, or bereavement."`

---

## 6. piece_themes

Junction table for many-to-many between `pieces` and `themes`.

### 6.1. Table definition (conceptual)

- `piece_id` – INTEGER, NOT NULL (FK → pieces.id)
- `theme_id` – INTEGER, NOT NULL (FK → themes.id)
- `PRIMARY KEY (piece_id, theme_id)`

### 6.2. Example rows

```text
piece_id | theme_id
-------- | --------
101      | 301      -- grief
101      | 302      -- family
```

---

## 7. Common query patterns

These patterns inform indexing and confirm that the schema supports your needs.

### 7.1. Latest featured pieces for homepage

```sql
SELECT p.*
FROM pieces p
WHERE p.featured = 1
  AND p.ingestion_status = 'published'
ORDER BY p.publication_date DESC
LIMIT 20;
```

### 7.2. All pieces from a given journal

```sql
SELECT p.*
FROM pieces p
JOIN journals j ON p.journal_id = j.id
WHERE j.slug = 'new-orleans-review'
  AND p.ingestion_status = 'published'
ORDER BY p.publication_date DESC;
```

### 7.3. All pieces by a given author

```sql
SELECT p.*
FROM pieces p
JOIN piece_authors pa ON pa.piece_id = p.id
JOIN authors a ON a.id = pa.author_id
WHERE a.slug = 'emily-farranto'
  AND p.ingestion_status = 'published'
ORDER BY p.publication_date DESC;
```

### 7.4. All pieces for a theme

```sql
SELECT p.*
FROM pieces p
JOIN piece_themes pt ON pt.piece_id = p.id
JOIN themes t ON t.id = pt.theme_id
WHERE t.slug = 'grief'
  AND p.ingestion_status = 'published'
ORDER BY p.publication_date DESC;
```

### 7.5. Find or upsert a piece by original URL

```sql
SELECT id, ingestion_status
FROM pieces
WHERE original_url = ?;
```

---

## 8. Relationship diagram (ASCII)

```text
+-----------+            +-------------+           +---------+
| journals  |            |   pieces    |           | authors |
+-----------+            +-------------+           +---------+
| id (PK)   |<--------+  | id (PK)     |  +------->| id (PK) |
| slug      |         |  | journal_id  |  |        | slug    |
| name      |         |  | slug        |  |        | name    |
| ...       |         |  | title       |  |        | ...     |
+-----------+         |  | ...         |  |        +---------+
                      |  +-------------+  |
                      |                   |
                      |                   |
                      |  +----------------v--------+
                      |  |     piece_authors      |
                      |  +------------------------+
                      +--| piece_id (PK, FK)      |
                         | author_id (PK, FK)     |
                         | author_order           |
                         +------------------------+


+---------+              +------------------+
| themes  |              |   piece_themes   |
+---------+              +------------------+
| id (PK) |<----------+  | piece_id (PK,FK) |
| slug    |           |  | theme_id (PK,FK) |
| name    |           |  +------------------+
| ...     |           |
+---------+           |
                      |
                      +------> pieces.id
```

---

## 9. Notes for future evolution

- If you later add a proper `issues` table, you can:
  - extract `issue_label`, `issue_url`, and `issue_metadata_json` into a dedicated table,
  - replace those fields on `pieces` with a foreign key `issue_id`.
- If you add more complex rights or partner features, consider normalizing `rights_status` into a separate table or using enumerated constraints.
- If search becomes important, consider:
  - SQLite FTS for `title` and `summary`,
  - or external search infrastructure.

For the MVP, this schema is intentionally modest but solid: it supports your main use cases (scraping, curation, display, and basic analytics) without over-modeling.
