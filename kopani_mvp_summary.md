# Kopani MVP – Project Summary

## 1. Name and high-level concept

**Project name:** Kopani  
**Front-page brand:** Kopani Post

Kopani is a **discovery platform and editorial front page for independent literary journals**. It curates standout poems, stories, essays, and related work from small and mid-size magazines and sends readers back to the original publications.

The first goal is not to be a full writer/journal ecosystem, but to prove that a solo founder can:

- Reliably surface strong work from independent journals.
- Package that work in a beautiful, credible front page.
- Drive measurable outbound traffic back to journals.
- Maintain the pipeline with manageable effort.

---

## 2. Scope of the MVP

### 2.1. What the MVP is

The MVP is:

- A **magazine-style homepage** (“Kopani Post”) that looks like a real editorial destination.
- A small but high-quality **database of journals and pieces**.
- A **repeatable scraping and normalization pipeline** for selected journals.
- Basic **categorization and discovery** (journal, content type, themes).
- **Outbound links** to original journal pages.
- **Newsletter signup** and basic **analytics**.

### 2.2. What the MVP is not

The MVP does *not* need to include:

- Writer accounts.
- Submission tracking tools.
- Full-text search across everything (beyond simple search/browse).
- AI recommendation engine.
- Journal dashboards or payments.
- Community comments / social features.

Those are future phases.

---

## 3. Users and goals

### 3.1. Reader

Reader goals:

- Discover great poems, stories, and essays quickly.
- Trust that Kopani’s front page is worth returning to.
- Click through to journals to read the full work.

### 3.2. Journal editor / staff

Journal goals:

- Get more **traffic and visibility**.
- Have their work presented in a respectful, curated way.
- See Kopani as additive, not extractive.

### 3.3. Founder-operator

Founder goals:

- Be able to **ingest and normalize** journal content regularly.
- Maintain **clean metadata** and controlled tags.
- Run the operation solo without being buried in manual work.

---

## 4. Data model (canonical schema)

The model focuses on two core entities:

- `Journal` – host publication.
- `Piece` – individual work (poem, story, essay, etc.).

“Issue” is **not** modeled as a separate table for the MVP; issue information is stored as free-form fields on `pieces` and light status/notes on `journals`.

### 4.1. Journal (conceptual fields)

Core fields:

- `id` – internal integer ID.
- `slug` – URL-friendly identifier (`"new-orleans-review"`).
- `name` – human name (`"New Orleans Review"`).
- `homepage_url` – canonical journal URL.
- `description` – short text description.
- `country`, `city` – optional location metadata.
- `genres_supported_json` – JSON array of high-level genres (e.g., `["poetry","fiction","nonfiction"]`).
- `issue_data_status` – enum-like:
  - `'none'`
  - `'partial'`
  - `'good'`
- `issue_notes` – free-text notes about issue coverage.
- `created_at`, `updated_at` – ISO timestamps.

### 4.2. Piece (canonical schema)

Guided by Dublin Core / MODS concepts:

Identifiers:

- `id` – internal integer ID.
- `slug` – Kopani URL slug (`"a-world-of-objects"`).
- `original_url` – canonical URL on the journal’s site.

Core descriptive fields:

- `title` – title as given by the journal.
- `journal_id` – FK to `journals.id`.
- `author_names` (conceptually) – modeled in DB via `authors` + `piece_authors` (see DB schema).
- `content_type` – controlled vocabulary:
  - `'poem'`, `'short_story'`, `'flash_fiction'`, `'essay'`, `'review'`, `'interview'`, `'hybrid'`, `'other'`.
- `format` – `'text/html'` by default; potential support for `application/pdf`, `audio`.

Dates:

- `publication_date` – normalized ISO date (`YYYY-MM-DD`), nullable.
- `publication_date_display` – human-readable string (`"Summer 2025"`), nullable.

Descriptive metadata:

- `summary` – **Kopani’s own short blurb**, nullable.
- `themes` – list of controlled subject tags, modeled via `themes` and `piece_themes`.
- `keywords` – optional free-form keywords (not structured in the DB at MVP).

Length and reading experience:

- `word_count_estimate` – integer, nullable.
- `read_time_minutes` – integer, nullable.

Issue references (without a separate table):

- `issue_label` – free text (`"Issue 53: Summer 2025"`).
- `issue_url` – URL of the journal’s issue landing page.
- `issue_metadata_json` – optional JSON blob with more structured issue info (e.g., `{ "number": 53, "season": "Summer", "year": 2025 }`).

Rights and images:

- `rights_status` – enum-like:
  - `'unknown'`
  - `'all_rights_reserved'`
  - `'partner_approved'`
  - `'public_domain'`
  - `'other'`
- `image_url` – Kopani-owned/licensed image URL (or `NULL`).
- `source_image_url` – original journal’s image URL (internal reference, not necessarily rendered).

Editorial and workflow:

- `featured` – 0/1 flag for homepage prominence.
- `ingestion_status` – pipeline state:
  - `'discovered'`
  - `'scraped'`
  - `'normalized'`
  - `'needs_review'`
  - `'ready'`
  - `'published'`
  - `'rejected'`
  - `'error'`
- `created_at`, `updated_at` – ISO timestamps.

---

## 5. Database design (SQLite, 6 tables)

For the MVP, the chosen relational structure uses **SQLite** with six tables:

1. `journals`
2. `pieces`
3. `authors`
4. `piece_authors` (junction)
5. `themes`
6. `piece_themes` (junction)

### 5.1. Primary key strategy

- **Entity tables** (`journals`, `pieces`, `authors`, `themes`):
  - `id INTEGER PRIMARY KEY` (surrogate key).
- **Junction tables**:
  - `piece_authors` → `PRIMARY KEY (piece_id, author_id)`
  - `piece_themes` → `PRIMARY KEY (piece_id, theme_id)`

This avoids duplicate relationships and makes joins straightforward.

### 5.2. Junction tables

**`piece_authors`**

- `piece_id` – FK → `pieces.id`.
- `author_id` – FK → `authors.id`.
- `author_order` – integer to preserve display order.
- PK: `(piece_id, author_id)`.
- Optional unique index: `(piece_id, author_order)`.

**`piece_themes`**

- `piece_id` – FK → `pieces.id`.
- `theme_id` – FK → `themes.id`.
- PK: `(piece_id, theme_id)`.

---

## 6. Ingestion workflow (`ingestion_status`)

`ingestion_status` on `pieces` tracks each record’s progress through the pipeline:

- `discovered` – URL found from a journal archive.
- `scraped` – raw metadata extracted from the page.
- `normalized` – mapped into Kopani’s canonical schema.
- `needs_review` – requires manual correction or fill-in.
- `ready` – clean enough to consider for publication.
- `published` – live on Kopani.
- `rejected` – intentionally not using this record.
- `error` – technical problem in scraping/normalization.

This supports queries like:

- “All `needs_review` pieces for manual curation.”
- “All `ready` pieces that could be featured next.”
- “All `published` pieces for a given journal/author/theme.”

---

## 7. Common query scenarios

The schema is optimized for these core queries:

1. **Homepage**: latest featured pieces  
   - Filter: `featured = 1 AND ingestion_status = 'published'`  
   - Sort by `publication_date DESC`.

2. **Journal view**: all published pieces from a journal  
   - Join `pieces` to `journals` via `journal_id`.
   - Filter by `journals.slug` and `pieces.ingestion_status`.

3. **Author view**: all pieces by a given author  
   - Join `authors` → `piece_authors` → `pieces`.
   - Filter by `authors.slug` and `pieces.ingestion_status`.

4. **Theme view**: all pieces tagged with a theme  
   - Join `themes` → `piece_themes` → `pieces`.
   - Filter by `themes.slug` and `pieces.ingestion_status`.

5. **Ingestion dedupe**: find by original URL  
   - Query `pieces` by `original_url` to avoid duplicates.

---

## 8. Visual/editorial intent

The MVP front page should:

- Feel like a **modern literary magazine** rather than a raw index.
- Use strong typography and clear hierarchy.
- Rely on **short, sharp blurbs** to make pieces clickable.
- Always link out to the **original journal** to respect rights and drive traffic.

Images:

- `image_url` should point to images Kopani has rights to use (its own or explicitly permitted).
- `source_image_url` can store original image URLs for internal reference, but public display should be cautious.

---

## 9. MVP priorities

In order of importance:

1. **Database & canonical schema** locked in.
2. **Scraper & normalization pipeline** for a small set of journals (10–20).
3. **Curation workflow**:
   - pick standout pieces,
   - write summaries,
   - assign themes.
4. **Kopani Post homepage UI**:
   - sections like “Editor’s Picks,” “Poems,” “Stories,” “From Small Journals.”
5. **Basic browse/search** by journal, author, content type, and theme.
6. **Newsletter signup** and minimal analytics (page views, outbound clicks).

Domain purchase and full production hosting are explicitly **deferred** until the data and pipeline feel solid.

---

## 10. Future evolution notes

Later stages might add:

- A dedicated `issues` table and richer issue modeling.
- Writer-facing tools (submission tracking, recommendations).
- Journal-facing dashboards (traffic analytics, promotion tools).
- Personalized feeds and AI-assisted recommendations.
- More robust search (full-text) and more complex tagging.

This document is the **reference for the MVP stage** and should be updated if the canonical schema or database structure changes.