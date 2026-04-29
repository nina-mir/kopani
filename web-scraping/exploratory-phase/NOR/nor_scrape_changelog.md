# Changelog: `scrape_issue_pieces.py` & `discover_issue_urls.py`

## Purpose

This scraper was built for the exploratory scraping phase of **New Orleans Review** so each piece URL can be stored as its own raw JSON record before heavier normalization work. The intended workflow is repeatable ingestion with `originalurl` treated as the source-level deduplication key, while raw author metadata and piece content are preserved for later review. [file:1]

## Architecture

The script is a two-stage companion to the issue URL discovery step: first collect piece URLs from the issue page, then scrape each piece page into one JSON file per URL. Each output JSON is designed to preserve piece-level metadata, raw author metadata, page-level content, and scrape notes rather than forcing early author or theme normalization. [file:1]

Core output areas:
- `piece`: canonical URL, title, categories, source slug, and issue-order metadata.
- `authors_raw`: displayed author names and `/writer/` links.
- `content`: full `<main>` text, HTML, and poetry subworks when detected.
- `derived` / `scrape_meta`: best-effort bio extraction, parser notes, and rerun metadata. [file:1]

## Intended use case

This script is for **exploratory journal scraping**, not final database ingestion. It is meant to produce reviewable sidecar JSON files that support manual QA, later author resolution, and future parser refinements when edge cases become clearer. [file:1]

## Change history

### `scrape_issue_pieces.py`

### v0.1
- Initial exploratory scraper for one JSON file per piece URL.
- Captured page-level metadata, raw authors, full main text, HTML, JSON-LD, and breadcrumbs.
- Good baseline for fiction, essays, interviews, and art pages. [file:53]

### v0.2
- Added Windows-safe output filenames using a shortened slug plus stable SHA-based suffix.
- Added resume behavior by skipping existing files unless a force overwrite is requested.
- Improved rerun safety for long-title pages and interrupted scraping sessions. [file:1]

### v0.3
- Added targeted multi-poem parsing logic for poetry pages.
- Improved `content.subworks` extraction by using inner headings and `<hr>` separators as structural cues.
- Reduced false author-bio detection on multi-poem pages where the previous parser could capture the tail of the final poem instead of the actual bio. [file:53]

## Known limitation

The scraper now performs well on prose-like pages, but poetry remains the most structurally sensitive template and should still be spot-checked during QA. The main issue discovered in review was not basic metadata capture, but segmenting multiple poems correctly within one piece URL. [file:53]


### discover_issue_urls.py — section detection fix for alternate issue layouts

Updated `gather_section_links()` to support New Orleans Review issue pages that do not use only `h3` section headers.

#### Change
- broadened section detection from `h3`-only to `h2`–`h5`
- added support for bold-only section labels inside `p`/`div` blocks (e.g. `Art`, `Poetry`)
- kept existing anchor filtering and URL deduplication logic unchanged

#### Why
The Iran issue page (`/iran-issue/`) returned `0` piece URLs because its structure used mixed heading styles and bold section labels rather than the `h3` pattern seen in later issues.

#### Result
- issue discovery now works on `/iran-issue/`
- re-tested on Issue 52 and returned the same results as before
- improves compatibility across multiple New Orleans Review issue-layout variants without regression