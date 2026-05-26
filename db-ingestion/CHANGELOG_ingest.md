# Changelog — `ingest.py`

All notable changes to the Kopani ingestion script. Newest first.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/);
versions are internal markers, not published releases.

---
## [0.5.0] — 2026-05-25

Editorial-field capture for Offing & Evergreen. No schema change.

### Added
- **Dek → `summary`.** `extract_offing` and `extract_evergreen` now read
  `derived.dek` into the canonical `summary` field. `upsert_piece` was wired to
  write `summary` (it previously ignored the column on both insert and update),
  so deks now land in `pieces.summary` for these two journals.
- **`descriptor_clause` → `issue_metadata_json`.** Both extractors add
  `derived.descriptor_clause` as a key inside `issue_metadata`, stored in the
  existing `issue_metadata_json` column. No new column.

### Fixed
- **Offing `piece_keywords` dropped.** `extract_offing` hardcoded
  `ai_keywords = None`, discarding keywords that were present in the source.
  Now reads `derived.piece_keywords` like Evergreen, so they flow into
  `ai_keywords_json`.

### Notes
- Schema unchanged — no migration needed.
- Re-running is idempotent and re-asserts `summary` from the JSON. Journals that
  emit no dek (Threepenny, Granta, NOR) will have `summary` set to NULL on
  re-ingest; switch hunk 3b to `COALESCE(excluded.summary, pieces.summary)` if
  you ever hand-write summaries into those rows.
- Bio insights (`author_bio_insights` etc.) remain in `raw_json` only — no
  column, by design.




## [0.4.1] - "Added essays & memoir, film_review, music review, art review, book review → review, and video to CONTENT_TYPE_MAP. Reclassified one NULL-type Mandarin translation as essay. Verified: only genuine 'other' (8) remain."

## [0.4.0] — 2026-05-22

[0.4.0] — applied to full dataset
Ran against all 1469 pieces: 0 errors. Verified dual-role contributors resolve to two legitimate self-translations (Bila, Miłosz). No false author credits remained.

The "shape tolerance" release. Hardens contributor extraction against
scraper-format drift and adds malformed-JSON recovery. This is the version
to run against the full ~1467-piece dataset.

### Added
- `_person_from(item, fallback_bio=None)` — normalizes a single person value
  into a `{'name', 'bio'}` record. Accepts a plain string, a
  `{"name", "bio"}` dict, or a `{"display_name": ...}` dict.
- `to_persons(value, fallback_bio=None)` — normalizes a whole person *field*
  (string | dict | list of either) into a list of `{'name', 'bio'}` records.
  `fallback_bio` is applied only to the first person.
- Tolerant JSON loader in the main loop: strict `json.loads` first, and only
  on failure does it strip trailing commas (`,}` / `,]`) and retry. Genuinely
  broken files still raise and are reported as errors rather than silently
  mangled.
- Ingest summary now lists any files that were auto-repaired by the tolerant
  loader, so they can be eyeballed afterward.
- Translator and visual-artist **bios** are now captured when the source
  provides them in dict form (previously dropped — stored as `NULL`).

### Fixed
- **Crash on dict-shaped person fields.** Evergreen's scraper evolved to emit
  `piece.translator` (and sometimes `visual_artist`) as `{"name", "bio"}`
  objects instead of strings. The old code passed the dict into `slugify()`,
  raising `normalize() argument 2 must be str, not dict`. Two known files
  affected: `fw_2024_bila_poetry_part_2.json`, `ss_2025_giudice_fic.json`.
- **Translator mis-credited as author (Evergreen only).** Evergreen sometimes
  lists the translator inside `authors_raw`, giving them a false `author`
  credit. New de-dupe rule: drop a person's `author` role if they also hold a
  `translator` role on the same piece **and** are not named in the explicit
  `piece.author` field. Genuine self-translations (where the author *is* the
  translator, e.g. Czesław Miłosz on "Borderlines", Gudani Ramikosi Bila) are
  preserved.

### Changed
- All five extractors (`extract_threepenny`, `extract_evergreen`,
  `extract_granta`, `extract_offing`, `extract_nor`) now route every
  contributor read through `_person_from` / `to_persons` instead of assuming
  strings or reading `.get("display_name")` directly. This makes them tolerant
  of future shape drift in any of the three roles.

### Notes
- Schema unchanged — no migration needed.
- Re-running is idempotent: pieces upsert on `original_url`, contributors are
  deleted and re-linked per piece. Re-running backfills the previously-dropped
  bios and corrects the false author credits.
- After running, re-check dual-role contributors (see the verification query
  in the README / chat). Anyone returned should be a real self-translation.

---

## [0.3.0] — 2026-05-21

Defensive robustness pass against non-string scalar fields.

### Added
- `_scalarize(value)` — coerces a dict/list/number into a representative
  string (prefers keys like `primary`, `value`, `name`, `type`, `label`,
  `display`, `text`; else first non-empty string; else stringified).

### Changed
- `slugify()` now accepts non-string input, scalarizing it first instead of
  crashing.
- `normalize_content_type()` now scalarizes dict/list `piece_type` /
  `content_type` values and preserves the original (JSON-stringified) value in
  `content_type_raw` for audit.

### Notes
- This release reduced the crash surface but did **not** fully fix dict-shaped
  *person* fields — names were scalarized for the slug but the raw dict could
  still reach the `authors.name` column. Fully resolved in 0.4.0.

---

## [0.2.0] — 2026-05-21

### Fixed
- **Threepenny `translator` stored as a list.** Files such as
  `atxaga_f09.json`, `atxaga_w07.json`, and `baudelaire_sp14.json` store
  `translator` (and occasionally `author`) as a JSON array, which crashed the
  string-only handling. Added an `_as_list` coercion in the Threepenny
  extractor so single values and lists are both handled. (Later superseded by
  the general `to_persons` helper in 0.4.0.)

### Notes
- After this fix, all 125 files in the original sample set ingested with 0
  errors.

---

## [0.1.0] — 2026-05-21

Initial ingestion script.

### Added
- Applies `schema.sql` (idempotent `CREATE TABLE IF NOT EXISTS`).
- Seeds the 5 journals: The Threepenny Review, New Orleans Review, Granta,
  The Offing, Evergreen Review.
- Per-journal extractor functions mapping each journal's distinct JSON shape
  to a common canonical record.
- `detect_journal()` to route each file to its extractor.
- Helpers: `slugify`, `coalesce`, `normalize_content_type` (free-text
  normalization via `CONTENT_TYPE_MAP`), `parse_reading_time`,
  `estimate_word_count`.
- Idempotent upserts:
  - `pieces` on `UNIQUE(original_url)` via `INSERT ... ON CONFLICT DO UPDATE`.
  - `authors` on `UNIQUE(slug)`, filling `bio` only when currently empty.
  - `piece_contributors` cleared and re-linked per piece, with `role`
    (`author` / `translator` / `visual_artist`) and `display_order`.
- Full original scraped JSON preserved in `pieces.raw_json`.
- AI-derived keywords stored in `pieces.ai_keywords_json`; curated `themes`
  kept separate and left empty for manual editorial use.
- CLI: `--db`, `--src`, `--schema`. Per-journal counts and first-10-errors
  summary on completion.

---

## Conventions for future entries

When you change `ingest.py`, add a new version block at the top using these
categories (omit any that don't apply):

- **Added** — new features, helpers, or fields.
- **Changed** — changes to existing behavior.
- **Fixed** — bug fixes.
- **Removed** — removed features.
- **Notes** — migration steps, re-run guidance, things to verify.

Bump the version: third digit for fixes/small changes, second digit for new
behavior, first digit for a breaking rewrite or schema-coupled change.
