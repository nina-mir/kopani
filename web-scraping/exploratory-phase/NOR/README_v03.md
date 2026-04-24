# New Orleans Review scraper v0.3

This version keeps the Windows-safe filename logic and resume-by-default behavior, and adds a more specific parser for multi-poem pages.

## What changed

- Output filenames are stable and Windows-safe: `short-slug` + SHA-1 suffix.
- Existing output files are skipped unless you pass `--force`.
- Poetry pages now try to segment `content.subworks` using inner headings and `<hr>` separators.
- The poetry bio detection prefers trailing content after segmented poem blocks.
- `content.text` still preserves the full `<main>` text for the whole page.

## How to run

```bash
python scrape_issue_pieces_v03.py piece_urls.json --outdir pieces_json_v03 --min-delay 2.0 --max-delay 4.0
```

To overwrite an existing output directory:

```bash
python scrape_issue_pieces_v03.py piece_urls.json --outdir pieces_json_v03 --min-delay 2.0 --max-delay 4.0 --force
```

## Recommended QA after rerun

Check these pages first:

- `refugee-farewell`
- `my-mother-tells-me-not-to-walk-alone-...`
- one fiction page like `inheritance`
- one essay like `a-clear-day-for-bombs`
- one art page like `re-stitch-the-past-...`

For the poetry pages, confirm:

- `content.subworks[].title` is correct
- `content.subworks[].text` contains the poem text for that title
- `derived.author_bio_raw` is the bio, not the tail of the second poem

## Notes

This is still an exploratory scraper. Keep the old outputs and compare them against the new ones on the multi-poem cases.
