# Kopani MVP Schema Decisions Resolved

Date: 2026-04-13

This note records schema-related decisions that have been resolved for now, so they can guide scraper and database work until fuller scraping rules are finalized.

## Purpose

The MVP needs a repeatable scraping and normalization workflow that a solo founder can maintain without getting buried in edge cases.

The canonical schema remains the reference point, but some practical ingestion decisions need to be handled in a staged way until scraping behavior is better understood.

## Resolved Decisions

### 1. Piece public URL structure

For the MVP, the intended public piece path is:

`/journal-slug/PIECE-ID/PIECE-TITLE`

Example:

`/new-orleans-review/101/a-world-of-objects`

This means the public URL is journal-scoped and includes the internal piece identifier as part of the route.

### 2. Meaning of `pieces.slug`

The `pieces.slug` field is the readable title component of the piece URL.

It is not the full public path by itself.

It is used for readability in the final route, together with the journal slug and piece ID.

### 3. Slug format

For the MVP, the working slug format for `pieces.slug` is:

- lowercase only
- ASCII letters and numbers only
- words separated by hyphens
- punctuation removed
- apostrophes removed
- repeated hyphens collapsed
- no trailing hyphen

Example:

- Title: `A World of Objects`
- Piece slug: `a-world-of-objects`

### 4. Slug uniqueness decision

`pieces.slug` does **not** need to be globally unique across the whole database.

Because the public route includes both `journal-slug` and `PIECE-ID`, the full public path is already unique even when the same title slug appears in multiple journals or multiple pieces.

This means the title slug is mainly a human-readable URL component, not the main unique identifier for the record.

### 5. Piece identity and deduplication

The real unique internal identifier for a piece is `pieces.id`.

The real source-level deduplication key for ingestion remains `originalurl`.

This means:

- `pieces.id` uniquely identifies the Kopani record
- `originalurl` uniquely identifies the source page for scraping and reruns
- `pieces.slug` is primarily for readable URLs

### 6. Database implication for slug

Because of this routing decision, `pieces.slug` should not be treated as a globally unique field in the database.

If the schema is updated to match this decision, the current global uniqueness rule on `pieces.slug` should be removed or relaxed.

A stricter optional alternative would be to make slug uniqueness scoped to a journal, but even that is not strictly necessary if `PIECE-ID` is always present in the public path.

### 7. Author normalization is deferred

Author data is often messy and may not be reliably normalized directly from scraped journal pages.

For the MVP scraping workflow, the scraper should capture raw author-related metadata first rather than forcing immediate inserts into normalized `authors` and `pieceauthors` tables.

### 8. Raw author metadata should be stored per piece

The scraper should collect whatever author information is available on the piece page, such as:

- displayed author name
- author bio
- author URL
- other relevant author metadata found on the page

This raw author data should be stored alongside the scraped piece output in structured JSON, for example a sidecar file such as `PIECE-ID.json`.

### 9. Manual author resolution comes later

Authors can be normalized manually later by reviewing the raw scraped metadata.

Only after manual review, or when a journal has a clean and consistent author structure, should data be inserted confidently into:

- `authors`
- `pieceauthors`

### 10. Themes are deferred

Themes are not essential to the scraping stage.

Theme assignment can be postponed and handled later during manual curation or at the same time author normalization is reviewed.

## Working Rule for Scraping

For now, the scraper should prioritize:

1. piece-level metadata
2. public URL construction support
3. raw author metadata capture
4. clean storage of scraped outputs
5. avoiding premature normalization of messy author or theme data

## Canonical Schema Note

The canonical database schema still includes normalized `authors`, `pieceauthors`, `themes`, and `piecethemes` tables.

However, until scraping behavior is better understood, raw author metadata capture in JSON is the temporary operational rule, themes are deferred, and piece slug uniqueness should follow the route strategy above rather than a global title-slug rule.

## Status

These decisions are temporary working rules for the MVP build phase and should be revisited after initial journal scraping patterns are better understood.