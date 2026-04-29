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

### To enrich the scraped JSON files consider doing this while doing manual checks:
```python 
"editorial": {
  "tags": ["grief", "revolutionary", "futures"],
  "rail_candidates": ["Poems", "Editor's Picks", "Political"],
  "curation_notes": null
}
```

## Original Content V.0

# New Orleans Review exploratory scraper

This folder contains two small Python scripts:

- `discover_issue_urls.py` — fetches the issue page and writes a JSON manifest of piece URLs.
- `scrape_issue_pieces.py` — reads that manifest and writes one JSON file per piece URL.

## What it captures

For each piece page, the scraper writes a JSON file with:

- original URL and canonical URL
- issue URL, issue label, and issue section
- display title and HTML `<title>` text
- raw author names and `/writer/` profile URLs
- inferred piece type from category tags and issue section
- the entirety of the page's `<main>` text in `content.text`
- the raw HTML for the page's `<main>` block in `content.html`
- JSON-LD, breadcrumbs, and a best-effort author bio field

## 1) Create a virtual environment

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Discover all piece URLs for the issue

```bash
python discover_issue_urls.py "https://www.neworleansreview.org/issue-53-summer-2025/" --out piece_urls.json
```

That creates `piece_urls.json` with issue metadata plus a `pieces` array.

## 3) Scrape every piece into one JSON file per piece

```bash
python scrape_issue_pieces.py piece_urls.json --outdir pieces_json
```

By default, the scraper sleeps 1.5 to 3.0 seconds between piece requests.

You can make it slower:

```bash
python scrape_issue_pieces.py piece_urls.json --outdir pieces_json --min-delay 2.0 --max-delay 4.0
```

## Output layout

```text
nor_scraper/
  discover_issue_urls.py
  scrape_issue_pieces.py
  requirements.txt
  README.md
  piece_urls.json
  pieces_json/
    inheritance.json
    throat-fish.json
    cetacean-stranding.json
    ...
```

## Notes

- This is an exploratory scraper, not a final normalized ingestion pipeline.
- Poetry pages with multiple poems under one URL stay as one JSON file; inner poem titles are captured in `content.subworks` when detected.
- The scraper preserves the full text of the `<main>` tag in `content.text`, which may include the author bio or artist statement when they appear inside `<main>`.
- `derived.author_bio_raw` is best-effort and should be reviewed manually.
